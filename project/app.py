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


def expire_permits_job():
    with app.app_context():
        from models.models import PermitModel
        from datetime import date
        today = date.today()
        expired = PermitModel.query.filter(
            PermitModel.status == 'active',
            PermitModel.valid_until < today
        ).all()
        for permit in expired:
            permit.status = 'expired'
        db.session.commit()


scheduler = BackgroundScheduler()
scheduler.add_job(expire_permits_job, 'interval', hours=1, id='expire_permits')
scheduler.start()


# limit access to certain routes based on authentication and role
@app.before_request
def before_request():
    g.user = User.query.get(session.get('user_id'))

    if request.path.startswith('/vessels') or request.path.startswith('/admin') or request.path.startswith('/permits') or request.path.startswith('/inspector') or request.path.startswith('/profile') or request.path.startswith('/pay'):
        if not session.get('user_id'):
            flash('Моля, влезте първо!')
            return redirect(url_for('auth.login'))

    if request.path.startswith('/admin'):
        if session.get('role') != 'admin':
            return redirect(url_for('index'))


@app.route('/profile')
def profile():
    from models.models import Fine, VesselModel, InspectionAct, PermitModel
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

    if user.role == 'user':
        vessels = VesselModel.query.filter_by(owner_id=user.id).all()
        vessel_ids = [v.id for v in vessels]
        fines = Fine.query.filter(Fine.vessel_id.in_(vessel_ids)).order_by(Fine.created_at.desc()).all() if vessel_ids else []
        permits = PermitModel.query.filter_by(holder_id=user.id).order_by(PermitModel.created_at.desc()).all()
    elif user.role == 'inspector':
        acts = InspectionAct.query.filter_by(inspector_id=user.id).order_by(InspectionAct.created_at.desc()).all()
        fines = Fine.query.filter_by(inspector_id=user.id).order_by(Fine.created_at.desc()).all()

    return render_template('profile.html', user=user, vessels=vessels, fines=fines, acts=acts, permits=permits)


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


@app.route('/')
def index():
    return render_template('index.html', user=g.user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)