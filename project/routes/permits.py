from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, PermitModel, VesselModel, UserModel, AdminLog
from datetime import date

permitsApp = Blueprint('permitsBp', __name__)

@permitsApp.route('/')
def list_permits():
    status_filter = request.args.get('status', None)
    
    if g.user.role == 'inspector':
        query = PermitModel.query
        if status_filter and status_filter in ('active', 'expired', 'revoked'):
            query = query.filter_by(status=status_filter)
        permits = query.order_by(PermitModel.created_at.desc()).all()
    else:
        query = PermitModel.query.filter_by(holder_id=g.user.id)
        if status_filter and status_filter in ('active', 'expired', 'revoked'):
            query = query.filter_by(status=status_filter)
        permits = query.order_by(PermitModel.created_at.desc()).all()
    
    return render_template('permits/list.html', user=g.user, permits=permits, current_filter=status_filter)


@permitsApp.route('/<int:permit_id>')
def permit_detail(permit_id):
    permit = PermitModel.query.get_or_404(permit_id)

    if permit.holder_id != g.user.id and g.user.role not in ('admin', 'inspector'):
        flash('Нямате достъп до това разрешително.', 'error')
        return redirect(url_for('permitsBp.list_permits'))

    return render_template('permits/detail.html', user=g.user, permit=permit)


@permitsApp.route('/issue', methods=['GET', 'POST'])
def issue_permit():
    if g.user.role != 'admin':
        return redirect(url_for('permitsBp.list_permits'))

    if request.method == 'POST':
        vessel_id = request.form.get('vessel_id')
        holder_id = request.form.get('holder_id')

        vessel = VesselModel.query.get_or_404(vessel_id)
        if vessel.status != 'approved':
            flash('Корабът трябва да бъде одобрен преди издаване на разрешително.', 'error')
            return redirect(url_for('permitsBp.issue_permit'))

        existing = PermitModel.query.filter_by(
            vessel_id=vessel_id, status='active'
        ).first()
        if existing:
            flash(f'Корабът вече има активно разрешително: {existing.permit_number}.', 'error')
            return redirect(url_for('permitsBp.issue_permit'))

        permit = PermitModel(
            holder_id = holder_id,
            vessel_id = vessel_id,
            permit_number = request.form['permit_number'],
            issued_date = date.fromisoformat(request.form['issued_date']),
            valid_until = date.fromisoformat(request.form['valid_until']),
            captain_name = request.form.get('captain_name'),
            captain_license = request.form.get('captain_license'),
            allowed_gear = request.form.get('allowed_gear'),
            status = 'active',
        )
        db.session.add(permit)
        db.session.commit()

        log_entry = AdminLog(admin_id=g.user.id, action='issue_permit', target=permit.permit_number, note=f'{permit.vessel.cfr_number} / {permit.vessel.marking}')
        db.session.add(log_entry)
        db.session.commit()

        flash(f'Разрешително {permit.permit_number} е издадено успешно.', 'success')
        return redirect(url_for('adminBp.index'))

    preselected_vessel_id = request.args.get('vessel_id', type=int)
    vessels = VesselModel.query.filter_by(status='approved').all()
    users = UserModel.query.filter_by(is_active=True).all()
    return render_template('permits/issue.html', user=g.user, vessels=vessels, users=users, preselected_vessel_id=preselected_vessel_id)



@permitsApp.route('/<int:permit_id>/revoke', methods=['POST'])
def revoke_permit(permit_id):
    if g.user.role != 'admin':
        return redirect(url_for('permitsBp.list_permits'))

    permit = PermitModel.query.get_or_404(permit_id)
    reason = request.form.get('reason', '').strip()

    if not reason:
        flash('Необходимо е посочване на причина при отнемане на разрешително.', 'error')
        return redirect(url_for('permitsBp.permit_detail', permit_id=permit_id))

    permit.status = 'revoked'
    permit.revoke_reason = reason
    db.session.commit()

    log_entry = AdminLog(admin_id=g.user.id, action='revoke_permit', target=permit.permit_number, note=reason)
    db.session.add(log_entry)
    db.session.commit()

    flash(f'Разрешително {permit.permit_number} е отнето.', 'success')
    return redirect(url_for('adminBp.index'))


def expire_permits():
    today = date.today()
    expired = PermitModel.query.filter(PermitModel.status == 'active',PermitModel.valid_until < today).all()
    for permit in expired:
        permit.status = 'expired'
    db.session.commit()