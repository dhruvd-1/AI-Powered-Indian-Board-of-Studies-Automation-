"""
Embedding model wrapper for converting text to vectors.
Uses sentence-transformers for local embeddings.
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import EMBEDDING_MODEL


class EmbeddingModel:
    """
    Wrapper for sentence-transformers embedding model.
    
    Converts text chunks into dense vectors for semantic search.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize embedding model.
        
        Args:
            model_name: Name of sentence-transformers model
        """
        print(f"📦 Loading embedding model: {model_name}")
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            
            # Get embedding dimension
            sample_embedding = self.model.encode(["test"])
            self.embedding_dim = sample_embedding.shape[1]
            
            print(f"✅ Embedding model loaded (dimension: {self.embedding_dim})")
            
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Convert single text to embedding vector.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode([text])[0]
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Convert batch of texts to embeddings.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding vector dimension."""
        return self.embedding_dim