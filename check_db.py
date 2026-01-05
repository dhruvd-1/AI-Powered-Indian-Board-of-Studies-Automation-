"""
Check database contents
"""
import sqlite3

conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables: {tables}")

# Count questions
cursor.execute("SELECT COUNT(*) FROM questions")
count = cursor.fetchone()[0]
print(f"Total questions in DB: {count}")

# Show sample question if exists
if count > 0:
    cursor.execute("SELECT id, question_text, bloom_level, difficulty FROM questions LIMIT 1")
    row = cursor.fetchone()
    print(f"\nSample Question:")
    print(f"  ID: {row[0]}")
    print(f"  Text: {row[1][:100]}...")
    print(f"  Bloom Level: {row[2]}")
    print(f"  Difficulty: {row[3]}")

conn.close()
