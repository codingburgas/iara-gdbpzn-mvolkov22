from flask import Flask, redirect, render_template, session, request, url_for, flash, g
from models.models import db, UserModel as User
from routes.auth import authApp as authBp
from routes.vessels import vesselsApp as vesselsBp
from database import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_CONNECTION_URI

db.init_app(app)
with app.app_context():
    db.create_all()

# register blueprints
app.register_blueprint(authBp, url_prefix='/auth')
app.register_blueprint(vesselsBp, url_prefix='/vessels')


# limit access to certain routes based on authentication and role
@app.before_request
def before_request():
    g.user = User.query.get(session.get('user_id'))

    if request.path.startswith('/vessels') or request.path.startswith('/admin'):
        if not session.get('user_id'):
            flash('Login first!')
            return redirect(url_for('auth.login'))

    if request.path.startswith('/admin'):
        if session.get('role') != 'admin':
            return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html', user=g.user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)