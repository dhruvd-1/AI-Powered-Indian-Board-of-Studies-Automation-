"""
Step 21: Asynchronous Background Job Processing

Handles long-running tasks like batch question generation
and paper creation without blocking the UI.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import threading
import time

from src.database.schema import QuestionBankDB
from src.orchestration.question_generator import QuestionGenerator


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Represents a background job."""
    
    def __init__(
        self,
        job_id: str,
        job_type: str,
        parameters: Dict,
        created_by: str
    ):
        self.job_id = job_id
        self.job_type = job_type
        self.parameters = parameters
        self.created_by = created_by
        self.status = JobStatus.PENDING
        self.progress = 0
        self.total = 100
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict:
        """Serialize job to dict."""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'parameters': self.parameters,
            'created_by': self.created_by,
            'status': self.status.value,
            'progress': self.progress,
            'total': self.total,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class JobQueue:
    """
    Simple in-memory job queue with background worker.
    
    For production, use Celery, RQ, or similar.
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.worker_thread = None
        self.running = False
    
    def start_worker(self):
        """Start background worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("✅ Job worker started")
    
    def stop_worker(self):
        """Stop background worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def submit_job(
        self,
        job_type: str,
        parameters: Dict,
        created_by: str
    ) -> str:
        """
        Submit a new job to the queue.
        
        Args:
            job_type: Type of job (e.g., 'generate_questions', 'create_paper')
            parameters: Job parameters
            created_by: User/faculty ID
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            job_type=job_type,
            parameters=parameters,
            created_by=created_by
        )
        
        self.jobs[job_id] = job
        
        print(f"📋 Job submitted: {job_id} ({job_type})")
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str) -> List[Job]:
        """Get all jobs for a user."""
        return [j for j in self.jobs.values() if j.created_by == user_id]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.jobs.get(job_id)
        
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            return True
        
        return False
    
    def _worker_loop(self):
        """Background worker loop."""
        
        while self.running:
            # Find next pending job
            pending_jobs = [
                j for j in self.jobs.values()
                if j.status == JobStatus.PENDING
            ]
            
            if pending_jobs:
                job = pending_jobs[0]
                self._execute_job(job)
            else:
                time.sleep(1)  # Wait for new jobs
    
    def _execute_job(self, job: Job):
        """Execute a job."""
        
        print(f"🚀 Starting job: {job.job_id} ({job.job_type})")
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            if job.job_type == 'generate_questions':
                result = self._execute_generate_questions(job)
            elif job.job_type == 'create_paper':
                result = self._execute_create_paper(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
            print(f"✅ Job completed: {job.job_id}")
        
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            
            print(f"❌ Job failed: {job.job_id} - {e}")
    
    def _execute_generate_questions(self, job: Job) -> Dict:
        """Execute question generation job."""
        
        params = job.parameters
        
        # Initialize components
        from src.retrieval.vector_store import VectorStoreManager
        from config.settings import PROCESSED_DATA_DIR, DATA_DIR
        
        chunks_file = PROCESSED_DATA_DIR / "chunks.jsonl"
        manager = VectorStoreManager(use_chromadb=False)
        manager.build_from_chunks(chunks_file)
        
        db_path = DATA_DIR / "question_bank.db"
        db = QuestionBankDB(db_path)
        
        # Load syllabus
        structure_files = list(PROCESSED_DATA_DIR.glob("*_structure.json"))
        with open(structure_files[0], 'r') as f:
            syllabus = json.load(f)
        
        generator = QuestionGenerator(manager, db, syllabus)
        
        # Generate questions
        count = params.get('count', 1)
        question_ids = []
        
        job.total = count
        
        for i in range(count):
            try:
                result = generator.generate_question(
                    unit_id=params['unit_id'],
                    co_id=params['co_id'],
                    bloom_level=params['bloom_level'],
                    difficulty=params['difficulty'],
                    faculty_id=job.created_by
                )
                
                question_ids.append(result['question_id'])
                job.progress = i + 1
                
            except Exception as e:
                print(f"Error generating question {i+1}: {e}")
        
        db.close()
        
        return {
            'generated': len(question_ids),
            'question_ids': question_ids
        }
    
    def _execute_create_paper(self, job: Job) -> Dict:
        """Execute paper creation job."""
        
        params = job.parameters
        
        # Initialize components
        from src.retrieval.vector_store import VectorStoreManager
        from src.paper.orchestrator import PaperOrchestrator
        from src.paper.blueprint import PaperBlueprint
        from config.settings import PROCESSED_DATA_DIR, DATA_DIR
        
        db_path = DATA_DIR / "question_bank.db"
        db = QuestionBankDB(db_path)
        
        # Create blueprint
        blueprint = PaperBlueprint.from_dict(params['blueprint'])
        
        # Initialize orchestrator
        if params['mode'] != 'bank_only':
            chunks_file = PROCESSED_DATA_DIR / "chunks.jsonl"
            manager = VectorStoreManager(use_chromadb=False)
            manager.build_from_chunks(chunks_file)
            
            structure_files = list(PROCESSED_DATA_DIR.glob("*_structure.json"))
            with open(structure_files[0], 'r') as f:
                syllabus = json.load(f)
            
            generator = QuestionGenerator(manager, db, syllabus)
            orchestrator = PaperOrchestrator(db, generator)
        else:
            orchestrator = PaperOrchestrator(db)
        
        # Generate paper
        output_dir = DATA_DIR / "papers"
        output_dir.mkdir(exist_ok=True)
        
        if params['mode'] == 'bank_only':
            pdf_path = orchestrator.generate_paper_from_bank(
                blueprint=blueprint,
                output_dir=output_dir,
                faculty_id=job.created_by
            )
        elif params['mode'] == 'fresh':
            pdf_path = orchestrator.generate_paper_fresh(
                blueprint=blueprint,
                output_dir=output_dir,
                faculty_id=job.created_by
            )
        else:  # hybrid
            pdf_path = orchestrator.generate_paper_hybrid(
                blueprint=blueprint,
                output_dir=output_dir,
                faculty_id=job.created_by
            )
        
        db.close()
        
        return {
            'pdf_path': str(pdf_path) if pdf_path else None,
            'paper_name': blueprint.paper_name
        }


# Global job queue instance
_job_queue = None


def get_job_queue() -> JobQueue:
    """Get global job queue instance."""
    global _job_queue
    
    if _job_queue is None:
        _job_queue = JobQueue()
        _job_queue.start_worker()
    
    return _job_queue