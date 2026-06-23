from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, InspectionAct, Fine, VesselModel, AdminLog
from datetime import date

inspectorApp = Blueprint('inspectorBp', __name__)


def generate_act_number():
    count = InspectionAct.query.count() + 1
    return f'IARA-ACT-{date.today().year}-{count:06d}'


def generate_fine_number():
    count = Fine.query.count() + 1
    return f'IARA-FINE-{date.today().year}-{count:06d}'


@inspectorApp.route('/')
def dashboard():
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    acts = InspectionAct.query.filter_by(inspector_id=g.user.id).order_by(InspectionAct.created_at.desc()).all()
    total_fines = Fine.query.filter_by(inspector_id=g.user.id).count()
    return render_template('inspector/dashboard.html', user=g.user, acts=acts, total_fines=total_fines)


@inspectorApp.route('/acts')
def list_acts():
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    status_filter = request.args.get('status', None)
    query = InspectionAct.query.filter_by(inspector_id=g.user.id)
    if status_filter and status_filter in ('draft', 'submitted', 'confirmed', 'cancelled'):
        query = query.filter_by(status=status_filter)
    acts = query.order_by(InspectionAct.created_at.desc()).all()
    return render_template('inspector/acts_list.html', user=g.user, acts=acts, current_filter=status_filter)


@inspectorApp.route('/acts/create', methods=['GET', 'POST'])
def create_act():
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        vessel_id = request.form.get('vessel_id', type=int)
        vessel = VesselModel.query.get_or_404(vessel_id)

        act = InspectionAct(
            act_number=generate_act_number(),
            inspector_id=g.user.id,
            vessel_id=vessel_id,
            inspection_date=date.fromisoformat(request.form['inspection_date']),
            location=request.form.get('location', ''),
            findings=request.form.get('findings', ''),
            violations=request.form.get('violations', ''),
            status='draft',
        )
        db.session.add(act)
        db.session.flush()

        fine_amount = request.form.get('fine_amount', type=float)
        if fine_amount and fine_amount > 0:
            fine = Fine(
                fine_number=generate_fine_number(),
                act_id=act.id,
                inspector_id=g.user.id,
                vessel_id=vessel_id,
                amount=fine_amount,
                violation_description=request.form.get('violation_description', ''),
                legal_basis=request.form.get('legal_basis', ''),
                status='approved',
            )
            db.session.add(fine)

        db.session.commit()
        flash(f'Акт {act.act_number} е създаден успешно.', 'success')
        return redirect(url_for('inspectorBp.act_detail', act_id=act.id))

    vessels = VesselModel.query.filter_by(status='approved').order_by(VesselModel.cfr_number).all()
    today = date.today().isoformat()
    return render_template('inspector/act_create.html', user=g.user, vessels=vessels, today=today)


@inspectorApp.route('/acts/<int:act_id>')
def act_detail(act_id):
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    act = InspectionAct.query.get_or_404(act_id)
    if act.inspector_id != g.user.id and g.user.role != 'admin':
        flash('Нямате достъп до този акт.', 'error')
        return redirect(url_for('inspectorBp.list_acts'))

    return render_template('inspector/act_detail.html', user=g.user, act=act)


@inspectorApp.route('/acts/<int:act_id>/submit', methods=['POST'])
def submit_act(act_id):
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    act = InspectionAct.query.get_or_404(act_id)
    if act.inspector_id != g.user.id:
        flash('Нямате достъп до този акт.', 'error')
        return redirect(url_for('inspectorBp.list_acts'))

    if act.status != 'draft':
        flash('Актът вече е изпратен.', 'error')
        return redirect(url_for('inspectorBp.act_detail', act_id=act_id))

    act.status = 'submitted'
    db.session.commit()

    log_entry = AdminLog(
        admin_id=g.user.id,
        action='submit_act',
        target=act.act_number,
        note=f'Акт за проверка на кораб {act.vessel.cfr_number}'
    )
    db.session.add(log_entry)
    db.session.commit()

    flash(f'Акт {act.act_number} е изпратен за обработка.', 'success')
    return redirect(url_for('inspectorBp.act_detail', act_id=act_id))


@inspectorApp.route('/acts/<int:act_id>/cancel', methods=['POST'])
def cancel_act(act_id):
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    act = InspectionAct.query.get_or_404(act_id)
    if act.inspector_id != g.user.id:
        flash('Нямате достъп до този акт.', 'error')
        return redirect(url_for('inspectorBp.list_acts'))

    if act.status != 'draft':
        flash('Може да отмените само чернови.', 'error')
        return redirect(url_for('inspectorBp.act_detail', act_id=act_id))

    act.status = 'cancelled'
    db.session.commit()
    flash(f'Акт {act.act_number} е отменен.', 'success')
    return redirect(url_for('inspectorBp.list_acts'))


@inspectorApp.route('/fines/create', methods=['GET', 'POST'])
def create_fine():
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        vessel_id = request.form.get('vessel_id', type=int)
        vessel = VesselModel.query.get_or_404(vessel_id)

        fine_amount = request.form.get('fine_amount', type=float)
        if not fine_amount or fine_amount <= 0:
            flash('Моля, въведете валидна сума на глобата.', 'error')
            return redirect(url_for('inspectorBp.create_fine'))

        act = InspectionAct(
            act_number=generate_act_number(),
            inspector_id=g.user.id,
            vessel_id=vessel_id,
            inspection_date=date.today(),
            location=request.form.get('location', ''),
            findings='Автоматично създаден акт за глоба',
            violations=request.form.get('violation_description', ''),
            status='draft',
        )
        db.session.add(act)
        db.session.flush()

        fine = Fine(
            fine_number=generate_fine_number(),
            act_id=act.id,
            inspector_id=g.user.id,
            vessel_id=vessel_id,
            amount=fine_amount,
            violation_description=request.form.get('violation_description', ''),
            legal_basis=request.form.get('legal_basis', ''),
            status='approved',
        )
        db.session.add(fine)
        db.session.commit()

        flash(f'Глоба {fine.fine_number} е създадена успешно.', 'success')
        return redirect(url_for('inspectorBp.fine_detail', fine_id=fine.id))

    vessels = VesselModel.query.filter_by(status='approved').order_by(VesselModel.cfr_number).all()
    today = date.today().isoformat()
    return render_template('inspector/fine_create.html', user=g.user, vessels=vessels, today=today)


@inspectorApp.route('/fines')
def list_fines():
    if g.user.role not in ('inspector', 'admin'):
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    status_filter = request.args.get('status', None)
    query = Fine.query.filter_by(inspector_id=g.user.id)
    if status_filter and status_filter in ('approved', 'paid', 'rejected'):
        query = query.filter_by(status=status_filter)
    fines = query.order_by(Fine.created_at.desc()).all()
    return render_template('inspector/fines_list.html', user=g.user, fines=fines, current_filter=status_filter)


@inspectorApp.route('/fines/<int:fine_id>')
def fine_detail(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    vessel_owner_id = fine.vessel.owner_id if fine.vessel else None
    if g.user.role not in ('inspector', 'admin') and g.user.id != vessel_owner_id:
        flash('Нямате достъп до тази страница.', 'error')
        return redirect(url_for('index'))

    return render_template('inspector/fine_detail.html', user=g.user, fine=fine)
