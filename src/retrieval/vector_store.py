
"""
Vector store implementations for storing and retrieving text chunks.

Supports both ChromaDB (preferred) and FAISS (fallback).
Each unit gets its own isolated vector database to enforce hard boundaries.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

from config.settings import VECTOR_DB_DIR
from src.retrieval.embeddings import EmbeddingModel


class VectorStore(ABC):
    """Abstract base class for vector database implementations."""
    
    @abstractmethod
    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """Add chunks with their embeddings to the store."""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar chunks."""
        pass
    
    @abstractmethod
    def get_count(self) -> int:
        """Get total number of chunks in store."""
        pass


class ChromaDBStore(VectorStore):
    """
    ChromaDB-based vector store.
    
    Uses persistent ChromaDB for vector storage and retrieval.
    """
    
    def __init__(self, collection_name: str, persist_directory: Path):
        """
        Initialize ChromaDB store.
        
        Args:
            collection_name: Name of collection (e.g., "unit_1")
            persist_directory: Directory to store database
        """
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.collection_name = collection_name
            self.persist_directory = persist_directory
            
            # Create persistent client
            self.client = chromadb.Client(Settings(
                persist_directory=str(persist_directory),
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            print(f"  ✓ ChromaDB collection '{collection_name}' ready")
            
        except ImportError:
            raise ImportError(
                "ChromaDB not installed. Install with: pip install chromadb\n"
                "Or use FAISS instead (will be auto-selected)"
            )
    
    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Add chunks to ChromaDB.
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: Corresponding embedding vectors
        """
        # Prepare data for ChromaDB
        ids = [f"{chunk['unit_id']}_{i}" for i, chunk in enumerate(chunks)]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Add to collection in batches (ChromaDB limit: 41666 per batch)
        batch_size = 5000
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))
            
            self.collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        
        print(f"  ✓ Added {len(chunks)} chunks to ChromaDB")
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """
        Search for similar chunks using ChromaDB.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of chunk dictionaries with similarity scores
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        chunks = []
        for i in range(len(results['documents'][0])):
            chunk = {
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
            }
            chunks.append(chunk)
        
        return chunks
    
    def get_count(self) -> int:
        """Get total number of chunks in collection."""
        return self.collection.count()


class FAISSStore(VectorStore):
    """
    FAISS-based vector store (fallback when ChromaDB unavailable).
    
    Uses FAISS for efficient vector similarity search.
    """
    
    def __init__(self, collection_name: str, persist_directory: Path, dimension: int = 384):
        """
        Initialize FAISS store.
        
        Args:
            collection_name: Name of collection (e.g., "unit_1")
            persist_directory: Directory to store index
            dimension: Embedding vector dimension
        """
        try:
            import faiss
            
            self.collection_name = collection_name
            self.persist_directory = persist_directory
            self.dimension = dimension
            
            # Create index file path
            self.index_path = persist_directory / f"{collection_name}.faiss"
            self.metadata_path = persist_directory / f"{collection_name}_metadata.json"
            
            # Initialize or load index
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            else:
                # Create new index (using inner product, normalized vectors)
                self.index = faiss.IndexFlatIP(dimension)
                self.metadata = []
            
            print(f"  ✓ FAISS index '{collection_name}' ready ({self.get_count()} chunks)")
            
        except ImportError:
            raise ImportError(
                "FAISS not installed. Install with: pip install faiss-cpu"
            )
    
    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Add chunks to FAISS index.
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: Corresponding embedding vectors
        """
        # Convert to numpy array and normalize
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Normalize vectors for cosine similarity with inner product
        faiss.normalize_L2(vectors)
        
        # Add to index
        self.index.add(vectors)
        
        # Store metadata
        for chunk in chunks:
            self.metadata.append({
                'text': chunk['text'],
                'metadata': chunk['metadata']
            })
        
        # Persist to disk
        self._save()
        
        print(f"  ✓ Added {len(chunks)} chunks to FAISS")
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """
        Search for similar chunks using FAISS.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of chunk dictionaries with similarity scores
        """
        # Convert to numpy and normalize
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)
        
        # Search
        k = min(k, self.get_count())  # Don't search for more than available
        if k == 0:
            return []
        
        distances, indices = self.index.search(query_vector, k)
        
        # Format results
        chunks = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):  # Valid index
                chunk = {
                    'text': self.metadata[idx]['text'],
                    'metadata': self.metadata[idx]['metadata'],
                    'similarity_score': float(distances[0][i]),
                }
                chunks.append(chunk)
        
        return chunks
    
    def get_count(self) -> int:
        """Get total number of vectors in index."""
        return self.index.ntotal
    
    def _save(self):
        """Persist index and metadata to disk."""
        import faiss
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save metadata
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)


class VectorStoreManager:
    """
    Manages vector stores for all units.
    
    Automatically selects ChromaDB or FAISS based on availability.
    Creates separate isolated stores for each unit.
    """
    
    def __init__(self, use_chromadb: bool = True):
        """
        Initialize vector store manager.
        
        Args:
            use_chromadb: Try to use ChromaDB first (fallback to FAISS if unavailable)
        """
        self.stores: Dict[str, VectorStore] = {}
        self.embedding_model = EmbeddingModel()
        
        # Determine which backend to use
        self.backend = self._select_backend(use_chromadb)
        print(f"🗄️  Using vector store backend: {self.backend}\n")
    
    def _select_backend(self, prefer_chromadb: bool) -> str:
        """
        Select vector store backend based on availability.
        
        Args:
            prefer_chromadb: Whether to try ChromaDB first
            
        Returns:
            "chromadb" or "faiss"
        """
        if prefer_chromadb:
            try:
                import chromadb
                return "chromadb"
            except ImportError:
                print("⚠️  ChromaDB not available, falling back to FAISS")
        
        try:
            import faiss
            return "faiss"
        except ImportError:
            raise ImportError(
                "Neither ChromaDB nor FAISS is installed!\n"
                "Install one of them:\n"
                "  - ChromaDB: pip install chromadb\n"
                "  - FAISS: pip install faiss-cpu"
            )
    
    def create_unit_store(self, unit_id: str) -> VectorStore:
        """
        Create a vector store for a specific unit.
        
        Args:
            unit_id: Unit identifier (e.g., "unit_1")
            
        Returns:
            VectorStore instance
        """
        # Create unit-specific directory
        unit_dir = VECTOR_DB_DIR / unit_id
        unit_dir.mkdir(parents=True, exist_ok=True)
        
        # Create appropriate store
        if self.backend == "chromadb":
            store = ChromaDBStore(unit_id, unit_dir)
        else:  # faiss
            store = FAISSStore(
                unit_id,
                unit_dir,
                dimension=self.embedding_model.get_dimension()
            )
        
        self.stores[unit_id] = store
        return store
    
    def get_store(self, unit_id: str) -> Optional[VectorStore]:
        """
        Get existing vector store for a unit.
        
        Args:
            unit_id: Unit identifier
            
        Returns:
            VectorStore instance or None if not found
        """
        return self.stores.get(unit_id)
    
    def build_from_chunks(self, chunks_file: Path):
        """
        Build vector stores from chunks.jsonl file.
        
        Args:
            chunks_file: Path to chunks.jsonl file
        """
        print("\n" + "="*60)
        print("STEP 3: MODULE-SCOPED VECTOR DATABASE SETUP")
        print("="*60 + "\n")
        
        # Load chunks
        print(f"📂 Loading chunks from: {chunks_file}")
        chunks_by_unit = self._load_and_group_chunks(chunks_file)
        
        if not chunks_by_unit:
            print("❌ No chunks found!")
            return
        
        print(f"✅ Loaded chunks for {len(chunks_by_unit)} units\n")
        
        # Process each unit
        for unit_id, chunks in chunks_by_unit.items():
            print(f"📚 Building vector store for: {unit_id}")
            print(f"   Chunks to process: {len(chunks)}")
            
            # Create store
            store = self.create_unit_store(unit_id)
            
            # Generate embeddings
            print(f"   Generating embeddings...")
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_model.embed_batch(texts)
            
            # Add to store
            store.add_chunks(chunks, embeddings)
            
            print(f"✅ {unit_id}: {store.get_count()} chunks indexed\n")
        
        print("="*60)
        print("✅ STEP 3 COMPLETE")
        print(f"   Vector stores created for {len(self.stores)} units")
        print(f"   Location: {VECTOR_DB_DIR}")
        print("="*60 + "\n")
    
    def _load_and_group_chunks(self, chunks_file: Path) -> Dict[str, List[Dict]]:
        """
        Load chunks from JSONL and group by unit_id.
        
        Args:
            chunks_file: Path to chunks.jsonl
            
        Returns:
            Dict mapping unit_id to list of chunks
        """
        chunks_by_unit = {}
        
        with open(chunks_file, 'r', encoding='utf-8') as f:
            for line in f:
                chunk = json.loads(line)
                unit_id = chunk['unit_id']
                
                if unit_id not in chunks_by_unit:
                    chunks_by_unit[unit_id] = []
                
                chunks_by_unit[unit_id].append(chunk)
        
        return chunks_by_unit
    
    def test_retrieval(self, unit_id: str, query: str, k: int = 3):
        """
        Test retrieval from a specific unit's vector store.
        
        Args:
            unit_id: Unit to search in
            query: Search query
            k: Number of results
        """
        store = self.get_store(unit_id)
        if not store:
            print(f"❌ No vector store found for {unit_id}")
            return
        
        print(f"\n🔍 Testing retrieval from {unit_id}")
        print(f"   Query: '{query}'")
        print(f"   Top {k} results:\n")
        
        # Embed query
        query_embedding = self.embedding_model.embed_text(query)
        
        # Search
        results = store.search(query_embedding, k=k)
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"   Result {i} (score: {result['similarity_score']:.3f}):")
            print(f"   Source: {result['metadata']['source_file']} (page {result['metadata']['page_number']})")
            print(f"   Text: {result['text'][:200]}...")
            print()