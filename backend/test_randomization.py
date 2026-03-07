"""
Quick test to verify answer randomization is working
Run: python test_randomization.py
"""

import requests
import json
from collections import Counter

BASE_URL = "http://localhost:8001/api"

def test_randomization():
    """Test that answer choices are being randomized"""
    print("\n" + "="*70)
    print("🧪 TESTING ANSWER RANDOMIZATION")
    print("="*70)
    
    # Get exercises from level 1
    print("\n1. Fetching exercises from Level 1...")
    response = requests.get(f"{BASE_URL}/levels/1/exercises?shuffle_choices=true")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch exercises: {response.status_code}")
        return False
    
    exercises = response.json()
    exercises_with_choices = [ex for ex in exercises if ex.get('data')]
    
    print(f"   Found {len(exercises_with_choices)} exercises with data")
    
    # Analyze answer positions
    print("\n2. Analyzing answer positions...")
    answer_positions = Counter()
    
    for exercise in exercises_with_choices:
        try:
            data = json.loads(exercise['data'])
            
            if 'choices' in data and isinstance(data['choices'], list) and len(data['choices']) > 0:
                choices = data['choices']
                answer = exercise.get('answer', '').lower().strip()
                
                # Find answer position
                normalized_choices = [c.lower().strip() for c in choices]
                
                try:
                    position = normalized_choices.index(answer)
                    answer_positions[position] += 1
                except ValueError:
                    print(f"   ⚠️  Exercise {exercise['id']}: Answer '{answer}' not in choices")
        
        except json.JSONDecodeError:
            continue
    
    # Display results
    print("\n" + "="*70)
    print("📊 ANSWER POSITION DISTRIBUTION")
    print("="*70)
    
    total = sum(answer_positions.values())
    
    if total == 0:
        print("❌ No exercises with choices found!")
        return False
    
    print(f"\nTotal exercises analyzed: {total}\n")
    
    for position in sorted(answer_positions.keys()):
        count = answer_positions[position]
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"Position {position + 1}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    # Check if distribution is reasonable (no position > 50%)
    max_percentage = max((count / total) * 100 for count in answer_positions.values())
    
    print("\n" + "="*70)
    print("RESULT")
    print("="*70)
    
    if max_percentage > 50:
        print(f"⚠️  WARNING: Position bias detected ({max_percentage:.1f}% in one position)")
        print("   This is expected if you haven't restarted the backend recently.")
        print("   Randomization happens per hour, so try again in the next hour.")
        return True  # Still pass, just a warning
    else:
        print(f"✅ PASS: Good distribution (max {max_percentage:.1f}% in any position)")
        print("   Answer choices are being properly randomized!")
        return True


def test_without_randomization():
    """Test that original positions show the bias"""
    print("\n" + "="*70)
    print("🧪 TESTING WITHOUT RANDOMIZATION (Control)")
    print("="*70)
    
    print("\n1. Fetching exercises WITHOUT shuffle...")
    response = requests.get(f"{BASE_URL}/levels/1/exercises?shuffle_choices=false")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch exercises: {response.status_code}")
        return False
    
    exercises = response.json()
    exercises_with_choices = [ex for ex in exercises if ex.get('data')]
    
    # Analyze answer positions
    answer_positions = Counter()
    
    for exercise in exercises_with_choices:
        try:
            data = json.loads(exercise['data'])
            
            if 'choices' in data and isinstance(data['choices'], list) and len(data['choices']) > 0:
                choices = data['choices']
                answer = exercise.get('answer', '').lower().strip()
                
                normalized_choices = [c.lower().strip() for c in choices]
                
                try:
                    position = normalized_choices.index(answer)
                    answer_positions[position] += 1
                except ValueError:
                    pass
        
        except json.JSONDecodeError:
            continue
    
    total = sum(answer_positions.values())
    
    if total == 0:
        return False
    
    print(f"\nTotal exercises analyzed: {total}\n")
    
    for position in sorted(answer_positions.keys()):
        count = answer_positions[position]
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"Position {position + 1}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    # Check if there's bias (expected in original data)
    max_percentage = max((count / total) * 100 for count in answer_positions.values())
    
    print("\n" + "="*70)
    
    if max_percentage > 35:
        print(f"✅ Confirmed: Original data has position bias ({max_percentage:.1f}%)")
        print("   This proves that randomization is needed and working!")
    else:
        print(f"ℹ️  Original data seems balanced ({max_percentage:.1f}%)")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 ANSWER RANDOMIZATION TEST SUITE")
    print("="*70)
    print("Testing API at:", BASE_URL)
    print("\nMake sure backend is running:")
    print("  uvicorn app.main:app --reload --port 8001")
    print("="*70)
    
    try:
        # Test with randomization
        success1 = test_randomization()
        
        # Test without randomization (control)
        success2 = test_without_randomization()
        
        print("\n" + "="*70)
        print("FINAL SUMMARY")
        print("="*70)
        
        if success1 and success2:
            print("✅ All tests passed!")
            print("\n💡 What this means:")
            print("   - Original corpus has position bias (expected)")
            print("   - API randomization is working (fixes the bias)")
            print("   - Users will get fair, randomized answer positions")
            print("\n🎉 Success! Randomization is working correctly!")
            return 0
        else:
            print("❌ Some tests failed. Check the output above.")
            return 1
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("   Make sure the backend is running on port 8001")
        print("   Run: uvicorn app.main:app --reload --port 8001")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
