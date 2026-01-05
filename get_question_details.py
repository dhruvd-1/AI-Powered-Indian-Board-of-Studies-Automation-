"""
Get detailed question information from database
"""
import sqlite3
import json

conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# Get the most recent question
cursor.execute("""
    SELECT id, question_text, unit_id, primary_co, bloom_level, difficulty, 
           compliance_score, retrieval_sources, created_at
    FROM questions 
    ORDER BY id DESC 
    LIMIT 1
""")

row = cursor.fetchone()

if row:
    print("="*80)
    print("MOST RECENT GENERATED QUESTION")
    print("="*80)
    print(f"\nQuestion ID: {row[0]}")
    print(f"Created: {row[8]}")
    print(f"\nQuestion Text:")
    print(f"  {row[1]}")
    print(f"\nMetadata:")
    print(f"  Unit ID: {row[2]}")
    print(f"  CO: {row[3]}")
    print(f"  Bloom Level: {row[4]}")
    print(f"  Difficulty: {row[5]}")
    print(f"  Compliance Score: {row[6]}/100")
    
    if row[7]:
        sources = json.loads(row[7])
        print(f"\nRetrieval Sources ({len(sources)} chunks):")
        for i, src in enumerate(sources, 1):
            print(f"  {i}. {src.get('file', 'N/A')} (page {src.get('page', 'N/A')})")
            if 'text' in src:
                print(f"     Preview: {src['text'][:100]}...")
    
    print("\n" + "="*80)

conn.close()
