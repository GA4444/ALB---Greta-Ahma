"""
Advanced AI Practice Generator - Ultra Personalized
---------------------------------------------------
Generates highly personalized exercises based on:
- User's specific mistakes
- Weakness patterns
- Learning progress
- Difficulty adaptation
- Spaced repetition principles
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pydantic import BaseModel
import random
import json
import re

from ..database import get_db
from .. import models

router = APIRouter()


# ============================================================================
# PATTERN NAMES - Albanian Translations
# ============================================================================

# Pattern names in Albanian for the spelling corpus
PATTERN_NAMES_SQ = {
    'pa_përgjigje': 'Pa Përgjigje',
    'e_saktë': 'E Saktë',
    'gabim_ë_e': 'Gabim ë/e',
    'gabim_ç_c': 'Gabim ç/c',
    'gabim_shkronjash_të_veçanta': 'Shkronja të Veçanta',
    'mungojnë_bashkëtingëllore_të_dyfishta': 'Mungojnë Bashkëtingëllore (ll, rr)',
    'bashkëtingëllore_shtesë': 'Bashkëtingëllore Shtesë',
    'gabim_dh_th': 'Gabim dh/th',
    'mungojnë_shkronja': 'Mungojnë Shkronja',
    'shkronja_shtesë': 'Shkronja Shtesë',
    'renditje_e_gabuar': 'Renditje e Gabuar',
    'zëvendësim_shkronjash': 'Zëvendësim Shkronjash',
}

# Descriptions in Albanian
PATTERN_DESCRIPTIONS_SQ = {
    'gabim_ë_e': 'Ngatërrimi i shkronjave ë dhe e',
    'gabim_ç_c': 'Ngatërrimi i shkronjave ç dhe c',
    'gabim_shkronjash_të_veçanta': 'Gabime me shkronjat e veçanta shqipe',
    'mungojnë_bashkëtingëllore_të_dyfishta': 'Harrohet të shkruhen dy bashkëtingëllore (ll, rr, nn)',
    'bashkëtingëllore_shtesë': 'Shtohen bashkëtingëllore të dyfishta ku nuk duhen',
    'gabim_dh_th': 'Harrohet shkronja e dytë e "dh" ose "th"',
    'mungojnë_shkronja': 'Harrohen shkronja në fjalë',
    'shkronja_shtesë': 'Shtohen shkronja që nuk duhen',
    'renditje_e_gabuar': 'Shkronjat janë në vend të gabuar',
    'zëvendësim_shkronjash': 'Një shkronjë zëvendësohet me një tjetër',
}

# ============================================================================
# SCHEMAS
# ============================================================================

class AdvancedPracticeRequest(BaseModel):
    user_id: str
    level_id: int
    count: int = 5  # Number of exercises to generate
    difficulty: Optional[str] = "adaptive"  # adaptive, easy, medium, hard
    focus_area: Optional[str] = None  # e.g., "diacritics", "double_consonants"


class PersonalizedExercise(BaseModel):
    id: str
    type: str  # discrimination, precision, context, fill_blank, error_detection
    prompt: str
    answer: str
    choices: Optional[List[str]] = None
    hint: str
    difficulty: str
    reason: str  # Why this exercise was generated
    focus_word: str
    mistake_pattern: Optional[str] = None


class AdvancedPracticeResponse(BaseModel):
    exercises: List[PersonalizedExercise]
    analysis: Dict[str, Any]
    recommendations: List[str]
    next_focus: str


# ============================================================================
# MISTAKE ANALYSIS ENGINE
# ============================================================================

class MistakeAnalyzer:
    """Advanced mistake pattern recognition"""
    
    @staticmethod
    def analyze_user_mistakes(db: Session, user_id: str, level_id: int) -> Dict[str, Any]:
        """
        Deep analysis of user's mistakes to identify patterns.
        
        Returns:
            {
                'patterns': {
                    'diacritics_ë_e': {'count': 5, 'words': [...], 'severity': 'high'},
                    'double_consonants': {'count': 3, 'words': [...], 'severity': 'medium'},
                    ...
                },
                'weak_words': [...],  # Words consistently wrong
                'improving_words': [...],  # Words getting better
                'mastered_words': [...],  # Words consistently right
                'overall_accuracy': 0.85,
                'trend': 'improving' | 'declining' | 'stable'
            }
        """
        
        # Get all attempts for this level
        attempts = db.query(models.Attempt).join(
            models.Exercise,
            models.Attempt.exercise_id == models.Exercise.id
        ).filter(
            models.Attempt.user_id == user_id,
            models.Exercise.level_id == level_id
        ).order_by(models.Attempt.id.desc()).limit(100).all()
        
        if not attempts:
            return {
                'patterns': {},
                'weak_words': [],
                'improving_words': [],
                'mastered_words': [],
                'overall_accuracy': 0.0,
                'trend': 'no_data'
            }
        
        # Analyze patterns
        patterns = defaultdict(lambda: {'count': 0, 'words': [], 'examples': []})
        word_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'attempts': []})
        
        for attempt in attempts:
            exercise = db.get(models.Exercise, attempt.exercise_id)
            if not exercise:
                continue
            
            word = exercise.answer
            word_performance[word]['total'] += 1
            word_performance[word]['attempts'].append(attempt.is_correct)
            
            if attempt.is_correct:
                word_performance[word]['correct'] += 1
            else:
                # Analyze the mistake
                pattern = MistakeAnalyzer._classify_mistake(word, attempt.response)
                patterns[pattern]['count'] += 1
                patterns[pattern]['words'].append(word)
                patterns[pattern]['examples'].append({
                    'correct': word,
                    'user': attempt.response,
                    'exercise_id': exercise.id
                })
        
        # Calculate severity for each pattern
        total_mistakes = sum(p['count'] for p in patterns.values())
        for pattern_name, pattern_data in patterns.items():
            percentage = (pattern_data['count'] / total_mistakes * 100) if total_mistakes > 0 else 0
            if percentage > 30:
                pattern_data['severity'] = 'high'
            elif percentage > 15:
                pattern_data['severity'] = 'medium'
            else:
                pattern_data['severity'] = 'low'
        
        # Categorize words by performance
        weak_words = []
        improving_words = []
        mastered_words = []
        
        for word, perf in word_performance.items():
            accuracy = perf['correct'] / perf['total']
            recent_trend = MistakeAnalyzer._calculate_trend(perf['attempts'])
            
            if accuracy < 0.4:
                weak_words.append({
                    'word': word,
                    'accuracy': accuracy,
                    'total': perf['total'],
                    'trend': recent_trend
                })
            elif accuracy > 0.8:
                mastered_words.append({
                    'word': word,
                    'accuracy': accuracy,
                    'total': perf['total']
                })
            elif recent_trend > 0:
                improving_words.append({
                    'word': word,
                    'accuracy': accuracy,
                    'trend': recent_trend
                })
            else:
                weak_words.append({
                    'word': word,
                    'accuracy': accuracy,
                    'total': perf['total'],
                    'trend': recent_trend
                })
        
        # Calculate overall metrics
        total_attempts = len(attempts)
        correct_attempts = sum(1 for a in attempts if a.is_correct)
        overall_accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0
        
        # Calculate trend (comparing recent vs older attempts)
        recent_accuracy = sum(1 for a in attempts[:20] if a.is_correct) / min(20, len(attempts)) if attempts else 0
        older_accuracy = sum(1 for a in attempts[20:40] if a.is_correct) / min(20, len(attempts[20:40])) if len(attempts) > 20 else recent_accuracy
        
        if recent_accuracy > older_accuracy + 0.1:
            trend = 'improving'
        elif recent_accuracy < older_accuracy - 0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'patterns': dict(patterns),
            'weak_words': sorted(weak_words, key=lambda x: x['accuracy'])[:10],
            'improving_words': sorted(improving_words, key=lambda x: -x['trend'])[:5],
            'mastered_words': sorted(mastered_words, key=lambda x: -x['accuracy'])[:5],
            'overall_accuracy': overall_accuracy,
            'trend': trend,
            'total_attempts': total_attempts
        }
    
    @staticmethod
    def _classify_mistake(correct: str, user_response: str) -> str:
        """
        Classify the type of mistake.
        Returns pattern names in ALBANIAN for the Albanian spelling corpus.
        """
        if not user_response:
            return "pa_përgjigje"
        
        c = correct.lower().strip()
        u = user_response.lower().strip()
        
        if c == u:
            return "e_saktë"
        
        # Check for diacritic mistakes (ë/e, ç/c)
        c_no_diac = c.replace('ë', 'e').replace('ç', 'c')
        u_no_diac = u.replace('ë', 'e').replace('ç', 'c')
        
        if c_no_diac == u_no_diac:
            if 'ë' in c and 'e' in u:
                return "gabim_ë_e"
            if 'ç' in c and 'c' in u:
                return "gabim_ç_c"
            return "gabim_shkronjash_të_veçanta"
        
        # Check for double consonants (ll, rr, etc.)
        if re.search(r'([lrns])\1', c) and not re.search(r'([lrns])\1', u):
            return "mungojnë_bashkëtingëllore_të_dyfishta"
        if not re.search(r'([lrns])\1', c) and re.search(r'([lrns])\1', u):
            return "bashkëtingëllore_shtesë"
        
        # Check for dh/th mistakes
        if ('dh' in c and 'd' in u) or ('th' in c and 't' in u):
            return "gabim_dh_th"
        
        # Check for missing letters
        if len(u) < len(c) and u in c:
            return "mungojnë_shkronja"
        
        # Check for extra letters
        if len(u) > len(c) and c in u:
            return "shkronja_shtesë"
        
        # Check for letter transposition (switching)
        if sorted(c) == sorted(u):
            return "renditje_e_gabuar"
        
        # Generic substitution
        return "zëvendësim_shkronjash"
    
    @staticmethod
    def _calculate_trend(attempts: List[bool]) -> float:
        """
        Calculate improvement trend from attempt history.
        Returns positive for improving, negative for declining.
        """
        if len(attempts) < 2:
            return 0.0
        
        # Weight recent attempts more heavily
        weights = [i / len(attempts) for i in range(len(attempts))]
        weighted_sum = sum(w * (1 if correct else 0) for w, correct in zip(weights, attempts))
        
        return weighted_sum / len(attempts)


# ============================================================================
# EXERCISE GENERATOR
# ============================================================================

class AdvancedExerciseGenerator:
    """Generates personalized exercises based on user analysis"""
    
    @staticmethod
    def generate_exercises(
        db: Session,
        user_id: str,
        level_id: int,
        analysis: Dict[str, Any],
        count: int = 5,
        difficulty: str = "adaptive"
    ) -> List[PersonalizedExercise]:
        """
        Generate highly personalized exercises.
        
        Strategy:
        1. Focus on weak areas (60% of exercises)
        2. Reinforce improving areas (20%)
        3. Challenge with new material (20%)
        """
        
        exercises = []
        exercise_types = []
        
        # Determine focus areas based on analysis
        patterns = analysis.get('patterns', {})
        weak_words = analysis.get('weak_words', [])
        
        # Priority: Most severe patterns
        priority_patterns = sorted(
            [(name, data) for name, data in patterns.items()],
            key=lambda x: (x[1].get('severity', 'low') == 'high', x[1]['count']),
            reverse=True
        )
        
        # Generate exercises
        for i in range(count):
            if i < count * 0.6 and weak_words:
                # 60%: Focus on weak words
                word_data = random.choice(weak_words[:5])
                word = word_data['word']
                
                # Find the pattern for this word
                mistake_pattern = AdvancedExerciseGenerator._find_pattern_for_word(
                    word, patterns
                )
                
                exercise = AdvancedExerciseGenerator._create_targeted_exercise(
                    db, word, mistake_pattern, difficulty, level_id
                )
                
            elif i < count * 0.8 and priority_patterns:
                # 20%: Focus on pattern practice
                pattern_name, pattern_data = priority_patterns[i % len(priority_patterns)]
                words = pattern_data.get('words', [])
                
                if words:
                    word = random.choice(words[:5])
                    exercise = AdvancedExerciseGenerator._create_pattern_exercise(
                        db, word, pattern_name, difficulty, level_id
                    )
                else:
                    continue
            else:
                # 20%: New material for challenge
                exercise = AdvancedExerciseGenerator._create_challenge_exercise(
                    db, level_id, difficulty
                )
            
            if exercise:
                # Avoid duplicate exercise types in a row
                if not exercise_types or exercise_types[-1] != exercise.type:
                    exercises.append(exercise)
                    exercise_types.append(exercise.type)
        
        return exercises
    
    @staticmethod
    def _find_pattern_for_word(word: str, patterns: Dict[str, Any]) -> Optional[str]:
        """Find which pattern this word is associated with"""
        for pattern_name, pattern_data in patterns.items():
            if word in pattern_data.get('words', []):
                return pattern_name
        return None
    
    @staticmethod
    def _create_targeted_exercise(
        db: Session,
        word: str,
        mistake_pattern: Optional[str],
        difficulty: str,
        level_id: int
    ) -> PersonalizedExercise:
        """Create an exercise targeted at a specific weak word"""
        
        import uuid
        
        # Get level info and check for special category
        level = db.get(models.Level, level_id)
        level_exercises = db.query(models.Exercise).filter(
            models.Exercise.level_id == level_id,
            models.Exercise.enabled == True
        ).limit(5).all()
        
        # Detect level theme/category
        level_category = None
        if level_exercises:
            # Check if this is a special category level (e.g., ALBANIAN_OR_LOANWORD)
            first_ex = level_exercises[0]
            if first_ex.category == models.CategoryEnum.ALBANIAN_OR_LOANWORD:
                level_category = 'ALBANIAN_OR_LOANWORD'
        
        # If level is ALBANIAN_OR_LOANWORD theme, generate appropriate exercise
        if level_category == 'ALBANIAN_OR_LOANWORD':
            ex_type = 'theme_based'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_loanword_exercise(
                db, level_id
            )
            reason = f"Stërvitje për temën: Shqip vs Huazim"
            
        # Choose exercise type based on mistake pattern
        elif mistake_pattern and 'gabim_' in mistake_pattern and ('ë_e' in mistake_pattern or 'ç_c' in mistake_pattern or 'shkronjash_të_veçanta' in mistake_pattern):
            ex_type = 'discrimination'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_discrimination_exercise(
                word, focus='diacritics'
            )
            reason = f"Fokus në gabimet me ë/e ose ç/c që ke bërë me '{word}'"
            
        elif mistake_pattern and 'bashkëtingëllore' in mistake_pattern:
            ex_type = 'precision'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_precision_exercise(
                word, focus='double_consonants'
            )
            reason = f"Fokus në bashkëtingëllore të dyfishta në '{word}'"
            
        elif mistake_pattern and 'dh_th' in mistake_pattern:
            ex_type = 'context'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_context_exercise(
                word, focus='digraphs'
            )
            reason = f"Përforcim i 'dh' dhe 'th' në '{word}'"
            
        else:
            # Default: error detection
            ex_type = 'error_detection'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_error_detection_exercise(word)
            reason = f"Identifikimi i gabimeve në '{word}'"
        
        return PersonalizedExercise(
            id=str(uuid.uuid4()),
            type=ex_type,
            prompt=prompt,
            answer=answer,
            choices=choices,
            hint=hint,
            difficulty=difficulty,
            reason=reason,
            focus_word=word,
            mistake_pattern=mistake_pattern
        )
    
    @staticmethod
    def _create_pattern_exercise(
        db: Session,
        word: str,
        pattern_name: str,
        difficulty: str,
        level_id: int
    ) -> PersonalizedExercise:
        """Create exercise focused on a specific mistake pattern"""
        
        import uuid
        
        if 'gabim_' in pattern_name and ('ë_e' in pattern_name or 'ç_c' in pattern_name or 'shkronjash_të_veçanta' in pattern_name):
            ex_type = 'discrimination'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_discrimination_exercise(
                word, focus='diacritics'
            )
            # Get readable name from mapping
            readable_name = PATTERN_NAMES_SQ.get(pattern_name, pattern_name)
            reason = f"Stërvitje për: {readable_name}"
            
        elif 'bashkëtingëllore' in pattern_name:
            ex_type = 'fill_blank'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_fill_blank_exercise(
                word, focus='double_consonants'
            )
            readable_name = PATTERN_NAMES_SQ.get(pattern_name, pattern_name)
            reason = f"Stërvitje për: {readable_name}"
            
        else:
            ex_type = 'context'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_context_exercise(
                word
            )
            reason = f"Pattern training: {pattern_name}"
        
        return PersonalizedExercise(
            id=str(uuid.uuid4()),
            type=ex_type,
            prompt=prompt,
            answer=answer,
            choices=choices,
            hint=hint,
            difficulty=difficulty,
            reason=reason,
            focus_word=word,
            mistake_pattern=pattern_name
        )
    
    @staticmethod
    def _create_challenge_exercise(
        db: Session,
        level_id: int,
        difficulty: str
    ) -> Optional[PersonalizedExercise]:
        """Create a challenging exercise from new material, respecting level theme"""
        
        import uuid
        
        # Get exercises from this level
        exercises = db.query(models.Exercise).filter(
            models.Exercise.level_id == level_id,
            models.Exercise.enabled == True
        ).order_by(func.random()).limit(10).all()
        
        if not exercises:
            return None
        
        exercise = random.choice(exercises)
        
        # Check if this level has a special theme (e.g., ALBANIAN_OR_LOANWORD)
        if exercise.category == models.CategoryEnum.ALBANIAN_OR_LOANWORD:
            # Generate loanword theme exercise
            ex_type = 'theme_based'
            prompt, answer, choices, hint = AdvancedExerciseGenerator._build_loanword_exercise(
                db, level_id
            )
            reason = "Sfidë: Identifikimi i fjalëve shqipe dhe huazimeve"
            word = exercise.prompt.replace("'", "").replace(" është:", "").strip()
            
        else:
            # Standard spelling/writing exercises
            word = exercise.answer
            ex_type = random.choice(['discrimination', 'context', 'fill_blank'])
            
            if ex_type == 'discrimination':
                prompt, answer, choices, hint = AdvancedExerciseGenerator._build_discrimination_exercise(
                    word, focus='challenge'
                )
            elif ex_type == 'fill_blank':
                prompt, answer, choices, hint = AdvancedExerciseGenerator._build_fill_blank_exercise(
                    word, focus='challenge'
                )
            else:
                prompt, answer, choices, hint = AdvancedExerciseGenerator._build_context_exercise(
                    word, focus='challenge'
                )
            
            reason = "Sfidë me material të ri për të zgjeruar njohuritë"
        
        return PersonalizedExercise(
            id=str(uuid.uuid4()),
            type=ex_type,
            prompt=prompt,
            answer=answer,
            choices=choices,
            hint=hint,
            difficulty=difficulty,
            reason=reason,
            focus_word=word,
            mistake_pattern=None
        )
    
    # ========================================================================
    # EXERCISE BUILDERS
    # ========================================================================
    
    @staticmethod
    def _build_loanword_exercise(
        db: Session,
        level_id: int
    ) -> Tuple[str, str, List[str], str]:
        """
        Build an exercise for ALBANIAN_OR_LOANWORD category.
        Generates exercises like: 'kompjuter' është: [Shqip / Huazim]
        """
        
        # Get exercises from this level
        level_exercises = db.query(models.Exercise).filter(
            models.Exercise.level_id == level_id,
            models.Exercise.category == models.CategoryEnum.ALBANIAN_OR_LOANWORD,
            models.Exercise.enabled == True
        ).order_by(func.random()).limit(10).all()
        
        if not level_exercises:
            # Fallback
            return (
                "[Temë] A është kjo fjalë shqipe apo huazim?",
                "Shqip",
                ["Shqip", "Huazim"],
                "Mendo nëse fjala vjen nga gjuha shqipe apo është marrë nga gjuhë të tjera."
            )
        
        # Pick a random word from this level
        exercise = random.choice(level_exercises)
        word = exercise.prompt.replace("'", "").replace(" është:", "").strip()
        answer = exercise.answer  # "Shqip" or "Huazim"
        
        prompt = (
            f"[Temë: Shqip vs Huazim] A është kjo fjalë shqipe apo huazim?\n\n"
            f"Fjala: {word}\n\n"
            f"Zgjedh dhe shkruaj: Shqip ose Huazim"
        )
        
        choices = ["Shqip", "Huazim"]
        
        hint = (
            "Fjalët shqipe janë autentike shqiptare (p.sh., shmang, libër). "
            "Huazimet janë marrë nga gjuhë të tjera (p.sh., kompjuter, telefon)."
        )
        
        return prompt, answer, choices, hint
    
    @staticmethod
    def _build_discrimination_exercise(
        word: str,
        focus: str = 'general'
    ) -> Tuple[str, str, Optional[List[str]], str]:
        """Build a discrimination exercise (choose correct spelling)"""
        
        # Generate distractors based on focus
        distractors = []
        
        if focus == 'diacritics':
            # Confuse ë/e and ç/c
            distractors.append(word.replace('ë', 'e'))
            distractors.append(word.replace('ç', 'c'))
            if 'ë' in word and 'ç' in word:
                distractors.append(word.replace('ë', 'e').replace('ç', 'c'))
        
        elif focus == 'double_consonants':
            # Add/remove double consonants
            distractors.append(re.sub(r'([lrns])\1', r'\1', word))  # Remove doubles
            if 'l' in word:
                distractors.append(word.replace('l', 'll', 1))
        
        else:
            # General mistakes
            distractors.append(word.replace('ë', 'e'))
            distractors.append(word.replace('ç', 'c'))
            if len(word) > 3:
                distractors.append(word[:-1])  # Missing last letter
        
        # Remove duplicates and empties
        distractors = [d for d in distractors if d and d != word][:3]
        
        # Ensure we have 3 options including correct
        while len(distractors) < 2:
            distractors.append(word + word[-1])
        
        choices = [word] + distractors[:2]
        random.shuffle(choices)
        
        prompt = f"[Dallim Drejtshkrimi] Zgjedh variantin e saktë dhe shkruaje si përgjigje:\n\n"
        for i, choice in enumerate(choices, 1):
            prompt += f"{chr(64+i)}) {choice}\n"
        
        hint = f"Fokus te {focus}. Shiko kujdesin me shkronjat e veçanta shqipe!"
        
        return prompt, word, choices, hint
    
    @staticmethod
    def _build_precision_exercise(
        word: str,
        focus: str = 'general'
    ) -> Tuple[str, str, None, str]:
        """Build a precision exercise (count and write exactly)"""
        
        letter_count = len(word)
        
        if focus == 'double_consonants':
            doubles = re.findall(r'([lrns])\1', word)
            hint_text = ""
            if doubles:
                hint_text = f" Kujdes: ka shkronja të dyfishta ({', '.join(doubles)})!"
        else:
            hint_text = ""
        
        prompt = (
            f"[Saktësi Absolute] Shkruaj fjalën me SAKTËSISHT {letter_count} shkronja.\n\n"
            f"Fjala: {word}\n\n"
            f"Kontrollo çdo shkronjë para se të dërgosh!{hint_text}"
        )
        
        hint = "Numëro shkronjat me kujdes. Mos harro asnjë dhe mos shto asnjë shtesë!"
        
        return prompt, word, None, hint
    
    @staticmethod
    def _build_context_exercise(
        word: str,
        focus: str = 'general'
    ) -> Tuple[str, str, None, str]:
        """
        Build a context exercise (use in sentence).
        
        IMPORTANT: Uses grammatically correct Albanian sentences.
        Avoids case inflection issues by using nominative contexts.
        """
        
        # Generate grammatically correct sentences
        # Using patterns that work with nominative case to avoid errors
        word_cap = word.capitalize()
        
        # Safe sentence patterns (no case inflection needed)
        # Note: We use generic patterns that work for both singular/plural
        sentences = [
            f"Sot mësuam për: {word}.",
            f"Shkruaj fjalën {word} me kujdes.",
            f"Fjala e sotme është: {word}.",
            f"Përsërite fjalën: {word}.",
            f"Në fletore shkruaj: {word}.",
            f"Kjo është fjala {word}.",
            f"Mëso fjalën: {word}.",
            f"Studioje fjalën: {word}.",
        ]
        
        sentence = random.choice(sentences)
        
        prompt = (
            f"[Kontekst] Lexo fjalinë dhe shkruaj vetëm fjalën e theksuar:\n\n"
            f"\"{sentence}\"\n\n"
            f"Shkruaj fjalën: {word}"
        )
        
        hint = "Shiko fjalën në kontekst. Kjo të ndihmon të kujtosh drejtshkrimin e saktë!"
        
        return prompt, word, None, hint
    
    @staticmethod
    def _build_fill_blank_exercise(
        word: str,
        focus: str = 'general'
    ) -> Tuple[str, str, Optional[List[str]], str]:
        """Build a fill-in-the-blank exercise"""
        
        if len(word) < 3:
            # Too short for blanks
            return AdvancedExerciseGenerator._build_context_exercise(word, focus)
        
        # Create blanks based on focus
        if focus == 'double_consonants':
            # Blank out double consonants
            pattern = re.search(r'([lrns])\1', word)
            if pattern:
                pos = pattern.start()
                blanked = word[:pos] + '_' * 2 + word[pos+2:]
                hint_text = "Kujdes: këtu duhen dy shkronja të njëjta!"
            else:
                pos = len(word) // 2
                blanked = word[:pos] + '_' + word[pos+1:]
                hint_text = "Plotëso shkronjën që mungon."
        
        elif focus == 'diacritics':
            # Blank out ë or ç
            if 'ë' in word:
                blanked = word.replace('ë', '_', 1)
                hint_text = "Kujdes: ë apo e?"
            elif 'ç' in word:
                blanked = word.replace('ç', '_', 1)
                hint_text = "Kujdes: ç apo c?"
            else:
                pos = len(word) // 2
                blanked = word[:pos] + '_' + word[pos+1:]
                hint_text = "Plotëso shkronjën që mungon."
        
        else:
            # Generic blank
            pos = len(word) // 2
            blanked = word[:pos] + '_' + word[pos+1:]
            hint_text = "Plotëso shkronjën që mungon."
        
        prompt = (
            f"[Plotëso Boshllëkun] Shkruaj fjalën e plotë:\n\n"
            f"Fjala me boshllëk: {blanked}\n\n"
            f"{hint_text}"
        )
        
        hint = "Mendo për fjalën e plotë dhe shkruaje saktë!"
        
        return prompt, word, None, hint
    
    @staticmethod
    def _build_error_detection_exercise(
        word: str
    ) -> Tuple[str, str, Optional[List[str]], str]:
        """Build an error detection exercise"""
        
        # Create an incorrect version
        if 'ë' in word:
            wrong = word.replace('ë', 'e', 1)
            error_type = "ë → e"
        elif 'ç' in word:
            wrong = word.replace('ç', 'c', 1)
            error_type = "ç → c"
        elif re.search(r'([lrns])\1', word):
            wrong = re.sub(r'([lrns])\1', r'\1', word, 1)
            error_type = "bashkëtingëllore e dyfishë"
        else:
            # Remove a letter
            wrong = word[:len(word)//2] + word[len(word)//2+1:]
            error_type = "shkronjë që mungon"
        
        prompt = (
            f"[Gjej Gabimin] Fjala më poshtë ka një gabim. Shkruaj versionin e saktë:\n\n"
            f"Fjala e gabuar: {wrong}\n\n"
            f"Shkruaj versionin e saktë:"
        )
        
        hint = f"Kujdes: gabimi është në {error_type}!"
        
        return prompt, word, None, hint


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate personalized study recommendations"""
    
    recommendations = []
    
    patterns = analysis.get('patterns', {})
    weak_words = analysis.get('weak_words', [])
    trend = analysis.get('trend', 'stable')
    overall_accuracy = analysis.get('overall_accuracy', 0.0)
    
    # Overall performance
    if overall_accuracy < 0.5:
        recommendations.append(
            "🎯 Fokusohu në themel: Merr kohën tënde për çdo ushtrim dhe përsërit fjalët e vështira."
        )
    elif overall_accuracy < 0.7:
        recommendations.append(
            "📈 Po përparon! Vazhdo të praktikosh rregullisht për të përmirësuar saktësinë."
        )
    else:
        recommendations.append(
            "⭐ Performancë e shkëlqyer! Sfidohu me ushtrime më të vështira."
        )
    
    # Trend-based
    if trend == 'improving':
        recommendations.append(
            "🚀 Trend pozitiv! Strategjia jote e mësimit po funksionon. Vazhdo kështu!"
        )
    elif trend == 'declining':
        recommendations.append(
            "⚠️ Saktësia po bie. Ndoshta ke nevojë për një pushim ose një approach të ri?"
        )
    
    # Pattern-specific
    for pattern_name, pattern_data in sorted(
        patterns.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:2]:
        severity = pattern_data.get('severity', 'low')
        severity_sq = {'high': 'I LARTË', 'medium': 'MESATAR', 'low': 'I ULËT'}.get(severity, severity.upper())
        
        # Get readable pattern name
        readable_name = PATTERN_NAMES_SQ.get(pattern_name, pattern_name)
        
        if 'gabim_ë_e' in pattern_name:
            recommendations.append(
                f"📝 {severity_sq}: Praktiko dallimin ë/e. Mundohu të dëgjosh tingullin dhe jo vetëm ta shkruash."
            )
        elif 'gabim_ç_c' in pattern_name:
            recommendations.append(
                f"📝 {severity_sq}: Fokusohu te ç/c. Përdor shembuj konkretë: çanta vs. canta."
            )
        elif 'bashkëtingëllore' in pattern_name:
            recommendations.append(
                f"📝 {severity_sq}: Kujdes me ll, rr, nn! Shqyrtoji këto me audio."
            )
        elif 'dh_th' in pattern_name:
            recommendations.append(
                f"📝 {severity_sq}: Përqendrohu te 'dh' dhe 'th'. Janë dy shkronja, jo një!"
            )
    
    # Weak words
    if len(weak_words) > 3:
        top_weak = ', '.join([w['word'] for w in weak_words[:3]])
        recommendations.append(
            f"🎯 Fjalë me prioritet: {top_weak}. Krijoni kartela flash ose shkruani 5 herë secilën!"
        )
    
    # Spaced repetition
    if len(weak_words) > 0:
        recommendations.append(
            "🔄 Përdor SRS (Spaced Repetition): Përsërit fjalët e vështira pas 1 ditë, pastaj 3 ditë, pastaj 7 ditë."
        )
    
    # Practice frequency
    if trend != 'improving':
        recommendations.append(
            "📅 Praktiko çdo ditë për 10-15 minuta. Konsistenca është çelësi!"
        )
    
    return recommendations[:5]  # Top 5 recommendations


def determine_next_focus(analysis: Dict[str, Any]) -> str:
    """Determine what the user should focus on next"""
    
    patterns = analysis.get('patterns', {})
    weak_words = analysis.get('weak_words', [])
    
    if not patterns:
        return "Vazhdo të praktikosh! Do të gjenerojmë ushtrime të personalizuara kur të kemi më shumë të dhëna."
    
    # Find most severe pattern
    priority_pattern = max(
        patterns.items(),
        key=lambda x: (x[1].get('severity', 'low') == 'high', x[1]['count'])
    )
    
    pattern_name, pattern_data = priority_pattern
    
    focus_messages = {
        'gabim_ë_e': "Fokusohu te dallimi i 'ë' dhe 'e'. Kjo është baza e drejtshkrimit shqip!",
        'gabim_ç_c': "Praktiko shkronjën 'ç'. Është shkronjë e veçantë shqipe!",
        'mungojnë_bashkëtingëllore_të_dyfishta': "Praktiko bashkëtingëllore të dyfishta (ll, rr, nn). Dëgjoji me audio!",
        'bashkëtingëllore_shtesë': "Kujdes të mos shtosh bashkëtingëllore të dyfishta ku nuk duhen!",
        'gabim_dh_th': "Fokusohu te 'dh' dhe 'th'. Janë DY shkronja bashkë!",
        'mungojnë_shkronja': "Shkruaj më ngadalë dhe kontrollo që të kesh të gjitha shkronjat.",
        'shkronja_shtesë': "Lexo përsëri përpara se të dërgosh. Mos shto shkronja shtesë!",
        'renditje_e_gabuar': "Kujdes me rendin e shkronjave. Shkruaj shkronjë pas shkronje!",
        'zëvendësim_shkronjash': "Kontrollo çdo shkronjë me kujdes. Mos zëvendëso shkronjat!",
    }
    
    # Get readable name from mapping
    readable_name = PATTERN_NAMES_SQ.get(pattern_name, pattern_name)
    return focus_messages.get(pattern_name, f"Fokusohu te {readable_name}")


# ============================================================================
# MAIN ENDPOINT
# ============================================================================

@router.post("/ai/advanced-practice", response_model=AdvancedPracticeResponse)
async def generate_advanced_practice(
    request: AdvancedPracticeRequest,
    db: Session = Depends(get_db)
):
    """
    Generate ultra-personalized practice exercises.
    
    This endpoint:
    1. Analyzes user's mistake patterns
    2. Identifies weak areas
    3. Generates targeted exercises
    4. Provides personalized recommendations
    """
    
    # Verify level exists
    level = db.get(models.Level, request.level_id)
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    
    # Analyze user's mistakes and patterns
    analysis = MistakeAnalyzer.analyze_user_mistakes(
        db,
        request.user_id,
        request.level_id
    )
    
    # Generate personalized exercises
    exercises = AdvancedExerciseGenerator.generate_exercises(
        db,
        request.user_id,
        request.level_id,
        analysis,
        count=request.count,
        difficulty=request.difficulty or "adaptive"
    )
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis)
    
    # Determine next focus area
    next_focus = determine_next_focus(analysis)
    
    return AdvancedPracticeResponse(
        exercises=exercises,
        analysis={
            'overall_accuracy': analysis['overall_accuracy'],
            'trend': analysis['trend'],
            'total_attempts': analysis.get('total_attempts', 0),
            'weak_count': len(analysis.get('weak_words', [])),
            'mastered_count': len(analysis.get('mastered_words', [])),
            'top_patterns': [
                {
                    'name': PATTERN_NAMES_SQ.get(name, name),  # Use Albanian name with stars and bold
                    'name_key': name,  # Keep original key for logic
                    'count': data['count'],
                    'severity': data.get('severity', 'low'),
                    'severity_sq': {'high': 'I Lartë', 'medium': 'Mesatar', 'low': 'I Ulët'}.get(data.get('severity', 'low'), 'I Ulët'),
                    'description': PATTERN_DESCRIPTIONS_SQ.get(name, '')
                }
                for name, data in sorted(
                    analysis.get('patterns', {}).items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:3]
            ]
        },
        recommendations=recommendations,
        next_focus=next_focus
    )


@router.get("/ai/practice-progress/{user_id}/{level_id}")
async def get_practice_progress(
    user_id: str,
    level_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed progress for AI practice"""
    
    analysis = MistakeAnalyzer.analyze_user_mistakes(db, user_id, level_id)
    
    return {
        'overall_accuracy': analysis['overall_accuracy'],
        'trend': analysis['trend'],
        'weak_words': analysis['weak_words'],
        'improving_words': analysis['improving_words'],
        'mastered_words': analysis['mastered_words'],
        'patterns': {
            name: {
                'count': data['count'],
                'severity': data.get('severity', 'low'),
                'example_count': len(data.get('examples', []))
            }
            for name, data in analysis.get('patterns', {}).items()
        }
    }
