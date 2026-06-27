import os
from flask import Flask, redirect, render_template, session, request, url_for, flash, g
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from models.models import db, UserModel as User
from datetime import datetime
from routes.auth import authApp as authBp
from routes.admin import adminApp as adminBp
from routes.vessels import vesselsApp as vesselsBp
from routes.permits import permitsApp as permitsApp
from routes.inspector import inspectorApp as inspectorBp
from routes.logbook import logbookApp as logbookBp
from routes.trace import traceBp as traceBp
from database import config
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_CONNECTION_URI
app.config['WTF_CSRF_TIME_LIMIT'] = None

csrf = CSRFProtect(app)

db.init_app(app)
with app.app_context():
    db.create_all()

# register blueprints
app.register_blueprint(authBp, url_prefix='/auth')
app.register_blueprint(adminBp, url_prefix='/admin')
app.register_blueprint(vesselsBp, url_prefix='/vessels')
app.register_blueprint(permitsApp, url_prefix='/permits')
app.register_blueprint(inspectorBp, url_prefix='/inspector')
app.register_blueprint(logbookBp, url_prefix='/logbook')
app.register_blueprint(traceBp, url_prefix='/trace')


def expire_permits_job():
    with app.app_context():
        from models.models import PermitModel, FishingTicket
        from datetime import date
        today = date.today()
        expired = PermitModel.query.filter(
            PermitModel.status == 'active',
            PermitModel.valid_until < today
        ).all()
        for permit in expired:
            permit.status = 'expired'

        expired_tickets = FishingTicket.query.filter(
            FishingTicket.status == 'active',
            FishingTicket.valid_until < today
        ).all()
        for ticket in expired_tickets:
            ticket.status = 'expired'

        db.session.commit()


scheduler = BackgroundScheduler()
scheduler.add_job(expire_permits_job, 'interval', hours=1, id='expire_permits')
scheduler.start()


# limit access to certain routes based on authentication and role
@app.before_request
def before_request():
    g.user = User.query.get(session.get('user_id'))

    if request.path.startswith('/vessels') or request.path.startswith('/admin') or request.path.startswith('/permits') or request.path.startswith('/inspector') or request.path.startswith('/profile') or request.path.startswith('/pay') or request.path.startswith('/logbook') or request.path.startswith('/trace') or request.path.startswith('/buy-ticket') or request.path.startswith('/tickets'):
        if not session.get('user_id'):
            flash('Моля, влезте първо!')
            return redirect(url_for('auth.login'))

    if request.path.startswith('/admin'):
        if session.get('role') != 'admin':
            return redirect(url_for('index'))


@app.route('/profile')
def profile():
    from models.models import Fine, VesselModel, InspectionAct, PermitModel, FishingLogEntry, FishLanding
    user = g.user
    if not user:
        flash('Моля, влезте първо!')
        return redirect(url_for('auth.login'))
    if user.role == 'admin':
        return redirect(url_for('adminBp.index'))

    vessels = []
    fines = []
    acts = []
    permits = []
    log_entries = []

    tickets = []
    if user.role == 'user':
        vessels = VesselModel.query.filter_by(owner_id=user.id).all()
        vessel_ids = [v.id for v in vessels]
        fines = Fine.query.filter(Fine.vessel_id.in_(vessel_ids)).order_by(Fine.created_at.desc()).all() if vessel_ids else []
        permits = PermitModel.query.filter_by(holder_id=user.id).order_by(PermitModel.created_at.desc()).all()
        log_entries = FishingLogEntry.query.filter_by(created_by=user.id).order_by(FishingLogEntry.created_at.desc()).all()
        fish_landings = FishLanding.query.filter_by(created_by=user.id).order_by(FishLanding.created_at.desc()).limit(5).all()
        from models.models import FishingTicket
        tickets = FishingTicket.query.filter_by(user_id=user.id).order_by(FishingTicket.created_at.desc()).all()
    elif user.role == 'inspector':
        acts = InspectionAct.query.filter_by(inspector_id=user.id).order_by(InspectionAct.created_at.desc()).all()
        fines = Fine.query.filter_by(inspector_id=user.id).order_by(Fine.created_at.desc()).all()
        fish_landings = []
        from models.models import FishingTicket
        tickets = FishingTicket.query.filter_by(user_id=user.id).order_by(FishingTicket.created_at.desc()).all()
    else:
        fish_landings = []
        tickets = []

    return render_template('profile.html', user=user, vessels=vessels, fines=fines, acts=acts, permits=permits, log_entries=log_entries, fish_landings=fish_landings, tickets=tickets)


@app.route('/pay/<int:fine_id>', methods=['GET', 'POST'])
def pay_fine(fine_id):
    from models.models import Fine
    fine = Fine.query.get_or_404(fine_id)

    if fine.status == 'pending':
        flash('Глобата все още не е одобрена от администратор. Моля, опитайте по-късно.', 'error')
        return redirect(url_for('profile'))

    if fine.status == 'paid':
        flash('Тази глоба вече е платена.', 'error')
        return redirect(url_for('profile'))

    if fine.status == 'rejected':
        flash('Тази глоба е отхвърлена и не може да бъде платена.', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        if payment_method in ('card', 'stripe'):
            fine.status = 'paid'
            fine.decided_at = datetime.now()
            db.session.commit()
            flash(f'Глоба {fine.fine_number} е платена успешно.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Невалиден метод на плащане.', 'error')
            return redirect(url_for('pay_fine', fine_id=fine_id))

    return render_template('payment.html', user=g.user, fine=fine)


@app.route('/buy-ticket', methods=['POST'])
def buy_ticket():
    from models.models import FishingTicket
    from datetime import date, timedelta

    ticket_type = request.form.get('ticket_type')
    period = request.form.get('period')

    valid_periods = {
        '1 седмица': 7,
        '1 месец': 30,
        '6 месеца': 180,
        '1 година': 365,
    }

    if ticket_type not in ('standard', 'reduced', 'disabled'):
        flash('Невалиден тип билет.', 'error')
        return redirect(url_for('index'))

    if period not in valid_periods:
        flash('Невалиден период.', 'error')
        return redirect(url_for('index'))

    prices = {
        'standard': {'1 седмица': 6.14, '1 месец': 8.18, '6 месеца': 15.34, '1 година': 25.56},
        'reduced': {'1 седмица': 3.07, '1 месец': 4.09, '6 месеца': 7.67, '1 година': 12.78},
        'disabled': {'1 седмица': 0, '1 месец': 0, '6 месеца': 0, '1 година': 0},
    }

    price = prices[ticket_type][period]
    telk_number = request.form.get('telk_number', '').strip()

    if ticket_type == 'disabled' and not telk_number:
        flash('За безплатен билет е необходим номер на ТЕЛК решение.', 'error')
        return redirect(url_for('index'))

    today = date.today()
    valid_until = today + timedelta(days=valid_periods[period])

    last_ticket = FishingTicket.query.order_by(FishingTicket.id.desc()).first()
    next_num = (last_ticket.id + 1) if last_ticket else 1
    receipt_number = f'TKT-{today.strftime("%Y%m%d")}-{next_num:04d}'

    is_disabled = ticket_type == 'disabled'
    ticket = FishingTicket(
        user_id=g.user.id,
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

    if is_disabled:
        flash(f'Заявлението за безплатен билет ({receipt_number}) е подадено и чака одобрение от администратор.', 'success')
    else:
        flash(f'Билет {receipt_number} е закупен успешно!', 'success')
    return redirect(url_for('profile') + '#tickets')


@app.route('/tickets/<int:ticket_id>/receipt')
def ticket_receipt(ticket_id):
    from models.models import FishingTicket
    ticket = FishingTicket.query.get_or_404(ticket_id)
    if ticket.user_id != g.user.id and g.user.role != 'admin':
        flash('Нямате достъп до този билет.', 'error')
        return redirect(url_for('index'))
    return render_template('receipt.html', user=g.user, ticket=ticket)


@app.route('/tickets/<int:ticket_id>/cancel', methods=['POST'])
def cancel_ticket(ticket_id):
    from models.models import FishingTicket
    ticket = FishingTicket.query.get_or_404(ticket_id)
    if ticket.user_id != g.user.id:
        flash('Нямате достъп до този билет.', 'error')
        return redirect(url_for('index'))
    if ticket.status not in ('active', 'pending'):
        flash('Този билет не може да бъде анулиран.', 'error')
        return redirect(url_for('profile'))
    ticket.status = 'cancelled'
    db.session.commit()
    flash(f'Билет {ticket.receipt_number} е анулиран.', 'success')
    return redirect(url_for('profile'))


@app.route('/tickets/<int:ticket_id>/approve', methods=['POST'])
def approve_ticket(ticket_id):
    from models.models import FishingTicket
    from datetime import date, timedelta
    ticket = FishingTicket.query.get_or_404(ticket_id)
    if g.user.role != 'admin':
        flash('Нямате права.', 'error')
        return redirect(url_for('index'))
    if ticket.status != 'pending':
        flash('Това заявление не е в статус "чакащо".', 'error')
        return redirect(url_for('adminBp.index'))
    valid_periods = {'1 седмица': 7, '1 месец': 30, '6 месеца': 180, '1 година': 365}
    today = date.today()
    ticket.status = 'active'
    ticket.valid_from = today
    ticket.valid_until = today + timedelta(days=valid_periods[ticket.period])
    ticket.paid_at = db.func.now()
    db.session.commit()
    flash(f'Билет {ticket.receipt_number} е одобрен.', 'success')
    return redirect(url_for('adminBp.index', ticket_filter='pending'))


@app.route('/tickets/<int:ticket_id>/reject', methods=['POST'])
def reject_ticket(ticket_id):
    from models.models import FishingTicket
    ticket = FishingTicket.query.get_or_404(ticket_id)
    if g.user.role != 'admin':
        flash('Нямате права.', 'error')
        return redirect(url_for('index'))
    if ticket.status != 'pending':
        flash('Това заявление не е в статус "чакащо".', 'error')
        return redirect(url_for('adminBp.index'))
    ticket.status = 'cancelled'
    db.session.commit()
    flash(f'Билет {ticket.receipt_number} е отхвърлен.', 'success')
    return redirect(url_for('adminBp.index', ticket_filter='pending'))


@app.route('/')
def index():
    return render_template('index.html', user=g.user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)