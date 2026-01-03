"""
Configuration settings for AI Question Generation System
"""
from pathlib import Path
from typing import Dict

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_DB_DIR = DATA_DIR / "vector_dbs"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# Ollama Configuration
OLLAMA_MODEL = "llama3.2:3b"  # Change this to your installed model
OLLAMA_BASE_URL = "http://localhost:11434"

# Embedding Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800  # tokens
CHUNK_OVERLAP = 200  # tokens

# Bloom Level → Retrieval Depth Mapping
BLOOM_RETRIEVAL_MAP: Dict[int, int] = {
    1: 2,   # Remember: 2 chunks
    2: 3,   # Understand: 3 chunks
    3: 5,   # Apply: 5 chunks
    4: 8,   # Analyze: 8 chunks
    5: 12,  # Evaluate: 12 chunks
    6: 15,  # Create: 15 chunks
}

# Question Generation Parameters
CRITIC_ITERATIONS = 2  # Number of refinement loops
QUALITY_SCORE_THRESHOLD = 70  # Minimum quality score (0-100)

# Database
DB_PATH = DATA_DIR / "question_bank.db"

# Subjects Configuration (you'll add more subjects here)
SUBJECTS = {
    "AIML": {
        "name": "Artificial Intelligence and Machine Learning",
        "code": "IS353IA",
        "syllabus_file": "ArtificialIntelligence_Syllabus_2022Scheme.pdf",
        "num_units": 5,
        "num_cos": 5,
    },
    # Add DBMS, OS, etc. later
}
