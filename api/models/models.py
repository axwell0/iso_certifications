import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import relationship

from api.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


# ------------------- Enums -------------------
class AuditStatusEnum(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CertificationStatusEnum(Enum):
    ISSUED = "issued"
    REVOKED = "revoked"


class RequestStatusEnum(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class InvitationStatusEnum(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class RoleEnum(Enum):
    ADMIN = 'admin'
    EMPLOYEE = 'employee'
    MANAGER = 'manager'
    GUEST = 'guest'


# ------------------- Models -------------------

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.EMPLOYEE, nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=True)
    certification_body_id = db.Column(db.String(36), db.ForeignKey('certification_bodies.id'), nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='users')
    certification_body = relationship('CertificationBody', back_populates='users')
    audits_managed = relationship('Audit', back_populates='manager')
    certifications_issued = relationship('Certification', back_populates='issuer')

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship('User', back_populates='organization', cascade='all, delete-orphan')
    certifications = relationship('Certification', back_populates='organization', cascade='all, delete-orphan')
    # documents = relationship('Document', back_populates='organization', cascade='all, delete-orphan')  # If you have a Document model
    invitations = relationship('Invitation', back_populates='organization', cascade='all, delete-orphan')
    audits = relationship('Audit', back_populates='organization', cascade='all, delete-orphan')


class CertificationBody(db.Model):
    __tablename__ = 'certification_bodies'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship('User', back_populates='certification_body', cascade='all, delete-orphan')
    audits = relationship('Audit', back_populates='certification_body', cascade='all, delete-orphan')
    invitations = relationship('Invitation', back_populates='certification_body', cascade='all, delete-orphan')
    # If you want to track all certifications via the certification body:
    # certifications = relationship('Certification', back_populates='certification_body', cascade='all, delete-orphan')


class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_id = db.Column(db.String(36), db.ForeignKey('audits.id'), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    certification_body_id = db.Column(db.String(36), db.ForeignKey('certification_bodies.id'), nullable=False)
    issued_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(CertificationStatusEnum), nullable=False, default=CertificationStatusEnum.ISSUED)
    certificate_pdf = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    issuer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    issuer = relationship('User', back_populates='certifications_issued')
    organization = relationship('Organization', back_populates='certifications')
    audit = relationship('Audit')

    def __repr__(self):
        return f"<Certification {self.id} for Audit {self.audit_id}>"


class Audit(db.Model):
    __tablename__ = 'audits'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.id'), nullable=False)
    certification_body_id = db.Column(db.String, db.ForeignKey('certification_bodies.id'), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(AuditStatusEnum), nullable=False, default=AuditStatusEnum.SCHEDULED)
    checklist = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    manager_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    manager = relationship('User', back_populates='audits_managed')
    organization = relationship('Organization', back_populates='audits')
    certification_body = relationship('CertificationBody', back_populates='audits')
    reports = relationship('AuditReport', back_populates='audit')

    def __repr__(self):
        return f"<Audit {self.name}>"


class AuditReport(db.Model):
    __tablename__ = 'audit_reports'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_id = db.Column(db.String(36), db.ForeignKey('audits.id'), nullable=False)
    report_file = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    audit = relationship('Audit', back_populates='reports')


class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    jti = db.Column(db.String, unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)


class Invitation(db.Model):
    __tablename__ = 'invitations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120),unique=True, nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=True)
    certification_body_id = db.Column(db.String(36), db.ForeignKey('certification_bodies.id'), nullable=True)
    token = db.Column(db.String, unique=True, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(InvitationStatusEnum), default=InvitationStatusEnum.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    organization = relationship('Organization', back_populates='invitations')
    certification_body = relationship('CertificationBody', back_populates='invitations')


class OrganizationCreationRequest(db.Model):
    __tablename__ = 'organization_creation_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    organization_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(RequestStatusEnum), default=RequestStatusEnum.PENDING, nullable=False)
    admin_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guest = relationship('User')


class CertificationBodyCreationRequest(db.Model):
    __tablename__ = 'certification_body_creation_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    certification_body_name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.Enum(RequestStatusEnum), nullable=False, default=RequestStatusEnum.PENDING)
    admin_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guest = relationship('User')

    def __repr__(self):
        return f"<CertificationBodyCreationRequest {self.certification_body_name} by Guest {self.guest_id}>"
