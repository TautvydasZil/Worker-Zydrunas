import re
import secrets
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, session

from extensions import db, limiter
from models import User, Invite, PasswordResetToken
from helpers import get_current_user, login_required, _validate_str, _validate_email
from email_utils import send_password_reset_email

logger = logging.getLogger('app')

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
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


@bp.route('/invite/validate', methods=['GET'])
def validate_invite():
    token  = request.args.get('token', '')
    invite = Invite.query.filter_by(token=token, used=False).first()
    if not invite or invite.expires_at < datetime.utcnow():
        return jsonify({'valid': False}), 400
    return jsonify({'valid': True, 'email': invite.email, 'role': invite.role})


@bp.route('/login', methods=['POST'])
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


@bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Atsijungta'})


@bp.route('/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Nesate prisijungęs'}), 401
    return jsonify(user.to_dict())


@bp.route('/me', methods=['PATCH'])
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


@bp.route('/forgot-password', methods=['POST'])
@limiter.limit('5 per hour')
def forgot_password():
    _EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    data  = request.json or {}
    email = str(data.get('email', '')).strip().lower()
    if not email or not _EMAIL_RE.match(email):
        return jsonify({'message': 'Jei el. paštas rastas — gausite laišką'}), 200

    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
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


@bp.route('/reset-password', methods=['POST'])
@limiter.limit('10 per hour')
def reset_password():
    data     = request.json or {}
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
