from flask import Blueprint, jsonify, request, session, g
from models.models import db, UserModel, VesselModel, PermitModel, InspectionAct, Fine, FishBatch, BatchMovement, TraceLocation

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
    return jsonify({
        'id': batch.id,
        'batch_number': batch.batch_number,
        'species': batch.species,
        'quantity_kg': batch.quantity_kg,
        'notes': batch.notes,
        'created_at': batch.created_at.isoformat() if batch.created_at else None,
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
