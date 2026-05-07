from flask import Blueprint, jsonify

from extensions import db
from models import User
from helpers import login_required, manager_or_admin_required, get_current_user

bp = Blueprint('users', __name__, url_prefix='/api')


@bp.route('/users', methods=['GET'])
@login_required
@manager_or_admin_required
def get_users():
    users = User.query.order_by(User.last_name, User.first_name).all()
    return jsonify([u.to_dict() for u in users])


@bp.route('/users/<int:user_id>/dismiss', methods=['PATCH'])
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


@bp.route('/users/<int:user_id>/reactivate', methods=['PATCH'])
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
