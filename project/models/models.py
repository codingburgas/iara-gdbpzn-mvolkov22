from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('admin', 'inspector', 'user'), default='user')
    full_name = db.Column(db.String(200), nullable=False)
    identifier = db.Column(db.String(13), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.now())

    is_company = db.Column(db.Boolean, default=False, nullable=False)

    relationships = db.relationship('VesselModel', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class VesselModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)

    cfr_number = db.Column(db.String(20), unique=True, nullable=False)
    call_sign = db.Column(db.String(10), unique=True)
    marking = db.Column(db.String(30), nullable=False)

    captain_name = db.Column(db.String(200))
    captain_license = db.Column(db.String(50))
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float)
    draft = db.Column(db.Float)
    gross_tonnage = db.Column(db.Float)
    engine_power = db.Column(db.Float)
    fuel_type = db.Column(db.Enum('diesel', 'petrol', 'electric', 'hybrid'))

    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending', nullable=False)
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    permits = db.relationship('PermitModel', backref='vessel', lazy=True)

class PermitModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    holder_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessel_model.id'), nullable=False)

    permit_number = db.Column(db.String(30), unique=True, nullable=False)
    issued_date = db.Column(db.Date, nullable=False)
    valid_until = db.Column(db.Date, nullable=False)

    captain_name = db.Column(db.String(200))
    captain_license = db.Column(db.String(50))

    allowed_gear = db.Column(db.Text)

    status = db.Column(db.Enum('active', 'expired', 'revoked'), default='active', nullable=False)
    revoke_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=db.func.now())