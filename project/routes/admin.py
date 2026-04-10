from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, VesselModel, UserModel

adminApp = Blueprint('admin', __name__)


@adminApp.route('/users')
def users():
    all_users = UserModel.query.order_by(UserModel.created_at.desc()).all()
    return render_template('admin/users.html', user=g.user, users=all_users)


@adminApp.route('/users/<int:user_id>/block', methods=['POST'])
def block_user(user_id):
    return redirect(url_for('admin.users'))


@adminApp.route('/')
def index():
    return render_template('admin/index.html', user=g.user)


@adminApp.route('/vessels')
def vessels():
    vessels = VesselModel.query.order_by(VesselModel.created_at.desc()).all()
    return render_template('admin/vessels.html',user=g.user,vessels=vessels)