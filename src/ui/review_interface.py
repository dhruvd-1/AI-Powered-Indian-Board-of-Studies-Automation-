"""
Step 11: Human-in-the-Loop Review Interface

Simple CLI interface for Accept/Edit/Reject workflow.
"""

from datetime import datetime
from typing import Dict, List
import json

from src.database.schema import QuestionBankDB, Question


class ReviewInterface:
    """
    Command-line interface for reviewing generated questions.
    
    Workflow:
    1. Show pending question
    2. Faculty chooses: Accept / Edit / Reject
    3. Record decision + feedback
    4. Update preference tracker
    """
    
    def __init__(self, db: QuestionBankDB, faculty_id: str):
        """
        Initialize review interface.
        
        Args:
            db: Question bank database
            faculty_id: Faculty identifier
        """
        self.db = db
        self.faculty_id = faculty_id
    
    def start_review_session(self):
        """Start interactive review session."""
        
        print("\n" + "="*70)
        print(" "*20 + "QUESTION REVIEW SESSION")
        print("="*70)
        print(f"Faculty: {self.faculty_id}\n")
        
        # Get pending questions
        pending = self.db.get_pending_questions()
        
        if not pending:
            print("✅ No pending questions to review!")
            print("\nGenerate new questions first using the Question Generator.\n")
            return
        
        print(f"Found {len(pending)} pending question(s)\n")
        
        reviewed_count = 0
        
        for i, question in enumerate(pending, 1):
            print(f"\n{'='*70}")
            print(f"QUESTION {i}/{len(pending)} (ID: {question.id})")
            print(f"{'='*70}\n")
            
            # Display question
            self._display_question(question)
            
            # Get faculty decision
            decision = self._get_faculty_decision()
            
            if decision == 'skip':
                print("⏭️  Skipped\n")
                continue
            elif decision == 'quit':
                print("\n👋 Review session ended\n")
                break
            
            # Process decision
            self._process_decision(question, decision)
            reviewed_count += 1
            
            print(f"\n✅ Question {question.id} {decision}!\n")
        
        # Summary
        print("\n" + "="*70)
        print("REVIEW SESSION SUMMARY")
        print("="*70)
        print(f"Questions reviewed: {reviewed_count}/{len(pending)}")
        
        # Show acceptance rate
        accepted = self.db.get_question_count(
            faculty_id=self.faculty_id,
            review_status='accepted'
        )
        total_reviewed = self.db.get_question_count(faculty_id=self.faculty_id)
        
        if total_reviewed > 0:
            acceptance_rate = (accepted / total_reviewed) * 100
            print(f"Overall acceptance rate: {acceptance_rate:.1f}%")
        
        print("="*70 + "\n")
    
    def _display_question(self, q: Question):
        """Display question details."""
        
        print(f"📝 Question:")
        print("-" * 70)
        print(f"{q.question_text}")
        print("-" * 70)
        
        print(f"\n📊 Metadata:")
        print(f"  Unit: {q.unit_name} ({q.unit_id})")
        print(f"  CO: {q.primary_co} | Bloom: L{q.bloom_level} | Difficulty: {q.difficulty}")
        print(f"  Type: {q.question_type} | Length: {q.expected_answer_length}")
        print(f"  Marks: {q.marks} | Time: {q.time_minutes} min")
        
        print(f"\n⚡ Quality Metrics:")
        print(f"  Quality Score: {q.quality_score}/100")
        print(f"  Compliance Score: {q.compliance_score}/100")
        print(f"  Refinements: {q.refinement_count} iteration(s)")
        
        print(f"\n📚 Sources:")
        sources = json.loads(q.retrieval_sources) if isinstance(q.retrieval_sources, str) else q.retrieval_sources
        for src in sources[:3]:
            print(f"  • {src['file']} (page {src['page']})")
        
        print()
    
    def _get_faculty_decision(self) -> str:
        """Get faculty decision via CLI."""
        
        while True:
            print("Choose action:")
            print("  [A] Accept")
            print("  [E] Edit")
            print("  [R] Reject")
            print("  [S] Skip (review later)")
            print("  [Q] Quit session")
            
            choice = input("\nYour choice: ").strip().upper()
            
            if choice in ['A', 'ACCEPT']:
                return 'accepted'
            elif choice in ['E', 'EDIT']:
                return 'edited'
            elif choice in ['R', 'REJECT']:
                return 'rejected'
            elif choice in ['S', 'SKIP']:
                return 'skip'
            elif choice in ['Q', 'QUIT']:
                return 'quit'
            else:
                print("❌ Invalid choice. Try again.\n")
    
    def _process_decision(self, question: Question, decision: str):
        """Process faculty decision and update database."""
        
        updates = {
            'review_status': decision,
            'reviewed_at': datetime.utcnow(),
            'faculty_id': self.faculty_id
        }
        
        if decision == 'edited':
            # Get edited question
            print("\n" + "-"*70)
            print("Enter edited question (or press Enter to keep original):")
            print("-"*70)
            edited_text = input().strip()
            
            if edited_text:
                updates['faculty_edits'] = json.dumps({
                    'original': question.question_text,
                    'edited': edited_text,
                    'timestamp': datetime.utcnow().isoformat()
                })
                updates['question_text'] = edited_text
        
        # Get optional feedback
        print("\nOptional feedback (press Enter to skip):")
        feedback = input().strip()
        if feedback:
            updates['faculty_feedback'] = feedback
        
        # Update database
        self.db.update_question(question.id, updates)


def quick_review_cli(db_path=None):
    """Quick CLI entry point for question review."""
    
    from src.database.schema import QuestionBankDB
    
    db = QuestionBankDB(db_path)
    
    print("\n" + "="*70)
    print("QUESTION BANK REVIEW SYSTEM")
    print("="*70)
    
    faculty_id = input("\nEnter your faculty ID (or press Enter for 'default_faculty'): ").strip()
    if not faculty_id:
        faculty_id = "default_faculty"
    
    interface = ReviewInterface(db, faculty_id)
    interface.start_review_session()
    
    db.close()


if __name__ == "__main__":
    quick_review_cli()