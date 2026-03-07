"""
Answer Shuffler Utility
-----------------------
Randomizes answer choices in exercises to prevent patterns where
the correct answer is always in the first position.
"""

import random
import json
from typing import Dict, List, Any, Optional


def shuffle_exercise_choices(exercise_data: str, seed: Optional[int] = None) -> str:
    """
    Shuffle choices in exercise data while maintaining data integrity.
    
    Args:
        exercise_data: JSON string containing exercise data
        seed: Optional seed for deterministic shuffling (use exercise_id for consistency)
    
    Returns:
        Shuffled JSON string
    """
    if not exercise_data:
        return exercise_data
    
    try:
        data = json.loads(exercise_data)
        
        # Only shuffle if choices exist and there are multiple choices
        if 'choices' in data and isinstance(data['choices'], list) and len(data['choices']) > 1:
            choices = data['choices'].copy()
            
            # Use seed for deterministic shuffling per session
            if seed is not None:
                random.seed(seed)
            
            random.shuffle(choices)
            data['choices'] = choices
            
        return json.dumps(data, ensure_ascii=False)
    
    except (json.JSONDecodeError, TypeError):
        # If data is not valid JSON, return as is
        return exercise_data


def shuffle_exercise_dict(exercise: Dict[str, Any], use_id_seed: bool = False) -> Dict[str, Any]:
    """
    Shuffle choices in an exercise dictionary.
    
    Args:
        exercise: Exercise dictionary with 'data' field
        use_id_seed: If True, use exercise['id'] as seed for consistent shuffling
    
    Returns:
        Exercise dictionary with shuffled choices
    """
    if 'data' not in exercise or not exercise['data']:
        return exercise
    
    seed = exercise.get('id') if use_id_seed else None
    exercise['data'] = shuffle_exercise_choices(exercise['data'], seed=seed)
    
    return exercise


def validate_exercise_choices(exercise_data: str, correct_answer: str) -> Dict[str, Any]:
    """
    Validate that exercise choices include the correct answer.
    
    Args:
        exercise_data: JSON string containing exercise data
        correct_answer: The correct answer for this exercise
    
    Returns:
        Validation result dictionary with 'valid', 'message', and 'issues' keys
    """
    result = {
        'valid': True,
        'message': '',
        'issues': []
    }
    
    if not exercise_data:
        result['valid'] = False
        result['message'] = 'No exercise data provided'
        return result
    
    try:
        data = json.loads(exercise_data)
        
        if 'choices' in data and isinstance(data['choices'], list):
            choices = data['choices']
            
            # Check if correct answer is in choices
            # Normalize for comparison
            normalized_choices = [c.lower().strip() for c in choices]
            normalized_answer = correct_answer.lower().strip()
            
            if normalized_answer not in normalized_choices:
                result['valid'] = False
                result['issues'].append(
                    f"Correct answer '{correct_answer}' not found in choices: {choices}"
                )
            
            # Check for duplicates
            if len(choices) != len(set(normalized_choices)):
                result['issues'].append(
                    f"Duplicate choices found: {choices}"
                )
            
            # Check for empty choices
            if any(not choice.strip() for choice in choices):
                result['issues'].append(
                    "Empty or whitespace-only choices found"
                )
        
        if result['issues']:
            result['message'] = '; '.join(result['issues'])
            result['valid'] = False
        else:
            result['message'] = 'Exercise choices are valid'
        
        return result
    
    except (json.JSONDecodeError, TypeError) as e:
        result['valid'] = False
        result['message'] = f'Invalid JSON data: {str(e)}'
        return result


def get_choice_statistics(exercises: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze choice distribution in exercises.
    
    Args:
        exercises: List of exercise dictionaries
    
    Returns:
        Statistics dictionary
    """
    stats = {
        'total_exercises': len(exercises),
        'exercises_with_choices': 0,
        'correct_answer_positions': {},  # position -> count
        'avg_choices_per_exercise': 0,
        'exercises_with_issues': []
    }
    
    total_choices = 0
    
    for exercise in exercises:
        if 'data' not in exercise or not exercise['data']:
            continue
        
        try:
            data = json.loads(exercise['data'])
            
            if 'choices' in data and isinstance(data['choices'], list):
                stats['exercises_with_choices'] += 1
                choices = data['choices']
                total_choices += len(choices)
                
                # Find position of correct answer
                answer = exercise.get('answer', '').lower().strip()
                normalized_choices = [c.lower().strip() for c in choices]
                
                try:
                    position = normalized_choices.index(answer)
                    stats['correct_answer_positions'][position] = \
                        stats['correct_answer_positions'].get(position, 0) + 1
                except ValueError:
                    stats['exercises_with_issues'].append({
                        'id': exercise.get('id'),
                        'prompt': exercise.get('prompt', '')[:50],
                        'issue': 'Correct answer not in choices'
                    })
        
        except (json.JSONDecodeError, TypeError):
            continue
    
    if stats['exercises_with_choices'] > 0:
        stats['avg_choices_per_exercise'] = total_choices / stats['exercises_with_choices']
    
    return stats


# ============================================================================
# CONVENIENCE FUNCTIONS FOR API USE
# ============================================================================

def shuffle_exercises_list(exercises: List[Dict[str, Any]], seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Shuffle choices for a list of exercises.
    
    Args:
        exercises: List of exercise dictionaries
        seed: Base seed for shuffling (each exercise gets seed + exercise_id)
    
    Returns:
        List of exercises with shuffled choices
    """
    shuffled_exercises = []
    
    for exercise in exercises:
        # Use unique seed per exercise for consistency within session
        exercise_seed = None
        if seed is not None and 'id' in exercise:
            exercise_seed = seed + exercise['id']
        
        shuffled_exercise = shuffle_exercise_dict(exercise.copy(), use_id_seed=False)
        
        # Apply seed if provided
        if exercise_seed is not None and shuffled_exercise.get('data'):
            shuffled_exercise['data'] = shuffle_exercise_choices(
                shuffled_exercise['data'],
                seed=exercise_seed
            )
        
        shuffled_exercises.append(shuffled_exercise)
    
    return shuffled_exercises
