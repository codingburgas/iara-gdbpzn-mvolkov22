from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, PermitModel, VesselModel, UserModel, AdminLog
from datetime import date
import random
import string

permitsApp = Blueprint('permitsBp', __name__)


def generate_permit_number():
    year = date.today().year
    count = PermitModel.query.count() + 1
    return f'IARA-{year}-{count:06d}'


@permitsApp.route('/')
def list_permits():
    status_filter = request.args.get('status', None)
    search = request.args.get('search', '').strip()

    valid_filters = ('pending', 'active', 'inactive', 'expired', 'revoked', 'rejected')

    if g.user.role in ('inspector', 'admin'):
        query = PermitModel.query
    else:
        query = PermitModel.query.filter_by(holder_id=g.user.id)

    if status_filter and status_filter in valid_filters:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.join(VesselModel).filter(
            db.or_(
                PermitModel.permit_number.ilike(f'%{search}%'),
                VesselModel.cfr_number.ilike(f'%{search}%'),
                VesselModel.marking.ilike(f'%{search}%'),
            )
        )
    permits = query.order_by(PermitModel.created_at.desc()).all()

    return render_template('permits/list.html', user=g.user, permits=permits, current_filter=status_filter, search=search)


@permitsApp.route('/request', methods=['GET', 'POST'])
def request_permit():
    if g.user.role != 'user':
        flash('Само потребители могат да заявяват разрешителни.', 'error')
        return redirect(url_for('permitsBp.list_permits'))

    if request.method == 'POST':
        vessel_id = request.form.get('vessel_id', type=int)
        vessel = VesselModel.query.get_or_404(vessel_id)

        if vessel.owner_id != g.user.id:
            flash('Можете да заявите разрешително само за ваш кораб.', 'error')
            return redirect(url_for('permitsBp.request_permit'))

        if vessel.status != 'approved':
            flash('Корабът трябва да бъде одобрен преди да заявите разрешително.', 'error')
            return redirect(url_for('permitsBp.request_permit'))

        existing_active = PermitModel.query.filter_by(vessel_id=vessel_id, status='active').first()
        if existing_active:
            flash(f'Корабът вече има активно разрешително: {existing_active.permit_number}.', 'error')
            return redirect(url_for('permitsBp.request_permit'))

        existing_pending = PermitModel.query.filter_by(vessel_id=vessel_id, status='pending').first()
        if existing_pending:
            flash('Вече имате чакаща заявка за разрешително за този кораб.', 'error')
            return redirect(url_for('permitsBp.request_permit'))

        permit = PermitModel(
            holder_id=g.user.id,
            vessel_id=vessel_id,
            permit_number=generate_permit_number(),
            issued_date=date.today(),
            valid_until=date.fromisoformat(request.form['valid_until']),
            captain_name=request.form.get('captain_name'),
            captain_license=request.form.get('captain_license'),
            allowed_gear=request.form.get('allowed_gear'),
            status='pending',
        )
        db.session.add(permit)
        db.session.commit()

        flash('Заявката за разрешително е изпратена. Изчакайте одобрение от администратор.', 'success')
        return redirect(url_for('permitsBp.list_permits'))

    vessels = VesselModel.query.filter_by(owner_id=g.user.id, status='approved').all()
    today = date.today().isoformat()
    return render_template('permits/request.html', user=g.user, vessels=vessels, today=today)


@permitsApp.route('/<int:permit_id>')
def permit_detail(permit_id):
    permit = PermitModel.query.get_or_404(permit_id)

    if permit.holder_id != g.user.id and g.user.role not in ('admin', 'inspector'):
        flash('Нямате достъп до това разрешително.', 'error')
        return redirect(url_for('permitsBp.list_permits'))

    from models.models import InspectionAct
    related_acts = InspectionAct.query.filter_by(related_permit_id=permit_id).order_by(InspectionAct.created_at.desc()).all()

    return render_template('permits/detail.html', user=g.user, permit=permit, related_acts=related_acts)


@permitsApp.route('/<int:permit_id>/edit', methods=['GET', 'POST'])
def edit_permit(permit_id):
    if g.user.role != 'admin':
        return redirect(url_for('permitsBp.list_permits'))

    permit = PermitModel.query.get_or_404(permit_id)

    if request.method == 'POST':
        permit.valid_until = date.fromisoformat(request.form['valid_until'])
        permit.captain_name = request.form.get('captain_name')
        permit.captain_license = request.form.get('captain_license')
        permit.allowed_gear = request.form.get('allowed_gear')
        db.session.commit()

        log_entry = AdminLog(admin_id=g.user.id, action='edit_permit', target=permit.permit_number)
        db.session.add(log_entry)
        db.session.commit()

        flash(f'Разрешително {permit.permit_number} е редактирано.', 'success')
        return redirect(url_for('permitsBp.permit_detail', permit_id=permit.id))

    return render_template('permits/edit.html', user=g.user, permit=permit)


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
            holder_id=holder_id,
            vessel_id=vessel_id,
            permit_number=request.form['permit_number'],
            issued_date=date.fromisoformat(request.form['issued_date']),
            valid_until=date.fromisoformat(request.form['valid_until']),
            captain_name=request.form.get('captain_name'),
            captain_license=request.form.get('captain_license'),
            allowed_gear=request.form.get('allowed_gear'),
            status='active',
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


@permitsApp.route('/<int:permit_id>/approve', methods=['POST'])
def approve_permit(permit_id):
    if g.user.role != 'admin':
        return redirect(url_for('permitsBp.list_permits'))

    permit = PermitModel.query.get_or_404(permit_id)
    if permit.status != 'pending':
        flash('Само чакащи заявки могат да бъдат одобрявани.', 'error')
        return redirect(url_for('adminBp.index'))

    existing = PermitModel.query.filter_by(vessel_id=permit.vessel_id, status='active').first()
    if existing:
        flash(f'Корабът вече има активно разрешително: {existing.permit_number}.', 'error')
        return redirect(url_for('adminBp.index'))

    permit.status = 'active'
    permit.issued_date = date.today()
    db.session.commit()

    log_entry = AdminLog(admin_id=g.user.id, action='approve_permit', target=permit.permit_number, note=f'Разрешително {permit.permit_number} е одобрено')
    db.session.add(log_entry)
    db.session.commit()

    flash(f'Разрешително {permit.permit_number} е одобрено.', 'success')
    return redirect(url_for('adminBp.index'))


@permitsApp.route('/<int:permit_id>/reject', methods=['POST'])
def reject_permit(permit_id):
    if g.user.role != 'admin':
        return redirect(url_for('permitsBp.list_permits'))

    permit = PermitModel.query.get_or_404(permit_id)
    if permit.status != 'pending':
        flash('Само чакащи заявки могат да бъдат отхвърляни.', 'error')
        return redirect(url_for('adminBp.index'))

    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Необходимо е посочване на причина при отхвърляне.', 'error')
        return redirect(url_for('adminBp.index'))

    permit.status = 'rejected'
    permit.revoke_reason = reason
    db.session.commit()

    log_entry = AdminLog(admin_id=g.user.id, action='reject_permit', target=permit.permit_number, note=reason)
    db.session.add(log_entry)
    db.session.commit()

    flash(f'Разрешително {permit.permit_number} е отхвърлено.', 'success')
    return redirect(url_for('adminBp.index'))


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
    expired = PermitModel.query.filter(PermitModel.status == 'active', PermitModel.valid_until < today).all()
    for permit in expired:
        permit.status = 'expired'
    db.session.commit()
