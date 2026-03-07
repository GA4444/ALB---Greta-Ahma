"""
Albanian Corpus Validator
-------------------------
Validates spelling and quality of the Albanian language corpus.
Checks for common mistakes in exercises, prompts, and answers.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Exercise, Course, Level
from sqlalchemy import func
import json
import re
from typing import List, Dict, Any, Tuple


# ============================================================================
# ALBANIAN SPELLING RULES
# ============================================================================

COMMON_MISTAKES = {
    # Common confusion patterns (STRICT - only real mistakes!)
    'ë vs e (në fjalë)': [
        (r'\bshtepi\b', 'shtëpi'),
        (r'\brruge\b', 'rrugë'),
        (r'\bpershendetje\b', 'përshëndetje'),
        (r'\bdjete\b', 'dhjetë'),
        (r'\bdhjete\b', 'dhjetë'),
        (r'\bfemije\b', 'fëmijë'),
        (r'\bpune\b', 'punë'),
        (r'\bmesues\b', 'mësues'),
    ],
    'ç vs c': [
        (r'\bcanta\b', 'çanta'),
        (r'\bcelesi\b', 'çelësi'),
        (r'\bcfare\b', 'çfarë'),
        (r'\bcdo\b', 'çdo'),
    ],
    'Missing dh': [
        (r'\bde\b(?!\s+të|\s+e|\s+dhe)', 'dhe'),  # "de" -> "dhe" (but not "de të", "de e")
        (r'\bdete\b', 'dhjetë'),
    ],
}

ALBANIAN_LETTERS = set('aAbBcCçÇdDdhDHdDðÐeEëËfFgGgGhHiIjJkKlLllLLmMnNnjNJoOpPqQrRrrRRsShShtHTthTHuUvVxXxHXHyYzZzhZH')

# Common words that should be checked
CORRECT_WORDS = {
    'dhe', 'shtëpi', 'përshëndetje', 'dhjetë', 'çanta', 'çelësi',
    'çfarë', 'rrugë', 'mësuesi', 'prindërit', 'fëmijë', 'bukë',
    'ujë', 'zog', 'zogj', 'mace', 'qen', 'libër', 'fletore'
}


def check_albanian_spelling(text: str) -> List[Dict[str, str]]:
    """
    Check text for common Albanian spelling mistakes.
    
    Returns:
        List of potential issues found
    """
    issues = []
    
    if not text:
        return issues
    
    # Check for common mistake patterns
    for category, patterns in COMMON_MISTAKES.items():
        for pattern, correction in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    'category': category,
                    'found': pattern,
                    'suggestion': correction,
                    'text': text
                })
    
    return issues


def validate_exercise(exercise: Exercise) -> Dict[str, Any]:
    """
    Validate a single exercise for quality and correctness.
    
    Returns:
        Validation result dictionary
    """
    result = {
        'id': exercise.id,
        'prompt': exercise.prompt,
        'answer': exercise.answer,
        'issues': [],
        'warnings': [],
        'is_valid': True
    }
    
    # Check prompt
    if not exercise.prompt or len(exercise.prompt.strip()) == 0:
        result['issues'].append('Empty prompt')
        result['is_valid'] = False
    else:
        # Check for spelling issues in prompt
        prompt_issues = check_albanian_spelling(exercise.prompt)
        if prompt_issues:
            result['warnings'].extend([
                f"Prompt spelling: {issue['category']} - found '{issue['found']}', suggest '{issue['suggestion']}'"
                for issue in prompt_issues
            ])
    
    # Check answer
    if not exercise.answer or len(exercise.answer.strip()) == 0:
        result['issues'].append('Empty answer')
        result['is_valid'] = False
    else:
        # Check for spelling issues in answer
        answer_issues = check_albanian_spelling(exercise.answer)
        if answer_issues:
            result['issues'].extend([
                f"Answer spelling: {issue['category']} - found '{issue['found']}', suggest '{issue['suggestion']}'"
                for issue in answer_issues
            ])
            result['is_valid'] = False
    
    # Check data (choices)
    if exercise.data:
        try:
            data = json.loads(exercise.data)
            
            # Validate choices if they exist
            if 'choices' in data and isinstance(data['choices'], list):
                choices = data['choices']
                
                # Only validate if choices list is not empty
                if len(choices) > 0:
                    # Check if answer is in choices
                    normalized_choices = [c.lower().strip() for c in choices]
                    normalized_answer = exercise.answer.lower().strip()
                    
                    if normalized_answer not in normalized_choices:
                        result['issues'].append(
                            f"Answer '{exercise.answer}' not found in choices: {choices}"
                        )
                        result['is_valid'] = False
                    
                    # Check for duplicate choices
                    if len(choices) != len(set(normalized_choices)):
                        result['warnings'].append(f"Duplicate choices: {choices}")
                    
                    # Check for empty choices
                    if any(not choice.strip() for choice in choices):
                        result['issues'].append("Empty choice found")
                        result['is_valid'] = False
                    
                    # Check each choice for spelling
                    for idx, choice in enumerate(choices):
                        choice_issues = check_albanian_spelling(choice)
                        if choice_issues:
                            result['warnings'].extend([
                                f"Choice {idx+1} spelling: {issue['category']} - '{issue['found']}' -> '{issue['suggestion']}'"
                                for issue in choice_issues
                            ])
                    
                    # Check answer position (warn if always first)
                    try:
                        answer_position = normalized_choices.index(normalized_answer)
                        if answer_position == 0:
                            result['warnings'].append("Answer is in first position (will be randomized)")
                    except ValueError:
                        pass  # Already caught above
        
        except (json.JSONDecodeError, TypeError) as e:
            result['issues'].append(f"Invalid JSON data: {str(e)}")
            result['is_valid'] = False
    
    return result


def validate_corpus(db: SessionLocal, limit: int = None, verbose: bool = True) -> Dict[str, Any]:
    """
    Validate the entire Albanian corpus.
    
    Args:
        db: Database session
        limit: Optional limit on number of exercises to check
        verbose: Print progress
    
    Returns:
        Validation statistics and issues
    """
    query = db.query(Exercise)
    if limit:
        exercises = query.limit(limit).all()
    else:
        exercises = query.all()
    
    stats = {
        'total_exercises': len(exercises),
        'valid_exercises': 0,
        'exercises_with_issues': 0,
        'exercises_with_warnings': 0,
        'critical_issues': [],
        'all_issues': [],
        'answer_position_stats': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 'other': 0}
    }
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"VALIDATING ALBANIAN CORPUS")
        print(f"{'='*70}")
        print(f"Total exercises to validate: {stats['total_exercises']}\n")
    
    for idx, exercise in enumerate(exercises):
        if verbose and (idx + 1) % 100 == 0:
            print(f"Progress: {idx + 1}/{stats['total_exercises']} exercises validated...")
        
        validation = validate_exercise(exercise)
        
        # Track answer positions
        if exercise.data:
            try:
                data = json.loads(exercise.data)
                if 'choices' in data and isinstance(data['choices'], list):
                    choices = data['choices']
                    normalized_choices = [c.lower().strip() for c in choices]
                    normalized_answer = exercise.answer.lower().strip()
                    
                    try:
                        position = normalized_choices.index(normalized_answer)
                        if position < 5:
                            stats['answer_position_stats'][position] += 1
                        else:
                            stats['answer_position_stats']['other'] += 1
                    except ValueError:
                        pass
            except:
                pass
        
        if validation['is_valid']:
            stats['valid_exercises'] += 1
        else:
            stats['exercises_with_issues'] += 1
            stats['critical_issues'].append(validation)
        
        if validation['warnings']:
            stats['exercises_with_warnings'] += 1
        
        if validation['issues'] or validation['warnings']:
            stats['all_issues'].append(validation)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"VALIDATION RESULTS")
        print(f"{'='*70}")
        print(f"✅ Valid exercises: {stats['valid_exercises']} ({stats['valid_exercises']/stats['total_exercises']*100:.1f}%)")
        print(f"❌ Exercises with critical issues: {stats['exercises_with_issues']}")
        print(f"⚠️  Exercises with warnings: {stats['exercises_with_warnings']}")
        
        print(f"\n📊 Answer Position Statistics:")
        total_with_choices = sum(stats['answer_position_stats'].values())
        if total_with_choices > 0:
            # Sort by key, but handle 'other' separately
            sorted_items = []
            for position, count in stats['answer_position_stats'].items():
                if isinstance(position, int):
                    sorted_items.append((position, count))
            
            sorted_items.sort(key=lambda x: x[0])
            
            for position, count in sorted_items:
                if count > 0:
                    percentage = (count / total_with_choices) * 100
                    print(f"   Position {position + 1}: {count} ({percentage:.1f}%)")
            
            # Show 'other' if exists
            if 'other' in stats['answer_position_stats'] and stats['answer_position_stats']['other'] > 0:
                count = stats['answer_position_stats']['other']
                percentage = (count / total_with_choices) * 100
                print(f"   Position 6+: {count} ({percentage:.1f}%)")
        
        # Show sample critical issues
        if stats['critical_issues']:
            print(f"\n🔴 CRITICAL ISSUES (showing first 10):")
            for issue in stats['critical_issues'][:10]:
                print(f"\n   Exercise ID {issue['id']}:")
                print(f"   Prompt: {issue['prompt'][:60]}...")
                print(f"   Answer: {issue['answer']}")
                for problem in issue['issues']:
                    print(f"      ❌ {problem}")
        
        # Show sample warnings
        if stats['all_issues']:
            print(f"\n⚠️  WARNINGS (showing first 5):")
            warning_count = 0
            for issue in stats['all_issues']:
                if issue['warnings'] and warning_count < 5:
                    print(f"\n   Exercise ID {issue['id']}:")
                    print(f"   Prompt: {issue['prompt'][:60]}...")
                    for warning in issue['warnings'][:2]:
                        print(f"      ⚠️  {warning}")
                    warning_count += 1
        
        print(f"\n{'='*70}\n")
    
    return stats


def fix_common_issues(db: SessionLocal, dry_run: bool = True) -> int:
    """
    Automatically fix common issues in the corpus.
    
    Args:
        db: Database session
        dry_run: If True, don't commit changes
    
    Returns:
        Number of exercises fixed
    """
    fixes_count = 0
    exercises = db.query(Exercise).all()
    
    print(f"\n🔧 FIXING COMMON ISSUES (dry_run={dry_run})")
    print(f"{'='*70}\n")
    
    for exercise in exercises:
        modified = False
        original_answer = exercise.answer
        
        # Fix common spelling mistakes in answer
        if exercise.answer:
            # Fix 'shtepi' -> 'shtëpi'
            if 'shtepi' in exercise.answer.lower():
                exercise.answer = exercise.answer.replace('shtepi', 'shtëpi').replace('Shtepi', 'Shtëpi')
                modified = True
            
            # Fix 'rruge' -> 'rrugë'
            if 'rruge' in exercise.answer.lower() and 'rrugë' not in exercise.answer.lower():
                exercise.answer = exercise.answer.replace('rruge', 'rrugë').replace('Rruge', 'Rrugë')
                modified = True
            
            # Fix 'dhjete' -> 'dhjetë'
            if 'dhjete' in exercise.answer.lower():
                exercise.answer = exercise.answer.replace('dhjete', 'dhjetë').replace('Dhjete', 'Dhjetë')
                modified = True
        
        if modified:
            fixes_count += 1
            print(f"Exercise {exercise.id}: '{original_answer}' -> '{exercise.answer}'")
            
            if not dry_run:
                db.add(exercise)
    
    if not dry_run:
        db.commit()
        print(f"\n✅ Fixed {fixes_count} exercises")
    else:
        print(f"\n📋 Would fix {fixes_count} exercises (dry run)")
    
    return fixes_count


def main():
    """Run corpus validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Albanian corpus')
    parser.add_argument('--limit', type=int, help='Limit number of exercises to validate')
    parser.add_argument('--fix', action='store_true', help='Fix common issues')
    parser.add_argument('--no-dry-run', action='store_true', help='Actually commit fixes (default is dry run)')
    parser.add_argument('--quiet', action='store_true', help='Less verbose output')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        # Validate corpus
        stats = validate_corpus(db, limit=args.limit, verbose=not args.quiet)
        
        # Fix issues if requested
        if args.fix:
            fixes = fix_common_issues(db, dry_run=not args.no_dry_run)
            
            # Re-validate after fixes
            if not args.no_dry_run and fixes > 0:
                print("\n" + "="*70)
                print("RE-VALIDATING AFTER FIXES")
                print("="*70)
                validate_corpus(db, limit=args.limit, verbose=not args.quiet)
        
        # Exit code based on critical issues
        if stats['exercises_with_issues'] > 0:
            print(f"\n⚠️  Validation failed: {stats['exercises_with_issues']} exercises have critical issues")
            return 1
        else:
            print(f"\n✅ Validation passed: All exercises are valid!")
            if stats['exercises_with_warnings'] > 0:
                print(f"   (Note: {stats['exercises_with_warnings']} exercises have warnings)")
            return 0
    
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())
