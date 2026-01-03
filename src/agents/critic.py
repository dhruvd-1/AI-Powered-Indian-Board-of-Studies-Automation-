"""
Step 6: Critic Agent - Question Refinement
"""

from typing import Dict, List, Optional
from src.agents.base_agent import BaseAgent
from config.prompts import CRITIC_PROMPT


class CriticAgent(BaseAgent):
    """
    Refines questions through iterative critique.
    
    Evaluates questions for clarity, Bloom alignment, difficulty,
    and syllabus compliance. Suggests improvements.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """Initialize Critic agent."""
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
        bloom_level: int,
        difficulty: str,
        co_description: str,
        retrieved_chunks: List[Dict],
        previous_critique: Optional[str] = None
    ) -> Dict:
        """
        Critique and refine a question.
        
        Args:
            question: Question to critique
            bloom_level: Target Bloom level
            difficulty: Target difficulty
            co_description: Course Outcome description
            retrieved_chunks: Retrieved content for reference
            previous_critique: Previous critique (for iteration 2+)
            
        Returns:
            Dict with critique results and refined question
        """
        # Format retrieved content
        retrieved_content = self._format_retrieved_content(retrieved_chunks)
        
        # Build prompt
        prompt = CRITIC_PROMPT.format(
            question=question,
            bloom_level=bloom_level,
            bloom_name=self.bloom_names[bloom_level],
            difficulty=difficulty,
            co_description=co_description,
            retrieved_content=retrieved_content[:2000],  # Limit length
            previous_critique=previous_critique or "None (first critique)"
        )
        
        # Call LLM
        print(f"   🔍 Critic: Evaluating question...")
        response = self.call_llm(prompt, temperature=0.5)
        
        # Parse response
        result = self.extract_json(response)
        
        if not result:
            # Fallback
            result = {
                "overall_quality": "fair",
                "issues_found": [],
                "refined_question": question,
                "changes_made": "Unable to parse critique",
                "ready_for_faculty": False
            }
        
        return result
    
    def _format_retrieved_content(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks (abbreviated for Critic)."""
        formatted = []
        
        for i, chunk in enumerate(chunks[:3], 1):  # Only top 3 for context
            text = chunk['text'][:300]  # Truncate
            formatted.append(f"[Chunk {i}] {text}...")
        
        return "\n".join(formatted)
