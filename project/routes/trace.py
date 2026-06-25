from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from models.models import db, FishLanding, FishBatch, TraceLocation, BatchMovement, FishingLogEntry, CatchEntry, VesselModel, PermitModel, InspectionAct, Fine, AdminLog
from datetime import date, datetime

traceBp = Blueprint('traceBp', __name__)


def generate_batch_number():
    count = FishBatch.query.count() + 1
    return f'IARA-BATCH-{date.today().year}-{count:06d}'


def log_admin(action, target, note=''):
    entry = AdminLog(admin_id=g.user.id, action=action, target=target, note=note)
    db.session.add(entry)


@traceBp.route('/')
def index():
    if g.user.role not in ('user', 'inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    stats = {}
    if g.user.role == 'user':
        stats['landings'] = FishLanding.query.filter_by(created_by=g.user.id).count()
        stats['batches'] = FishBatch.query.join(FishLanding).filter(FishLanding.created_by == g.user.id).count()
    elif g.user.role == 'inspector':
        stats['landings'] = FishLanding.query.count()
        stats['batches'] = FishBatch.query.count()
        stats['locations'] = TraceLocation.query.count()
    else:
        stats['landings'] = FishLanding.query.count()
        stats['batches'] = FishBatch.query.count()
        stats['locations'] = TraceLocation.query.count()

    recent_landings = FishLanding.query.order_by(FishLanding.created_at.desc()).limit(5).all()
    return render_template('trace/index.html', user=g.user, stats=stats, recent_landings=recent_landings)


@traceBp.route('/landings')
def list_landings():
    search = request.args.get('search', '').strip()
    query = FishLanding.query
    if g.user.role == 'user':
        query = query.filter_by(created_by=g.user.id)
    if search:
        query = query.join(FishingLogEntry).join(VesselModel).filter(
            db.or_(
                FishLanding.location.ilike(f'%{search}%'),
                VesselModel.cfr_number.ilike(f'%{search}%'),
                VesselModel.marking.ilike(f'%{search}%'),
            )
        )
    landings = query.order_by(FishLanding.created_at.desc()).all()
    return render_template('trace/landings/list.html', user=g.user, landings=landings, search=search)


@traceBp.route('/landings/create', methods=['GET', 'POST'])
def create_landing():
    if g.user.role not in ('user', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        log_entry_id = request.form.get('log_entry_id', type=int)
        log_entry = FishingLogEntry.query.get_or_404(log_entry_id)

        if log_entry.created_by != g.user.id and g.user.role != 'admin':
            flash('Нямате достъп до този дневник.', 'error')
            return redirect(url_for('traceBp.list_landings'))

        landing = FishLanding(
            log_entry_id=log_entry_id,
            created_by=g.user.id,
            landing_date=date.fromisoformat(request.form['landing_date']),
            location=request.form.get('location', ''),
            notes=request.form.get('notes', ''),
        )
        db.session.add(landing)
        db.session.flush()

        species_list = request.form.getlist('species[]')
        quantity_list = request.form.getlist('quantity_kg[]')

        has_batches = False
        for i in range(len(species_list)):
            species = species_list[i].strip()
            try:
                qty = float(quantity_list[i])
            except (ValueError, IndexError):
                continue
            if species and qty > 0:
                batch = FishBatch(
                    batch_number=generate_batch_number(),
                    landing_id=landing.id,
                    species=species,
                    quantity_kg=qty,
                )
                db.session.add(batch)
                has_batches = True

        if not has_batches:
            db.session.rollback()
            flash('Моля, добавете поне една партида с улов.', 'error')
            return redirect(url_for('traceBp.create_landing'))

        db.session.commit()
        flash(f'Разтоварването е регистрирано с {len(species_list)} партиди.', 'success')
        return redirect(url_for('traceBp.landing_detail', landing_id=landing.id))

    user_logs = FishingLogEntry.query.filter(
        FishingLogEntry.created_by == g.user.id,
        FishingLogEntry.status.in_(['submitted', 'confirmed'])
    ).order_by(FishingLogEntry.created_at.desc()).all()
    today = date.today().isoformat()
    return render_template('trace/landings/create.html', user=g.user, log_entries=user_logs, today=today)


@traceBp.route('/landings/<int:landing_id>')
def landing_detail(landing_id):
    landing = FishLanding.query.get_or_404(landing_id)
    if g.user.role == 'user' and landing.created_by != g.user.id:
        flash('Нямате достъп до това разтоварване.', 'error')
        return redirect(url_for('traceBp.list_landings'))

    return render_template('trace/landings/detail.html', user=g.user, landing=landing)


@traceBp.route('/landings/<int:landing_id>/add_batch', methods=['POST'])
def add_batch(landing_id):
    if g.user.role not in ('user', 'admin'):
        flash('Нямате достъп.', 'error')
        return redirect(url_for('index'))

    landing = FishLanding.query.get_or_404(landing_id)
    if g.user.role == 'user' and landing.created_by != g.user.id:
        flash('Нямате достъп.', 'error')
        return redirect(url_for('traceBp.list_landings'))

    species = request.form.get('species', '').strip()
    try:
        qty = float(request.form.get('quantity_kg', 0))
    except (ValueError, TypeError):
        qty = 0

    if not species or qty <= 0:
        flash('Моля, въведете валиден вид риба и количество.', 'error')
        return redirect(url_for('traceBp.landing_detail', landing_id=landing_id))

    batch = FishBatch(
        batch_number=generate_batch_number(),
        landing_id=landing.id,
        species=species,
        quantity_kg=qty,
        notes=request.form.get('notes', ''),
    )
    db.session.add(batch)
    db.session.commit()
    flash(f'Партида {batch.batch_number} е добавена.', 'success')
    return redirect(url_for('traceBp.landing_detail', landing_id=landing_id))


@traceBp.route('/batches/<int:batch_id>')
def batch_detail(batch_id):
    batch = FishBatch.query.get_or_404(batch_id)
    landing = batch.landing
    if g.user.role == 'user' and landing.created_by != g.user.id:
        flash('Нямате достъп до тази партида.', 'error')
        return redirect(url_for('traceBp.index'))

    return render_template('trace/batches/detail.html', user=g.user, batch=batch)


@traceBp.route('/batches/<int:batch_id>/move', methods=['POST'])
def move_batch(batch_id):
    if g.user.role not in ('user', 'admin'):
        flash('Нямате достъп.', 'error')
        return redirect(url_for('index'))

    batch = FishBatch.query.get_or_404(batch_id)
    if g.user.role == 'user' and batch.landing.created_by != g.user.id:
        flash('Нямате достъп.', 'error')
        return redirect(url_for('traceBp.index'))

    to_location_id = request.form.get('to_location_id', type=int)
    from_location_id = request.form.get('from_location_id', type=int) or None
    movement_type = request.form.get('movement_type', 'delivery')
    notes = request.form.get('notes', '')

    to_location = TraceLocation.query.get_or_404(to_location_id)
    if not to_location.is_active:
        flash('Избраната локация не е активна.', 'error')
        return redirect(url_for('traceBp.batch_detail', batch_id=batch_id))

    try:
        arrival_date = datetime.fromisoformat(request.form['arrival_date'])
    except (ValueError, KeyError):
        arrival_date = datetime.now()

    departure_date = None
    if request.form.get('departure_date'):
        try:
            departure_date = datetime.fromisoformat(request.form['departure_date'])
        except ValueError:
            pass

    movement = BatchMovement(
        batch_id=batch.id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        movement_type=movement_type,
        departure_date=departure_date,
        arrival_date=arrival_date,
        notes=notes,
        created_by=g.user.id,
    )
    db.session.add(movement)
    db.session.commit()
    flash(f'Партида {batch.batch_number} е преместена до {to_location.name}.', 'success')
    return redirect(url_for('traceBp.batch_detail', batch_id=batch_id))


@traceBp.route('/locations')
def list_locations():
    search = request.args.get('search', '').strip()
    location_type = request.args.get('type', None)
    query = TraceLocation.query
    if location_type and location_type in ('shop', 'warehouse', 'truck'):
        query = query.filter_by(location_type=location_type)
    if search:
        query = query.filter(
            db.or_(
                TraceLocation.name.ilike(f'%{search}%'),
                TraceLocation.address.ilike(f'%{search}%'),
                TraceLocation.license_number.ilike(f'%{search}%'),
            )
        )
    locations = query.order_by(TraceLocation.created_at.desc()).all()
    import json
    from flask import url_for
    locations_json = json.dumps([{
        'id': loc.id,
        'name': loc.name,
        'address': loc.address or '',
        'type': loc.location_type,
        'url': url_for('traceBp.location_detail', location_id=loc.id, _external=False),
    } for loc in locations])
    return render_template('trace/locations/list.html', user=g.user, locations=locations, search=search, location_type=location_type, locations_json=locations_json)


@traceBp.route('/locations/create', methods=['GET', 'POST'])
def create_location():
    if g.user.role not in ('user', 'inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        location = TraceLocation(
            location_type=request.form['location_type'],
            name=request.form['name'],
            address=request.form.get('address', ''),
            owner_name=request.form.get('owner_name', ''),
            license_number=request.form.get('license_number', ''),
            contact_phone=request.form.get('contact_phone', ''),
            created_by=g.user.id,
        )
        db.session.add(location)
        db.session.commit()
        type_names = {'shop': 'Магазин', 'warehouse': 'Склад', 'truck': 'Хладилен камион'}
        flash(f'{type_names.get(location.location_type, location.location_type)} "{location.name}" е регистриран.', 'success')
        return redirect(url_for('traceBp.location_detail', location_id=location.id))

    return render_template('trace/locations/create.html', user=g.user)


@traceBp.route('/locations/<int:location_id>')
def location_detail(location_id):
    location = TraceLocation.query.get_or_404(location_id)
    incoming = BatchMovement.query.filter_by(to_location_id=location_id).order_by(BatchMovement.arrival_date.desc()).all()
    outgoing = BatchMovement.query.filter_by(from_location_id=location_id).order_by(BatchMovement.created_at.desc()).all()
    return render_template('trace/locations/detail.html', user=g.user, location=location, incoming=incoming, outgoing=outgoing)


@traceBp.route('/locations/<int:location_id>/toggle', methods=['POST'])
def toggle_location(location_id):
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп.', 'error')
        return redirect(url_for('index'))

    location = TraceLocation.query.get_or_404(location_id)
    location.is_active = not location.is_active
    db.session.commit()
    state = 'активен' if location.is_active else 'неактивен'
    flash(f'{location.name} е {state}.', 'success')
    return redirect(url_for('traceBp.location_detail', location_id=location_id))


@traceBp.route('/search')
def search():
    if g.user.role not in ('user', 'inspector', 'admin'):
        flash('Нямате достъп.', 'error')
        return redirect(url_for('index'))

    q = request.args.get('q', '').strip()
    batches = []
    if q:
        batches = FishBatch.query.filter(FishBatch.batch_number.ilike(f'%{q}%')).all()
        if not batches:
            batches = FishBatch.query.join(FishLanding).filter(
                FishBatch.species.ilike(f'%{q}%')
            ).all()

    return render_template('trace/search.html', user=g.user, query=q, batches=batches)


@traceBp.route('/api/locations')
def locations_json():
    if g.user.role not in ('user', 'inspector', 'admin'):
        return jsonify([])
    locs = TraceLocation.query.filter_by(is_active=True).order_by(TraceLocation.name).all()
    return jsonify([{
        'id': l.id,
        'name': l.name,
        'type': {'shop': 'Магазин', 'warehouse': 'Склад', 'truck': 'Хладилен камион'}.get(l.location_type, l.location_type),
        'address': l.address or '',
    } for l in locs])


@traceBp.route('/api/logs/<int:log_id>/catches')
def log_catches_json(log_id):
    if g.user.role not in ('user', 'inspector', 'admin'):
        return jsonify([])
    catches = CatchEntry.query.filter_by(log_entry_id=log_id).all()
    return jsonify([{
        'species': c.species,
        'quantity_kg': c.quantity_kg,
        'quantity_pcs': c.quantity_pcs or 0,
    } for c in catches])
