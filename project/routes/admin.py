from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, VesselModel, UserModel, AdminLog

adminApp = Blueprint('adminBp', __name__)


def log(action, target, note=''):
    entry = AdminLog(admin_id=g.user.id, action=action, target=target, note=note)
    db.session.add(entry)


@adminApp.route('/')
def index():
    pending   = VesselModel.query.filter_by(status='pending').all()
    all_users = UserModel.query.order_by(UserModel.created_at.desc()).all()
    logs      = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(50).all()
    stats = {
        'approved': VesselModel.query.filter_by(status='approved').count(),
        'rejected': VesselModel.query.filter_by(status='rejected').count(),
        'revoked':  VesselModel.query.filter_by(status='revoked').count(),
        'users':    UserModel.query.count(),
    }
    return render_template('admin/index.html', user=g.user, pending=pending, all_users=all_users, logs=logs, stats=stats)


# Vessels

@adminApp.route('/vessels/<int:vessel_id>/approve', methods=['POST'])
def approve(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    vessel.status = 'approved'
    log('approve', vessel.cfr_number)
    db.session.commit()
    flash(f'Vessel {vessel.cfr_number} approved.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/vessels/<int:vessel_id>/reject', methods=['POST'])
def reject(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    note = request.form.get('note', '').strip()
    if not note:
        flash('A reason is required when rejecting.', 'error')
        return redirect(url_for('adminBp.index'))
    vessel.status = 'rejected'
    vessel.admin_note = note
    log('reject', vessel.cfr_number, note)
    db.session.commit()
    flash(f'Vessel {vessel.cfr_number} rejected.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/vessels/<int:vessel_id>/revoke', methods=['POST'])
def revoke(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    note = request.form.get('note', '').strip()
    if not note:
        flash('A reason is required when revoking.', 'error')
        return redirect(url_for('adminBp.index'))
    vessel.status     = 'revoked'
    vessel.admin_note = note
    log('revoke', vessel.cfr_number, note)
    db.session.commit()
    flash(f'Vessel {vessel.cfr_number} revoked.', 'success')
    return redirect(url_for('adminBp.index'))


# Users

@adminApp.route('/users/<int:user_id>/role', methods=['POST'])
def change_role(user_id):
    user = UserModel.query.get_or_404(user_id)
    role = request.form.get('role')
    if role not in ('user', 'inspector', 'admin'):
        flash('Invalid role.', 'error')
        return redirect(url_for('adminBp.index'))
    if user.id == g.user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('adminBp.index'))
    log('change_role', user.email, f'{user.role} → {role}')
    user.role = role
    db.session.commit()
    flash(f'Role of {user.full_name} updated to {role}.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user(user_id):
    user = UserModel.query.get_or_404(user_id)
    if user.id == g.user.id:
        flash('You cannot block yourself.', 'error')
        return redirect(url_for('adminBp.index'))
    action = 'deactivate' if user.is_active else 'activate'
    log(action, user.email)
    user.is_active = not user.is_active
    db.session.commit()
    state = 'активиран' if user.is_active else 'блокиран'
    flash(f'{user.full_name} е {state}.', 'success')
    return redirect(url_for('adminBp.index'))