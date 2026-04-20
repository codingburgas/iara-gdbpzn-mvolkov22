from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.models import db, VesselModel, UserModel

adminApp = Blueprint('adminBp', __name__)


@adminApp.route('/')
def index():
    pending = VesselModel.query.filter_by(status='pending').all()
    stats = {
        'approved': VesselModel.query.filter_by(status='approved').count(),
        'rejected': VesselModel.query.filter_by(status='rejected').count(),
        'revoked':  VesselModel.query.filter_by(status='revoked').count(),
    }
    return render_template('admin/index.html',user=g.user,pending=pending,stats=stats)


@adminApp.route('/vessels/<int:vessel_id>/approve', methods=['POST'])
def approve(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    vessel.status = 'approved'
    vessel.admin_note = request.form.get('note', '')
    db.session.commit()
    flash(f'Vessel {vessel.cfr_number} approved.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/vessels/<int:vessel_id>/reject', methods=['POST'])
def reject(vessel_id):
    vessel = VesselModel.query.get_or_404(vessel_id)
    note = request.form.get('note', '').strip()
    if not note:
        flash('A reason is required when rejecting.', 'error')
        return redirect(url_for('adminBp.index'))
    vessel.status = 'rejected'
    vessel.admin_note = note
    db.session.commit()
    flash(f'Vessel {vessel.cfr_number} rejected.', 'success')
    return redirect(url_for('adminBp.index'))


@adminApp.route('/vessels/<int:vessel_id>/revoke', methods=['POST'])
def revoke():
    return redirect(url_for('adminBp.index'))