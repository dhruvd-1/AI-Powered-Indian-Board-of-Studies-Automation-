"""Quick script to build vector databases for units 2, 3, 4"""
import json
from pathlib import Path
from src.retrieval.embeddings import EmbeddingModel
from src.retrieval.vector_store import ChromaDBStore

print("🚀 Quick Vector DB Builder")
print("=" * 60)

# Load chunks
chunks_file = Path("data/processed/chunks.jsonl")
if not chunks_file.exists():
    print("❌ No chunks file found!")
    exit(1)

# Read all chunks
print(f"\n📖 Reading chunks from {chunks_file}...")
chunks_by_unit = {}
with open(chunks_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                chunk = json.loads(line)
                unit_id = chunk.get('unit_id', 'unknown')
                if unit_id not in chunks_by_unit:
                    chunks_by_unit[unit_id] = []
                chunks_by_unit[unit_id].append(chunk)
            except:
                continue

print(f"   Found chunks for units: {sorted(chunks_by_unit.keys())}")
for unit, chunks in chunks_by_unit.items():
    print(f"   - {unit}: {len(chunks)} chunks")

# Initialize embedding model
print("\n🤖 Loading embedding model...")
embedder = EmbeddingModel()
vector_dbs_dir = Path("data/vector_dbs")

# Build each unit
for unit_id in sorted(chunks_by_unit.keys()):
    chunks = chunks_by_unit[unit_id]
    print(f"\n{'='*60}")
    print(f"📦 Building vector DB for {unit_id}")
    print(f"{'='*60}")
    
    try:
        # Check if unit store exists
        unit_dir = vector_dbs_dir / unit_id
        if unit_dir.exists():
            print(f"   ⚠️  Vector DB already exists for {unit_id}, skipping...")
            continue
        
        # Create ChromaDB store
        print(f"   Creating ChromaDB collection for {unit_id}...")
        store = ChromaDBStore(
            collection_name=unit_id,
            persist_directory=vector_dbs_dir
        )
        
        # Prepare data
        print(f"   Generating embeddings for {len(chunks)} chunks...")
        texts = [c.get('text', c.get('content', '')) for c in chunks]
        
        # Reformat chunks for ChromaDBStore
        formatted_chunks = []
        for c in chunks:
            formatted_chunks.append({
                'text': c.get('text', c.get('content', '')),
                'unit_id': c.get('unit_id', ''),
                'metadata': {
                    'chunk_id': c.get('chunk_id', ''),
                    'unit_id': c.get('unit_id', ''),
                    'source_file': c.get('source', c.get('source_file', '')),
                    'page': str(c.get('page', 0))
                }
            })
        
        # Generate embeddings
        embeddings = embedder.embed_batch(texts)
        
        # Add to store
        print(f"   Adding to ChromaDB...")
        store.add_chunks(formatted_chunks, embeddings)
        
        print(f"   ✅ {unit_id} completed - {len(chunks)} chunks added")
        
    except Exception as e:
        print(f"   ❌ Error building {unit_id}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("✅ Vector DB build complete!")
print("="*60)
