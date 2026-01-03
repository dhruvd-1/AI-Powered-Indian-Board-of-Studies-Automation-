"""
Step 8: Pedagogy Agent - Educational Metadata Tagging
"""

from typing import Dict, List
from src.agents.base_agent import BaseAgent
from config.prompts import PEDAGOGY_PROMPT


class PedagogyAgent(BaseAgent):
    """
    Assigns educational metadata to questions.
    
    Maps questions to Course Outcomes, verifies Bloom level,
    assesses difficulty, and suggests Program Outcomes.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """Initialize Pedagogy agent."""
        super().__init__(model_name)
        
        self.bloom_names = {
            1: "Remember",
            2: "Understand",
            3: "Apply",
            4: "Analyze",
            5: "Evaluate",
            6: "Create"
        }
    
    def process(
        self,
        question: str,
        course_outcomes: List[Dict],
        intended_co: str,
        intended_bloom_level: int,
        intended_difficulty: str
    ) -> Dict:
        """
        Assign pedagogical metadata to question.
        
        Args:
            question: Question to analyze
            course_outcomes: List of COs with descriptions
            intended_co: Originally intended CO (e.g., "CO1")
            intended_bloom_level: Originally intended Bloom level
            intended_difficulty: Originally intended difficulty
            
        Returns:
            Dict with pedagogical metadata
        """
        # Format course outcomes
        cos_formatted = self._format_course_outcomes(course_outcomes)
        
        # Build prompt
        prompt = PEDAGOGY_PROMPT.format(
            question=question,
            course_outcomes=cos_formatted,
            intended_co=intended_co,
            intended_bloom_level=intended_bloom_level,
            bloom_name=self.bloom_names[intended_bloom_level],
            intended_difficulty=intended_difficulty
        )
        
        # Call LLM
        print(f"   📚 Pedagogy: Tagging metadata...")
        response = self.call_llm(prompt, temperature=0.4)
        
        # Parse response
        result = self.extract_json(response)
        
        if not result:
            # Fallback to intended values
            result = {
                "primary_co": intended_co,
                "secondary_cos": [],
                "co_justification": "Default assignment",
                "verified_bloom_level": intended_bloom_level,
                "bloom_level_match": True,
                "bloom_justification": "Default assignment",
                "verified_difficulty": intended_difficulty,
                "difficulty_match": True,
                "difficulty_justification": "Default assignment",
                "program_outcomes": ["PO1", "PO2"],
                "po_justification": "Default assignment",
                "marks_recommended": 5,
                "time_recommended_minutes": 10
            }
        
        return result
    
    def _format_course_outcomes(self, course_outcomes: List[Dict]) -> str:
        """Format course outcomes for prompt."""
        formatted = []
        
        for co in course_outcomes:
            co_id = co.get('co_id', 'CO?')
            description = co.get('description', 'No description')
            formatted.append(f"- {co_id}: {description}")
        
        return "\n".join(formatted)
