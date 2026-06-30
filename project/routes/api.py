from flask import Blueprint, jsonify, request, session, g
from models.models import db, UserModel, VesselModel, PermitModel, InspectionAct, Fine, FishBatch, BatchMovement, TraceLocation, FishingTicket, FishingLogEntry, CatchEntry, FishLanding
from datetime import date, datetime, timedelta

apiBp = Blueprint('apiBp', __name__)


def require_auth():
    user = UserModel.query.get(session.get('user_id'))
    if not user:
        return None
    g.user = user
    return user


def require_inspector():
    user = require_auth()
    if not user:
        return None
    if user.role not in ('inspector', 'admin'):
        return None
    return user


@apiBp.route('/me')
def me():
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'identifier': user.identifier,
        'phone': user.phone,
    })


@apiBp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    password2 = data.get('password2', '')
    full_name = data.get('full_name', '').strip()
    identifier = data.get('identifier', '').strip()
    phone = data.get('phone', '').strip()

    if not all([email, password, password2, full_name, identifier]):
        return jsonify({'error': 'Попълнете всички задължителни полета'}), 400
    if password != password2:
        return jsonify({'error': 'Паролите не съвпадат'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Паролата трябва да е поне 6 символа'}), 400
    if UserModel.query.filter_by(email=email).first():
        return jsonify({'error': 'Акаунт с този имейл вече съществува'}), 400
    if UserModel.query.filter_by(identifier=identifier).first():
        return jsonify({'error': 'Акаунт с това ЕГН/ЕИК вече съществува'}), 400

    from validators import validate_identifier, validate_phone, validate_password_strength
    valid, msg = validate_password_strength(password)
    if not valid:
        return jsonify({'error': msg}), 400
    valid, msg = validate_identifier(identifier)
    if not valid:
        return jsonify({'error': msg}), 400
    valid, msg = validate_phone(phone)
    if not valid:
        return jsonify({'error': msg}), 400

    try:
        user = UserModel(email=email, full_name=full_name, identifier=identifier, phone=phone or None)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({'ok': True, 'user': {
            'id': user.id, 'email': user.email, 'full_name': user.full_name,
            'role': user.role, 'identifier': user.identifier, 'phone': user.phone,
        }}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@apiBp.route('/vessels')
def vessel_list():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    query = VesselModel.query
    if search:
        query = query.filter(
            db.or_(
                VesselModel.cfr_number.ilike(f'%{search}%'),
                VesselModel.marking.ilike(f'%{search}%'),
                VesselModel.call_sign.ilike(f'%{search}%'),
            )
        )
    if status:
        query = query.filter_by(status=status)

    vessels = query.order_by(VesselModel.created_at.desc()).all()
    return jsonify([{
        'id': v.id,
        'cfr_number': v.cfr_number,
        'marking': v.marking,
        'call_sign': v.call_sign,
        'status': v.status,
        'length': v.length,
        'width': v.width,
        'gross_tonnage': v.gross_tonnage,
        'engine_power': v.engine_power,
        'owner_name': v.owner.full_name if v.owner else None,
    } for v in vessels])


@apiBp.route('/vessels/<int:vessel_id>/permits')
def vessel_permits(vessel_id):
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    permits = PermitModel.query.filter_by(vessel_id=vessel_id, status='active').all()
    return jsonify([{
        'id': p.id,
        'permit_number': p.permit_number,
        'status': p.status,
        'valid_until': p.valid_until.isoformat() if p.valid_until else None,
        'holder': p.holder.full_name if p.holder else None,
    } for p in permits])


@apiBp.route('/vessels/<int:vessel_id>')
def vessel_detail(vessel_id):
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    vessel = VesselModel.query.get_or_404(vessel_id)
    permits = PermitModel.query.filter_by(vessel_id=vessel_id).order_by(PermitModel.created_at.desc()).all()
    acts = InspectionAct.query.filter_by(vessel_id=vessel_id).order_by(InspectionAct.created_at.desc()).limit(10).all()

    return jsonify({
        'id': vessel.id,
        'cfr_number': vessel.cfr_number,
        'call_sign': vessel.call_sign,
        'marking': vessel.marking,
        'captain_name': vessel.captain_name,
        'captain_license': vessel.captain_license,
        'length': vessel.length,
        'width': vessel.width,
        'draft': vessel.draft,
        'gross_tonnage': vessel.gross_tonnage,
        'engine_power': vessel.engine_power,
        'fuel_type': vessel.fuel_type,
        'status': vessel.status,
        'created_at': vessel.created_at.isoformat() if vessel.created_at else None,
        'owner': {'id': vessel.owner.id, 'full_name': vessel.owner.full_name} if vessel.owner else None,
        'permits': [{
            'id': p.id,
            'permit_number': p.permit_number,
            'status': p.status,
            'valid_until': p.valid_until.isoformat() if p.valid_until else None,
            'holder': p.holder.full_name if p.holder else None,
        } for p in permits],
        'acts': [{
            'id': a.id,
            'act_number': a.act_number,
            'status': a.status,
            'inspection_date': a.inspection_date.isoformat() if a.inspection_date else None,
            'location': a.location,
        } for a in acts],
    })


@apiBp.route('/acts')
def act_list():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    status_filter = request.args.get('status', '')
    query = InspectionAct.query.filter_by(inspector_id=user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    acts = query.order_by(InspectionAct.created_at.desc()).all()
    return jsonify([{
        'id': a.id,
        'act_number': a.act_number,
        'inspection_date': a.inspection_date.isoformat() if a.inspection_date else None,
        'location': a.location,
        'status': a.status,
        'findings': a.findings,
        'violations': a.violations,
        'vessel_id': a.vessel_id,
        'vessel_marking': a.vessel.marking if a.vessel else None,
        'vessel_cfr': a.vessel.cfr_number if a.vessel else None,
        'created_at': a.created_at.isoformat() if a.created_at else None,
    } for a in acts])


@apiBp.route('/acts', methods=['POST'])
def act_create():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True) or request.form
    vessel_id = data.get('vessel_id')
    if not vessel_id:
        return jsonify({'error': 'vessel_id is required'}), 400
    vessel_id = int(vessel_id)

    vessel = VesselModel.query.get(vessel_id)
    if not vessel:
        return jsonify({'error': 'vessel not found'}), 404

    permit_id = data.get('permit_id')
    if permit_id:
        permit_id = int(permit_id)
        permit = PermitModel.query.get(permit_id)
        if not permit:
            return jsonify({'error': 'permit not found'}), 404
        if permit.vessel_id != vessel_id:
            return jsonify({'error': 'permit does not belong to this vessel'}), 400

    from datetime import date, datetime
    count = InspectionAct.query.count() + 1
    act_number = f'IARA-ACT-{date.today().year}-{count:06d}'

    raw_date = data.get('inspection_date')
    if raw_date:
        inspection_date = date.fromisoformat(raw_date)
    else:
        inspection_date = date.today()

    act = InspectionAct(
        act_number=act_number,
        inspector_id=user.id,
        vessel_id=vessel_id,
        related_permit_id=permit_id,
        inspection_date=inspection_date,
        location=data.get('location', ''),
        findings=data.get('findings', ''),
        violations=data.get('violations', ''),
        status='confirmed',
    )
    db.session.add(act)
    db.session.flush()

    fine_amount = float(data['fine_amount']) if data.get('fine_amount') else None
    if fine_amount and fine_amount > 0:
        fine_count = Fine.query.count() + 1
        fine_number = f'IARA-FINE-{date.today().year}-{fine_count:06d}'
        fine = Fine(
            fine_number=fine_number,
            act_id=act.id,
            inspector_id=user.id,
            vessel_id=vessel_id,
            amount=fine_amount,
            violation_description=data.get('violation_description', data.get('violations', '')),
            legal_basis=data.get('legal_basis', ''),
            status='approved',
        )
        db.session.add(fine)

    db.session.commit()
    return jsonify({'id': act.id, 'act_number': act.act_number}), 201


@apiBp.route('/acts/<int:act_id>')
def act_detail(act_id):
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    act = InspectionAct.query.get_or_404(act_id)
    if act.inspector_id != user.id and user.role != 'admin':
        return jsonify({'error': 'forbidden'}), 403

    return jsonify({
        'id': act.id,
        'act_number': act.act_number,
        'inspection_date': act.inspection_date.isoformat() if act.inspection_date else None,
        'location': act.location,
        'status': act.status,
        'findings': act.findings,
        'violations': act.violations,
        'created_at': act.created_at.isoformat() if act.created_at else None,
        'vessel': {
            'id': act.vessel.id,
            'cfr_number': act.vessel.cfr_number,
            'marking': act.vessel.marking,
        } if act.vessel else None,
        'related_permit': {
            'id': act.related_permit.id,
            'permit_number': act.related_permit.permit_number,
            'status': act.related_permit.status,
        } if act.related_permit else None,
        'fines': [{
            'id': f.id,
            'fine_number': f.fine_number,
            'amount': f.amount,
            'status': f.status,
        } for f in act.fines],
    })


@apiBp.route('/fines')
def fine_list():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    status_filter = request.args.get('status', '')
    query = Fine.query.filter_by(inspector_id=user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    fines = query.order_by(Fine.created_at.desc()).all()
    return jsonify([{
        'id': f.id,
        'fine_number': f.fine_number,
        'amount': f.amount,
        'status': f.status,
        'violation_description': f.violation_description,
        'legal_basis': f.legal_basis,
        'vessel_marking': f.vessel.marking if f.vessel else None,
        'vessel_cfr': f.vessel.cfr_number if f.vessel else None,
        'created_at': f.created_at.isoformat() if f.created_at else None,
        'act_id': f.act_id,
    } for f in fines])


@apiBp.route('/fines', methods=['POST'])
def fine_create():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True) or request.form
    vessel_id = data.get('vessel_id')
    if vessel_id:
        vessel_id = int(vessel_id)
    amount = data.get('amount')
    if amount:
        amount = float(amount)
    if not vessel_id:
        return jsonify({'error': 'vessel_id is required'}), 400
    if not amount or amount <= 0:
        return jsonify({'error': 'invalid amount'}), 400

    vessel = VesselModel.query.get(vessel_id)
    if not vessel:
        return jsonify({'error': 'vessel not found'}), 404

    permit_id = data.get('permit_id')
    if permit_id:
        permit_id = int(permit_id)
        permit = PermitModel.query.get(permit_id)
        if not permit:
            return jsonify({'error': 'permit not found'}), 404
        if permit.vessel_id != vessel_id:
            return jsonify({'error': 'permit does not belong to this vessel'}), 400

    from datetime import date, datetime
    act_count = InspectionAct.query.count() + 1
    act_number = f'IARA-ACT-{date.today().year}-{act_count:06d}'

    raw_date = data.get('inspection_date')
    if raw_date:
        inspection_date = date.fromisoformat(raw_date)
    else:
        inspection_date = date.today()

    act = InspectionAct(
        act_number=act_number,
        inspector_id=user.id,
        vessel_id=vessel_id,
        related_permit_id=permit_id,
        inspection_date=inspection_date,
        location=data.get('location', ''),
        findings='Автоматично създаден акт за глоба',
        violations=data.get('violation_description', ''),
        status='confirmed',
    )
    db.session.add(act)
    db.session.flush()

    fine_count = Fine.query.count() + 1
    fine_number = f'IARA-FINE-{date.today().year}-{fine_count:06d}'
    fine = Fine(
        fine_number=fine_number,
        act_id=act.id,
        inspector_id=user.id,
        vessel_id=vessel_id,
        amount=amount,
        violation_description=data.get('violation_description', ''),
        legal_basis=data.get('legal_basis', ''),
        status='approved',
    )
    db.session.add(fine)
    db.session.commit()

    return jsonify({'id': fine.id, 'fine_number': fine.fine_number}), 201


@apiBp.route('/fines/<int:fine_id>')
def fine_detail(fine_id):
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    fine = Fine.query.get_or_404(fine_id)
    return jsonify({
        'id': fine.id,
        'fine_number': fine.fine_number,
        'amount': fine.amount,
        'status': fine.status,
        'violation_description': fine.violation_description,
        'legal_basis': fine.legal_basis,
        'created_at': fine.created_at.isoformat() if fine.created_at else None,
        'vessel': {
            'id': fine.vessel.id,
            'cfr_number': fine.vessel.cfr_number,
            'marking': fine.vessel.marking,
        } if fine.vessel else None,
        'act': {
            'id': fine.act.id,
            'act_number': fine.act.act_number,
        } if fine.act else None,
    })


@apiBp.route('/trace/batches/search')
def batch_search():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify([])

    batches = FishBatch.query.filter(
        db.or_(
            FishBatch.batch_number.ilike(f'%{query_text}%'),
            FishBatch.species.ilike(f'%{query_text}%'),
        )
    ).order_by(FishBatch.created_at.desc()).limit(30).all()

    return jsonify([{
        'id': b.id,
        'batch_number': b.batch_number,
        'species': b.species,
        'quantity_kg': b.quantity_kg,
        'created_at': b.created_at.isoformat() if b.created_at else None,
        'landing_date': b.landing.landing_date.isoformat() if b.landing and b.landing.landing_date else None,
    } for b in batches])


@apiBp.route('/trace/batches/<int:batch_id>')
def batch_detail(batch_id):
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    batch = FishBatch.query.get_or_404(batch_id)
    vessel = None
    if batch.landing and batch.landing.log_entry and batch.landing.log_entry.vessel:
        v = batch.landing.log_entry.vessel
        vessel = {'id': v.id, 'cfr_number': v.cfr_number, 'marking': v.marking}
    return jsonify({
        'id': batch.id,
        'batch_number': batch.batch_number,
        'species': batch.species,
        'quantity_kg': batch.quantity_kg,
        'notes': batch.notes,
        'created_at': batch.created_at.isoformat() if batch.created_at else None,
        'vessel': vessel,
        'landing': {
            'id': batch.landing.id,
            'landing_date': batch.landing.landing_date.isoformat() if batch.landing.landing_date else None,
            'location': batch.landing.location,
        } if batch.landing else None,
        'movements': [{
            'id': m.id,
            'movement_type': m.movement_type,
            'departure_date': m.departure_date.isoformat() if m.departure_date else None,
            'arrival_date': m.arrival_date.isoformat() if m.arrival_date else None,
            'from_location': m.from_location.name if m.from_location else None,
            'to_location': m.to_location.name if m.to_location else None,
            'notes': m.notes,
        } for m in batch.movements],
    })


@apiBp.route('/trace/locations')
def location_list():
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    location_type = request.args.get('type')
    query = TraceLocation.query.filter_by(is_active=True)
    if location_type and location_type in ('shop', 'warehouse', 'truck'):
        query = query.filter_by(location_type=location_type)
    locations = query.order_by(TraceLocation.name).all()
    return jsonify([{
        'id': l.id,
        'name': l.name,
        'type': l.location_type,
        'address': l.address or '',
        'owner_name': l.owner_name or '',
        'is_active': l.is_active,
    } for l in locations])


@apiBp.route('/trace/locations/<int:location_id>')
def location_detail(location_id):
    user = require_inspector()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    location = TraceLocation.query.get_or_404(location_id)
    incoming = BatchMovement.query.filter_by(to_location_id=location_id).order_by(BatchMovement.arrival_date.desc()).all()
    outgoing = BatchMovement.query.filter_by(from_location_id=location_id).order_by(BatchMovement.created_at.desc()).all()

    type_names = {'shop': 'Магазин', 'warehouse': 'Склад', 'truck': 'Хладилен камион'}
    return jsonify({
        'id': location.id,
        'name': location.name,
        'type': location.location_type,
        'type_label': type_names.get(location.location_type, location.location_type),
        'address': location.address or '',
        'owner_name': location.owner_name or '',
        'license_number': location.license_number or '',
        'contact_phone': location.contact_phone or '',
        'is_active': location.is_active,
        'incoming': [{
            'id': m.id,
            'batch_id': m.batch_id,
            'batch_number': m.batch.batch_number,
            'species': m.batch.species,
            'quantity_kg': m.batch.quantity_kg,
            'movement_type': m.movement_type,
            'from_location': m.from_location.name if m.from_location else None,
            'arrival_date': m.arrival_date.isoformat() if m.arrival_date else None,
            'notes': m.notes or '',
        } for m in incoming],
        'outgoing': [{
            'id': m.id,
            'batch_id': m.batch_id,
            'batch_number': m.batch.batch_number,
            'species': m.batch.species,
            'quantity_kg': m.batch.quantity_kg,
            'movement_type': m.movement_type,
            'to_location': m.to_location.name if m.to_location else None,
            'departure_date': m.departure_date.isoformat() if m.departure_date else None,
            'notes': m.notes or '',
        } for m in outgoing],
    })


@apiBp.route('/tickets')
def ticket_list():
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    tickets = FishingTicket.query.filter_by(user_id=user.id).order_by(FishingTicket.created_at.desc()).all()
    return jsonify([{
        'id': t.id,
        'receipt_number': t.receipt_number,
        'ticket_type': t.ticket_type,
        'period': t.period,
        'price': t.price,
        'status': t.status,
        'valid_from': t.valid_from.isoformat() if t.valid_from else None,
        'valid_until': t.valid_until.isoformat() if t.valid_until else None,
        'created_at': t.created_at.isoformat() if t.created_at else None,
    } for t in tickets])


@apiBp.route('/tickets/buy', methods=['POST'])
def ticket_buy():
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    ticket_type = request.json.get('ticket_type')
    period = request.json.get('period')
    telk_number = request.json.get('telk_number', '').strip()

    valid_periods = {'1 седмица': 7, '1 месец': 30, '6 месеца': 180, '1 година': 365}
    prices = {
        'standard': {'1 седмица': 6.14, '1 месец': 8.18, '6 месеца': 15.34, '1 година': 25.56},
        'reduced': {'1 седмица': 3.07, '1 месец': 4.09, '6 месеца': 7.67, '1 година': 12.78},
        'disabled': {'1 седмица': 0, '1 месец': 0, '6 месеца': 0, '1 година': 0},
    }

    if ticket_type not in ('standard', 'reduced', 'disabled'):
        return jsonify({'error': 'invalid ticket_type'}), 400
    if period not in valid_periods:
        return jsonify({'error': 'invalid period'}), 400
    if ticket_type == 'disabled' and not telk_number:
        return jsonify({'error': 'telk_number required for disabled tickets'}), 400

    price = prices[ticket_type][period]
    today = date.today()
    valid_until = today + timedelta(days=valid_periods[period])

    last_ticket = FishingTicket.query.order_by(FishingTicket.id.desc()).first()
    next_num = (last_ticket.id + 1) if last_ticket else 1
    receipt_number = f'TKT-{today.strftime("%Y%m%d")}-{next_num:04d}'

    is_disabled = ticket_type == 'disabled'
    ticket = FishingTicket(
        user_id=user.id,
        ticket_type=ticket_type,
        period=period,
        price=price,
        receipt_number=receipt_number,
        telk_number=telk_number if telk_number else None,
        valid_from=today if not is_disabled else None,
        valid_until=valid_until if not is_disabled else None,
        status='pending' if is_disabled else 'active',
        paid_at=db.func.now() if not is_disabled else None,
    )
    db.session.add(ticket)
    db.session.commit()

    return jsonify({
        'id': ticket.id,
        'receipt_number': receipt_number,
        'status': ticket.status,
        'price': price,
    }), 201


@apiBp.route('/tickets/<int:ticket_id>')
def ticket_detail(ticket_id):
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    ticket = FishingTicket.query.get_or_404(ticket_id)
    if ticket.user_id != user.id:
        return jsonify({'error': 'forbidden'}), 403
    type_labels = {'standard': 'Стандартен', 'reduced': 'Намален', 'disabled': 'Инвалиден'}
    status_labels = {'active': 'Активен', 'expired': 'Изтекъл', 'cancelled': 'Анулиран', 'pending': 'Чака одобрение'}
    return jsonify({
        'id': ticket.id,
        'receipt_number': ticket.receipt_number,
        'ticket_type': ticket.ticket_type,
        'ticket_type_label': type_labels.get(ticket.ticket_type, ticket.ticket_type),
        'period': ticket.period,
        'price': ticket.price,
        'status': ticket.status,
        'status_label': status_labels.get(ticket.status, ticket.status),
        'telk_number': ticket.telk_number or '',
        'valid_from': ticket.valid_from.isoformat() if ticket.valid_from else None,
        'valid_until': ticket.valid_until.isoformat() if ticket.valid_until else None,
        'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
        'paid_at': ticket.paid_at.isoformat() if ticket.paid_at else None,
    })


@apiBp.route('/tickets/<int:ticket_id>/cancel', methods=['POST'])
def ticket_cancel(ticket_id):
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    ticket = FishingTicket.query.get_or_404(ticket_id)
    if ticket.user_id != user.id:
        return jsonify({'error': 'forbidden'}), 403
    if ticket.status not in ('active', 'pending'):
        return jsonify({'error': 'ticket cannot be cancelled'}), 400
    ticket.status = 'cancelled'
    db.session.commit()
    return jsonify({'status': 'cancelled'})


@apiBp.route('/logbook')
def logbook_list():
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    query = FishingLogEntry.query
    if user.role == 'user':
        query = query.filter_by(created_by=user.id)
    query = query.order_by(FishingLogEntry.created_at.desc()).all()

    return jsonify([{
        'id': e.id,
        'start_datetime': e.start_datetime.isoformat() if e.start_datetime else None,
        'end_datetime': e.end_datetime.isoformat() if e.end_datetime else None,
        'start_location': e.start_location or '',
        'end_location': e.end_location or '',
        'gear_used': e.gear_used or '',
        'status': e.status,
        'vessel': {
            'id': e.vessel.id,
            'cfr_number': e.vessel.cfr_number,
            'marking': e.vessel.marking,
        } if e.vessel else None,
        'catches': [{
            'species': c.species,
            'quantity_kg': c.quantity_kg,
            'quantity_pcs': c.quantity_pcs or 0,
            'notes': c.notes or '',
        } for c in e.catches],
        'created_at': e.created_at.isoformat() if e.created_at else None,
    } for e in query])


@apiBp.route('/logbook', methods=['POST'])
def logbook_create():
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'invalid JSON'}), 400

    vessel_id = data.get('vessel_id')
    if vessel_id:
        vessel = VesselModel.query.get(int(vessel_id))
        if not vessel:
            return jsonify({'error': 'vessel not found'}), 404

    start_dt = None
    if data.get('start_datetime'):
        try:
            start_dt = datetime.fromisoformat(data['start_datetime'])
        except ValueError:
            start_dt = datetime.strptime(data['start_datetime'], '%Y-%m-%d %H:%M')

    end_dt = None
    if data.get('end_datetime'):
        try:
            end_dt = datetime.fromisoformat(data['end_datetime'])
        except ValueError:
            end_dt = datetime.strptime(data['end_datetime'], '%Y-%m-%d %H:%M')

    entry = FishingLogEntry(
        vessel_id=int(vessel_id) if vessel_id else None,
        created_by=user.id,
        start_datetime=start_dt or datetime.now(),
        end_datetime=end_dt,
        start_location=data.get('start_location', ''),
        end_location=data.get('end_location', ''),
        gear_used=data.get('gear_used', ''),
        notes=data.get('notes', ''),
        status=data.get('status', 'submitted'),
    )
    db.session.add(entry)
    db.session.flush()

    for c in data.get('catches', []):
        if c.get('species') and c.get('quantity_kg'):
            catch = CatchEntry(
                log_entry_id=entry.id,
                species=c['species'],
                quantity_kg=float(c['quantity_kg']),
                quantity_pcs=int(c['quantity_pcs']) if c.get('quantity_pcs') else None,
                notes=c.get('notes', ''),
            )
            db.session.add(catch)

    db.session.commit()
    return jsonify({'id': entry.id}), 201


@apiBp.route('/logbook/<int:log_id>')
def logbook_detail(log_id):
    user = require_auth()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401
    entry = FishingLogEntry.query.get_or_404(log_id)
    if user.role == 'user' and entry.created_by != user.id:
        return jsonify({'error': 'forbidden'}), 403

    return jsonify({
        'id': entry.id,
        'start_datetime': entry.start_datetime.isoformat() if entry.start_datetime else None,
        'end_datetime': entry.end_datetime.isoformat() if entry.end_datetime else None,
        'start_location': entry.start_location or '',
        'end_location': entry.end_location or '',
        'gear_used': entry.gear_used or '',
        'notes': entry.notes or '',
        'status': entry.status,
        'vessel': {
            'id': entry.vessel.id,
            'cfr_number': entry.vessel.cfr_number,
            'marking': entry.vessel.marking,
        } if entry.vessel else None,
        'catches': [{
            'id': c.id,
            'species': c.species,
            'quantity_kg': c.quantity_kg,
            'quantity_pcs': c.quantity_pcs or 0,
            'notes': c.notes or '',
        } for c in entry.catches],
        'created_at': entry.created_at.isoformat() if entry.created_at else None,
    })
