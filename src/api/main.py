"""
FastAPI REST API - Thin wrapper around existing AI pipeline
NO AI LOGIC HERE - Only API endpoints and validation
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import json
from datetime import datetime

# Import existing verified pipeline components
from src.orchestration.question_generator import QuestionGenerator
from src.retrieval.vector_store import VectorStoreManager
from src.database.schema import QuestionBankDB
from config.settings import PROCESSED_DATA_DIR

# Initialize FastAPI
app = FastAPI(
    title="AI Board of Studies Automation API",
    description="REST API for AI-powered question generation system",
    version="1.0.0"
)

# CORS - Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class QuestionGenerateRequest(BaseModel):
    unit_id: str = Field(..., example="unit_1")
    co_id: str = Field(..., example="CO1")
    bloom_level: int = Field(..., ge=1, le=6, example=2)
    difficulty: str = Field(..., example="medium")
    faculty_id: Optional[str] = Field("default", example="faculty_001")

class QuestionResponse(BaseModel):
    id: Optional[int]
    question_text: str
    unit_id: str
    unit_name: Optional[str]
    primary_co: str
    bloom_level: int
    difficulty: str
    compliance_score: Optional[float]
    marks: Optional[int]
    retrieval_sources: Optional[List[Dict]]
    created_at: Optional[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]

# Global instances (loaded once at startup)
_generator = None
_db = None
_syllabus = None

def get_generator():
    """Lazy load question generator"""
    global _generator, _db, _syllabus
    
    if _generator is None:
        try:
            # Load syllabus - try to find any structure file
            syllabus_files = list(Path(PROCESSED_DATA_DIR).glob("*_structure.json"))
            if not syllabus_files:
                print(f"WARNING: No syllabus JSON files found in {PROCESSED_DATA_DIR}")
                raise HTTPException(status_code=500, detail="No syllabus structure files found")
            
            syllabus_file = syllabus_files[0]
            print(f"Loading syllabus from: {syllabus_file}")
            
            with open(syllabus_file, 'r') as f:
                _syllabus = json.load(f)
            
            # Initialize components
            vector_manager = VectorStoreManager()
            _db = QuestionBankDB()
            _generator = QuestionGenerator(vector_manager, _db, _syllabus)
            
            print("✅ Components initialized successfully")
        except HTTPException:
            raise
        except Exception as e:
            print(f"ERROR initializing components: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to initialize components: {str(e)}")
    
    return _generator, _db, _syllabus


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Board of Studies Automation API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        generator, db, syllabus = get_generator()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "operational",
                "vector_store": "operational",
                "question_generator": "operational",
                "syllabus": f"{len(syllabus.get('units', []))} units loaded"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.post("/api/generate-question", response_model=QuestionResponse, tags=["Questions"])
async def generate_question(request: QuestionGenerateRequest):
    """
    Generate a new question using AI pipeline
    
    This endpoint wraps the existing verified pipeline:
    PDF → RAG → Multi-Agent → Database
    """
    try:
        generator, db, syllabus = get_generator()
        
        # Call existing verified pipeline (NO MODIFICATIONS)
        result = generator.generate_question(
            unit_id=request.unit_id,
            co_id=request.co_id,
            bloom_level=request.bloom_level,
            difficulty=request.difficulty,
            faculty_id=request.faculty_id
        )
        
        # Format response - ensure all fields are properly mapped
        response = {
            "id": result.get("question_id") or result.get("id"),
            "question_text": result.get("question_text", ""),
            "unit_id": result.get("unit_id", request.unit_id),
            "unit_name": result.get("unit_name", ""),
            "primary_co": result.get("primary_co", request.co_id),
            "bloom_level": result.get("bloom_level", request.bloom_level),
            "difficulty": result.get("difficulty", request.difficulty),
            "compliance_score": result.get("compliance_score", 0.0),
            "marks": result.get("marks", 0),
            "retrieval_sources": result.get("retrieval_sources", []),
            "created_at": result.get("created_at")
        }
        
        # Ensure id is not None or empty
        if not response["id"]:
            raise ValueError("Question ID was not returned from generator")
        
        return response
        
    except ValueError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/api/questions", tags=["Questions"])
async def get_questions(
    unit_id: Optional[str] = None,
    bloom_level: Optional[int] = None,
    difficulty: Optional[str] = None,
    limit: int = 100
):
    """Get all questions with optional filters"""
    try:
        _, db, _ = get_generator()
        
        # Use existing database methods with increased limit for filtering
        questions = db.get_all_questions(limit=limit * 2)  # Get extra to account for filtering
        
        # Apply filters
        filtered = []
        for q in questions:
            if unit_id and q.unit_id != unit_id:
                continue
            if bloom_level is not None and q.bloom_level != bloom_level:
                continue
            if difficulty and q.difficulty != difficulty:
                continue
            
            # Parse retrieval sources JSON safely
            sources = []
            if q.retrieval_sources:
                try:
                    if isinstance(q.retrieval_sources, str):
                        sources = json.loads(q.retrieval_sources)
                    elif isinstance(q.retrieval_sources, list):
                        sources = q.retrieval_sources
                except (json.JSONDecodeError, TypeError):
                    sources = []
            
            filtered.append({
                "id": q.id,
                "question_text": q.question_text or "",
                "unit_id": q.unit_id or "",
                "unit_name": q.unit_name or "",
                "primary_co": q.primary_co or "",
                "bloom_level": q.bloom_level or 0,
                "difficulty": q.difficulty or "medium",
                "marks": q.marks or 0,
                "compliance_score": q.compliance_score if q.compliance_score is not None else 0.0,
                "created_at": q.created_at.isoformat() if q.created_at else None,
                "retrieval_sources_count": len(sources)
            })
            
            # Limit results
            if len(filtered) >= limit:
                break
        
        return {
            "total": len(filtered),
            "questions": filtered
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")

@app.get("/api/questions/{question_id}", response_model=QuestionResponse, tags=["Questions"])
async def get_question_detail(question_id: int):
    """Get detailed information about a specific question"""
    try:
        _, db, _ = get_generator()
        
        question = db.get_question(question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found")
        
        # Parse JSON fields safely
        sources = []
        if question.retrieval_sources:
            try:
                if isinstance(question.retrieval_sources, str):
                    sources = json.loads(question.retrieval_sources)
                elif isinstance(question.retrieval_sources, list):
                    sources = question.retrieval_sources
            except (json.JSONDecodeError, TypeError):
                sources = []
        
        return {
            "id": question.id,
            "question_text": question.question_text or "",
            "unit_id": question.unit_id or "",
            "unit_name": question.unit_name or "",
            "primary_co": question.primary_co or "",
            "bloom_level": question.bloom_level or 0,
            "difficulty": question.difficulty or "medium",
            "compliance_score": question.compliance_score if question.compliance_score is not None else 0.0,
            "marks": question.marks or 0,
            "retrieval_sources": sources,
            "created_at": question.created_at.isoformat() if question.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch question: {str(e)}")

@app.get("/api/analytics", tags=["Analytics"])
async def get_analytics():
    """Get analytics about question bank"""
    try:
        _, db, syllabus = get_generator()
        
        # Get all questions using the new method
        questions = db.get_all_questions(limit=1000)  # Get more for analytics
        
        if not questions:
            # Return empty analytics if no questions exist yet
            return {
                "total_questions": 0,
                "bloom_distribution": {f"L{i}": 0 for i in range(1, 7)},
                "co_distribution": {},
                "unit_distribution": {},
                "difficulty_distribution": {},
                "average_compliance_score": 0.0,
                "syllabus_units": len(syllabus.get('units', [])),
                "course_outcomes": len(syllabus.get('course_outcomes', []))
            }
        
        # Bloom distribution
        bloom_dist = {f"L{i}": 0 for i in range(1, 7)}
        for q in questions:
            if q.bloom_level and 1 <= q.bloom_level <= 6:
                bloom_dist[f"L{q.bloom_level}"] += 1
        
        # CO distribution
        co_dist = {}
        for q in questions:
            co = q.primary_co or "Unknown"
            co_dist[co] = co_dist.get(co, 0) + 1
        
        # Unit distribution
        unit_dist = {}
        for q in questions:
            unit = q.unit_id or "Unknown"
            unit_dist[unit] = unit_dist.get(unit, 0) + 1
        
        # Difficulty distribution
        diff_dist = {}
        for q in questions:
            diff = q.difficulty or "Unknown"
            diff_dist[diff] = diff_dist.get(diff, 0) + 1
        
        # Average compliance - only include non-null values
        compliances = [q.compliance_score for q in questions if q.compliance_score is not None and q.compliance_score > 0]
        avg_compliance = sum(compliances) / len(compliances) if compliances else 0
        
        return {
            "total_questions": len(questions),
            "bloom_distribution": bloom_dist,
            "co_distribution": co_dist,
            "unit_distribution": unit_dist,
            "difficulty_distribution": diff_dist,
            "average_compliance_score": round(avg_compliance, 2),
            "syllabus_units": len(syllabus.get('units', [])),
            "course_outcomes": len(syllabus.get('course_outcomes', []))
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@app.get("/api/syllabus", tags=["Syllabus"])
async def get_syllabus():
    """Get syllabus structure"""
    try:
        _, _, syllabus = get_generator()
        return syllabus
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
