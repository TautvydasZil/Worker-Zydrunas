from flask import Blueprint, request, jsonify

from extensions import db
from models import Project, HoursLogged
from helpers import login_required, manager_or_admin_required, _validate_str

bp = Blueprint('projects', __name__, url_prefix='/api')


@bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.order_by(Project.name).all()
    return jsonify([p.to_dict() for p in projects])


@bp.route('/projects', methods=['POST'])
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


@bp.route('/projects/<int:project_id>', methods=['PUT'])
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


@bp.route('/projects/<int:project_id>/complete', methods=['PATCH'])
@login_required
@manager_or_admin_required
def toggle_project_complete(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'error': 'Projektas nerastas'}), 404
    project.is_completed = not project.is_completed
    db.session.commit()
    return jsonify(project.to_dict())


@bp.route('/projects/<int:project_id>', methods=['DELETE'])
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
