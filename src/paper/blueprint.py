"""
Step 13: Exam Paper Blueprint Schema

Defines constraints for exam paper generation.
"""

from typing import Dict, List
from dataclasses import dataclass
import json


@dataclass
class BlueprintConstraint:
    """Single constraint for exam paper."""
    
    constraint_type: str  # 'marks_total', 'bloom_distribution', 'co_coverage', etc.
    value: any
    is_hard_constraint: bool = True  # False = preference, True = requirement


class PaperBlueprint:
    """
    Blueprint for generating exam papers.
    
    Defines all constraints:
    - Total marks
    - Duration
    - Bloom level distribution
    - CO coverage
    - Difficulty mix
    - Topic coverage
    """
    
    def __init__(
        self,
        paper_name: str,
        course_code: str,
        exam_type: str = "midterm"
    ):
        """Initialize blueprint."""
        self.paper_name = paper_name
        self.course_code = course_code
        self.exam_type = exam_type
        
        self.constraints = []
    
    def set_total_marks(self, total_marks: int, duration_minutes: int):
        """Set total marks and duration."""
        self.constraints.append(
            BlueprintConstraint('marks_total', total_marks, is_hard_constraint=True)
        )
        self.constraints.append(
            BlueprintConstraint('duration', duration_minutes, is_hard_constraint=True)
        )
    
    def set_bloom_distribution(self, distribution: Dict[int, float]):
        """
        Set Bloom level distribution.
        
        Args:
            distribution: {bloom_level: percentage}
            Example: {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.3, 5: 0.1}
        """
        self.constraints.append(
            BlueprintConstraint('bloom_distribution', distribution, is_hard_constraint=False)
        )
    
    def set_co_coverage(self, co_requirements: Dict[str, int]):
        """
        Set CO coverage requirements.
        
        Args:
            co_requirements: {co_id: min_marks}
            Example: {'CO1': 10, 'CO2': 15, 'CO3': 5}
        """
        self.constraints.append(
            BlueprintConstraint('co_coverage', co_requirements, is_hard_constraint=True)
        )
    
    def set_difficulty_mix(self, easy: float, medium: float, hard: float):
        """
        Set difficulty distribution.
        
        Args:
            easy, medium, hard: Percentages (should sum to 1.0)
        """
        if abs((easy + medium + hard) - 1.0) > 0.01:
            raise ValueError("Difficulty percentages must sum to 1.0")
        
        self.constraints.append(
            BlueprintConstraint(
                'difficulty_mix',
                {'easy': easy, 'medium': medium, 'hard': hard},
                is_hard_constraint=False
            )
        )
    
    def set_unit_coverage(self, unit_requirements: Dict[str, int]):
        """
        Set unit coverage requirements.
        
        Args:
            unit_requirements: {unit_id: min_marks}
            Example: {'unit_1': 20, 'unit_2': 20, 'unit_3': 10}
        """
        self.constraints.append(
            BlueprintConstraint('unit_coverage', unit_requirements, is_hard_constraint=True)
        )
    
    def set_question_count_range(self, min_questions: int, max_questions: int):
        """Set allowed range for total number of questions."""
        self.constraints.append(
            BlueprintConstraint(
                'question_count',
                {'min': min_questions, 'max': max_questions},
                is_hard_constraint=False
            )
        )
    
    def to_dict(self) -> Dict:
        """Convert blueprint to dictionary for storage."""
        return {
            'paper_name': self.paper_name,
            'course_code': self.course_code,
            'exam_type': self.exam_type,
            'constraints': [
                {
                    'type': c.constraint_type,
                    'value': c.value,
                    'is_hard': c.is_hard_constraint
                }
                for c in self.constraints
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PaperBlueprint':
        """Load blueprint from dictionary."""
        blueprint = cls(
            paper_name=data['paper_name'],
            course_code=data['course_code'],
            exam_type=data.get('exam_type', 'midterm')
        )
        
        for constraint_data in data.get('constraints', []):
            blueprint.constraints.append(
                BlueprintConstraint(
                    constraint_type=constraint_data['type'],
                    value=constraint_data['value'],
                    is_hard_constraint=constraint_data['is_hard']
                )
            )
        
        return blueprint
    
    def get_constraint(self, constraint_type: str) -> BlueprintConstraint:
        """Get constraint by type."""
        for c in self.constraints:
            if c.constraint_type == constraint_type:
                return c
        return None
    
    def validate(self) -> bool:
        """Validate blueprint has minimum required constraints."""
        required = ['marks_total', 'duration']
        
        for req in required:
            if not self.get_constraint(req):
                raise ValueError(f"Missing required constraint: {req}")
        
        return True
    
    def print_summary(self):
        """Print human-readable blueprint summary."""
        print("\n" + "="*60)
        print(f"EXAM PAPER BLUEPRINT: {self.paper_name}")
        print("="*60)
        print(f"Course: {self.course_code}")
        print(f"Type: {self.exam_type}")
        print()
        
        # Hard constraints
        print("Hard Constraints (MUST satisfy):")
        print("-" * 60)
        hard = [c for c in self.constraints if c.is_hard_constraint]
        for c in hard:
            print(f"  • {c.constraint_type}: {c.value}")
        print()
        
        # Soft constraints
        print("Preferences (SHOULD satisfy):")
        print("-" * 60)
        soft = [c for c in self.constraints if not c.is_hard_constraint]
        for c in soft:
            print(f"  • {c.constraint_type}: {c.value}")
        
        print("="*60 + "\n")


# Example blueprint templates
def create_midterm_blueprint(course_code: str) -> PaperBlueprint:
    """Create standard midterm blueprint."""
    blueprint = PaperBlueprint(
        paper_name="Midterm Examination",
        course_code=course_code,
        exam_type="midterm"
    )
    
    blueprint.set_total_marks(50, duration_minutes=90)
    
    blueprint.set_bloom_distribution({
        1: 0.15,  # 15% Remember
        2: 0.25,  # 25% Understand
        3: 0.30,  # 30% Apply
        4: 0.20,  # 20% Analyze
        5: 0.10,  # 10% Evaluate
    })
    
    blueprint.set_difficulty_mix(easy=0.2, medium=0.6, hard=0.2)
    
    blueprint.set_co_coverage({
        'CO1': 10,
        'CO2': 15,
        'CO3': 15,
        'CO4': 10
    })
    
    blueprint.set_question_count_range(min_questions=5, max_questions=10)
    
    return blueprint


def create_final_blueprint(course_code: str) -> PaperBlueprint:
    """Create standard final exam blueprint."""
    blueprint = PaperBlueprint(
        paper_name="Final Examination",
        course_code=course_code,
        exam_type="final"
    )
    
    blueprint.set_total_marks(100, duration_minutes=180)
    
    blueprint.set_bloom_distribution({
        1: 0.10,
        2: 0.20,
        3: 0.30,
        4: 0.25,
        5: 0.10,
        6: 0.05
    })
    
    blueprint.set_difficulty_mix(easy=0.15, medium=0.60, hard=0.25)
    
    blueprint.set_co_coverage({
        'CO1': 20,
        'CO2': 20,
        'CO3': 20,
        'CO4': 20,
        'CO5': 20
    })
    
    blueprint.set_unit_coverage({
        'unit_1': 20,
        'unit_2': 20,
        'unit_3': 20,
        'unit_4': 20,
        'unit_5': 20
    })
    
    blueprint.set_question_count_range(min_questions=8, max_questions=15)
    
    return blueprint