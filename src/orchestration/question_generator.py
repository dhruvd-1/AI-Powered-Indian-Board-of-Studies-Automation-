"""
Step 9: Orchestration Pipeline

Chains all agents together into single generate_question() function.
"""

from typing import Dict, List
import json

from src.retrieval.vector_store import VectorStoreManager
from src.retrieval.retriever import BloomAdaptiveRetriever, RetrievalTracker
from src.agents.drafter import DrafterAgent
from src.agents.critic import CriticAgent
from src.agents.guardian import GuardianAgent
from src.agents.pedagogy import PedagogyAgent
from src.database.schema import QuestionBankDB

from config.settings import CRITIC_ITERATIONS, QUALITY_SCORE_THRESHOLD


class QuestionGenerator:
    """
    Orchestrates the complete question generation pipeline.
    
    Workflow:
    1. Retrieve content (Bloom-adaptive)
    2. Draft question (Drafter Agent)
    3. Refine 2-3 times (Critic Agent)
    4. Validate compliance (Guardian Agent)
    5. Tag metadata (Pedagogy Agent)
    6. Save to database
    """
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        db: QuestionBankDB,
        syllabus_structure: Dict
    ):
        """
        Initialize generator with all components.
        
        Args:
            vector_store_manager: Loaded vector stores
            db: Question bank database
            syllabus_structure: Parsed syllabus JSON
        """
        self.retriever = BloomAdaptiveRetriever(vector_store_manager)
        self.db = db
        self.syllabus = syllabus_structure
        
        # Initialize agents
        self.drafter = DrafterAgent()
        self.critic = CriticAgent()
        self.guardian = GuardianAgent()
        self.pedagogy = PedagogyAgent()
        
        # Tracker for reasoning traces
        self.tracker = RetrievalTracker()
    
    def generate_question(
        self,
        unit_id: str,
        co_id: str,
        bloom_level: int,
        difficulty: str,
        faculty_id: str = "default_faculty"
    ) -> Dict:
        """
        Generate a complete question with full pipeline.
        
        Args:
            unit_id: e.g., "unit_1"
            co_id: e.g., "CO1"
            bloom_level: 1-6
            difficulty: "easy", "medium", or "hard"
            faculty_id: Faculty identifier
            
        Returns:
            Dict with question data and metadata
        """
        print(f"\n{'='*60}")
        print(f"GENERATING QUESTION")
        print(f"{'='*60}")
        print(f"Unit: {unit_id} | CO: {co_id} | Bloom: L{bloom_level} | Difficulty: {difficulty}")
        print()
        
        # Get unit and CO info
        unit = self._get_unit_info(unit_id)
        co = self._get_co_info(co_id)
        
        # Step 1: Retrieve
        print("Step 1/6: Retrieval")
        query = self._generate_retrieval_query(unit, co, bloom_level)
        chunks = self.retriever.retrieve(query, unit_id, bloom_level)
        self.tracker.log_retrieval(query, unit_id, bloom_level, chunks)
        print(f"   ✅ Retrieved {len(chunks)} chunks\n")
        
        # Step 2: Draft
        print("Step 2/6: Drafting")
        draft_result = self.drafter.process(
            retrieved_chunks=chunks,
            unit_name=unit['unit_name'],
            course_name=self.syllabus['course_info']['course_name'],
            co_description=co['description'],
            bloom_level=bloom_level,
            difficulty=difficulty
        )
        question_text = draft_result['question']
        print(f"   ✅ Generated draft\n")
        
        # Step 3: Critique (multiple iterations)
        print(f"Step 3/6: Critique ({CRITIC_ITERATIONS} iterations)")
        critique_history = []
        previous_critique = None
        
        for i in range(CRITIC_ITERATIONS):
            critique_result = self.critic.process(
                question=question_text,
                bloom_level=bloom_level,
                difficulty=difficulty,
                co_description=co['description'],
                retrieved_chunks=chunks,
                previous_critique=previous_critique
            )
            
            critique_history.append(critique_result)
            question_text = critique_result['refined_question']
            previous_critique = json.dumps(critique_result)
            
            print(f"   Iteration {i+1}: {critique_result.get('overall_quality', 'N/A')}")
        
        print(f"   ✅ Final quality: {critique_history[-1].get('overall_quality', 'N/A')}\n")
        
        # Step 4: Guardian validation
        print("Step 4/6: Validation")
        validation = self.guardian.process(
            question=question_text,
            unit_name=unit['unit_name'],
            unit_topics=unit['topics'],
            retrieved_chunks=chunks
        )
        print(f"   ✅ Compliance: {validation['compliance_score']}/100\n")
        
        # Step 5: Pedagogy tagging
        print("Step 5/6: Metadata Tagging")
        pedagogy_tags = self.pedagogy.process(
            question=question_text,
            course_outcomes=self.syllabus['course_outcomes'],
            intended_co=co_id,
            intended_bloom_level=bloom_level,
            intended_difficulty=difficulty
        )
        print(f"   ✅ Tagged: CO={pedagogy_tags['primary_co']}, "
              f"Bloom=L{pedagogy_tags['verified_bloom_level']}, "
              f"Marks={pedagogy_tags['marks_recommended']}\n")
        
        # Step 6: Save to database
        print("Step 6/6: Saving to Database")
        question_data = self._build_question_data(
            question_text=question_text,
            draft_result=draft_result,
            critique_history=critique_history,
            validation=validation,
            pedagogy_tags=pedagogy_tags,
            unit=unit,
            co=co,
            chunks=chunks,
            faculty_id=faculty_id
        )
        
        question_id = self.db.add_question(question_data)
        print(f"   ✅ Saved as Question #{question_id}\n")
        
        print(f"{'='*60}")
        print(f"✅ GENERATION COMPLETE")
        print(f"{'='*60}\n")
        
        # Get saved question for complete data
        saved_question = self.db.get_question(question_id)
        
        return {
            'question_id': question_id,
            'id': question_id,
            'question_text': question_text,
            'unit_id': unit['unit_id'],
            'unit_name': unit['unit_name'],
            'primary_co': pedagogy_tags['primary_co'],
            'bloom_level': pedagogy_tags['verified_bloom_level'],
            'difficulty': pedagogy_tags['verified_difficulty'],
            'marks': pedagogy_tags.get('marks_recommended', 5),
            'metadata': pedagogy_tags,
            'quality_score': critique_history[-1].get('overall_quality', 'unknown'),
            'compliance_score': float(validation['compliance_score']),
            'retrieval_sources': question_data.get('retrieval_sources', []),
            'created_at': saved_question.created_at.isoformat() if saved_question and saved_question.created_at else None
        }
    
    def _get_unit_info(self, unit_id: str) -> Dict:
        """Get unit information from syllabus."""
        for unit in self.syllabus['units']:
            if unit['unit_id'] == unit_id:
                return unit
        raise ValueError(f"Unit {unit_id} not found in syllabus")
    
    def _get_co_info(self, co_id: str) -> Dict:
        """Get CO information from syllabus."""
        for co in self.syllabus['course_outcomes']:
            if co['co_id'] == co_id:
                return co
        raise ValueError(f"CO {co_id} not found in syllabus")
    
    def _generate_retrieval_query(self, unit: Dict, co: Dict, bloom_level: int) -> str:
        """Generate retrieval query from unit and CO."""
        # Use first few topics from unit
        topics = ", ".join(unit['topics'][:3])
        return f"{topics} from {unit['unit_name']}"
    
    def _build_question_data(
        self,
        question_text: str,
        draft_result: Dict,
        critique_history: List,
        validation: Dict,
        pedagogy_tags: Dict,
        unit: Dict,
        co: Dict,
        chunks: List,
        faculty_id: str
    ) -> Dict:
        """Build complete question data for database."""
        
        return {
            'question_text': question_text,
            'question_type': draft_result.get('question_type', 'short_answer'),
            'expected_answer_length': draft_result.get('expected_answer_length', '1 paragraph'),
            
            'primary_co': pedagogy_tags['primary_co'],
            'secondary_cos': pedagogy_tags.get('secondary_cos', []),
            'bloom_level': pedagogy_tags['verified_bloom_level'],
            'difficulty': pedagogy_tags['verified_difficulty'],
            'program_outcomes': pedagogy_tags.get('program_outcomes', []),
            
            'marks': pedagogy_tags.get('marks_recommended', 5),
            'time_minutes': pedagogy_tags.get('time_recommended_minutes', 10),
            
            'course_code': self.syllabus['course_info']['course_code'],
            'course_name': self.syllabus['course_info']['course_name'],
            'unit_id': unit['unit_id'],
            'unit_name': unit['unit_name'],
            
            'quality_score': self._quality_to_score(critique_history[-1].get('overall_quality', 'fair')),
            'compliance_score': validation['compliance_score'],
            
            'retrieval_sources': [
                {
                    'file': c['metadata']['source_file'],
                    'page': c['metadata']['page_number'],
                    'score': c['similarity_score']
                }
                for c in chunks[:5]
            ],
            'draft_version': draft_result['question'],
            'critique_history': [
                {
                    'iteration': i+1,
                    'quality': c.get('overall_quality', 'unknown'),
                    'changes': c.get('changes_made', '')
                }
                for i, c in enumerate(critique_history)
            ],
            'refinement_count': len(critique_history),
            
            'review_status': 'pending',
            'faculty_id': faculty_id
        }
    
    def _quality_to_score(self, quality: str) -> float:
        """Convert quality label to numeric score."""
        mapping = {
            'poor': 40,
            'fair': 60,
            'good': 80,
            'excellent': 95
        }
        return mapping.get(quality, 70)