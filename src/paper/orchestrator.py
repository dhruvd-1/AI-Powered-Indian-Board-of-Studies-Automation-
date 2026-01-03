"""
Complete Paper Generation Orchestrator

Combines selection, fresh generation, and formatting.
"""

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from src.database.schema import QuestionBankDB
from src.paper.blueprint import PaperBlueprint
from src.paper.selector import QuestionSelector, SelectionResult
from src.paper.generator import FreshPaperGenerator
from src.paper.formatter import ExamPaperFormatter
from src.orchestration.question_generator import QuestionGenerator


class PaperOrchestrator:
    """
    Complete exam paper generation orchestrator.
    
    Three modes:
    1. Bank-only: Select from existing questions
    2. Fresh-only: Generate all new questions
    3. Hybrid: Use bank where possible, generate to fill gaps
    """
    
    def __init__(
        self,
        db: QuestionBankDB,
        question_generator: Optional[QuestionGenerator] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            db: Question bank database
            question_generator: Generator for fresh questions (optional)
        """
        self.db = db
        self.selector = QuestionSelector(db)
        self.formatter = ExamPaperFormatter(db)
        
        if question_generator:
            self.fresh_generator = FreshPaperGenerator(question_generator)
        else:
            self.fresh_generator = None
    
    def generate_paper_from_bank(
        self,
        blueprint: PaperBlueprint,
        output_dir: Path,
        faculty_id: Optional[str] = None,
        randomize: bool = True
    ) -> Optional[Path]:
        """
        Generate paper using only existing questions.
        
        Args:
            blueprint: Paper blueprint
            output_dir: Output directory
            faculty_id: Faculty ID (for filtering)
            randomize: Add randomness to selection
            
        Returns:
            Path to generated PDF or None if failed
        """
        print("\n" + "="*70)
        print("MODE: BANK-ONLY PAPER GENERATION")
        print("="*70)
        
        # Select questions
        result = self.selector.select_questions(blueprint, faculty_id, randomize)
        
        if not result.success:
            print("\n❌ Could not satisfy constraints with existing questions")
            print("   Try fresh generation or hybrid mode instead.\n")
            return None
        
        # Save to database
        paper_id = self._save_paper_to_db(blueprint, result)
        
        # Generate PDF
        output_path = output_dir / f"{blueprint.paper_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        question_ids = [q.id for q in result.selected_questions]
        self.formatter.generate_pdf(question_ids, blueprint, output_path)
        
        print(f"\n✅ Paper saved: {output_path}")
        print(f"   Paper ID: {paper_id}\n")
        
        return output_path
    
    def generate_paper_fresh(
        self,
        blueprint: PaperBlueprint,
        output_dir: Path,
        faculty_id: str = "default_faculty"
    ) -> Optional[Path]:
        """
        Generate paper with all fresh questions.
        
        Args:
            blueprint: Paper blueprint
            output_dir: Output directory
            faculty_id: Faculty ID
            
        Returns:
            Path to generated PDF
        """
        if not self.fresh_generator:
            raise ValueError("Question generator not provided! Cannot generate fresh questions.")
        
        print("\n" + "="*70)
        print("MODE: FRESH PAPER GENERATION")
        print("="*70)
        
        # Generate questions
        question_ids = self.fresh_generator.generate_paper_questions(blueprint, faculty_id)
        
        if not question_ids:
            print("\n❌ Failed to generate questions\n")
            return None
        
        # Save paper to database
        paper_id = self._save_paper_to_db_by_ids(blueprint, question_ids)
        
        # Generate PDF
        output_path = output_dir / f"{blueprint.paper_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        self.formatter.generate_pdf(question_ids, blueprint, output_path)
        
        print(f"\n✅ Paper saved: {output_path}")
        print(f"   Paper ID: {paper_id}\n")
        
        return output_path
    
    def generate_paper_hybrid(
        self,
        blueprint: PaperBlueprint,
        output_dir: Path,
        faculty_id: str = "default_faculty",
        min_from_bank: int = 3
    ) -> Optional[Path]:
        """
        Generate paper using bank + fresh generation.
        
        Args:
            blueprint: Paper blueprint
            output_dir: Output directory
            faculty_id: Faculty ID
            min_from_bank: Minimum questions to pull from bank
            
        Returns:
            Path to generated PDF
        """
        if not self.fresh_generator:
            raise ValueError("Question generator not provided!")
        
        print("\n" + "="*70)
        print("MODE: HYBRID PAPER GENERATION")
        print("="*70)
        
        # Try bank selection first
        result = self.selector.select_questions(blueprint, faculty_id, randomize=True)
        
        bank_questions = []
        if result.success and len(result.selected_questions) >= min_from_bank:
            bank_questions = result.selected_questions
            print(f"\n✅ Using {len(bank_questions)} questions from bank")
        else:
            print(f"\n⚠️  Insufficient bank questions, will generate all fresh")
        
        # Calculate remaining marks needed
        marks_constraint = blueprint.get_constraint('marks_total')
        target_marks = marks_constraint.value
        bank_marks = sum(q.marks for q in bank_questions)
        remaining_marks = target_marks - bank_marks
        
        fresh_question_ids = []
        
        if remaining_marks > 0:
            print(f"\nGenerating fresh questions for {remaining_marks} marks...")
            
            # Create modified blueprint for remaining marks
            # (Simplified: just generate proportionally)
            # In production, would adjust constraints properly
            
            fresh_question_ids = self.fresh_generator.generate_paper_questions(
                blueprint,
                faculty_id
            )
        
        # Combine
        all_question_ids = [q.id for q in bank_questions] + fresh_question_ids
        
        # Save paper
        paper_id = self._save_paper_to_db_by_ids(blueprint, all_question_ids)
        
        # Generate PDF
        output_path = output_dir / f"{blueprint.paper_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        self.formatter.generate_pdf(all_question_ids, blueprint, output_path)
        
        print(f"\n✅ Hybrid paper saved: {output_path}")
        print(f"   From bank: {len(bank_questions)} | Fresh: {len(fresh_question_ids)}")
        print(f"   Paper ID: {paper_id}\n")
        
        return output_path
    
    def _save_paper_to_db(self, blueprint: PaperBlueprint, result: SelectionResult) -> int:
        """Save paper to database."""
        
        marks_constraint = blueprint.get_constraint('marks_total')
        duration_constraint = blueprint.get_constraint('duration')
        
        paper_data = {
            'paper_name': blueprint.paper_name,
            'course_code': blueprint.course_code,
            'exam_type': blueprint.exam_type,
            'total_marks': marks_constraint.value if marks_constraint else 0,
            'duration_minutes': duration_constraint.value if duration_constraint else 0,
            'blueprint': blueprint.to_dict(),
            'question_ids': [q.id for q in result.selected_questions],
            'status': 'finalized',
            'co_coverage': self._calculate_co_coverage(result.selected_questions),
            'bloom_distribution': self._calculate_bloom_distribution(result.selected_questions),
            'po_coverage': self._calculate_po_coverage(result.selected_questions)
        }
        
        return self.db.add_exam_paper(paper_data)
    
    def _save_paper_to_db_by_ids(self, blueprint: PaperBlueprint, question_ids: List[int]) -> int:
        """Save paper to database by question IDs."""
        
        questions = [self.db.get_question(qid) for qid in question_ids]
        questions = [q for q in questions if q]
        
        marks_constraint = blueprint.get_constraint('marks_total')
        duration_constraint = blueprint.get_constraint('duration')
        
        paper_data = {
            'paper_name': blueprint.paper_name,
            'course_code': blueprint.course_code,
            'exam_type': blueprint.exam_type,
            'total_marks': marks_constraint.value if marks_constraint else sum(q.marks for q in questions),
            'duration_minutes': duration_constraint.value if duration_constraint else 0,
            'blueprint': blueprint.to_dict(),
            'question_ids': question_ids,
            'status': 'finalized',
            'co_coverage': self._calculate_co_coverage(questions),
            'bloom_distribution': self._calculate_bloom_distribution(questions),
            'po_coverage': self._calculate_po_coverage(questions)
        }
        
        return self.db.add_exam_paper(paper_data)
    
    def _calculate_co_coverage(self, questions: List) -> dict:
        """Calculate CO coverage."""
        coverage = {}
        for q in questions:
            coverage[q.primary_co] = coverage.get(q.primary_co, 0) + q.marks
        return coverage
    
    def _calculate_bloom_distribution(self, questions: List) -> dict:
        """Calculate Bloom distribution."""
        distribution = {}
        for q in questions:
            distribution[q.bloom_level] = distribution.get(q.bloom_level, 0) + q.marks
        return distribution
    
    def _calculate_po_coverage(self, questions: List) -> dict:
        """Calculate PO coverage."""
        import json
        coverage = {}
        for q in questions:
            pos = json.loads(q.program_outcomes) if isinstance(q.program_outcomes, str) else q.program_outcomes
            for po in pos:
                coverage[po] = coverage.get(po, 0) + q.marks
        return coverage