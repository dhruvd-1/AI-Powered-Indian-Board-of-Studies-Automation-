"""
Build vector database from chunks.jsonl
"""
import sys
sys.path.insert(0, '.')

from pathlib import Path
from src.retrieval.vector_store import VectorStoreManager
from config.settings import PROCESSED_DATA_DIR

print("\n" + "="*60)
print("VECTOR DATABASE CREATION")
print("="*60 + "\n")

# Initialize vector store manager
print("📦 Initializing vector store manager...")
manager = VectorStoreManager()

# Path to chunks file
chunks_file = PROCESSED_DATA_DIR / "chunks.jsonl"

if not chunks_file.exists():
    print(f"❌ chunks.jsonl not found at {chunks_file}")
    print("   Run chunking script first!")
    sys.exit(1)

print(f"✓ Found chunks file: {chunks_file}\n")

# Build vector databases for all units
print("🔨 Building vector databases...")
manager.build_from_chunks(chunks_file)

print("\n" + "="*60)
print("✅ VECTOR DATABASE BUILD COMPLETE")
print("="*60)
