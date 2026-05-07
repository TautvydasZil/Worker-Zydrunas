import re
from functools import wraps
from flask import session, jsonify
from extensions import db
from models import User

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
