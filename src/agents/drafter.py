"""
Step 5: Drafter Agent - Initial Question Generation
"""

from typing import Dict, List
from src.agents.base_agent import BaseAgent
from config.prompts import DRAFTER_PROMPT


class DrafterAgent(BaseAgent):
    """
    Generates initial draft questions from retrieved content.
    
    Takes syllabus chunks and creates questions aligned with
    Bloom level and difficulty requirements.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """Initialize Drafter agent."""
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
        retrieved_chunks: List[Dict],
        unit_name: str,
        course_name: str,
        co_description: str,
        bloom_level: int,
        difficulty: str
    ) -> Dict:
        """
        Generate initial question draft.
        
        Args:
            retrieved_chunks: Chunks from retrieval step
            unit_name: Name of the unit
            course_name: Name of the course
            co_description: Course Outcome description
            bloom_level: Bloom's taxonomy level (1-6)
            difficulty: "easy", "medium", or "hard"
            
        Returns:
            Dict with question and metadata
        """
        # Format retrieved content
        retrieved_content = self._format_retrieved_content(retrieved_chunks)
        
        # Build prompt
        prompt = DRAFTER_PROMPT.format(
            course_name=course_name,
            unit_name=unit_name,
            co_description=co_description,
            bloom_level=bloom_level,
            bloom_name=self.bloom_names[bloom_level],
            difficulty=difficulty,
            retrieved_content=retrieved_content
        )
        
        # Call LLM
        print(f"   🖊️  Drafter: Generating initial question...")
        response = self.call_llm(prompt, temperature=0.8)
        
        # Parse response
        result = self.extract_json(response)
        
        if not result:
            # Fallback if JSON parsing fails
            result = {
                "question": response[:500],  # Take first 500 chars as question
                "question_type": "short_answer",
                "expected_answer_length": "1 paragraph",
                "key_concepts": []
            }
        
        # Add metadata
        result['draft_metadata'] = {
            'bloom_level': bloom_level,
            'difficulty': difficulty,
            'retrieved_chunks': len(retrieved_chunks),
            'sources': [
                f"{c['metadata']['source_file']} (p.{c['metadata']['page_number']})"
                for c in retrieved_chunks[:3]
            ]
        }
        
        return result
    
    def _format_retrieved_content(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks for prompt."""
        formatted = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk['metadata']['source_file']
            page = chunk['metadata']['page_number']
            text = chunk['text']
            
            formatted.append(
                f"[Source {i}: {source}, page {page}]\n{text}\n"
            )
        
        return "\n".join(formatted)
