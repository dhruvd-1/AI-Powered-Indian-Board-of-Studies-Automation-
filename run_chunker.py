"""
Custom chunker runner using actual PDFs in data/raw/
"""
import sys
sys.path.insert(0, '.')

from src.data_processing.chunker import run_step2_demo

# Map all available PDFs to units
unit_pdfs = {
    "unit_1": ["AIML Unit-1.pdf"],
    "unit_2": ["AIML Unit-2.pdf"],
    "unit_3": ["PPT.pdf"],  # Using PPT.pdf for unit 3
    "unit_4": ["PPT.pdf"],  # Using PPT.pdf for unit 4 as well (as fallback)
}

print("Running chunker with actual PDFs for all units...")
chunks, stats = run_step2_demo(unit_pdfs)

if chunks:
    print(f"\n✅ SUCCESS: Generated {len(chunks)} chunks")
    print(f"\nSample chunk:")
    print(f"  ID: {chunks[0]['chunk_id']}")
    print(f"  Unit: {chunks[0]['metadata']['unit_id']}")
    print(f"  Text preview: {chunks[0]['text'][:150]}...")
    
    # Show distribution by unit
    from collections import Counter
    unit_dist = Counter(c['metadata']['unit_id'] for c in chunks)
    print(f"\nChunks per unit:")
    for unit, count in sorted(unit_dist.items()):
        print(f"  {unit}: {count} chunks")
else:
    print("\n❌ FAILED: No chunks generated")
