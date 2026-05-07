from datetime import datetime

from flask import Blueprint, request, jsonify

from extensions import db
from models import HoursLogged, Project, LeaveRequest
from helpers import login_required, manager_or_admin_required, get_current_user, _validate_str

bp = Blueprint('hours', __name__, url_prefix='/api')


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


@bp.route('/hours', methods=['POST'])
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


@bp.route('/hours', methods=['GET'])
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


@bp.route('/hours/<int:entry_id>', methods=['PUT'])
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


@bp.route('/hours/<int:entry_id>', methods=['DELETE'])
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
