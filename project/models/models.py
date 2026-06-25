from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class UserModel(db.Model):
    is_active = db.Column(db.Boolean, default=True, nullable=False)
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
    inspection_acts = db.relationship('InspectionAct', foreign_keys='InspectionAct.inspector_id', back_populates='inspector', lazy=True)
    issued_fines = db.relationship('Fine', foreign_keys='Fine.inspector_id', back_populates='inspector', lazy=True)
    decided_fines = db.relationship('Fine', foreign_keys='Fine.admin_id', back_populates='admin', lazy=True)

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

    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'suspended', 'revoked'), default='pending', nullable=False)
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    permits = db.relationship('PermitModel', backref='vessel', lazy=True)
    inspection_acts = db.relationship('InspectionAct', back_populates='vessel', lazy=True)
    fines = db.relationship('Fine', back_populates='vessel', lazy=True)

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

    status = db.Column(db.Enum('pending', 'active', 'inactive', 'expired', 'revoked', 'rejected'), default='pending', nullable=False)
    revoke_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=db.func.now())
    holder = db.relationship('UserModel', foreign_keys=[holder_id])

class AdminLog(db.Model):
    table_name = 'admin_log'
  
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(200), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
  
    admin = db.relationship('UserModel', foreign_keys=[admin_id])


class InspectionAct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    act_number = db.Column(db.String(30), unique=True, nullable=False)
    inspector_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessel_model.id'), nullable=False)
    related_permit_id = db.Column(db.Integer, db.ForeignKey('permit_model.id'), nullable=True)
    inspection_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    findings = db.Column(db.Text)
    violations = db.Column(db.Text)
    status = db.Column(db.Enum('draft', 'submitted', 'confirmed', 'cancelled', 'resolved'), default='draft', nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    inspector = db.relationship('UserModel', foreign_keys=[inspector_id], back_populates='inspection_acts')
    vessel = db.relationship('VesselModel', foreign_keys=[vessel_id], back_populates='inspection_acts')
    related_permit = db.relationship('PermitModel', foreign_keys=[related_permit_id])
    fines = db.relationship('Fine', backref='act', lazy=True)


class Fine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fine_number = db.Column(db.String(30), unique=True, nullable=False)
    act_id = db.Column(db.Integer, db.ForeignKey('inspection_act.id'), nullable=False)
    inspector_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessel_model.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    violation_description = db.Column(db.Text)
    legal_basis = db.Column(db.String(200))
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'paid'), default='pending', nullable=False)
    admin_note = db.Column(db.Text)
    admin_id = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    inspector = db.relationship('UserModel', foreign_keys=[inspector_id], back_populates='issued_fines')
    vessel = db.relationship('VesselModel', foreign_keys=[vessel_id], back_populates='fines')
    admin = db.relationship('UserModel', foreign_keys=[admin_id], back_populates='decided_fines')


class FishingLogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessel_model.id'), nullable=False)
    permit_id = db.Column(db.Integer, db.ForeignKey('permit_model.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)

    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=True)
    start_location = db.Column(db.String(300))
    end_location = db.Column(db.String(300))
    gear_used = db.Column(db.Text)
    notes = db.Column(db.Text)

    status = db.Column(db.Enum('draft', 'submitted', 'confirmed'), default='draft', nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    vessel = db.relationship('VesselModel', backref='log_entries', lazy=True)
    permit = db.relationship('PermitModel', backref='log_entries', lazy=True)
    creator = db.relationship('UserModel', foreign_keys=[created_by])
    catches = db.relationship('CatchEntry', back_populates='log_entry', lazy=True, cascade='all, delete-orphan')


class CatchEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_entry_id = db.Column(db.Integer, db.ForeignKey('fishing_log_entry.id'), nullable=False)
    species = db.Column(db.String(100), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    quantity_pcs = db.Column(db.Integer)
    notes = db.Column(db.Text)

    log_entry = db.relationship('FishingLogEntry', back_populates='catches')


class FishLanding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_entry_id = db.Column(db.Integer, db.ForeignKey('fishing_log_entry.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    landing_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    log_entry = db.relationship('FishingLogEntry', backref='landings', lazy=True)
    creator = db.relationship('UserModel', foreign_keys=[created_by])
    batches = db.relationship('FishBatch', back_populates='landing', lazy=True, cascade='all, delete-orphan')


class FishBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(30), unique=True, nullable=False)
    landing_id = db.Column(db.Integer, db.ForeignKey('fish_landing.id'), nullable=False)
    species = db.Column(db.String(100), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

    landing = db.relationship('FishLanding', back_populates='batches')
    movements = db.relationship('BatchMovement', back_populates='batch', lazy=True, cascade='all, delete-orphan')


class TraceLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_type = db.Column(db.Enum('shop', 'warehouse', 'truck'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300))
    owner_name = db.Column(db.String(200))
    license_number = db.Column(db.String(50))
    contact_phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    creator = db.relationship('UserModel', foreign_keys=[created_by])
    incoming_movements = db.relationship('BatchMovement', foreign_keys='BatchMovement.to_location_id', back_populates='to_location', lazy=True)
    outgoing_movements = db.relationship('BatchMovement', foreign_keys='BatchMovement.from_location_id', back_populates='from_location', lazy=True)


class BatchMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('fish_batch.id'), nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey('trace_location.id'), nullable=True)
    to_location_id = db.Column(db.Integer, db.ForeignKey('trace_location.id'), nullable=False)
    movement_type = db.Column(db.Enum('landing', 'transport', 'storage', 'delivery'), nullable=False)
    departure_date = db.Column(db.DateTime, nullable=True)
    arrival_date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user_model.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    batch = db.relationship('FishBatch', back_populates='movements')
    from_location = db.relationship('TraceLocation', foreign_keys=[from_location_id], back_populates='outgoing_movements')
    to_location = db.relationship('TraceLocation', foreign_keys=[to_location_id], back_populates='incoming_movements')
    creator = db.relationship('UserModel', foreign_keys=[created_by])