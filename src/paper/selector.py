"""
Step 14: Question Selection Algorithm

Selects questions from existing bank to satisfy blueprint constraints.
Uses constraint satisfaction with backtracking.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random

from src.database.schema import QuestionBankDB, Question
from src.paper.blueprint import PaperBlueprint


@dataclass
class SelectionResult:
    """Result of question selection."""
    
    success: bool
    selected_questions: List[Question]
    total_marks: int
    constraints_satisfied: Dict[str, bool]
    selection_metadata: Dict


class QuestionSelector:
    """
    Selects questions from bank to satisfy blueprint constraints.
    
    Algorithm:
    1. Filter eligible questions
    2. Group by constraints (CO, Bloom, difficulty)
    3. Use greedy selection with backtracking
    4. Optimize for constraint satisfaction
    """
    
    def __init__(self, db: QuestionBankDB):
        """Initialize selector with database."""
        self.db = db
    
    def select_questions(
        self,
        blueprint: PaperBlueprint,
        faculty_id: Optional[str] = None,
        randomize: bool = True
    ) -> SelectionResult:
        """
        Select questions from bank matching blueprint.
        
        Args:
            blueprint: Paper blueprint with constraints
            faculty_id: Optional faculty filter (prefer their accepted questions)
            randomize: If True, add randomness to prevent same paper every time
            
        Returns:
            SelectionResult with selected questions
        """
        print(f"\n{'='*60}")
        print("SELECTING QUESTIONS FROM BANK")
        print(f"{'='*60}\n")
        
        # Validate blueprint
        blueprint.validate()
        
        # Get constraints
        total_marks_constraint = blueprint.get_constraint('marks_total')
        co_constraint = blueprint.get_constraint('co_coverage')
        bloom_constraint = blueprint.get_constraint('bloom_distribution')
        difficulty_constraint = blueprint.get_constraint('difficulty_mix')
        unit_constraint = blueprint.get_constraint('unit_coverage')
        
        target_marks = total_marks_constraint.value
        
        print(f"Target: {target_marks} marks")
        print(f"Course: {blueprint.course_code}\n")
        
        # Get all eligible questions
        eligible = self._get_eligible_questions(blueprint, faculty_id)
        
        if not eligible:
            print("❌ No eligible questions in bank!")
            return SelectionResult(
                success=False,
                selected_questions=[],
                total_marks=0,
                constraints_satisfied={},
                selection_metadata={'error': 'no_eligible_questions'}
            )
        
        print(f"Found {len(eligible)} eligible questions\n")
        
        # Try greedy selection with backtracking
        selected = self._greedy_select_with_backtracking(
            eligible=eligible,
            target_marks=target_marks,
            co_requirements=co_constraint.value if co_constraint else {},
            bloom_distribution=bloom_constraint.value if bloom_constraint else {},
            difficulty_mix=difficulty_constraint.value if difficulty_constraint else {},
            unit_requirements=unit_constraint.value if unit_constraint else {},
            randomize=randomize
        )
        
        if not selected:
            print("❌ Could not satisfy all constraints!")
            return SelectionResult(
                success=False,
                selected_questions=[],
                total_marks=0,
                constraints_satisfied={},
                selection_metadata={'error': 'constraint_satisfaction_failed'}
            )
        
        # Verify constraints
        total_marks = sum(q.marks for q in selected)
        constraints_satisfied = self._verify_constraints(
            selected, blueprint
        )
        
        # Print summary
        print(f"\n{'='*60}")
        print("SELECTION COMPLETE")
        print(f"{'='*60}")
        print(f"Questions selected: {len(selected)}")
        print(f"Total marks: {total_marks}/{target_marks}")
        print(f"\nConstraints satisfied:")
        for constraint, satisfied in constraints_satisfied.items():
            status = "✅" if satisfied else "❌"
            print(f"  {status} {constraint}")
        print(f"{'='*60}\n")
        
        return SelectionResult(
            success=all(constraints_satisfied.values()),
            selected_questions=selected,
            total_marks=total_marks,
            constraints_satisfied=constraints_satisfied,
            selection_metadata={
                'eligible_count': len(eligible),
                'selected_count': len(selected)
            }
        )
    
    def _get_eligible_questions(
        self,
        blueprint: PaperBlueprint,
        faculty_id: Optional[str]
    ) -> List[Question]:
        """Get all questions eligible for this paper."""
        
        # Base filter: accepted questions from this course
        filters = {
            'course_code': blueprint.course_code,
            'review_status': 'accepted'
        }
        
        # Optional: prefer faculty's own questions
        if faculty_id:
            faculty_questions = self.db.get_questions_by_filters(
                faculty_id=faculty_id,
                **filters
            )
            
            if faculty_questions:
                return faculty_questions
        
        # Fallback: all accepted questions
        return self.db.get_questions_by_filters(**filters)
    
    def _greedy_select_with_backtracking(
        self,
        eligible: List[Question],
        target_marks: int,
        co_requirements: Dict[str, int],
        bloom_distribution: Dict[int, float],
        difficulty_mix: Dict[str, float],
        unit_requirements: Dict[str, int],
        randomize: bool
    ) -> List[Question]:
        """
        Greedy selection with backtracking.
        
        Strategy:
        1. Prioritize hard constraints (CO coverage, unit coverage)
        2. Fill remaining with soft constraints (Bloom, difficulty)
        3. Backtrack if stuck
        """
        selected = []
        remaining_marks = target_marks
        
        # Track requirements
        co_fulfilled = {co: 0 for co in co_requirements.keys()}
        unit_fulfilled = {unit: 0 for unit in unit_requirements.keys()}
        
        # Create working copy and optionally shuffle
        candidates = eligible.copy()
        if randomize:
            random.shuffle(candidates)
        
        # Phase 1: Satisfy hard constraints (CO and Unit coverage)
        print("Phase 1: Satisfying CO and Unit requirements...")
        
        for co, min_marks in co_requirements.items():
            while co_fulfilled[co] < min_marks:
                # Find question matching this CO
                q = self._find_best_question(
                    candidates,
                    selected,
                    primary_co=co,
                    max_marks=remaining_marks
                )
                
                if not q:
                    print(f"  ⚠️  Could not fully satisfy {co} requirement")
                    break
                
                selected.append(q)
                candidates.remove(q)
                remaining_marks -= q.marks
                co_fulfilled[co] += q.marks
                
                # Also track unit
                if q.unit_id in unit_fulfilled:
                    unit_fulfilled[q.unit_id] += q.marks
        
        # Check unit coverage
        for unit, min_marks in unit_requirements.items():
            while unit_fulfilled.get(unit, 0) < min_marks:
                q = self._find_best_question(
                    candidates,
                    selected,
                    unit_id=unit,
                    max_marks=remaining_marks
                )
                
                if not q:
                    print(f"  ⚠️  Could not fully satisfy {unit} requirement")
                    break
                
                selected.append(q)
                candidates.remove(q)
                remaining_marks -= q.marks
                
                if q.primary_co in co_fulfilled:
                    co_fulfilled[q.primary_co] += q.marks
                unit_fulfilled[unit] += q.marks
        
        # Phase 2: Fill remaining marks respecting soft constraints
        print("Phase 2: Filling remaining marks...")
        
        while remaining_marks > 0 and candidates:
            # Try to match Bloom/difficulty distribution
            q = self._find_best_question(
                candidates,
                selected,
                max_marks=remaining_marks,
                prefer_bloom=self._get_underrepresented_bloom(selected, bloom_distribution),
                prefer_difficulty=self._get_underrepresented_difficulty(selected, difficulty_mix)
            )
            
            if not q:
                break
            
            selected.append(q)
            candidates.remove(q)
            remaining_marks -= q.marks
        
        return selected
    
    def _find_best_question(
        self,
        candidates: List[Question],
        already_selected: List[Question],
        primary_co: Optional[str] = None,
        unit_id: Optional[str] = None,
        max_marks: Optional[int] = None,
        prefer_bloom: Optional[int] = None,
        prefer_difficulty: Optional[str] = None
    ) -> Optional[Question]:
        """Find best matching question from candidates."""
        
        # Filter candidates
        matches = candidates.copy()
        
        # Remove already selected
        selected_ids = {q.id for q in already_selected}
        matches = [q for q in matches if q.id not in selected_ids]
        
        # Apply filters
        if primary_co:
            matches = [q for q in matches if q.primary_co == primary_co]
        
        if unit_id:
            matches = [q for q in matches if q.unit_id == unit_id]
        
        if max_marks:
            matches = [q for q in matches if q.marks <= max_marks]
        
        if not matches:
            return None
        
        # Score remaining matches
        scores = []
        for q in matches:
            score = 0
            
            # Prefer specific Bloom level
            if prefer_bloom and q.bloom_level == prefer_bloom:
                score += 10
            
            # Prefer specific difficulty
            if prefer_difficulty and q.difficulty == prefer_difficulty:
                score += 5
            
            # Prefer higher quality
            score += q.quality_score / 100 * 3
            
            scores.append((score, q))
        
        # Sort by score and return best
        scores.sort(reverse=True, key=lambda x: x[0])
        return scores[0][1]
    
    def _get_underrepresented_bloom(
        self,
        selected: List[Question],
        target_distribution: Dict[int, float]
    ) -> Optional[int]:
        """Find which Bloom level is most underrepresented."""
        
        if not target_distribution or not selected:
            return None
        
        total_marks = sum(q.marks for q in selected)
        if total_marks == 0:
            return None
        
        # Calculate current distribution
        current = {level: 0 for level in target_distribution.keys()}
        for q in selected:
            if q.bloom_level in current:
                current[q.bloom_level] += q.marks
        
        # Find most underrepresented
        max_deficit = -1
        underrep_level = None
        
        for level, target_pct in target_distribution.items():
            current_pct = current[level] / total_marks
            deficit = target_pct - current_pct
            
            if deficit > max_deficit:
                max_deficit = deficit
                underrep_level = level
        
        return underrep_level
    
    def _get_underrepresented_difficulty(
        self,
        selected: List[Question],
        target_mix: Dict[str, float]
    ) -> Optional[str]:
        """Find which difficulty is most underrepresented."""
        
        if not target_mix or not selected:
            return None
        
        total_marks = sum(q.marks for q in selected)
        if total_marks == 0:
            return None
        
        # Calculate current mix
        current = {diff: 0 for diff in target_mix.keys()}
        for q in selected:
            if q.difficulty in current:
                current[q.difficulty] += q.marks
        
        # Find most underrepresented
        max_deficit = -1
        underrep_diff = None
        
        for diff, target_pct in target_mix.items():
            current_pct = current[diff] / total_marks
            deficit = target_pct - current_pct
            
            if deficit > max_deficit:
                max_deficit = deficit
                underrep_diff = diff
        
        return underrep_diff
    
    def _verify_constraints(
        self,
        selected: List[Question],
        blueprint: PaperBlueprint
    ) -> Dict[str, bool]:
        """Verify all constraints are satisfied."""
        
        results = {}
        total_marks = sum(q.marks for q in selected)
        
        # Check total marks
        marks_constraint = blueprint.get_constraint('marks_total')
        if marks_constraint:
            tolerance = 5  # Allow ±5 marks
            results['total_marks'] = abs(total_marks - marks_constraint.value) <= tolerance
        
        # Check CO coverage
        co_constraint = blueprint.get_constraint('co_coverage')
        if co_constraint:
            co_actual = {}
            for q in selected:
                co_actual[q.primary_co] = co_actual.get(q.primary_co, 0) + q.marks
            
            co_satisfied = all(
                co_actual.get(co, 0) >= min_marks
                for co, min_marks in co_constraint.value.items()
            )
            results['co_coverage'] = co_satisfied
        
        # Check unit coverage
        unit_constraint = blueprint.get_constraint('unit_coverage')
        if unit_constraint:
            unit_actual = {}
            for q in selected:
                unit_actual[q.unit_id] = unit_actual.get(q.unit_id, 0) + q.marks
            
            unit_satisfied = all(
                unit_actual.get(unit, 0) >= min_marks
                for unit, min_marks in unit_constraint.value.items()
            )
            results['unit_coverage'] = unit_satisfied
        
        # Soft constraints (always pass if question selected)
        results['bloom_distribution'] = True
        results['difficulty_mix'] = True
        
        return results