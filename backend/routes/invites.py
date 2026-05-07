import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from extensions import db
from models import Invite
from helpers import login_required, manager_or_admin_required, get_current_user, _validate_email
from email_utils import send_invite_email

bp = Blueprint('invites', __name__, url_prefix='/api')

INVITE_EXPIRY_DAYS = 7

INVITE_PERMISSIONS = {
    'admin':   {'worker', 'manager', 'admin'},
    'manager': {'worker', 'manager'},
}


@bp.route('/invites', methods=['POST'])
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


@bp.route('/invites', methods=['GET'])
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


@bp.route('/invites/<int:invite_id>', methods=['DELETE'])
@login_required
@manager_or_admin_required
def delete_invite(invite_id):
    invite = db.session.get(Invite, invite_id)
    if not invite:
        return jsonify({'error': 'Nerasta'}), 404
    db.session.delete(invite)
    db.session.commit()
    return jsonify({'message': 'Pakvietimas atšauktas'})
