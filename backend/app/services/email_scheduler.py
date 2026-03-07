"""
Email Scheduler Service
Handles automatic email sending tasks
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
import logging

from ..database import SessionLocal
from ..models import User
from .email_service import email_service

logger = logging.getLogger(__name__)


class EmailScheduler:
    """Background task scheduler për emails"""
    
    @staticmethod
    def check_and_send_streak_warnings():
        """
        Kontrollon përdoruesit që nuk janë futur për 20+ orë
        dhe u dërgon streak warning
        """
        db = SessionLocal()
        try:
            # Time threshold (20 orë më parë)
            threshold = datetime.utcnow() - timedelta(hours=20)
            
            # Gjej përdoruesit që:
            # - Janë aktiv
            # - Nuk janë futur për 20+ orë
            # - Kanë email
            # - Kanë streak > 0
            
            # Note: Duhet të kesh një field last_login në User model
            # Për tani do të përdorim created_at si placeholder
            users = db.query(User).filter(
                User.is_active == True,
                User.email.isnot(None),
                User.email != ""
            ).all()
            
            sent_count = 0
            for user in users:
                # Check nëse duhet të dërgojmë email
                # Këtu do të kontrollosh last_login në të ardhmen
                
                # Për demonstrim, dërgo vetëm nëse nuk ka marrë email sot
                # (në production do të kontrollohet last_login)
                
                current_streak = 5  # Placeholder - do të llogaritet nga activity
                last_login = user.created_at  # Placeholder
                
                if (datetime.utcnow() - last_login).total_seconds() > 72000:  # 20 orë
                    success = email_service.send_streak_warning_email(
                        user.email,
                        user.username,
                        current_streak,
                        last_login
                    )
                    
                    if success:
                        sent_count += 1
                        logger.info(f"Streak warning sent to {user.username}")
            
            logger.info(f"Sent {sent_count} streak warning emails")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in check_and_send_streak_warnings: {str(e)}")
            return 0
        finally:
            db.close()
    
    @staticmethod
    def send_weekly_reports():
        """
        Dërgon raporte javore të personalizuara
        Ekzekutohet çdo të dielë në mbrëmje
        """
        db = SessionLocal()
        try:
            # Gjej të gjithë përdoruesit aktivë me email
            users = db.query(User).filter(
                User.is_active == True,
                User.email.isnot(None),
                User.email != ""
            ).all()
            
            sent_count = 0
            for user in users:
                # Calculate statistics për javën e kaluar
                # Këtu do të query-osh attempts, scores, etc.
                
                stats = {
                    'exercises_completed': 25,  # Placeholder
                    'avg_score': 78,  # Placeholder
                    'time_spent_minutes': 150,  # Placeholder
                    'current_streak': 5,  # Placeholder
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
                
                success = email_service.send_weekly_personalized_email(
                    user.email,
                    user.username,
                    stats
                )
                
                if success:
                    sent_count += 1
                    logger.info(f"Weekly report sent to {user.username}")
            
            logger.info(f"Sent {sent_count} weekly report emails")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in send_weekly_reports: {str(e)}")
            return 0
        finally:
            db.close()
    
    @staticmethod
    def cleanup_old_email_logs(days: int = 90):
        """
        Fshin email logs më të vjetër se X ditë
        """
        db = SessionLocal()
        try:
            threshold = datetime.utcnow() - timedelta(days=days)
            
            # Delete old logs
            # Note: Duhet të importosh EmailLog model kur të jetë i disponueshëm
            # deleted = db.query(EmailLog).filter(
            #     EmailLog.sent_at < threshold
            # ).delete()
            
            # db.commit()
            # logger.info(f"Deleted {deleted} old email logs")
            
            logger.info("Cleanup executed (placeholder)")
            return 0
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_email_logs: {str(e)}")
            db.rollback()
            return 0
        finally:
            db.close()


# Global instance
email_scheduler = EmailScheduler()


# Background task functions për të ekzekutuar
def run_streak_check():
    """Run streak warning check"""
    print("🔍 Running streak warning check...")
    count = email_scheduler.check_and_send_streak_warnings()
    print(f"✅ Sent {count} streak warnings")


def run_weekly_reports():
    """Run weekly reports"""
    print("📊 Running weekly reports...")
    count = email_scheduler.send_weekly_reports()
    print(f"✅ Sent {count} weekly reports")


def run_cleanup():
    """Run cleanup"""
    print("🧹 Running cleanup...")
    email_scheduler.cleanup_old_email_logs()
    print("✅ Cleanup completed")
