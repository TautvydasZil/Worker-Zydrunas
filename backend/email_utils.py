import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger('app')

SMTP_HOST    = os.getenv('SMTP_HOST', '')
SMTP_PORT    = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER    = os.getenv('SMTP_USER', '')
SMTP_PASS    = os.getenv('SMTP_PASS', '')
SMTP_FROM    = os.getenv('SMTP_FROM', '') or os.getenv('SMTP_USER', '')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

ROLE_LT = {'worker': 'darbuotojo', 'manager': 'vadybininko', 'admin': 'administratoriaus'}


def _send_email(to_email: str, subject: str, html: str) -> bool:
    if not SMTP_HOST or not SMTP_USER:
        logger.warning('SMTP not configured — email not sent to %s', to_email)
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = SMTP_FROM
    msg['To']      = to_email
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        return True
    except Exception as exc:
        logger.error('Failed to send email to %s: %s', to_email, exc)
        return False


def send_invite_email(to_email: str, token: str, role: str) -> None:
    link    = f'{FRONTEND_URL}/register?token={token}'
    role_lt = ROLE_LT.get(role, role)
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px;color:#1e293b">Pakvietimas į Darbuotojų Apskaitą</h2>
      <p style="color:#475569;margin:0 0 24px">
        Jus pakvietė prisijungti kaip <strong>{role_lt}</strong>.
        Nuoroda galioja 7 dienas ir yra vienkartinė.
      </p>
      <a href="{link}"
         style="display:inline-block;padding:12px 24px;background:#4f46e5;color:#fff;
                border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Registruotis
      </a>
      <p style="color:#94a3b8;font-size:12px;margin:24px 0 0">
        Arba nukopijuokite šią nuorodą:<br>
        <span style="color:#4f46e5">{link}</span>
      </p>
    </div>"""
    _send_email(to_email, 'Pakvietimas registruotis', html)


def send_password_reset_email(to_email: str, token: str) -> None:
    link = f'{FRONTEND_URL}/reset-password?token={token}'
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px;color:#1e293b">Slaptažodžio keitimas</h2>
      <p style="color:#475569;margin:0 0 24px">
        Gautas prašymas pakeisti slaptažodį. Nuoroda galioja 1 valandą.
        Jei to neprašėte — nieko nedarykite.
      </p>
      <a href="{link}"
         style="display:inline-block;padding:12px 24px;background:#4f46e5;color:#fff;
                border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Keisti slaptažodį
      </a>
      <p style="color:#94a3b8;font-size:12px;margin:24px 0 0">
        Arba nukopijuokite šią nuorodą:<br>
        <span style="color:#4f46e5">{link}</span>
      </p>
    </div>"""
    _send_email(to_email, 'Slaptažodžio keitimas', html)
