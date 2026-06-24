from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from models.models import db, FishingLogEntry, CatchEntry, VesselModel, PermitModel
from datetime import datetime

logbookApp = Blueprint('logbookBp', __name__)


@logbookApp.route('/')
def list_entries():
    if g.user.role not in ('user', 'inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    status_filter = request.args.get('status', None)
    search = request.args.get('search', '').strip()

    if g.user.role == 'user':
        query = FishingLogEntry.query.filter_by(created_by=g.user.id)
    elif g.user.role in ('inspector', 'admin'):
        query = FishingLogEntry.query

    if status_filter and status_filter in ('draft', 'submitted', 'confirmed'):
        query = query.filter(FishingLogEntry.status == status_filter)
    if search:
        query = query.join(VesselModel).filter(
            db.or_(
                VesselModel.cfr_number.ilike(f'%{search}%'),
                VesselModel.marking.ilike(f'%{search}%'),
            )
        )
    entries = query.order_by(FishingLogEntry.created_at.desc()).all()
    return render_template('logbook/list.html', user=g.user, entries=entries, current_filter=status_filter, search=search)


@logbookApp.route('/create', methods=['GET', 'POST'])
def create_entry():
    if g.user.role != 'user':
        flash('Само потребители могат да създават дневници.', 'error')
        return redirect(url_for('logbookBp.list_entries'))

    if request.method == 'POST':
        vessel_id = request.form.get('vessel_id', type=int)
        vessel = VesselModel.query.get_or_404(vessel_id)

        if vessel.owner_id != g.user.id:
            flash('Можете да създадете дневник само за ваш кораб.', 'error')
            return redirect(url_for('logbookBp.create_entry'))

        permit_id = request.form.get('permit_id', type=int) or None

        start_dt_str = request.form['start_datetime']
        end_dt_str = request.form.get('end_datetime')
        try:
            start_datetime = datetime.fromisoformat(start_dt_str)
            end_datetime = datetime.fromisoformat(end_dt_str) if end_dt_str else None
        except ValueError:
            flash('Невалиден формат на дата/час.', 'error')
            return redirect(url_for('logbookBp.create_entry'))

        entry = FishingLogEntry(
            vessel_id=vessel_id,
            permit_id=permit_id,
            created_by=g.user.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            start_location=request.form.get('start_location', ''),
            end_location=request.form.get('end_location', ''),
            gear_used=request.form.get('gear_used', ''),
            notes=request.form.get('notes', ''),
            status='submitted',
        )
        db.session.add(entry)
        db.session.flush()

        species_list = request.form.getlist('species[]')
        kg_list = request.form.getlist('quantity_kg[]')
        pcs_list = request.form.getlist('quantity_pcs[]')

        for i, species in enumerate(species_list):
            if species.strip():
                kg = kg_list[i] if i < len(kg_list) else 0
                pcs = pcs_list[i] if i < len(pcs_list) else None
                catch = CatchEntry(
                    log_entry_id=entry.id,
                    species=species.strip(),
                    quantity_kg=float(kg) if kg else 0,
                    quantity_pcs=int(pcs) if pcs and pcs.strip() else None,
                )
                db.session.add(catch)

        db.session.commit()
        flash('Дневникът е подаден успешно.', 'success')
        return redirect(url_for('logbookBp.entry_detail', entry_id=entry.id))

    vessels = VesselModel.query.filter_by(owner_id=g.user.id, status='approved').all()
    return render_template('logbook/create.html', user=g.user, vessels=vessels)


@logbookApp.route('/<int:entry_id>')
def entry_detail(entry_id):
    entry = FishingLogEntry.query.get_or_404(entry_id)

    if entry.created_by != g.user.id and g.user.role not in ('admin', 'inspector'):
        flash('Нямате достъп до този дневник.', 'error')
        return redirect(url_for('logbookBp.list_entries'))

    return render_template('logbook/detail.html', user=g.user, entry=entry)


@logbookApp.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_entry(entry_id):
    entry = FishingLogEntry.query.get_or_404(entry_id)

    if entry.created_by != g.user.id:
        flash('Нямате достъп до този дневник.', 'error')
        return redirect(url_for('logbookBp.list_entries'))

    if entry.status != 'draft':
        flash('Могат да се редактират само чернови.', 'error')
        return redirect(url_for('logbookBp.entry_detail', entry_id=entry_id))

    if request.method == 'POST':
        start_dt_str = request.form['start_datetime']
        end_dt_str = request.form.get('end_datetime')
        try:
            entry.start_datetime = datetime.fromisoformat(start_dt_str)
            entry.end_datetime = datetime.fromisoformat(end_dt_str) if end_dt_str else None
        except ValueError:
            flash('Невалиден формат на дата/час.', 'error')
            return redirect(url_for('logbookBp.edit_entry', entry_id=entry_id))

        entry.start_location = request.form.get('start_location', '')
        entry.end_location = request.form.get('end_location', '')
        entry.gear_used = request.form.get('gear_used', '')
        entry.notes = request.form.get('notes', '')

        if request.form.get('submit') == '1':
            entry.status = 'submitted'

        CatchEntry.query.filter_by(log_entry_id=entry.id).delete()

        species_list = request.form.getlist('species[]')
        kg_list = request.form.getlist('quantity_kg[]')
        pcs_list = request.form.getlist('quantity_pcs[]')

        for i, species in enumerate(species_list):
            if species.strip():
                kg = kg_list[i] if i < len(kg_list) else 0
                pcs = pcs_list[i] if i < len(pcs_list) else None
                catch = CatchEntry(
                    log_entry_id=entry.id,
                    species=species.strip(),
                    quantity_kg=float(kg) if kg else 0,
                    quantity_pcs=int(pcs) if pcs and pcs.strip() else None,
                )
                db.session.add(catch)

        db.session.commit()
        flash('Дневникът е обновен.', 'success')
        return redirect(url_for('logbookBp.entry_detail', entry_id=entry.id))

    return render_template('logbook/edit.html', user=g.user, entry=entry)


@logbookApp.route('/vessels/<int:vessel_id>/permits')
def vessel_permits_json(vessel_id):
    if g.user.role not in ('user', 'inspector', 'admin'):
        return jsonify([])
    permits = PermitModel.query.filter_by(vessel_id=vessel_id, status='active').all()
    return jsonify([{
        'id': p.id,
        'permit_number': p.permit_number,
        'valid_until': p.valid_until.strftime('%d.%m.%Y'),
    } for p in permits])
