from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, VesselModel, UserModel, AdminLog

adminApp = Blueprint('adminBp', __name__)


def log(action, target, note=''):
    entry = AdminLog(admin_id=g.user.id, action=action, target=target, note=note)
    db.session.add(entry)


@adminApp.route('/')
def index():
    from models.models import PermitModel
    pending = VesselModel.query.filter_by(status='pending').all()
    approved = VesselModel.query.filter_by(status='approved').all()
    all_users = UserModel.query.order_by(UserModel.created_at.desc()).all()
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(50).all()
    
    approved_without_permit = []
    approved_with_info = []

    approved_filter = request.args.get('approved_filter', 'all')

    for vessel in approved:
        latest_permit = PermitModel.query.filter_by(vessel_id=vessel.id).order_by(PermitModel.created_at.desc()).first()
        active_permit = latest_permit if latest_permit and latest_permit.status == 'active' else None

        if not active_permit:
            approved_without_permit.append(vessel)

        include = False
        if approved_filter in ('all', None):
            include = True
        elif approved_filter == 'without':
            include = (latest_permit is None)
        elif approved_filter == 'with':
            include = (latest_permit is not None)
        elif approved_filter in ('active', 'expired', 'revoked'):
            include = (latest_permit is not None and latest_permit.status == approved_filter)

        if include:
            approved_with_info.append({
                'vessel': vessel,
                'permit': latest_permit
            })
    
    stats = {
        'approved': VesselModel.query.filter_by(status='approved').count(),
        'rejected': VesselModel.query.filter_by(status='rejected').count(),
        'revoked':  VesselModel.query.filter_by(status='revoked').count(),
        'users':    UserModel.query.count(),
    }
    return render_template('admin/index.html', user=g.user, pending=pending, approved_without_permit=approved_without_permit, approved_with_info=approved_with_info, all_users=all_users, logs=logs, stats=stats, approved_filter=approved_filter)


# Vessels

@adminApp.route('/vessels/<int:vessel_id>/approve', methods=['POST'])
def approve(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    vessel.status = 'approved'
    log('approve', vessel.cfr_number)
    db.session.commit()
    flash(f'Кораб {vessel.cfr_number} е одобрен.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/vessels/<int:vessel_id>/reject', methods=['POST'])
def reject(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    note = request.form.get('note', '').strip()
    if not note:
        flash('Необходимо е посочване на причина при отказ.', 'error')
        return redirect(url_for('adminBp.index'))
    vessel.status = 'rejected'
    vessel.admin_note = note
    log('reject', vessel.cfr_number, note)
    db.session.commit()
    flash(f'Корабът {vessel.cfr_number} е отхвърлен.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/vessels/<int:vessel_id>/revoke', methods=['POST'])
def revoke(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    note = request.form.get('note', '').strip()
    if not note:
        flash('Необходимо е посочване на причина при отнемане.', 'error')
        return redirect(url_for('adminBp.index'))
    vessel.status     = 'revoked'
    vessel.admin_note = note
    log('revoke', vessel.cfr_number, note)
    db.session.commit()
    flash(f'Корабът {vessel.cfr_number} е отнет.', 'success')
    return redirect(url_for('adminBp.index'))


# Users

@adminApp.route('/users/<int:user_id>/role', methods=['POST'])
def change_role(user_id):
    user = UserModel.query.get_or_404(user_id)
    role = request.form.get('role')
    if role not in ('user', 'inspector', 'admin'):
        flash('Невалидна роля.', 'error')
        return redirect(url_for('adminBp.index'))
    if user.id == g.user.id:
        flash('Не можете да променяте собствената си роля.', 'error')
        return redirect(url_for('adminBp.index'))
    log('change_role', user.email, f'{user.role} → {role}')
    user.role = role
    db.session.commit()
    role_names = {'user': 'потребител', 'inspector': 'инспектор', 'admin': 'администратор'}
    flash(f'Ролята на {user.full_name} е променена на {role_names.get(role, role)}.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user(user_id):
    user = UserModel.query.get_or_404(user_id)
    if user.id == g.user.id:
        flash('Не можете да блокирате себе си.', 'error')
        return redirect(url_for('adminBp.index'))
    action = 'deactivate' if user.is_active else 'activate'
    log(action, user.email)
    user.is_active = not user.is_active
    db.session.commit()
    state = 'активиран' if user.is_active else 'блокиран'
    flash(f'{user.full_name} е {state}.', 'success')
    return redirect(url_for('adminBp.index'))