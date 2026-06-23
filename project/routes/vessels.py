from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, VesselModel, Fine, PermitModel
from validators import validate_cfr

vesselsApp = Blueprint('vessels', __name__)


@vesselsApp.route('/')
def list_vessels():
    search = request.args.get('search', '').strip()
    query = VesselModel.query.filter_by(owner_id=g.user.id)
    if search:
        query = query.filter(
            db.or_(
                VesselModel.cfr_number.ilike(f'%{search}%'),
                VesselModel.marking.ilike(f'%{search}%'),
                VesselModel.call_sign.ilike(f'%{search}%'),
            )
        )
    vessels = query.all()
    return render_template('vessels/list.html', user=g.user, vessels=vessels, search=search)


@vesselsApp.route('/add', methods=['GET', 'POST'])
def add_vessel():
    if request.method == 'POST':
        cfr_number = request.form['cfr_number'].strip().upper()

        valid, msg = validate_cfr(cfr_number)
        if not valid:
            flash(msg)
            return redirect(url_for('vessels.add_vessel'))

        if VesselModel.query.filter_by(cfr_number=cfr_number).first():
            flash('Кораб със същия CFR номер вече съществува!')
            return redirect(url_for('vessels.add_vessel'))

        call_sign = request.form.get('call_sign', '').strip().upper() or None
        if call_sign and VesselModel.query.filter_by(call_sign=call_sign).first():
            flash('Кораб със същия позивен вече съществува!')
            return redirect(url_for('vessels.add_vessel'))

        vessel = VesselModel(
            owner_id = g.user.id,
            cfr_number = cfr_number,
            call_sign = call_sign,
            marking = request.form['marking'],
            captain_name = request.form.get('captain_name'),
            captain_license = request.form.get('captain_license'),
            length = request.form['length'],
            width = request.form.get('width') or None,
            draft = request.form.get('draft') or None,
            gross_tonnage = request.form.get('gross_tonnage') or None,
            engine_power = request.form.get('engine_power') or None,
            fuel_type = request.form.get('fuel_type') or None,
            status = 'pending',
        )
        db.session.add(vessel)
        db.session.commit()

        flash('Корабът е регистриран успешно. Изчаква одобрение от администратор.', 'success')
        return redirect(url_for('vessels.list_vessels'))

    return render_template('vessels/add.html', user=g.user)


@vesselsApp.route('/<int:vessel_id>/edit', methods=['GET', 'POST'])
def edit_vessel(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)

    if vessel.owner_id != g.user.id:
        flash('Нямате достъп до този кораб.')
        return redirect(url_for('vessels.list_vessels'))

    if vessel.status not in ('pending', 'approved', 'suspended'):
        flash('Този кораб не може да бъде редактиран.')
        return redirect(url_for('vessels.vessel_detail', vessel_id=vessel_id))

    if request.method == 'POST':
        was_approved = vessel.status in ('approved', 'suspended')
        vessel.marking = request.form['marking']
        vessel.captain_name = request.form.get('captain_name')
        vessel.captain_license = request.form.get('captain_license')
        vessel.length = request.form['length']
        vessel.width = request.form.get('width') or None
        vessel.draft = request.form.get('draft') or None
        vessel.gross_tonnage = request.form.get('gross_tonnage') or None
        vessel.engine_power = request.form.get('engine_power') or None
        vessel.fuel_type = request.form.get('fuel_type') or None

        if was_approved:
            vessel.status = 'pending'
            vessel.admin_note = None

        db.session.commit()

        if was_approved:
            flash('Корабът е редактиран. Промените изискват ново одобрение от администратор.', 'success')
        else:
            flash('Корабът е редактиран успешно.', 'success')

        return redirect(url_for('vessels.vessel_detail', vessel_id=vessel_id))

    return render_template('vessels/edit.html', user=g.user, vessel=vessel)


@vesselsApp.route('/<int:vessel_id>')
def vessel_detail(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)

    if vessel.owner_id != g.user.id:
        flash('Нямате достъп до този кораб.')
        return redirect(url_for('vessels.list_vessels'))

    fines = Fine.query.filter_by(vessel_id=vessel_id).order_by(Fine.created_at.desc()).all()
    permits = PermitModel.query.filter_by(vessel_id=vessel_id).order_by(PermitModel.created_at.desc()).all()
    return render_template('vessels/detail.html', user=g.user, vessel=vessel, fines=fines, permits=permits)


@vesselsApp.route('/<int:vessel_id>/suspend', methods=['POST'])
def suspend_vessel(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)

    if vessel.owner_id != g.user.id:
        flash('Нямате достъп до този кораб.')
        return redirect(url_for('vessels.list_vessels'))

    if vessel.status != 'approved':
        flash('Само одобрени кораби могат да бъдат спрени.')
        return redirect(url_for('vessels.vessel_detail', vessel_id=vessel_id))

    vessel.status = 'suspended'
    db.session.commit()
    flash('Корабът е спрян.')
    return redirect(url_for('vessels.vessel_detail', vessel_id=vessel_id))


@vesselsApp.route('/<int:vessel_id>/reactivate', methods=['POST'])
def reactivate_vessel(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)

    if vessel.owner_id != g.user.id:
        flash('Нямате достъп до този кораб.')
        return redirect(url_for('vessels.list_vessels'))

    if vessel.status != 'suspended':
        flash('Само спрени кораби могат да бъдат реактивирани.')
        return redirect(url_for('vessels.vessel_detail', vessel_id=vessel_id))

    vessel.status = 'approved'
    db.session.commit()
    flash('Корабът е реактивиран.')
    return redirect(url_for('vessels.vessel_detail', vessel_id=vessel_id))
