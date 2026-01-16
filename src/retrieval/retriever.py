"""
Step 4: Bloom-Adaptive Retrieval Logic

Retrieves chunks from module-scoped vector databases with adaptive depth
based on Bloom's taxonomy level.

Key principle: Higher Bloom levels need more context
- L1 (Remember): 2-3 chunks (narrow factual recall)
- L6 (Create): 12-15 chunks (broad synthesis)
"""

from typing import List, Dict, Optional
from pathlib import Path
import json

from config.settings import BLOOM_RETRIEVAL_MAP, PROCESSED_DATA_DIR
from src.retrieval.vector_store import VectorStoreManager
from src.retrieval.embeddings import EmbeddingModel


class BloomAdaptiveRetriever:
    """
    Retrieves content with depth adapted to Bloom's taxonomy level.
    
    Enforces hard module boundaries by only querying the specified unit's
    vector database.
    """
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        """
        Initialize retriever with vector store manager.
        
        Args:
            vector_store_manager: Manager with loaded vector stores
        """
        self.store_manager = vector_store_manager
        self.embedding_model = vector_store_manager.embedding_model
        
        # Load syllabus structure for validation
        self.syllabus_structure = self._load_syllabus_structure()
    
    def _load_syllabus_structure(self) -> Dict:
        """Load syllabus structure for unit validation."""
        # Look for any syllabus structure JSON
        structure_files = list(PROCESSED_DATA_DIR.glob("*_structure.json"))
        
        if not structure_files:
            print("⚠️ No syllabus structure found, unit validation disabled")
            return {}
        
        with open(structure_files[0], 'r') as f:
            return json.load(f)
    
    def retrieve(
        self,
        query: str,
        unit_id: str,
        bloom_level: int,
        k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve chunks from specified unit with Bloom-adaptive depth.
        
        Args:
            query: Search query text
            unit_id: Unit to search in (e.g., "unit_1")
            bloom_level: Bloom's taxonomy level (1-6)
            k: Optional override for number of chunks (uses Bloom map if None)
            
        Returns:
            List of retrieved chunks with metadata and scores
            
        Raises:
            ValueError: If unit_id or bloom_level is invalid
        """
        # Validate inputs
        self._validate_unit(unit_id)
        self._validate_bloom_level(bloom_level)
        
        # Get vector store for this unit
        store = self.store_manager.get_store(unit_id)
        if not store:
            raise ValueError(f"No vector store found for {unit_id}")
        
        # Determine retrieval depth
        if k is None:
            k = BLOOM_RETRIEVAL_MAP.get(bloom_level, 5)
        
        # Ensure we don't request more chunks than exist
        available_chunks = store.get_count()
        k = min(k, available_chunks)
        
        if k == 0:
            print(f"⚠️ No chunks available in {unit_id}")
            return []
        
        # Embed query
        query_embedding = self.embedding_model.embed_text(query)
        
        # Retrieve from unit-specific store
        results = store.search(query_embedding, k=k)
        
        # Add retrieval metadata
        for result in results:
            result['retrieval_metadata'] = {
                'query': query,
                'unit_id': unit_id,
                'bloom_level': bloom_level,
                'chunks_requested': k,
                'chunks_retrieved': len(results),
            }
        
        return results
    
    def _validate_unit(self, unit_id: str):
        """
        Validate that unit_id is valid.
        
        Args:
            unit_id: Unit identifier to validate
            
        Raises:
            ValueError: If unit is invalid
        """
        # Check if vector store exists for this unit
        if not self.store_manager.get_store(unit_id):
            available_units = list(self.store_manager.stores.keys())
            
            # If no units available at all, create empty store for requested unit
            if not available_units:
                print(f"⚠️  No vector stores found. Creating empty store for {unit_id}")
                self.store_manager.create_unit_store(unit_id)
                return
            
            # If requested unit doesn't exist but others do, try to create it
            print(f"⚠️  Unit {unit_id} not found. Creating empty store.")
            self.store_manager.create_unit_store(unit_id)
    
    def _validate_bloom_level(self, bloom_level: int):
        """
        Validate Bloom's taxonomy level.
        
        Args:
            bloom_level: Level to validate (should be 1-6)
            
        Raises:
            ValueError: If level is invalid
        """
        if bloom_level not in range(1, 7):
            raise ValueError(
                f"Invalid bloom_level: {bloom_level}\n"
                f"Must be between 1-6:\n"
                f"  1: Remember, 2: Understand, 3: Apply\n"
                f"  4: Analyze, 5: Evaluate, 6: Create"
            )
    
    def retrieve_multi_query(
        self,
        queries: List[str],
        unit_id: str,
        bloom_level: int
    ) -> List[Dict]:
        """
        Retrieve chunks using multiple related queries and merge results.
        
        Useful for complex questions that need multiple perspectives.
        
        Args:
            queries: List of query strings
            unit_id: Unit to search in
            bloom_level: Bloom's taxonomy level
            
        Returns:
            Merged and deduplicated list of chunks
        """
        all_results = []
        seen_texts = set()
        
        for query in queries:
            results = self.retrieve(query, unit_id, bloom_level)
            
            # Deduplicate by text content
            for result in results:
                text = result['text']
                if text not in seen_texts:
                    all_results.append(result)
                    seen_texts.add(text)
        
        # Sort by similarity score
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit to Bloom-appropriate size
        k = BLOOM_RETRIEVAL_MAP.get(bloom_level, 5)
        return all_results[:k]
    
    def get_retrieval_stats(self, unit_id: str) -> Dict:
        """
        Get statistics about retrieval for a unit.
        
        Args:
            unit_id: Unit to get stats for
            
        Returns:
            Dict with retrieval statistics
        """
        store = self.store_manager.get_store(unit_id)
        if not store:
            return {}
        
        # Get unit info from syllabus
        unit_info = {}
        if self.syllabus_structure:
            units = self.syllabus_structure.get('units', [])
            for unit in units:
                if unit['unit_id'] == unit_id:
                    unit_info = unit
                    break
        
        return {
            'unit_id': unit_id,
            'unit_name': unit_info.get('title', 'Unknown'),
            'total_chunks': store.get_count(),
            'bloom_retrieval_map': BLOOM_RETRIEVAL_MAP,
        }


class RetrievalTracker:
    """
    Tracks retrieval history for reasoning trace generation.
    
    Used in Step 9 (orchestration) to log which chunks were retrieved
    and why they were selected.
    """
    
    def __init__(self):
        """Initialize empty retrieval history."""
        self.history: List[Dict] = []
    
    def log_retrieval(
        self,
        query: str,
        unit_id: str,
        bloom_level: int,
        results: List[Dict]
    ):
        """
        Log a retrieval operation.
        
        Args:
            query: Search query used
            unit_id: Unit searched
            bloom_level: Bloom level used
            results: Retrieved chunks
        """
        log_entry = {
            'query': query,
            'unit_id': unit_id,
            'bloom_level': bloom_level,
            'chunks_retrieved': len(results),
            'top_scores': [r['similarity_score'] for r in results[:3]],
            'sources': [
                {
                    'file': r['metadata']['source_file'],
                    'page': r['metadata']['page_number']
                }
                for r in results[:3]
            ]
        }
        
        self.history.append(log_entry)
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of retrieval history.
        
        Returns:
            Formatted string summary
        """
        if not self.history:
            return "No retrieval operations logged"
        
        summary_parts = []
        
        for i, entry in enumerate(self.history, 1):
            sources_str = ', '.join([f"p.{s['page']}" for s in entry['sources']])
            summary_parts.append(
                f"Retrieval {i}:\n"
                f"  Query: '{entry['query']}'\n"
                f"  Unit: {entry['unit_id']}\n"
                f"  Bloom Level: {entry['bloom_level']}\n"
                f"  Retrieved: {entry['chunks_retrieved']} chunks\n"
                f"  Top sources: {sources_str}"
            )
        
        return "\n\n".join(summary_parts)
    
    def clear(self):
        """Clear retrieval history."""
        self.history.clear()
