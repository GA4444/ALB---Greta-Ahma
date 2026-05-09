"""
Email Service - AlbLingo Platform
Sends welcome, streak-warning, and weekly report emails.
Settings are read fresh from .env on every send call,
so you never need to restart the server after editing .env.
"""

import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Absolute path to backend/.env  (works regardless of cwd)
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _cfg(key: str, default: str = "") -> str:
    """Read a key from .env every time (no cache), then fall back to os.environ."""
    values = dotenv_values(_ENV_PATH) if _ENV_PATH.exists() else {}
    out = (values.get(key) or os.getenv(key, default) or "").strip()
    return out if out else default


# ─────────────────────────────────────────────
# Core send function
# ─────────────────────────────────────────────

def _send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """
    Sends an HTML email via SMTP.
    Reads SMTP credentials fresh from .env on each call.
    Returns True on success, False on any error.
    """
    enabled = _cfg("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() in ("true", "1", "yes")
    if not enabled:
        print("[EMAIL] Notifications disabled (ENABLE_EMAIL_NOTIFICATIONS=false).")
        return False

    smtp_host = _cfg("SMTP_HOST", "smtp.gmail.com") or "smtp.gmail.com"
    smtp_host = smtp_host.strip()
    if not smtp_host or "@" in smtp_host or "your-" in smtp_host.lower():
        smtp_host = "smtp.gmail.com"
    try:
        smtp_port = int(_cfg("SMTP_PORT", "587"))
    except ValueError:
        smtp_port = 587
    smtp_user = _cfg("SMTP_USER", "")
    smtp_pass = _cfg("SMTP_PASSWORD", "")
    from_email = _cfg("FROM_EMAIL") or smtp_user
    from_name = _cfg("FROM_NAME", "AlbLingo Platform")

    # Treat placeholders as "not configured" to avoid DNS/connection errors
    if not smtp_user or not smtp_pass:
        return False
    if "your-gmail" in smtp_user.lower() or "your-app-password" in (smtp_pass or "").lower():
        print(
            "[EMAIL] SMTP still using placeholders. Edit backend/.env:\n"
            "  SMTP_USER=your-real@gmail.com\n"
            "  SMTP_PASSWORD=16-char-app-password (Gmail: Security > App Passwords)"
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print(f"[EMAIL] ✅ Sent to {to_email}: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(
            "[EMAIL] ❌ Authentication failed.\n"
            "  Sigurohuni se keni vendosur App Password te Gmail (jo fjalekalimin normal).\n"
            "  Hapi: myaccount.google.com > Security > App Passwords"
        )
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] ❌ SMTP error: {e}")
        return False
    except OSError as e:
        if e.errno == 8 or "nodename" in str(e).lower() or "servname" in str(e).lower():
            print(
                "[EMAIL] ❌ Cannot resolve SMTP server (DNS/network).\n"
                f"  SMTP_HOST={smtp_host!r} – kontrollo .env dhe lidhjen e internetit."
            )
        else:
            print(f"[EMAIL] ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] ❌ Unexpected error: {e}")
        return False


def _send_in_thread(to_email: str, subject: str, html: str, text: str) -> None:
    """Fires _send_email in a daemon thread so it never blocks the HTTP response."""
    t = threading.Thread(
        target=_send_email,
        args=(to_email, subject, html, text),
        daemon=True,
    )
    t.start()


# ─────────────────────────────────────────────
# Email templates
# ─────────────────────────────────────────────

_BASE_STYLE = """
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
         line-height: 1.6; color: #1e293b; margin: 0; padding: 0; background: #f8fafc; }
  .wrap { max-width: 600px; margin: 32px auto; background: #fff;
          border-radius: 14px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,.09); }
  .hdr  { padding: 36px 30px; text-align: center; color: #fff; }
  .hdr h1 { margin: 0; font-size: 26px; font-weight: 800; }
  .hdr .ico { font-size: 52px; display: block; margin-bottom: 12px; }
  .body { padding: 36px 30px; }
  .body p  { color: #475569; font-size: 15px; margin: 0 0 16px; }
  .body h2 { color: #1e293b; font-size: 18px; margin: 0 0 12px; }
  .card { background: #f0f9ff; border-radius: 10px; padding: 20px; margin: 20px 0; }
  .row  { display: flex; align-items: flex-start; margin-bottom: 14px; }
  .row .icon { font-size: 22px; margin-right: 12px; flex-shrink: 0; }
  .row strong { display: block; color: #1e293b; margin-bottom: 2px; font-size: 14px; }
  .row span   { color: #64748b; font-size: 13px; }
  .btn { display: inline-block; padding: 14px 32px; border-radius: 10px; color: #fff !important;
         font-weight: 700; font-size: 15px; text-decoration: none;
         box-shadow: 0 4px 12px rgba(0,0,0,.15); }
  .center { text-align: center; margin: 28px 0; }
  .ftr { background: #f8fafc; border-top: 1px solid #e2e8f0;
         padding: 22px 30px; text-align: center; color: #94a3b8; font-size: 13px; }
  .ftr a { color: #4A9FD4; text-decoration: none; }
  .box-warn { background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 8px;
              padding: 16px; margin: 16px 0; color: #7f1d1d; font-size: 14px; }
  .stat-grid { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }
  .stat-box  { flex: 1 1 120px; background: #f8fafc; border: 1px solid #e2e8f0;
               border-radius: 10px; padding: 14px; text-align: center; }
  .stat-box .num { font-size: 28px; font-weight: 800; color: #2563eb; }
  .stat-box .lbl { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; }
</style>
"""


def _footer_html() -> str:
    return """
    <div class="ftr">
      <strong>AlbLingo</strong> — Platformë Edukative për Gjuhën Shqipe<br>
      © 2026 AlbLingo. Të gjitha të drejtat e rezervuara.<br>
      <a href="mailto:support@alblingo.com">support@alblingo.com</a>
    </div>
    """


# ─────── 1. Welcome ───────

def send_welcome_email(user_email: str, username: str, blocking: bool = False) -> bool:
    """
    Dërgon emailin e mirëseardhjes pas regjistrimit.
    blocking=False (default) → dërgon në thread të veçantë, nuk bllokojë HTTP-në.
    """
    app_url = _cfg("APP_URL", "http://localhost:5173")
    subject = f"Mirë se erdhe në AlbLingo, {username}!"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{_BASE_STYLE}</head><body>
<div class="wrap">
  <div class="hdr" style="background:linear-gradient(135deg,#1e3a8a 0%,#2563eb 100%)">
    <span class="ico">🎓</span>
    <h1>Mirë se erdhe në AlbLingo!</h1>
  </div>
  <div class="body">
    <h2>Përshëndetje, {username}!</h2>
    <p>Faleminderit që u regjistrove. Platforma AlbLingo është krijuar për të ndihmuar
       nxënësit të mësojnë gjuhën shqipe në mënyrë të thjeshtë dhe efektive.</p>

    <div class="card">
      <div class="row"><span class="icon">📚</span>
        <div><strong>Kurse të strukturuara</strong>
             <span>Klasa dhe nivele të organizuara sipas vështirësisë</span></div>
      </div>
      <div class="row"><span class="icon">🤖</span>
        <div><strong>AI i avancuar</strong>
             <span>Ushtrime të personalizuara bazuar në performancën tënde</span></div>
      </div>
      <div class="row"><span class="icon">📊</span>
        <div><strong>Progres i detajuar</strong>
             <span>Shih ecurinë tënde dhe arritjet në çdo nivel</span></div>
      </div>
      <div class="row"><span class="icon">🔥</span>
        <div><strong>Streak &amp; Gamifikim</strong>
             <span>Qëndro i motivuar duke praktikuar çdo ditë</span></div>
      </div>
    </div>

    <div class="center">
      <a href="{app_url}" class="btn" style="background:#2563eb">Fillo mësimin tani</a>
    </div>

    <p style="font-size:13px;color:#94a3b8;text-align:center;">
      Nëse nuk ke krijuar ti këtë llogari, injoro këtë email.
    </p>
  </div>
  {_footer_html()}
</div>
</body></html>"""

    text = (
        f"Mirë se erdhe në AlbLingo, {username}!\n\n"
        "Platforma jonë ofron:\n"
        "- Kurse të strukturuara\n"
        "- Ushtrime me AI\n"
        "- Progres i detajuar\n"
        "- Gamifikim dhe streak\n\n"
        f"Fillo mësimin: {app_url}\n\n"
        "Ekipi i AlbLingo"
    )

    if blocking:
        return _send_email(user_email, subject, html, text)
    _send_in_thread(user_email, subject, html, text)
    return True


# ─────── 2. Streak warning ───────

def send_streak_warning_email(
    user_email: str,
    username: str,
    current_streak: int,
    last_login: datetime,
    blocking: bool = False,
) -> bool:
    app_url = _cfg("APP_URL", "http://localhost:5173")
    hours_since = (datetime.utcnow() - last_login).total_seconds() / 3600
    hours_left = max(0, 24 - hours_since)
    subject = f"{username}, streak-u yt i {current_streak} ditëve është në rrezik!"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{_BASE_STYLE}</head><body>
<div class="wrap">
  <div class="hdr" style="background:linear-gradient(135deg,#dc2626 0%,#ef4444 100%)">
    <span class="ico">🔥</span>
    <h1>Streak-u yt është në rrezik!</h1>
  </div>
  <div class="body">
    <h2>Përshëndetje, {username}!</h2>

    <div class="box-warn">
      Ti nuk je futur në AlbLingo prej <strong>{int(hours_since)} orësh</strong>.
      Nëse nuk praktikon sot, humb streak-un tënd të <strong>{current_streak} ditëve</strong>!
    </div>

    <div class="stat-grid">
      <div class="stat-box">
        <div class="num">{current_streak}</div>
        <div class="lbl">Ditë streak</div>
      </div>
      <div class="stat-box">
        <div class="num">~{int(hours_left)}h</div>
        <div class="lbl">Kohë e mbetur</div>
      </div>
    </div>

    <p>Vetëm <strong>5 minuta praktikë</strong> janë të mjaftueshme për ta mbajtur streakun gjallë!</p>

    <div class="center">
      <a href="{app_url}" class="btn" style="background:#dc2626">Praktiko tani</a>
    </div>

    <p style="text-align:center;color:#94a3b8;font-size:13px;">
      <em>"Konsistenca është çelësi i suksesit."</em>
    </p>
  </div>
  {_footer_html()}
</div>
</body></html>"""

    text = (
        f"Përshëndetje {username},\n\n"
        f"Streak-u yt i {current_streak} ditëve është në rrezik!\n"
        f"Nuk je futur prej {int(hours_since)} orësh. Koha e mbetur: ~{int(hours_left)} orë.\n\n"
        f"Praktiko tani: {app_url}\n\n"
        "Ekipi i AlbLingo"
    )

    if blocking:
        return _send_email(user_email, subject, html, text)
    _send_in_thread(user_email, subject, html, text)
    return True


# ─────── 3. Weekly report ───────

def send_weekly_report_email(
    user_email: str,
    username: str,
    stats: Dict[str, Any],
    blocking: bool = False,
) -> bool:
    app_url = _cfg("APP_URL", "http://localhost:5173")
    exercises = stats.get("exercises_completed", 0)
    avg_score = stats.get("avg_score", 0)
    time_spent = stats.get("time_spent_minutes", 0)
    streak = stats.get("current_streak", 0)
    strengths = stats.get("strengths", [])
    weaknesses = stats.get("weaknesses", [])

    if avg_score >= 85:
        perf_msg, perf_color = "Performanca jote ka qenë SHKËLQYESE! 🌟", "#10b981"
    elif avg_score >= 70:
        perf_msg, perf_color = "Po bën progres të mirë! 👍", "#3b82f6"
    else:
        perf_msg, perf_color = "Vazhdo me përpjekjet! 💪", "#f59e0b"

    strengths_html = "".join(
        f'<div style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:6px;'
        f'padding:10px 14px;margin:6px 0;font-size:14px;">{s}</div>'
        for s in strengths[:3]
    )
    weaknesses_html = "".join(
        f'<div style="background:#fff7ed;border-left:4px solid #f59e0b;border-radius:6px;'
        f'padding:10px 14px;margin:6px 0;font-size:14px;">{w}</div>'
        for w in weaknesses[:2]
    )

    subject = f"Raporti yt javor në AlbLingo — {username}"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{_BASE_STYLE}</head><body>
<div class="wrap">
  <div class="hdr" style="background:linear-gradient(135deg,#7c3aed 0%,#6366f1 100%)">
    <span class="ico">📊</span>
    <h1>Raporti Yt Javor</h1>
  </div>
  <div class="body">
    <h2>Përshëndetje, {username}!</h2>
    <p>Ja çfarë arrite këtë javë në AlbLingo:</p>

    <div class="stat-grid">
      <div class="stat-box"><div class="num">{exercises}</div><div class="lbl">Ushtrime</div></div>
      <div class="stat-box"><div class="num">{avg_score}%</div><div class="lbl">Saktësi</div></div>
      <div class="stat-box"><div class="num">{time_spent}m</div><div class="lbl">Kohë</div></div>
      <div class="stat-box"><div class="num">{streak}🔥</div><div class="lbl">Streak</div></div>
    </div>

    <div style="background:{perf_color};color:#fff;border-radius:10px;
                padding:16px;text-align:center;font-weight:700;font-size:15px;margin:16px 0;">
      {perf_msg}
    </div>

    {"<h2>Pikat e Forta</h2>" + strengths_html if strengths_html else ""}
    {"<h2>Fusha për Përmirësim</h2>" + weaknesses_html if weaknesses_html else ""}

    <div class="center">
      <a href="{app_url}" class="btn" style="background:#7c3aed">Vazhdo mësimin</a>
    </div>

    <p style="text-align:center;color:#94a3b8;font-size:13px;">
      <em>"Çdo ditë praktike të afron drejt qëllimit tënd!"</em>
    </p>
  </div>
  {_footer_html()}
</div>
</body></html>"""

    text = (
        f"Raporti javor — {username}\n\n"
        f"Ushtrime: {exercises}\n"
        f"Saktësi: {avg_score}%\n"
        f"Kohë: {time_spent} min\n"
        f"Streak: {streak} ditë\n\n"
        f"{perf_msg}\n\n"
        f"Vazhdo: {app_url}\n\n"
        "Ekipi i AlbLingo"
    )

    if blocking:
        return _send_email(user_email, subject, html, text)
    _send_in_thread(user_email, subject, html, text)
    return True


# ─────────────────────────────────────────────
# Backward-compatibility wrapper (old call style)
# ─────────────────────────────────────────────

class EmailService:
    """Thin wrapper kept for backward compatibility with existing call sites."""

    def send_welcome_email(self, user_email: str, username: str) -> bool:
        return send_welcome_email(user_email, username, blocking=True)

    def send_streak_warning_email(
        self, user_email: str, username: str, current_streak: int, last_login: datetime
    ) -> bool:
        return send_streak_warning_email(user_email, username, current_streak, last_login, blocking=True)

    def send_weekly_personalized_email(
        self, user_email: str, username: str, stats: Dict[str, Any]
    ) -> bool:
        return send_weekly_report_email(user_email, username, stats, blocking=True)


email_service = EmailService()
