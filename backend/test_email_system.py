"""
Test Script për Email System
Run: python test_email_system.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import email_service


def test_welcome_email():
    """Test welcome email"""
    print("\n" + "="*60)
    print("🧪 Testing Welcome Email")
    print("="*60)
    
    test_email = input("Enter test email address: ").strip()
    test_username = input("Enter test username: ").strip() or "TestUser"
    
    print(f"\n📧 Sending welcome email to {test_email}...")
    
    success = email_service.send_welcome_email(test_email, test_username)
    
    if success:
        print("✅ Welcome email sent successfully!")
        print(f"📬 Check inbox at {test_email}")
    else:
        print("❌ Failed to send email. Check SMTP configuration.")


def test_streak_warning():
    """Test streak warning email"""
    print("\n" + "="*60)
    print("🧪 Testing Streak Warning Email")
    print("="*60)
    
    test_email = input("Enter test email address: ").strip()
    test_username = input("Enter test username: ").strip() or "TestUser"
    current_streak = int(input("Enter current streak (e.g., 7): ").strip() or "7")
    
    last_login = datetime.utcnow() - timedelta(hours=22)
    
    print(f"\n⚠️ Sending streak warning to {test_email}...")
    print(f"   Streak: {current_streak} ditë")
    print(f"   Last login: {last_login.strftime('%Y-%m-%d %H:%M')}")
    
    success = email_service.send_streak_warning_email(
        test_email,
        test_username,
        current_streak,
        last_login
    )
    
    if success:
        print("✅ Streak warning sent successfully!")
        print(f"📬 Check inbox at {test_email}")
    else:
        print("❌ Failed to send email. Check SMTP configuration.")


def test_weekly_report():
    """Test weekly personalized email"""
    print("\n" + "="*60)
    print("🧪 Testing Weekly Report Email")
    print("="*60)
    
    test_email = input("Enter test email address: ").strip()
    test_username = input("Enter test username: ").strip() or "TestUser"
    
    # Mock statistics
    stats = {
        'exercises_completed': 25,
        'avg_score': 78,
        'time_spent_minutes': 150,
        'current_streak': 5,
        'strengths': [
            'Vocabulary - 85% sukses',
            'Reading - 82% sukses',
            'Writing - 79% sukses'
        ],
        'weaknesses': [
            'Grammar - 68% sukses',
            'Listening - 72% sukses'
        ]
    }
    
    print(f"\n📊 Sending weekly report to {test_email}...")
    print(f"   Exercises: {stats['exercises_completed']}")
    print(f"   Avg Score: {stats['avg_score']}%")
    print(f"   Time: {stats['time_spent_minutes']} min")
    
    success = email_service.send_weekly_personalized_email(
        test_email,
        test_username,
        stats
    )
    
    if success:
        print("✅ Weekly report sent successfully!")
        print(f"📬 Check inbox at {test_email}")
    else:
        print("❌ Failed to send email. Check SMTP configuration.")


def main():
    """Main test menu"""
    print("\n" + "="*60)
    print("📧 EMAIL SYSTEM TEST")
    print("="*60)
    print("\nKy script teston email system-in e AlbLingo.")
    print("Make sure you have configured .env file me SMTP credentials.\n")
    
    # Check configuration
    smtp_user = os.getenv("SMTP_USER", "")
    if not smtp_user:
        print("⚠️ WARNING: SMTP_USER not configured në .env file!")
        print("   Please create backend/.env file me SMTP credentials.")
        print("   See backend/.env.example për template.\n")
        
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Exiting...")
            return
    
    while True:
        print("\n" + "-"*60)
        print("Select test to run:")
        print("-"*60)
        print("1. Test Welcome Email (Registration)")
        print("2. Test Streak Warning Email")
        print("3. Test Weekly Report Email")
        print("4. Test All Emails")
        print("5. Exit")
        print("-"*60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            test_welcome_email()
        elif choice == '2':
            test_streak_warning()
        elif choice == '3':
            test_weekly_report()
        elif choice == '4':
            test_email = input("Enter test email address: ").strip()
            test_username = input("Enter test username: ").strip() or "TestUser"
            
            print("\n📧 Sending all test emails...")
            test_welcome_email()
            time.sleep(2)
            test_streak_warning()
            time.sleep(2)
            test_weekly_report()
            print("\n✅ All tests completed!")
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
    
    print("\n" + "="*60)
    print("Testing completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    import time
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
