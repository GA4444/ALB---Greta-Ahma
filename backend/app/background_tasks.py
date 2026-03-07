"""
Background Tasks për Email System
Uses simple threading për scheduled tasks
"""

import threading
import time
from datetime import datetime, timedelta, time as dt_time
import logging

from .services.email_scheduler import run_streak_check, run_weekly_reports, run_cleanup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Simple scheduler për background tasks"""
    
    def __init__(self):
        self.running = False
        self.threads = []
    
    def start(self):
        """Start background tasks"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("🚀 Starting background scheduler...")
        
        # Thread për streak check (çdo 6 orë)
        streak_thread = threading.Thread(
            target=self._run_periodic_task,
            args=(run_streak_check, 6 * 3600, "Streak Check"),  # 6 hours
            daemon=True
        )
        streak_thread.start()
        self.threads.append(streak_thread)
        
        # Thread për weekly reports (çdo të dielë në 20:00)
        weekly_thread = threading.Thread(
            target=self._run_weekly_task,
            args=(run_weekly_reports, "Weekly Reports"),
            daemon=True
        )
        weekly_thread.start()
        self.threads.append(weekly_thread)
        
        # Thread për cleanup (çdo ditë në 02:00)
        cleanup_thread = threading.Thread(
            target=self._run_daily_task,
            args=(run_cleanup, dt_time(2, 0), "Cleanup"),
            daemon=True
        )
        cleanup_thread.start()
        self.threads.append(cleanup_thread)
        
        logger.info("✅ Background scheduler started successfully")
    
    def stop(self):
        """Stop background tasks"""
        self.running = False
        logger.info("🛑 Stopping background scheduler...")
    
    def _run_periodic_task(self, task_func, interval_seconds: int, task_name: str):
        """
        Run task periodically every X seconds
        
        Args:
            task_func: Function to execute
            interval_seconds: Interval në sekonda
            task_name: Emri i task-ut për logging
        """
        logger.info(f"⏰ {task_name} scheduled every {interval_seconds/3600:.1f} hours")
        
        while self.running:
            try:
                logger.info(f"▶️ Executing {task_name}...")
                task_func()
                logger.info(f"✅ {task_name} completed")
            except Exception as e:
                logger.error(f"❌ Error in {task_name}: {str(e)}")
            
            # Sleep until next execution
            time.sleep(interval_seconds)
    
    def _run_weekly_task(self, task_func, task_name: str):
        """
        Run task every Sunday at 20:00
        
        Args:
            task_func: Function to execute
            task_name: Emri i task-ut për logging
        """
        logger.info(f"⏰ {task_name} scheduled every Sunday at 20:00")
        
        while self.running:
            now = datetime.now()
            
            # Calculate next Sunday 20:00
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 20:
                days_until_sunday = 7
            
            next_run = datetime(
                now.year, now.month, now.day, 20, 0
            ) + timedelta(days=days_until_sunday)
            
            # Wait until next run
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"⏰ {task_name} next run: {next_run.strftime('%Y-%m-%d %H:%M')}")
            
            if wait_seconds > 0:
                time.sleep(min(wait_seconds, 3600))  # Check every hour
                continue
            
            # Execute task
            try:
                logger.info(f"▶️ Executing {task_name}...")
                task_func()
                logger.info(f"✅ {task_name} completed")
            except Exception as e:
                logger.error(f"❌ Error in {task_name}: {str(e)}")
            
            # Wait 1 hour before checking again
            time.sleep(3600)
    
    def _run_daily_task(self, task_func, run_time: dt_time, task_name: str):
        """
        Run task daily at specified time
        
        Args:
            task_func: Function to execute
            run_time: Time to run (datetime.time object)
            task_name: Emri i task-ut për logging
        """
        logger.info(f"⏰ {task_name} scheduled daily at {run_time.strftime('%H:%M')}")
        
        while self.running:
            now = datetime.now()
            
            # Calculate next run time
            next_run = datetime.combine(now.date(), run_time)
            if next_run <= now:
                next_run += timedelta(days=1)
            
            # Wait until next run
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"⏰ {task_name} next run: {next_run.strftime('%Y-%m-%d %H:%M')}")
            
            if wait_seconds > 0:
                time.sleep(min(wait_seconds, 3600))  # Check every hour
                continue
            
            # Execute task
            try:
                logger.info(f"▶️ Executing {task_name}...")
                task_func()
                logger.info(f"✅ {task_name} completed")
            except Exception as e:
                logger.error(f"❌ Error in {task_name}: {str(e)}")
            
            # Wait 1 hour before checking again
            time.sleep(3600)


# Global scheduler instance
scheduler = BackgroundScheduler()


# Import në main.py për të filluar scheduler
def start_background_tasks():
    """Start background tasks when app starts"""
    scheduler.start()


def stop_background_tasks():
    """Stop background tasks when app shuts down"""
    scheduler.stop()


# Për testing manual
if __name__ == "__main__":
    from datetime import timedelta
    
    print("🧪 Testing background scheduler...")
    print("Press Ctrl+C to stop\n")
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        scheduler.stop()
        print("✅ Scheduler stopped")
