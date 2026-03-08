from flask import Blueprint, render_template, request, session, redirect, url_for, flash, g
from models.models import db, UserModel

authApp = Blueprint('auth', __name__)


@authApp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email      = request.form['email']
        password   = request.form['password']
        full_name  = request.form['full_name']
        identifier = request.form['identifier']
        phone      = request.form.get('phone')
        is_company = bool(request.form.get('is_company', False))

        if UserModel.query.filter_by(email=email).first():
            flash('An account with this email already exists!')
            return redirect(url_for('auth.register'))

        if UserModel.query.filter_by(identifier=identifier).first():
            flash('An account with this EGN/EIK already exists!')
            return redirect(url_for('auth.register'))

        try:
            user = UserModel(
                email      = email,
                full_name  = full_name,
                identifier = identifier,
                phone      = phone,
                is_company = is_company,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            session['role']    = user.role
            return redirect(url_for('index'))

        except ValueError as e:
            flash(str(e))
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html', user=g.user)


@authApp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']

        user = UserModel.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Wrong email or password!')
            return redirect(url_for('auth.login'))

        session['user_id'] = user.id
        session['role']    = user.role
        return redirect(url_for('index'))

    return render_template('auth/login.html', user=g.user)


@authApp.route('/logout')
def logout():
    session['user_id'] = None
    session['role']    = None
    return redirect(url_for('auth.login'))