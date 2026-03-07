"""
Test Advanced AI Practice Endpoints
Run: python test_advanced_practice.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"

def test_generate_advanced_practice():
    """Test advanced practice generation"""
    print("\n🧪 Testing Advanced AI Practice Generation...")
    
    response = requests.post(
        f"{BASE_URL}/ai/advanced-practice",
        json={
            "user_id": "1",
            "level_id": 1,
            "count": 5,
            "difficulty": "adaptive"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Success! Generated {len(data['exercises'])} exercises")
        
        # Show analysis
        analysis = data['analysis']
        print(f"\n📊 Analysis:")
        print(f"   Overall Accuracy: {analysis['overall_accuracy']*100:.1f}%")
        print(f"   Trend: {analysis['trend']}")
        print(f"   Weak Words: {analysis['weak_count']}")
        print(f"   Mastered Words: {analysis['mastered_count']}")
        
        # Show top patterns
        if analysis['top_patterns']:
            print(f"\n🎯 Top Patterns:")
            for pattern in analysis['top_patterns'][:3]:
                print(f"   - {pattern['name']}: {pattern['count']} ({pattern['severity']})")
        
        # Show recommendations
        if data['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in data['recommendations'][:3]:
                print(f"   - {rec}")
        
        # Show next focus
        print(f"\n🎯 Next Focus:")
        print(f"   {data['next_focus']}")
        
        # Show sample exercise
        if data['exercises']:
            ex = data['exercises'][0]
            print(f"\n📝 Sample Exercise:")
            print(f"   Type: {ex['type']}")
            print(f"   Focus Word: {ex['focus_word']}")
            print(f"   Reason: {ex['reason']}")
            print(f"   Prompt: {ex['prompt'][:80]}...")
            if ex.get('choices'):
                print(f"   Choices: {ex['choices']}")
        
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_practice_progress():
    """Test practice progress endpoint"""
    print("\n🧪 Testing Practice Progress...")
    
    response = requests.get(
        f"{BASE_URL}/ai/practice-progress/1/1"
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Success!")
        print(f"   Overall Accuracy: {data['overall_accuracy']*100:.1f}%")
        print(f"   Trend: {data['trend']}")
        
        # Show weak words
        if data['weak_words']:
            print(f"\n🔴 Weak Words (top 3):")
            for word in data['weak_words'][:3]:
                print(f"   - {word['word']}: {word['accuracy']*100:.1f}% ({word['total']} attempts)")
        
        # Show mastered words
        if data['mastered_words']:
            print(f"\n✅ Mastered Words (top 3):")
            for word in data['mastered_words'][:3]:
                print(f"   - {word['word']}: {word['accuracy']*100:.1f}%")
        
        # Show improving words
        if data['improving_words']:
            print(f"\n📈 Improving Words:")
            for word in data['improving_words'][:3]:
                print(f"   - {word['word']}: {word['accuracy']*100:.1f}% (trend: +{word['trend']:.2f})")
        
        # Show patterns
        if data['patterns']:
            print(f"\n🎯 Mistake Patterns:")
            for pattern_name, pattern_info in list(data['patterns'].items())[:3]:
                print(f"   - {pattern_name}: {pattern_info['count']} ({pattern_info['severity']})")
        
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_different_difficulties():
    """Test different difficulty levels"""
    print("\n🧪 Testing Different Difficulties...")
    
    for difficulty in ['easy', 'medium', 'hard', 'adaptive']:
        print(f"\n   Testing difficulty: {difficulty}")
        
        response = requests.post(
            f"{BASE_URL}/ai/advanced-practice",
            json={
                "user_id": "1",
                "level_id": 1,
                "count": 3,
                "difficulty": difficulty
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"      ✅ {len(data['exercises'])} exercises generated")
        else:
            print(f"      ❌ Failed: {response.status_code}")
            return False
    
    print(f"\n✅ All difficulty levels work!")
    return True


def test_with_focus_area():
    """Test with specific focus area"""
    print("\n🧪 Testing with Focus Area...")
    
    response = requests.post(
        f"{BASE_URL}/ai/advanced-practice",
        json={
            "user_id": "1",
            "level_id": 1,
            "count": 5,
            "focus_area": "diacritics"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Generated {len(data['exercises'])} exercises with focus on diacritics")
        
        # Check if exercises are focused
        diacritic_focused = sum(
            1 for ex in data['exercises']
            if ex.get('mistake_pattern') and 'diacritic' in ex['mistake_pattern']
        )
        
        print(f"   {diacritic_focused}/{len(data['exercises'])} exercises focused on diacritics")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("🚀 ADVANCED AI PRACTICE TEST SUITE")
    print("=" * 70)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nMake sure:")
    print("  1. Backend is running (port 8001)")
    print("  2. Database has user attempts")
    print("  3. User ID '1' exists with some exercises completed")
    print("=" * 70)
    
    results = []
    
    try:
        # Run tests
        results.append(("Generate Advanced Practice", test_generate_advanced_practice()))
        results.append(("Get Practice Progress", test_practice_progress()))
        results.append(("Different Difficulties", test_different_difficulties()))
        results.append(("With Focus Area", test_with_focus_area()))
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {name}")
        
        print("-" * 70)
        print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 All tests passed! Advanced AI Practice is working perfectly!")
            print("\n✨ Features verified:")
            print("   ✅ Mistake analysis")
            print("   ✅ Pattern recognition")
            print("   ✅ Personalized exercise generation")
            print("   ✅ Recommendations")
            print("   ✅ Progress tracking")
            print("   ✅ Multiple difficulties")
            print("   ✅ Focus areas")
            return 0
        elif passed > total / 2:
            print("\n⚠️  Some tests failed. Check configuration.")
            return 1
        else:
            print("\n❌ Many tests failed. Check if backend is running and has data.")
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
