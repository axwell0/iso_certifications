import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import relationship

from api.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

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


class OrganizationCreationRequest(db.Model):
    __tablename__ = 'organization_creation_requests'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    organization_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(RequestStatusEnum), default=RequestStatusEnum.PENDING, nullable=False)
    admin_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guest = relationship('User')

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.EMPLOYEE, nullable=False)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.id'), nullable=True)
    certification_body_id = db.Column(db.String, db.ForeignKey('certification_bodies.id'), nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='users')
    certification_body = relationship('CertificationBody', back_populates='users')

    def set_password(self, password):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship('User', back_populates='organization', cascade='all, delete-orphan')
    certifications = relationship('Certification', back_populates='organization', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='organization', cascade='all, delete-orphan')
    invitations = relationship('Invitation', back_populates='organization', cascade='all, delete-orphan')

class CertificationBody(db.Model):
    __tablename__ = 'certification_bodies'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), unique=True, nullable=False)
    accreditation_number = db.Column(db.String(100), unique=True, nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship('User', back_populates='certification_body', cascade='all, delete-orphan')
    audits = relationship('Audit', back_populates='certification_body', cascade='all, delete-orphan')
    invitations = relationship('Invitation', back_populates='certification_body', cascade='all, delete-orphan')

class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    iso_standard = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='certifications')
    audits = relationship('Audit', back_populates='certification', cascade='all, delete-orphan')

class Audit(db.Model):
    __tablename__ = 'audits'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_date = db.Column(db.Date, nullable=False)
    findings = db.Column(db.Text, nullable=True)
    certification_id = db.Column(db.String, db.ForeignKey('certifications.id'), nullable=False)
    certification_body_id = db.Column(db.String, db.ForeignKey('certification_bodies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    certification = relationship('Certification', back_populates='audits')
    certification_body = relationship('CertificationBody', back_populates='audits')
    reports = relationship('AuditReport', back_populates='audit', cascade='all, delete-orphan')

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.id'), nullable=False)

    uploader = relationship('User')
    organization = relationship('Organization', back_populates='documents')

class AuditReport(db.Model):
    __tablename__ = 'audit_reports'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_id = db.Column(db.String, db.ForeignKey('audits.id'), nullable=False)
    report_file = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    audit = relationship('Audit', back_populates='reports')

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship('User')

class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship('User')
    organization = relationship('Organization')

# RevokedToken Model
class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    jti = db.Column(db.String, unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)

# Invitation Model
class Invitation(db.Model):
    __tablename__ = 'invitations'

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.id'), nullable=True)
    certification_body_id = db.Column(db.String, db.ForeignKey('certification_bodies.id'), nullable=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(InvitationStatusEnum), default=InvitationStatusEnum.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)

    organization = relationship('Organization', back_populates='invitations')
    certification_body = relationship('CertificationBody', back_populates='invitations')