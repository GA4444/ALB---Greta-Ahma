"""
Email Scheduler Service
Handles automatic email sending tasks
"""

from datetime import datetime, timedelta
import logging

from ..database import SessionLocal
from ..models import User, EmailLog
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
            now = datetime.utcnow()
            warning_threshold = now - timedelta(hours=20)
            expiry_threshold = now - timedelta(hours=24)

            # Activity, not account creation/login, is the source of truth.
            # Only warn during the 20–24 hour risk window.
            users = db.query(User).filter(
                User.is_active == True,
                User.email.isnot(None),
                User.email != "",
                User.current_streak > 0,
                User.last_activity_date.isnot(None),
                User.last_activity_date <= warning_threshold,
                User.last_activity_date > expiry_threshold,
            ).all()
            
            sent_count = 0
            for user in users:
                if (
                    user.last_streak_warning_at
                    and user.last_streak_warning_at >= user.last_activity_date
                ):
                    continue

                success = email_service.send_streak_warning_email(
                    user.email,
                    user.username,
                    user.current_streak,
                    user.last_activity_date,
                    user_id=user.id,
                )

                if success:
                    user.last_streak_warning_at = now
                    db.commit()
                    sent_count += 1
                    logger.info("Streak warning sent: user_id=%s", user.id)
            
            logger.info("Streak warning run complete: sent=%s", sent_count)
            return sent_count
            
        except Exception as e:
            logger.exception("Error in streak warning run")
            return 0
        finally:
            db.close()
    
    @staticmethod
    def send_weekly_reports():
        """
        Dërgon raporte javore të personalizuara
        Ekzekutohet çdo të dielë në mbrëmje.
        Stats are computed live from Attempt rows for the last 7 days.
        """
        from .period_stats import compute_user_period_stats, period_bounds, utcnow

        db = SessionLocal()
        try:
            now = utcnow()
            period_start, _ = period_bounds("weekly", now)

            users = db.query(User).filter(
                User.is_active == True,
                User.email.isnot(None),
                User.email != ""
            ).all()
            
            sent_count = 0
            for user in users:
                if user.last_weekly_report_at and user.last_weekly_report_at >= period_start:
                    continue

                stats = compute_user_period_stats(db, user.id, "weekly", now)

                success = email_service.send_weekly_personalized_email(
                    user.email,
                    user.username,
                    {
                        "exercises_completed": stats["exercises_completed"],
                        "avg_score": stats["avg_score"],
                        "time_spent_minutes": stats["time_spent_minutes"],
                        "current_streak": stats["current_streak"],
                        "strengths": stats["strengths"],
                        "weaknesses": stats["weaknesses"],
                    },
                    user_id=user.id,
                )

                if success:
                    user.last_weekly_report_at = now
                    db.commit()
                    sent_count += 1
                    logger.info("Weekly report sent: user_id=%s", user.id)
            
            logger.info("Weekly report run complete: sent=%s", sent_count)
            return sent_count
            
        except Exception as e:
            logger.exception("Error in weekly report run")
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
            
            deleted = db.query(EmailLog).filter(EmailLog.sent_at < threshold).delete()
            db.commit()
            logger.info("Old email logs deleted: count=%s", deleted)
            return deleted
            
        except Exception as e:
            logger.exception("Error cleaning old email logs")
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
