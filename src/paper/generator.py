"""
Step 15: Fresh Question Generation for Papers

Generates new questions on-the-fly to fill paper requirements.
"""

from typing import Dict, List
import json

from src.orchestration.question_generator import QuestionGenerator
from src.paper.blueprint import PaperBlueprint
from src.database.schema import Question


class FreshPaperGenerator:
    """
    Generates fresh questions to satisfy paper blueprint.
    
    Used when:
    - Question bank is insufficient
    - Faculty wants all-new questions
    - Hybrid approach (some from bank, fill gaps with fresh)
    """
    
    def __init__(self, question_generator: QuestionGenerator):
        """
        Initialize with question generator.
        
        Args:
            question_generator: Orchestrated question generator
        """
        self.generator = question_generator
    
    def generate_paper_questions(
        self,
        blueprint: PaperBlueprint,
        faculty_id: str = "default_faculty"
    ) -> List[int]:
        """
        Generate fresh questions matching blueprint.
        
        Args:
            blueprint: Paper blueprint with constraints
            faculty_id: Faculty identifier
            
        Returns:
            List of question IDs (saved to database)
        """
        print(f"\n{'='*60}")
        print("GENERATING FRESH QUESTIONS FOR PAPER")
        print(f"{'='*60}\n")
        
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
        
        # Build generation plan
        generation_plan = self._build_generation_plan(
            target_marks=target_marks,
            co_requirements=co_constraint.value if co_constraint else {},
            bloom_distribution=bloom_constraint.value if bloom_constraint else {},
            difficulty_mix=difficulty_constraint.value if difficulty_constraint else {},
            unit_requirements=unit_constraint.value if unit_constraint else {}
        )
        
        print(f"Generation plan: {len(generation_plan)} questions\n")
        
        # Generate each question
        question_ids = []
        
        for i, spec in enumerate(generation_plan, 1):
            print(f"Generating question {i}/{len(generation_plan)}...")
            print(f"  Spec: {spec['unit_id']}, {spec['co_id']}, L{spec['bloom_level']}, {spec['difficulty']}, {spec['marks']} marks")
            
            try:
                result = self.generator.generate_question(
                    unit_id=spec['unit_id'],
                    co_id=spec['co_id'],
                    bloom_level=spec['bloom_level'],
                    difficulty=spec['difficulty'],
                    faculty_id=faculty_id
                )
                
                # Update marks in database
                self.generator.db.update_question(
                    result['question_id'],
                    {'marks': spec['marks']}
                )
                
                question_ids.append(result['question_id'])
                print(f"  ✅ Generated Question #{result['question_id']}\n")
                
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
                continue
        
        print(f"{'='*60}")
        print(f"✅ GENERATED {len(question_ids)}/{len(generation_plan)} QUESTIONS")
        print(f"{'='*60}\n")
        
        return question_ids
    
    def _build_generation_plan(
        self,
        target_marks: int,
        co_requirements: Dict[str, int],
        bloom_distribution: Dict[int, float],
        difficulty_mix: Dict[str, float],
        unit_requirements: Dict[str, int]
    ) -> List[Dict]:
        """
        Build question generation plan from constraints.
        
        Returns:
            List of question specs: [
                {'unit_id': 'unit_1', 'co_id': 'CO1', 'bloom_level': 2, 'difficulty': 'medium', 'marks': 5},
                ...
            ]
        """
        plan = []
        remaining_marks = target_marks
        
        # Standard question mark values
        STANDARD_MARKS = [2, 5, 10, 16]
        
        # Phase 1: Satisfy CO requirements
        for co_id, min_marks in sorted(co_requirements.items()):
            marks_allocated = 0
            
            while marks_allocated < min_marks and remaining_marks > 0:
                # Choose mark value
                marks = self._choose_marks(min_marks - marks_allocated, remaining_marks, STANDARD_MARKS)
                
                # Choose Bloom level from distribution
                bloom_level = self._choose_bloom_level(bloom_distribution)
                
                # Choose difficulty from mix
                difficulty = self._choose_difficulty(difficulty_mix)
                
                # Choose unit (prefer CO-related unit, for simplicity use round-robin)
                unit_id = self._map_co_to_unit(co_id)
                
                plan.append({
                    'unit_id': unit_id,
                    'co_id': co_id,
                    'bloom_level': bloom_level,
                    'difficulty': difficulty,
                    'marks': marks
                })
                
                marks_allocated += marks
                remaining_marks -= marks
        
        # Phase 2: Satisfy unit requirements (if any additional marks needed)
        if unit_requirements:
            for unit_id, min_marks in sorted(unit_requirements.items()):
                # Check how much already allocated to this unit
                allocated = sum(q['marks'] for q in plan if q['unit_id'] == unit_id)
                
                while allocated < min_marks and remaining_marks > 0:
                    marks = self._choose_marks(min_marks - allocated, remaining_marks, STANDARD_MARKS)
                    bloom_level = self._choose_bloom_level(bloom_distribution)
                    difficulty = self._choose_difficulty(difficulty_mix)
                    co_id = self._map_unit_to_co(unit_id)
                    
                    plan.append({
                        'unit_id': unit_id,
                        'co_id': co_id,
                        'bloom_level': bloom_level,
                        'difficulty': difficulty,
                        'marks': marks
                    })
                    
                    allocated += marks
                    remaining_marks -= marks
        
        # Phase 3: Fill remaining marks
        while remaining_marks > 0:
            marks = self._choose_marks(remaining_marks, remaining_marks, STANDARD_MARKS)
            bloom_level = self._choose_bloom_level(bloom_distribution)
            difficulty = self._choose_difficulty(difficulty_mix)
            
            # Distribute across COs evenly
            co_id = list(co_requirements.keys())[len(plan) % len(co_requirements)]
            unit_id = self._map_co_to_unit(co_id)
            
            plan.append({
                'unit_id': unit_id,
                'co_id': co_id,
                'bloom_level': bloom_level,
                'difficulty': difficulty,
                'marks': marks
            })
            
            remaining_marks -= marks
        
        return plan
    
    def _choose_marks(self, needed: int, available: int, standard: List[int]) -> int:
        """Choose appropriate mark value."""
        for marks in reversed(standard):
            if marks <= needed and marks <= available:
                return marks
        return min(2, available)  # Minimum 2 marks
    
    def _choose_bloom_level(self, distribution: Dict[int, float]) -> int:
        """Choose Bloom level based on distribution."""
        if not distribution:
            return 2  # Default: Understand
        
        # Weighted random choice
        import random
        levels = list(distribution.keys())
        weights = [distribution[l] for l in levels]
        return random.choices(levels, weights=weights)[0]
    
    def _choose_difficulty(self, mix: Dict[str, float]) -> str:
        """Choose difficulty based on mix."""
        if not mix:
            return 'medium'
        
        import random
        difficulties = list(mix.keys())
        weights = [mix[d] for d in difficulties]
        return random.choices(difficulties, weights=weights)[0]
    
    def _map_co_to_unit(self, co_id: str) -> str:
        """Map CO to likely unit (simple heuristic)."""
        # CO1 -> unit_1, CO2 -> unit_2, etc.
        co_num = int(co_id.replace('CO', ''))
        return f'unit_{min(co_num, 5)}'  # Max 5 units
    
    def _map_unit_to_co(self, unit_id: str) -> str:
        """Map unit to likely CO."""
        unit_num = int(unit_id.replace('unit_', ''))
        return f'CO{min(unit_num, 5)}'