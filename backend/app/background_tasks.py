"""
Background Tasks për Email System
Uses simple threading për scheduled tasks.

Weekly reports: every Sunday at 20:00 Europe/Tirane, with a catch-up
window so a sleeping host (e.g. Render free) can still send on Monday.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, time as dt_time
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from .services.email_scheduler import run_streak_check, run_weekly_reports, run_cleanup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kosovo / Albania local time for "e diel në 20:00"
WEEKLY_TZ = ZoneInfo("Europe/Tirane")
WEEKLY_HOUR = 20
WEEKLY_MINUTE = 0
# Keep trying for this long after Sunday 20:00 so free-tier wakeups still send.
WEEKLY_CATCHUP_HOURS = 36


def _now_local() -> datetime:
	return datetime.now(WEEKLY_TZ)


def _iso_week_sunday_20(year: int, week: int) -> datetime:
	"""Sunday 20:00 Europe/Tirane for the given ISO year/week."""
	sunday = datetime.fromisocalendar(year, week, 7)
	return sunday.replace(hour=WEEKLY_HOUR, minute=WEEKLY_MINUTE, second=0, microsecond=0, tzinfo=WEEKLY_TZ)


def weekly_send_window(now: Optional[datetime] = None) -> Tuple[bool, Optional[Tuple[int, int]], Optional[datetime]]:
	"""
	Returns (should_run, iso_week_id, sunday_20_local).

	should_run is True from that week's Sunday 20:00 until +WEEKLY_CATCHUP_HOURS.
	"""
	now = now or _now_local()
	if now.tzinfo is None:
		now = now.replace(tzinfo=WEEKLY_TZ)
	else:
		now = now.astimezone(WEEKLY_TZ)

	y, w, _wd = now.isocalendar()
	this_sunday_20 = _iso_week_sunday_20(y, w)

	if now >= this_sunday_20:
		target = this_sunday_20
		week_id = (y, w)
	else:
		# Before this week's Sunday 20:00 → previous ISO week is the active due week
		prev = this_sunday_20 - timedelta(days=7)
		py, pw, _ = prev.isocalendar()
		target = _iso_week_sunday_20(py, pw)
		week_id = (py, pw)

	window_end = target + timedelta(hours=WEEKLY_CATCHUP_HOURS)
	should_run = target <= now <= window_end
	return should_run, week_id, target


class BackgroundScheduler:
	"""Simple scheduler për background tasks"""

	def __init__(self):
		self.running = False
		self.threads = []
		self.last_weekly_week: Optional[Tuple[int, int]] = None
		self.last_weekly_result: Optional[dict] = None

	def start(self):
		"""Start background tasks"""
		if self.running:
			logger.warning("Scheduler is already running")
			return

		self.running = True
		logger.info("Starting background scheduler...")

		should, week_id, sunday_20 = weekly_send_window()
		logger.info(
			"Weekly reports: Sundays %02d:%02d %s | next/current window Sunday=%s should_run_now=%s week=%s",
			WEEKLY_HOUR,
			WEEKLY_MINUTE,
			WEEKLY_TZ.key,
			sunday_20.isoformat() if sunday_20 else None,
			should,
			week_id,
		)

		streak_thread = threading.Thread(
			target=self._run_periodic_task,
			args=(run_streak_check, 6 * 3600, "Streak Check"),
			daemon=True,
		)
		streak_thread.start()
		self.threads.append(streak_thread)

		weekly_thread = threading.Thread(
			target=self._run_weekly_task,
			args=(run_weekly_reports, "Weekly Reports"),
			daemon=True,
		)
		weekly_thread.start()
		self.threads.append(weekly_thread)

		cleanup_thread = threading.Thread(
			target=self._run_daily_task,
			args=(run_cleanup, dt_time(2, 0), "Cleanup"),
			daemon=True,
		)
		cleanup_thread.start()
		self.threads.append(cleanup_thread)

		logger.info("Background scheduler started successfully")

	def stop(self):
		"""Stop background tasks"""
		self.running = False
		logger.info("Stopping background scheduler...")

	def _run_periodic_task(self, task_func, interval_seconds: int, task_name: str):
		logger.info("%s scheduled every %.1f hours", task_name, interval_seconds / 3600)

		while self.running:
			try:
				logger.info("Executing %s...", task_name)
				task_func()
				logger.info("%s completed", task_name)
			except Exception:
				logger.exception("Error in %s", task_name)

			time.sleep(interval_seconds)

	def _run_weekly_task(self, task_func, task_name: str):
		"""
		Run weekly reports every Sunday at 20:00 Europe/Tirane.
		Also retries during a catch-up window if the host was asleep.
		"""
		logger.info(
			"%s scheduled every Sunday at %02d:%02d %s (catch-up %sh)",
			task_name,
			WEEKLY_HOUR,
			WEEKLY_MINUTE,
			WEEKLY_TZ.key,
			WEEKLY_CATCHUP_HOURS,
		)

		while self.running:
			try:
				should_run, week_id, sunday_20 = weekly_send_window()
				if should_run and week_id is not None:
					# Re-run within the window until users are marked sent, or SMTP keeps failing.
					# Per-user last_weekly_report_at prevents duplicate successful emails.
					logger.info(
						"Executing %s for week %s (Sunday 20:00 was %s)...",
						task_name,
						week_id,
						sunday_20.isoformat() if sunday_20 else "?",
					)
					result = task_func()
					self.last_weekly_week = week_id
					self.last_weekly_result = {
						"week": week_id,
						"ran_at": _now_local().isoformat(),
						"result": result,
					}
					logger.info("%s completed: %s", task_name, result)
				else:
					logger.debug(
						"%s idle (local=%s should_run=%s week=%s)",
						task_name,
						_now_local().isoformat(),
						should_run,
						week_id,
					)
			except Exception:
				logger.exception("Error in %s", task_name)

			# Poll every 15 minutes (survives delayed starts / free-tier wakeups).
			time.sleep(15 * 60)

	def _run_daily_task(self, task_func, run_time: dt_time, task_name: str):
		logger.info("%s scheduled daily at %s %s", task_name, run_time.strftime("%H:%M"), WEEKLY_TZ.key)

		while self.running:
			now = _now_local()
			next_run = datetime.combine(now.date(), run_time, tzinfo=WEEKLY_TZ)
			if next_run <= now:
				next_run += timedelta(days=1)

			wait_seconds = (next_run - now).total_seconds()
			logger.info("%s next run: %s", task_name, next_run.strftime("%Y-%m-%d %H:%M %Z"))

			if wait_seconds > 0:
				time.sleep(min(wait_seconds, 3600))
				continue

			try:
				logger.info("Executing %s...", task_name)
				task_func()
				logger.info("%s completed", task_name)
			except Exception:
				logger.exception("Error in %s", task_name)

			time.sleep(3600)


# Global scheduler instance
scheduler = BackgroundScheduler()


def start_background_tasks():
	"""Start background tasks when app starts"""
	scheduler.start()


def stop_background_tasks():
	"""Stop background tasks when app shuts down"""
	scheduler.stop()


if __name__ == "__main__":
	print("Testing background scheduler...")
	print("Press Ctrl+C to stop\n")
	scheduler.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("\nStopping scheduler...")
		scheduler.stop()
		print("Scheduler stopped")
