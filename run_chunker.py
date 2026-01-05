"""
Custom chunker runner using actual PDFs in data/raw/
"""
import sys
sys.path.insert(0, '.')

from src.data_processing.chunker import run_step2_demo

# Use the actual PDF we have
unit_pdfs = {
    "unit_4": ["UNIT 4 EM.pdf"],  # The actual PDF in data/raw
}

print("Running chunker with actual PDF...")
chunks, stats = run_step2_demo(unit_pdfs)

if chunks:
    print(f"\n✅ SUCCESS: Generated {len(chunks)} chunks")
    print(f"\nSample chunk:")
    print(f"  ID: {chunks[0]['chunk_id']}")
    print(f"  Unit: {chunks[0]['metadata']['unit_id']}")
    print(f"  Text preview: {chunks[0]['text'][:150]}...")
else:
    print("\n❌ FAILED: No chunks generated")
