"""
Test script for Advanced Chatbot API endpoints
Run: python test_chatbot.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"

def test_basic_chatbot():
    """Test basic chatbot endpoint"""
    print("\n🧪 Testing Basic Chatbot...")
    
    response = requests.post(
        f"{BASE_URL}/chatbot/ask",
        json={
            "message": "Si filloj të përdor platformën?",
            "user_id": "1"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Response: {data['response'][:100]}...")
        if data.get('suggestions'):
            print(f"   Suggestions: {', '.join(data['suggestions'][:3])}")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_advanced_chatbot():
    """Test advanced chatbot endpoint"""
    print("\n🧪 Testing Advanced Chatbot...")
    
    response = requests.post(
        f"{BASE_URL}/chatbot/advanced/ask",
        json={
            "message": "Më jep këshilla për drejtshkrimin shqip",
            "use_llm": False,  # Set to True if you have API keys
            "context": {
                "current_level": "Klasa 1, Niveli 2",
                "recent_mistakes": ["shtepi", "rruge"]
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Model used: {data['model_used']}")
        print(f"   Response: {data['response'][:100]}...")
        print(f"   Context aware: {data.get('context_aware', False)}")
        
        # Save session token for further tests
        return data.get('session_token')
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_chat_history(session_token):
    """Test chat history endpoint"""
    if not session_token:
        print("\n⚠️  Skipping history test (no session token)")
        return False
    
    print(f"\n🧪 Testing Chat History...")
    
    response = requests.get(
        f"{BASE_URL}/chatbot/advanced/history/{session_token}"
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Total messages: {data['total_messages']}")
        print(f"   Session started: {data['started_at']}")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def test_suggestions():
    """Test chat suggestions endpoint"""
    print("\n🧪 Testing Chat Suggestions...")
    
    response = requests.get(f"{BASE_URL}/chatbot/suggestions")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got {len(data['suggestions'])} suggestions")
        print(f"   Examples: {', '.join(data['suggestions'][:3])}")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def test_topics():
    """Test chat topics endpoint"""
    print("\n🧪 Testing Chat Topics...")
    
    response = requests.get(f"{BASE_URL}/chatbot/topics")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Got {len(data['topics'])} topics")
        for topic in data['topics'][:3]:
            print(f"   {topic['icon']} {topic['title']}")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def test_stats():
    """Test chatbot stats endpoint"""
    print("\n🧪 Testing Chatbot Stats...")
    
    response = requests.get(f"{BASE_URL}/chatbot/advanced/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Total sessions: {data['total_sessions']}")
        print(f"   Active sessions: {data['active_sessions']}")
        print(f"   Total messages: {data['total_messages']}")
        print(f"   Avg messages/session: {data['avg_messages_per_session']}")
        if data.get('model_usage'):
            print(f"   Model usage: {data['model_usage']}")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def test_clear_session(session_token):
    """Test clear session endpoint"""
    if not session_token:
        print("\n⚠️  Skipping clear session test (no session token)")
        return False
    
    print(f"\n🧪 Testing Clear Session...")
    
    response = requests.delete(
        f"{BASE_URL}/chatbot/advanced/session/{session_token}"
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! {data['message']}")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def test_export(session_token):
    """Test export endpoint"""
    if not session_token:
        print("\n⚠️  Skipping export test (no session token)")
        return False
    
    print(f"\n🧪 Testing Export Conversation...")
    
    response = requests.get(
        f"{BASE_URL}/chatbot/advanced/export/{session_token}?format=json"
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Exported {len(data['messages'])} messages")
        return True
    else:
        print(f"❌ Failed! Status: {response.status_code}")
        return False


def test_feedback(session_token):
    """Test feedback endpoint (requires message ID)"""
    print("\n⚠️  Skipping feedback test (requires message ID)")
    # You would need to get a message ID from history first
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 CHATBOT API TESTS")
    print("=" * 60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run tests
    results.append(("Basic Chatbot", test_basic_chatbot()))
    results.append(("Chat Suggestions", test_suggestions()))
    results.append(("Chat Topics", test_topics()))
    
    # Advanced chatbot tests
    session_token = test_advanced_chatbot()
    results.append(("Advanced Chatbot", session_token is not None))
    
    results.append(("Chat History", test_chat_history(session_token)))
    results.append(("Export Conversation", test_export(session_token)))
    results.append(("Chatbot Stats", test_stats()))
    
    # Clean up (optional)
    # results.append(("Clear Session", test_clear_session(session_token)))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Chatbot is working perfectly!")
    elif passed > total / 2:
        print("\n⚠️  Some tests failed. Check configuration.")
    else:
        print("\n❌ Many tests failed. Check if backend is running.")
    
    print("\n💡 Tips:")
    print("   - Make sure backend is running: uvicorn app.main:app --reload --port 8001")
    print("   - Check .env for API keys (optional)")
    print("   - See CHATBOT_SETUP.md for full setup guide")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("   Make sure the backend is running on port 8001")
        print("   Run: uvicorn app.main:app --reload --port 8001")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
