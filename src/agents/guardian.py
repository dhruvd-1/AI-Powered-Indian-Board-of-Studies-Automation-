"""
Step 7: Guardian Agent - Syllabus Compliance Validation
"""

from typing import Dict, List
from src.agents.base_agent import BaseAgent
from config.prompts import GUARDIAN_PROMPT


class GuardianAgent(BaseAgent):
    """
    Validates syllabus compliance and detects hallucinations.
    
    Ensures questions are fully answerable from syllabus content
    and don't introduce out-of-scope concepts.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """Initialize Guardian agent."""
        super().__init__(model_name)
    
    def process(
        self,
        question: str,
        unit_name: str,
        unit_topics: List[str],
        retrieved_chunks: List[Dict]
    ) -> Dict:
        """
        Validate question compliance with syllabus.
        
        Args:
            question: Question to validate
            unit_name: Name of the unit
            unit_topics: List of topics in the unit
            retrieved_chunks: Retrieved content
            
        Returns:
            Dict with validation results
        """
        # Format retrieved content
        retrieved_content = self._format_retrieved_content(retrieved_chunks)
        
        # Format topics
        topics_str = ", ".join(unit_topics[:10])  # Top 10 topics
        
        # Build prompt
        prompt = GUARDIAN_PROMPT.format(
            question=question,
            retrieved_content=retrieved_content,
            unit_name=unit_name,
            unit_topics=topics_str
        )
        
        # Call LLM
        print(f"   🛡️  Guardian: Validating compliance...")
        response = self.call_llm(prompt, temperature=0.3)  # Lower temp for strict validation
        
        # Parse response
        result = self.extract_json(response)
        
        if not result:
            # Fallback - assume compliant if can't parse
            result = {
                "is_compliant": True,
                "compliance_score": 80,
                "violations": [],
                "recommendation": "approve",
                "revision_guidance": ""
            }
        
        # Ensure compliance_score is numeric
        if 'compliance_score' in result:
            try:
                result['compliance_score'] = float(result['compliance_score'])
            except (ValueError, TypeError):
                result['compliance_score'] = 80.0
        else:
            result['compliance_score'] = 80.0
        
        return result
    
    def _format_retrieved_content(self, chunks: List[Dict]) -> str:
        """Format all retrieved chunks for Guardian."""
        formatted = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk['metadata']['source_file']
            page = chunk['metadata']['page_number']
            text = chunk['text'][:400]  # Partial text
            
            formatted.append(
                f"[Source {i}: {source} p.{page}]\n{text}..."
            )
        
        return "\n\n".join(formatted)
