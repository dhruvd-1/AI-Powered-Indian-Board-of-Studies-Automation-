"""
Step 12: Faculty Preference Learning

Analyzes Accept/Edit/Reject patterns to learn faculty preferences.
Kicks in after 20+ reviewed questions.
"""

from typing import Dict, List
import json
from collections import Counter
import re

from src.database.schema import QuestionBankDB, Question


class PreferenceLearner:
    """
    Learns faculty preferences from review history.
    
    Analyzes:
    - Accepted vs rejected question patterns
    - Common edits made
    - Difficulty/verbosity preferences
    """
    
    def __init__(self, db: QuestionBankDB):
        """Initialize preference learner."""
        self.db = db
        self.activation_threshold = 20  # Need 20+ reviews before learning kicks in
    
    def analyze_preferences(self, faculty_id: str) -> Dict:
        """
        Analyze faculty preferences from review history.
        
        Args:
            faculty_id: Faculty identifier
            
        Returns:
            Dict with learned preferences
        """
        # Get all reviewed questions
        all_reviewed = self.db.get_questions_by_filters(faculty_id=faculty_id)
        all_reviewed = [q for q in all_reviewed if q.review_status != 'pending']
        
        if len(all_reviewed) < self.activation_threshold:
            return {
                'status': 'insufficient_data',
                'reviews_needed': self.activation_threshold - len(all_reviewed),
                'message': f'Need {self.activation_threshold - len(all_reviewed)} more reviews before learning activates'
            }
        
        # Separate by decision
        accepted = [q for q in all_reviewed if q.review_status == 'accepted']
        edited = [q for q in all_reviewed if q.review_status == 'edited']
        rejected = [q for q in all_reviewed if q.review_status == 'rejected']
        
        # Analyze patterns
        preferences = {
            'status': 'active',
            'total_reviews': len(all_reviewed),
            'acceptance_rate': len(accepted) / len(all_reviewed) if all_reviewed else 0,
            
            # Question style preferences
            'preferred_question_style': self._analyze_question_style(accepted),
            'avoided_patterns': self._analyze_question_style(rejected),
            
            # Edit patterns
            'edit_patterns': self._analyze_edits(edited),
            
            # Difficulty preferences
            'difficulty_bias': self._analyze_difficulty_bias(accepted, rejected),
            
            # Verbosity preferences
            'verbosity_preference': self._analyze_verbosity(accepted, rejected),
            
            # Tone preferences
            'tone_preference': self._analyze_tone(accepted, rejected)
        }
        
        # Update database
        self.db.update_preferences(faculty_id, {
            'preferred_question_style': json.dumps(preferences['preferred_question_style']),
            'avoided_patterns': json.dumps(preferences['avoided_patterns']),
            'edit_patterns': json.dumps(preferences['edit_patterns']),
            'total_reviews': preferences['total_reviews'],
            'acceptance_rate': preferences['acceptance_rate'],
            'difficulty_bias': preferences['difficulty_bias'],
            'verbosity_preference': preferences['verbosity_preference'],
            'tone_preference': preferences['tone_preference']
        })
        
        return preferences
    
    def _analyze_question_style(self, questions: List[Question]) -> Dict:
        """Analyze common patterns in questions."""
        if not questions:
            return {}
        
        # Analyze starting words
        start_words = [q.question_text.split()[0] for q in questions if q.question_text]
        start_word_counts = Counter(start_words)
        
        # Analyze question length
        lengths = [len(q.question_text.split()) for q in questions if q.question_text]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        # Analyze question types
        types = [q.question_type for q in questions if q.question_type]
        type_counts = Counter(types)
        
        return {
            'common_starters': dict(start_word_counts.most_common(5)),
            'avg_question_length_words': round(avg_length, 1),
            'preferred_types': dict(type_counts.most_common())
        }
    
    def _analyze_edits(self, edited_questions: List[Question]) -> Dict:
        """Analyze common edit patterns."""
        if not edited_questions:
            return {}
        
        edit_types = []
        
        for q in edited_questions:
            if not q.faculty_edits:
                continue
            
            try:
                edits = json.loads(q.faculty_edits) if isinstance(q.faculty_edits, str) else q.faculty_edits
                original = edits.get('original', '')
                edited = edits.get('edited', '')
                
                # Detect edit type
                if len(edited.split()) < len(original.split()) * 0.8:
                    edit_types.append('made_more_concise')
                elif len(edited.split()) > len(original.split()) * 1.2:
                    edit_types.append('added_more_detail')
                elif original.split()[0] != edited.split()[0]:
                    edit_types.append('changed_starter_word')
                else:
                    edit_types.append('minor_rewording')
                
            except:
                continue
        
        edit_counts = Counter(edit_types)
        
        return {
            'common_edit_types': dict(edit_counts.most_common()),
            'total_edits': len(edited_questions)
        }
    
    def _analyze_difficulty_bias(self, accepted: List[Question], rejected: List[Question]) -> str:
        """Analyze if faculty prefers easier/harder questions than requested."""
        
        if not accepted and not rejected:
            return 'as_requested'
        
        # Map difficulties to numeric
        diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
        
        # For accepted questions, check if actual difficulty matches intended
        # (We'd need intended difficulty stored separately - for now use heuristic)
        
        accepted_diffs = [diff_map.get(q.difficulty, 2) for q in accepted]
        rejected_diffs = [diff_map.get(q.difficulty, 2) for q in rejected]
        
        avg_accepted = sum(accepted_diffs) / len(accepted_diffs) if accepted_diffs else 2
        avg_rejected = sum(rejected_diffs) / len(rejected_diffs) if rejected_diffs else 2
        
        if avg_accepted < avg_rejected - 0.3:
            return 'prefers_easier'
        elif avg_accepted > avg_rejected + 0.3:
            return 'prefers_harder'
        else:
            return 'as_requested'
    
    def _analyze_verbosity(self, accepted: List[Question], rejected: List[Question]) -> str:
        """Analyze verbosity preference."""
        
        if not accepted:
            return 'moderate'
        
        # Average word count
        accepted_lengths = [len(q.question_text.split()) for q in accepted if q.question_text]
        avg_length = sum(accepted_lengths) / len(accepted_lengths) if accepted_lengths else 15
        
        if avg_length < 12:
            return 'concise'
        elif avg_length > 25:
            return 'detailed'
        else:
            return 'moderate'
    
    def _analyze_tone(self, accepted: List[Question], rejected: List[Question]) -> str:
        """Analyze preferred tone."""
        
        if not accepted:
            return 'formal'
        
        # Look for formal vs conversational indicators
        formal_indicators = ['analyze', 'evaluate', 'discuss', 'explain', 'describe']
        conversational_indicators = ['how', 'why', 'what if', 'can you', 'think about']
        
        formal_count = 0
        conversational_count = 0
        
        for q in accepted:
            text_lower = q.question_text.lower()
            
            if any(indicator in text_lower for indicator in formal_indicators):
                formal_count += 1
            
            if any(indicator in text_lower for indicator in conversational_indicators):
                conversational_count += 1
        
        if formal_count > conversational_count * 1.5:
            return 'formal'
        elif conversational_count > formal_count * 1.5:
            return 'conversational'
        else:
            return 'balanced'
    
    def get_preference_summary(self, faculty_id: str) -> str:
        """Get human-readable preference summary."""
        
        prefs = self.analyze_preferences(faculty_id)
        
        if prefs['status'] == 'insufficient_data':
            return prefs['message']
        
        summary_parts = [
            f"✅ Preference Learning Active ({prefs['total_reviews']} reviews)",
            f"",
            f"Acceptance Rate: {prefs['acceptance_rate']*100:.1f}%",
            f"",
            f"Preferences Detected:",
            f"  • Difficulty: {prefs['difficulty_bias'].replace('_', ' ').title()}",
            f"  • Verbosity: {prefs['verbosity_preference'].title()}",
            f"  • Tone: {prefs['tone_preference'].title()}",
            f"",
            f"Common Question Starters:",
        ]
        
        starters = prefs['preferred_question_style'].get('common_starters', {})
        for word, count in list(starters.items())[:3]:
            summary_parts.append(f"  • '{word}' ({count} times)")
        
        if prefs['edit_patterns'].get('common_edit_types'):
            summary_parts.append(f"")
            summary_parts.append(f"Common Edits:")
            for edit_type, count in list(prefs['edit_patterns']['common_edit_types'].items())[:3]:
                summary_parts.append(f"  • {edit_type.replace('_', ' ').title()} ({count} times)")
        
        return "\n".join(summary_parts)