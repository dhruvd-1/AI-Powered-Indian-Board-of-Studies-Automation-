"""
Step 10: SQLite Question Bank Schema

Stores questions with full metadata and reasoning traces for NBA audits.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path

from config.settings import DATA_DIR

Base = declarative_base()


class Question(Base):
    """Question with full metadata and reasoning trace."""
    
    __tablename__ = 'questions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Question content
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # short_answer, long_answer, mcq, numerical
    expected_answer_length = Column(String(100))
    
    # Educational metadata (from Pedagogy Agent)
    primary_co = Column(String(10), nullable=False)
    secondary_cos = Column(JSON)  # List of COs
    bloom_level = Column(Integer, nullable=False)  # 1-6
    difficulty = Column(String(20), nullable=False)  # easy, medium, hard
    program_outcomes = Column(JSON)  # List of POs
    
    # Assessment parameters
    marks = Column(Integer)
    time_minutes = Column(Integer)
    
    # Syllabus metadata
    course_code = Column(String(20))
    course_name = Column(String(200))
    unit_id = Column(String(20), nullable=False)
    unit_name = Column(String(200))
    
    # Quality metrics
    quality_score = Column(Float)  # 0-100 from Critic
    compliance_score = Column(Float)  # 0-100 from Guardian
    
    # Reasoning trace (for NBA audit)
    retrieval_sources = Column(JSON)  # List of sources used
    draft_version = Column(Text)  # Original draft
    critique_history = Column(JSON)  # List of critiques
    refinement_count = Column(Integer, default=0)
    
    # Human review status
    review_status = Column(String(20), default='pending')  # pending, accepted, edited, rejected
    faculty_id = Column(String(50))
    faculty_edits = Column(Text)  # If edited, what changed
    faculty_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    
    # Usage tracking
    times_used_in_exams = Column(Integer, default=0)
    last_used_date = Column(DateTime)


class ExamPaper(Base):
    """Exam paper with blueprint and question selections."""
    
    __tablename__ = 'exam_papers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Paper metadata
    paper_name = Column(String(200), nullable=False)
    course_code = Column(String(20), nullable=False)
    exam_type = Column(String(50))  # midterm, final, quiz
    academic_year = Column(String(20))
    semester = Column(String(20))
    
    # Blueprint (constraints)
    total_marks = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    blueprint = Column(JSON, nullable=False)  # Detailed constraints
    
    # Question selections
    question_ids = Column(JSON, nullable=False)  # List of question IDs
    
    # Status
    status = Column(String(20), default='draft')  # draft, finalized, published
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    finalized_at = Column(DateTime)
    
    # NBA compliance
    co_coverage = Column(JSON)  # CO distribution
    bloom_distribution = Column(JSON)  # Bloom level distribution
    po_coverage = Column(JSON)  # PO distribution


class FacultyPreference(Base):
    """Faculty preference learning data."""
    
    __tablename__ = 'faculty_preferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    faculty_id = Column(String(50), nullable=False)
    
    # Learned preferences
    preferred_question_style = Column(JSON)  # Patterns from accepted questions
    avoided_patterns = Column(JSON)  # Patterns from rejected questions
    edit_patterns = Column(JSON)  # Common edits made
    
    # Statistics
    total_reviews = Column(Integer, default=0)
    acceptance_rate = Column(Float)
    avg_edits_per_question = Column(Float)
    
    # Preference categories
    tone_preference = Column(String(50))  # formal, conversational, technical
    verbosity_preference = Column(String(50))  # concise, moderate, detailed
    difficulty_bias = Column(String(50))  # easier, as_requested, harder
    
    # Last updated
    updated_at = Column(DateTime, default=datetime.utcnow)


class QuestionBankDB:
    """Database manager for question bank."""
    
    def __init__(self, db_path: Path = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = DATA_DIR / "question_bank.db"
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_question(self, question_data: dict) -> int:
        """
        Add question to database.
        
        Args:
            question_data: Dict with question fields
            
        Returns:
            Question ID
        """
        question = Question(**question_data)
        self.session.add(question)
        self.session.commit()
        return question.id
    
    def get_question(self, question_id: int) -> Question:
        """Get question by ID."""
        return self.session.query(Question).filter_by(id=question_id).first()
    
    def update_question(self, question_id: int, updates: dict):
        """Update question fields."""
        self.session.query(Question).filter_by(id=question_id).update(updates)
        self.session.commit()
    
    def get_questions_by_filters(self, **filters) -> list:
        """
        Get questions matching filters.
        
        Example:
            db.get_questions_by_filters(unit_id='unit_1', bloom_level=2)
        """
        return self.session.query(Question).filter_by(**filters).all()
    
    def get_pending_questions(self) -> list:
        """Get all questions awaiting review."""
        return self.session.query(Question).filter_by(review_status='pending').all()
    
    def get_accepted_questions(self, faculty_id: str = None) -> list:
        """Get accepted questions, optionally filtered by faculty."""
        query = self.session.query(Question).filter_by(review_status='accepted')
        if faculty_id:
            query = query.filter_by(faculty_id=faculty_id)
        return query.all()
    
    def get_question_count(self, **filters) -> int:
        """Count questions matching filters."""
        return self.session.query(Question).filter_by(**filters).count()
    
    def add_exam_paper(self, paper_data: dict) -> int:
        """Add exam paper to database."""
        paper = ExamPaper(**paper_data)
        self.session.add(paper)
        self.session.commit()
        return paper.id
    
    def get_exam_paper(self, paper_id: int) -> ExamPaper:
        """Get exam paper by ID."""
        return self.session.query(ExamPaper).filter_by(id=paper_id).first()
    
    def get_faculty_preferences(self, faculty_id: str) -> FacultyPreference:
        """Get or create faculty preferences."""
        prefs = self.session.query(FacultyPreference).filter_by(faculty_id=faculty_id).first()
        
        if not prefs:
            prefs = FacultyPreference(faculty_id=faculty_id)
            self.session.add(prefs)
            self.session.commit()
        
        return prefs
    
    def update_preferences(self, faculty_id: str, updates: dict):
        """Update faculty preferences."""
        self.session.query(FacultyPreference).filter_by(faculty_id=faculty_id).update(updates)
        self.session.commit()
    
    def close(self):
        """Close database connection."""
        self.session.close()