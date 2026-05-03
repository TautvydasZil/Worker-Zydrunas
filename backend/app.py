import os
import re
import secrets
import smtplib
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# ---------------------------------------------------------------------------
# Environment flags
# ---------------------------------------------------------------------------

IS_PROD = os.getenv('FLASK_ENV') == 'production'
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')]
FRONTEND_URL    = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = logging.INFO if IS_PROD else logging.DEBUG
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('app')

if IS_PROD:
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

# ---------------------------------------------------------------------------
# App & extensions
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY']                  = os.getenv('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI']     = os.getenv('DATABASE_URL', 'sqlite:///worker_hours.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE']    = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY']    = True
app.config['SESSION_COOKIE_SECURE']      = IS_PROD

CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
limiter = Limiter(get_remote_address, app=app, default_limits=[], storage_uri='memory://')

# ---------------------------------------------------------------------------
# SMTP config
# ---------------------------------------------------------------------------

SMTP_HOST  = os.getenv('SMTP_HOST', '')
SMTP_PORT  = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER  = os.getenv('SMTP_USER', '')
SMTP_PASS  = os.getenv('SMTP_PASS', '')
SMTP_FROM  = os.getenv('SMTP_FROM', SMTP_USER)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(255), nullable=True, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name    = db.Column(db.String(80), nullable=False, default='')
    last_name     = db.Column(db.String(80), nullable=False, default='')
    role          = db.Column(db.String(20), default='worker')  # worker | manager | admin
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active
        }


class Project(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(200), nullable=False)
    latitude     = db.Column(db.Float, nullable=True)
    longitude    = db.Column(db.Float, nullable=True)
    address      = db.Column(db.String(500))
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'is_completed': self.is_completed,
        }


class HoursLogged(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    date       = db.Column(db.Date, nullable=False)
    hours      = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.String(5), nullable=True)
    end_time   = db.Column(db.String(5), nullable=True)
    lunch_break = db.Column(db.Integer, nullable=True)
    notes      = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LeaveRequest(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type        = db.Column(db.String(20), nullable=False)
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    notes       = db.Column(db.String(255))
    status      = db.Column(db.String(20), default='pending')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        days = (self.end_date - self.start_date).days + 1
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'days': days,
            'notes': self.notes,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class Invite(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20), nullable=False, default='worker')
    used       = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PasswordResetToken(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _validate_str(val, field, min_len=1, max_len=255, required=True):
    if val is None or str(val).strip() == '':
        if required:
            raise ValueError(f'{field}: laukas privalomas')
        return ''
    s = str(val).strip()
    if len(s) < min_len:
        raise ValueError(f'{field}: per trumpas (min {min_len} simboliai)')
    if len(s) > max_len:
        raise ValueError(f'{field}: per ilgas (maks {max_len} simboliai)')
    return s


def _validate_email(val, field='El. paštas'):
    s = _validate_str(val, field, max_len=255)
    if not _EMAIL_RE.match(s):
        raise ValueError(f'{field}: netinkamas formatas')
    return s.lower()


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return jsonify({'error': 'Resurso nerasta'}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({'error': 'Metodas neleidžiamas'}), 405


@app.errorhandler(429)
def rate_limited(_e):
    return jsonify({'error': 'Per daug užklausų. Bandykite vėliau.'}), 429


@app.errorhandler(500)
def server_error(_e):
    logger.error('Unhandled exception', exc_info=True)
    return jsonify({'error': 'Vidinė serverio klaida. Bandykite vėliau.'}), 500


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Nesate prisijungęs'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin':
            return jsonify({'error': 'Prieiga uždrausta'}), 403
        return f(*args, **kwargs)
    return decorated


def manager_or_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user.role not in ('manager', 'admin'):
            return jsonify({'error': 'Prieiga uždrausta'}), 403
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Email helper
# ---------------------------------------------------------------------------

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


ROLE_LT = {'worker': 'darbuotojo', 'manager': 'vadybininko', 'admin': 'administratoriaus'}


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


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    required = ['token', 'username', 'password', 'first_name', 'last_name']
    if not all(k in data for k in required):
        return jsonify({'error': 'Trūksta laukų'}), 400

    invite = Invite.query.filter_by(token=data['token'], used=False).first()
    if not invite:
        return jsonify({'error': 'Netinkama arba jau panaudota pakvietimo nuoroda'}), 400
    if invite.expires_at < datetime.utcnow():
        return jsonify({'error': 'Pakvietimo nuorodos galiojimo laikas baigėsi'}), 400

    try:
        username   = _validate_str(data.get('username'), 'Vartotojo vardas', min_len=3, max_len=80)
        password   = _validate_str(data.get('password'), 'Slaptažodis', min_len=8, max_len=128)
        first_name = _validate_str(data.get('first_name'), 'Vardas', max_len=80)
        last_name  = _validate_str(data.get('last_name'), 'Pavardė', max_len=80)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if not re.match(r'^[\w.\-]+$', username):
        return jsonify({'error': 'Vartotojo vardas gali turėti tik raides, skaičius, taškus ir brūkšnelius'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Toks vartotojo vardas jau užimtas'}), 409

    if invite.email and User.query.filter_by(email=invite.email).first():
        return jsonify({'error': 'Ši el. pašto adresu paskyra jau egzistuoja'}), 409

    user = User(
        username=username,
        email=invite.email,
        first_name=first_name,
        last_name=last_name,
        role=invite.role
    )
    user.set_password(password)
    invite.used = True
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@app.route('/api/auth/invite/validate', methods=['GET'])
def validate_invite():
    token = request.args.get('token', '')
    invite = Invite.query.filter_by(token=token, used=False).first()
    if not invite or invite.expires_at < datetime.utcnow():
        return jsonify({'valid': False}), 400
    return jsonify({'valid': True, 'email': invite.email, 'role': invite.role})


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit('10 per minute; 50 per hour')
def login():
    data = request.json or {}
    if not all(k in data for k in ['username', 'password']):
        return jsonify({'error': 'Trūksta laukų'}), 400

    username = str(data.get('username', '')).strip()[:80]
    password = str(data.get('password', ''))[:128]

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Neteisingas vartotojo vardas arba slaptažodis'}), 401
    if not user.is_active:
        return jsonify({'error': 'Ši paskyra yra išjungta'}), 403

    session['user_id'] = user.id
    logger.info('User %s logged in from %s', user.username, request.remote_addr)
    return jsonify(user.to_dict())


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Atsijungta'})


@app.route('/api/auth/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Nesate prisijungęs'}), 401
    return jsonify(user.to_dict())


@app.route('/api/auth/me', methods=['PATCH'])
@login_required
def update_me():
    user = get_current_user()
    data = request.json or {}

    if 'email' in data:
        try:
            new_email = _validate_email(data['email'], 'El. paštas')
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Šis el. paštas jau naudojamas'}), 409
        user.email = new_email

    if 'first_name' in data:
        try:
            user.first_name = _validate_str(data['first_name'], 'Vardas', max_len=80)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    if 'last_name' in data:
        try:
            user.last_name = _validate_str(data['last_name'], 'Pavardė', max_len=80)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    if 'password' in data:
        current = str(data.get('current_password', ''))
        if not user.check_password(current):
            return jsonify({'error': 'Dabartinis slaptažodis neteisingas'}), 400
        try:
            new_pw = _validate_str(data['password'], 'Naujas slaptažodis', min_len=8, max_len=128)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        user.set_password(new_pw)

    db.session.commit()
    return jsonify(user.to_dict())


@app.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit('5 per hour')
def forgot_password():
    data = request.json or {}
    email = str(data.get('email', '')).strip().lower()
    # Always return 200 so we don't reveal which emails exist
    if not email or not _EMAIL_RE.match(email):
        return jsonify({'message': 'Jei el. paštas rastas — gausite laišką'}), 200

    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
        # Invalidate previous tokens
        PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
        db.session.commit()

        token = secrets.token_urlsafe(32)
        reset = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(reset)
        db.session.commit()
        send_password_reset_email(email, token)
        logger.info('Password reset requested for %s', email)

    return jsonify({'message': 'Jei el. paštas rastas — gausite laišką'}), 200


@app.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit('10 per hour')
def reset_password():
    data = request.json or {}
    token    = str(data.get('token', '')).strip()
    password = str(data.get('password', ''))

    if not token:
        return jsonify({'error': 'Trūksta žetono'}), 400

    try:
        password = _validate_str(password, 'Slaptažodis', min_len=8, max_len=128)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        return jsonify({'error': 'Nuoroda negaliojanti arba pasibaigusi'}), 400

    user = db.session.get(User, reset.user_id)
    if not user or not user.is_active:
        return jsonify({'error': 'Vartotojas nerastas'}), 404

    user.set_password(password)
    reset.used = True
    db.session.commit()
    logger.info('Password reset completed for user %s', user.username)
    return jsonify({'message': 'Slaptažodis pakeistas'}), 200


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@app.route('/api/users', methods=['GET'])
@login_required
@manager_or_admin_required
def get_users():
    users = User.query.order_by(User.last_name, User.first_name).all()
    return jsonify([u.to_dict() for u in users])


@app.route('/api/users/<int:user_id>/dismiss', methods=['PATCH'])
@login_required
@manager_or_admin_required
def dismiss_user(user_id):
    actor  = get_current_user()
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({'error': 'Vartotojas nerastas'}), 404
    if target.id == actor.id:
        return jsonify({'error': 'Negalite atleisti savęs'}), 400
    if target.role == 'admin':
        return jsonify({'error': 'Negalite atleisti administratoriaus'}), 403
    if actor.role == 'manager' and target.role == 'manager':
        return jsonify({'error': 'Vadybininkas negali atleisti kito vadybininko'}), 403
    target.is_active = False
    db.session.commit()
    return jsonify(target.to_dict())


@app.route('/api/users/<int:user_id>/reactivate', methods=['PATCH'])
@login_required
@manager_or_admin_required
def reactivate_user(user_id):
    actor  = get_current_user()
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({'error': 'Vartotojas nerastas'}), 404
    if actor.role == 'manager' and target.role == 'manager':
        return jsonify({'error': 'Vadybininkas negali aktyvuoti kito vadybininko'}), 403
    target.is_active = True
    db.session.commit()
    return jsonify(target.to_dict())


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.order_by(Project.name).all()
    return jsonify([p.to_dict() for p in projects])


@app.route('/api/projects', methods=['POST'])
@login_required
@manager_or_admin_required
def create_project():
    data = request.json or {}
    try:
        name = _validate_str(data.get('name'), 'Pavadinimas', max_len=200)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    project = Project(
        name=name,
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        address=_validate_str(data.get('address', ''), 'Adresas', min_len=0, max_len=500, required=False) or None
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@login_required
@manager_or_admin_required
def update_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404

    data = request.json or {}
    try:
        if 'name' in data:
            project.name = _validate_str(data['name'], 'Pavadinimas', max_len=200)
        if 'address' in data:
            project.address = _validate_str(data['address'], 'Adresas', min_len=0, max_len=500, required=False) or None
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if 'latitude' in data:
        project.latitude  = data['latitude']
    if 'longitude' in data:
        project.longitude = data['longitude']

    db.session.commit()
    return jsonify(project.to_dict())


@app.route('/api/projects/<int:project_id>/complete', methods=['PATCH'])
@login_required
@manager_or_admin_required
def toggle_project_complete(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    project.is_completed = not project.is_completed
    db.session.commit()
    return jsonify(project.to_dict())


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
@manager_or_admin_required
def delete_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    HoursLogged.query.filter_by(project_id=project_id).update({'project_id': None})
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Projektas ištrintas'})


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------

INVITE_EXPIRY_DAYS = 7

INVITE_PERMISSIONS = {
    'admin':   {'worker', 'manager', 'admin'},
    'manager': {'worker', 'manager'},
}


@app.route('/api/invites', methods=['POST'])
@login_required
@manager_or_admin_required
def create_invite():
    data = request.json or {}
    user = get_current_user()

    try:
        email = _validate_email(data.get('email'), 'El. paštas')
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    role    = data.get('role', 'worker')
    allowed = INVITE_PERMISSIONS.get(user.role, set())
    if role not in allowed:
        return jsonify({'error': 'Negalite pakviesti tokio vaidmens'}), 403

    token  = secrets.token_urlsafe(32)
    invite = Invite(
        token=token,
        email=email,
        role=role,
        expires_at=datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)
    )
    db.session.add(invite)
    db.session.commit()

    send_invite_email(email, token, role)

    return jsonify({
        'id': invite.id,
        'token': token,
        'email': invite.email,
        'role': invite.role,
        'expires_at': invite.expires_at.isoformat()
    }), 201


@app.route('/api/invites', methods=['GET'])
@login_required
@manager_or_admin_required
def list_invites():
    invites = Invite.query.order_by(Invite.created_at.desc()).all()
    return jsonify([{
        'id': i.id,
        'token': i.token,
        'email': i.email,
        'role': i.role,
        'used': i.used,
        'expires_at': i.expires_at.isoformat()
    } for i in invites])


@app.route('/api/invites/<int:invite_id>', methods=['DELETE'])
@login_required
@manager_or_admin_required
def delete_invite(invite_id):
    invite = db.session.get(Invite, invite_id)
    if not invite:
        return jsonify({'error': 'Nerasta'}), 404
    db.session.delete(invite)
    db.session.commit()
    return jsonify({'message': 'Pakvietimas atšauktas'})


# ---------------------------------------------------------------------------
# Hours
# ---------------------------------------------------------------------------

def _time_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m


def _overlapping_entry(user_id, date, new_start, new_end, exclude_id=None):
    entries = HoursLogged.query.filter(
        HoursLogged.user_id == user_id,
        HoursLogged.date == date,
        HoursLogged.start_time.isnot(None),
        HoursLogged.end_time.isnot(None)
    ).all()
    for e in entries:
        if exclude_id and e.id == exclude_id:
            continue
        s  = _time_to_minutes(e.start_time)
        en = _time_to_minutes(e.end_time)
        if new_start < en and new_end > s:
            return e
    return None


def _hours_to_dict(e, project_map):
    return {
        'id': e.id,
        'user_id': e.user_id,
        'project_id': e.project_id,
        'project_name': project_map.get(e.project_id),
        'date': e.date.isoformat(),
        'hours': e.hours,
        'start_time': e.start_time,
        'end_time': e.end_time,
        'lunch_break': e.lunch_break,
        'notes': e.notes
    }


@app.route('/api/hours', methods=['POST'])
@login_required
def log_hours():
    data = request.json or {}
    user = get_current_user()

    if not all(k in data for k in ['date', 'start_time', 'end_time']):
        return jsonify({'error': 'Trūksta laukų'}), 400

    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Netinkamas datos formatas'}), 400

    try:
        start_h, start_m = map(int, data['start_time'].split(':'))
        end_h,   end_m   = map(int, data['end_time'].split(':'))
    except (ValueError, AttributeError):
        return jsonify({'error': 'Netinkamas laiko formatas'}), 400

    try:
        notes = _validate_str(data.get('notes', ''), 'Pastabos', min_len=0, max_len=255, required=False)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    lunch_break   = max(0, int(data.get('lunch_break') or 0))
    total_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m) - lunch_break
    if total_minutes <= 0:
        return jsonify({'error': 'Darbo laikas turi būti teigiamas (patikrinkite pradžios, pabaigos laiką ir pietų pertrauką)'}), 400
    if total_minutes > 24 * 60:
        return jsonify({'error': 'Valandos negali viršyti 24'}), 400

    conflict = LeaveRequest.query.filter(
        LeaveRequest.user_id == user.id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= date,
        LeaveRequest.end_date >= date
    ).first()
    if conflict:
        type_str = 'atostogų' if conflict.type == 'vacation' else 'nedarbingumo'
        return jsonify({'error': f'Šią dieną turite patvirtintą {type_str} prašymą — darbo valandų įvesti negalima'}), 400

    new_start = start_h * 60 + start_m
    new_end   = end_h   * 60 + end_m
    overlap   = _overlapping_entry(user.id, date, new_start, new_end)
    if overlap:
        return jsonify({'error': f'Šis laikas persidengia su jau įvestu įrašu ({overlap.start_time}–{overlap.end_time})'}), 400

    project_id = data.get('project_id')
    if project_id and not db.session.get(Project, project_id):
        return jsonify({'error': 'Projektas nerastas'}), 404

    entry = HoursLogged(
        user_id=user.id,
        project_id=project_id or None,
        date=date,
        hours=round(total_minutes / 60, 2),
        start_time=data['start_time'],
        end_time=data['end_time'],
        lunch_break=lunch_break if lunch_break else None,
        notes=notes
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'id': entry.id, 'message': 'Valandos įvestos!'}), 201


@app.route('/api/hours', methods=['GET'])
@login_required
def get_hours():
    user = get_current_user()
    if user.role in ('admin', 'manager'):
        target_id = request.args.get('user_id', type=int)
        date_from = request.args.get('date_from')
        date_to   = request.args.get('date_to')
        q         = HoursLogged.query
        if target_id:
            q = q.filter_by(user_id=target_id)
        if date_from:
            try:
                q = q.filter(HoursLogged.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                pass
        if date_to:
            try:
                q = q.filter(HoursLogged.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                pass
        entries = q.order_by(HoursLogged.date.desc()).all()
    else:
        entries = HoursLogged.query.filter_by(user_id=user.id).order_by(HoursLogged.date.desc()).all()

    proj_ids    = {e.project_id for e in entries if e.project_id}
    project_map = {p.id: p.name for p in Project.query.filter(Project.id.in_(proj_ids)).all()} if proj_ids else {}
    return jsonify([_hours_to_dict(e, project_map) for e in entries])


@app.route('/api/hours/<int:entry_id>', methods=['PUT'])
@login_required
def update_hours(entry_id):
    user  = get_current_user()
    entry = db.session.get(HoursLogged, entry_id)
    if not entry:
        return jsonify({'error': 'Nerasta'}), 404
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403

    data = request.json or {}
    if not all(k in data for k in ['date', 'start_time', 'end_time']):
        return jsonify({'error': 'Trūksta laukų'}), 400

    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Netinkamas datos formatas'}), 400

    try:
        start_h, start_m = map(int, data['start_time'].split(':'))
        end_h,   end_m   = map(int, data['end_time'].split(':'))
    except (ValueError, AttributeError):
        return jsonify({'error': 'Netinkamas laiko formatas'}), 400

    try:
        notes = _validate_str(data.get('notes', ''), 'Pastabos', min_len=0, max_len=255, required=False)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    lunch_break   = max(0, int(data.get('lunch_break') or 0))
    total_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m) - lunch_break
    if total_minutes <= 0:
        return jsonify({'error': 'Darbo laikas turi būti teigiamas'}), 400

    conflict = LeaveRequest.query.filter(
        LeaveRequest.user_id == entry.user_id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= date,
        LeaveRequest.end_date >= date
    ).first()
    if conflict:
        type_str = 'atostogų' if conflict.type == 'vacation' else 'nedarbingumo'
        return jsonify({'error': f'Šią dieną turite patvirtintą {type_str} prašymą'}), 400

    new_start = start_h * 60 + start_m
    new_end   = end_h   * 60 + end_m
    overlap   = _overlapping_entry(entry.user_id, date, new_start, new_end, exclude_id=entry_id)
    if overlap:
        return jsonify({'error': f'Šis laikas persidengia su jau įvestu įrašu ({overlap.start_time}–{overlap.end_time})'}), 400

    project_id = data.get('project_id')
    if project_id and not db.session.get(Project, project_id):
        return jsonify({'error': 'Projektas nerastas'}), 404

    entry.date        = date
    entry.start_time  = data['start_time']
    entry.end_time    = data['end_time']
    entry.lunch_break = lunch_break if lunch_break else None
    entry.hours       = round(total_minutes / 60, 2)
    entry.project_id  = project_id or None
    entry.notes       = notes
    db.session.commit()

    proj_map = {entry.project_id: db.session.get(Project, entry.project_id).name} if entry.project_id else {}
    return jsonify(_hours_to_dict(entry, proj_map))


@app.route('/api/hours/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_hours(entry_id):
    user  = get_current_user()
    entry = db.session.get(HoursLogged, entry_id)
    if not entry:
        return jsonify({'error': 'Nerasta'}), 404
    if entry.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Ištrinta'})


# ---------------------------------------------------------------------------
# Leave requests
# ---------------------------------------------------------------------------

@app.route('/api/leave', methods=['POST'])
@login_required
def submit_leave():
    data = request.json or {}
    user = get_current_user()

    if not all(k in data for k in ['type', 'start_date', 'end_date']):
        return jsonify({'error': 'Trūksta laukų'}), 400

    if data['type'] not in ('vacation', 'sick'):
        return jsonify({'error': 'Netinkamas prašymo tipas'}), 400

    try:
        start = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end   = datetime.strptime(data['end_date'],   '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Netinkamas datos formatas'}), 400

    if end < start:
        return jsonify({'error': 'Pabaigos data negali būti ankstesnė už pradžios datą'}), 400

    try:
        notes = _validate_str(data.get('notes', ''), 'Pastabos', min_len=0, max_len=255, required=False)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    overlap = LeaveRequest.query.filter(
        LeaveRequest.user_id == user.id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start
    ).first()
    if overlap:
        return jsonify({'error': 'Pasirinktos datos jau dengiamos patvirtinto prašymo'}), 400

    auto_approve = data['type'] == 'sick'
    req = LeaveRequest(
        user_id=user.id,
        type=data['type'],
        start_date=start,
        end_date=end,
        notes=notes,
        status='approved' if auto_approve else 'pending',
        reviewed_at=datetime.utcnow() if auto_approve else None
    )
    db.session.add(req)
    db.session.commit()
    return jsonify(req.to_dict()), 201


@app.route('/api/leave', methods=['GET'])
@login_required
def get_leave():
    user = get_current_user()
    if user.role in ('admin', 'manager'):
        target_id     = request.args.get('user_id', type=int)
        status_filter = request.args.get('status')
        q             = LeaveRequest.query
        if target_id:
            q = q.filter_by(user_id=target_id)
        if status_filter:
            q = q.filter_by(status=status_filter)
        requests = q.order_by(LeaveRequest.created_at.desc()).all()
    else:
        requests = LeaveRequest.query.filter_by(user_id=user.id).order_by(LeaveRequest.created_at.desc()).all()

    return jsonify([r.to_dict() for r in requests])


@app.route('/api/leave/<int:req_id>', methods=['DELETE'])
@login_required
def delete_leave(req_id):
    user = get_current_user()
    req  = db.session.get(LeaveRequest, req_id)
    if not req:
        return jsonify({'error': 'Nerasta'}), 404
    if req.user_id != user.id and user.role not in ('admin', 'manager'):
        return jsonify({'error': 'Prieiga uždrausta'}), 403
    if req.user_id == user.id and req.status != 'pending':
        return jsonify({'error': 'Galima atšaukti tik laukiančius prašymus'}), 400
    db.session.delete(req)
    db.session.commit()
    return jsonify({'message': 'Prašymas atšauktas'})


@app.route('/api/leave/<int:req_id>/review', methods=['PATCH'])
@login_required
@manager_or_admin_required
def review_leave(req_id):
    data     = request.json or {}
    reviewer = get_current_user()

    if 'status' not in data or data['status'] not in ('approved', 'denied'):
        return jsonify({'error': 'Būsena turi būti "approved" arba "denied"'}), 400

    req = db.session.get(LeaveRequest, req_id)
    if not req:
        return jsonify({'error': 'Nerasta'}), 404
    if req.status != 'pending':
        return jsonify({'error': 'Galima peržiūrėti tik laukiančius prašymus'}), 400

    req.status      = data['status']
    req.reviewed_by = reviewer.id
    req.reviewed_at = datetime.utcnow()
    db.session.commit()
    return jsonify(req.to_dict())


if __name__ == '__main__':
    app.run(debug=not IS_PROD)
