import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "wevnsec"}
    id = Column(UUID(as_uuid=False), primary_key=True)  # mirrors auth.users.id; FK enforced in migration SQL
    name = Column(String(255), nullable=False, default="")
    role = Column(String(32), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = {"schema": "wevnsec"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    share_id = Column(String(16), unique=True, nullable=False, index=True)
    target = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("wevnsec.profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    score = Column(Integer, nullable=False)
    grade = Column(String(4), nullable=False)
    counts = Column(JSONB, nullable=False)
    duration_ms = Column(Integer)
    checks = Column(JSONB, nullable=False)
    source = Column(String(16), nullable=False, default="manual")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Domain(Base):
    __tablename__ = "domains"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("wevnsec.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String(255), nullable=False)
    # ------------Ownership verification------------
    verified = Column(Boolean, nullable=False, default=False)
    verification_method = Column(String(32), nullable=True)
    verification_token = Column(String(128), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_status = Column(String(32), nullable=False, default="pending")
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    last_verification_at = Column(DateTime(timezone=True), nullable=True)
    last_verification_error = Column(Text, nullable=True)
    # ------------------------------------------------
    monitoring_enabled = Column(Boolean, nullable=False, default=True)
    email_alerts_enabled = Column(Boolean, nullable=False, default=False)
    next_scan_at = Column(DateTime(timezone=True), default=utcnow)
    last_scheduled_at = Column(DateTime(timezone=True))
    scan_lock_until = Column(DateTime(timezone=True))
    scan_lock_token = Column(String(36))
    last_scan_error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "domain", name="uq_domains_user_domain"), UniqueConstraint("domain", name="uq_domains_domain"), {"schema": "wevnsec"})


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "wevnsec"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("wevnsec.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String(255), nullable=False)
    scan_share_id = Column(String(16), nullable=False)
    delta = Column(Integer, nullable=False)
    message = Column(Text, nullable=False, default="")
    read = Column(Boolean, nullable=False, default=False)
    previous_grade = Column(String(4))
    current_grade = Column(String(4))
    previous_score = Column(Integer)
    current_score = Column(Integer)
    email_status = Column(String(24), nullable=False, default="disabled")
    email_attempts = Column(Integer, nullable=False, default=0)
    email_next_attempt_at = Column(DateTime(timezone=True))
    email_sent_at = Column(DateTime(timezone=True))
    email_provider_id = Column(String(255))
    email_error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class LoginThrottle(Base):
    __tablename__ = 'login_throttle'
    __table_args__ = {'schema': 'wevnsec'}
    identifier = Column(String(64), primary_key=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    cooldown_until = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class CronDelivery(Base):
    __tablename__ = 'cron_deliveries'
    __table_args__ = {'schema': 'wevnsec'}
    run_id = Column(String(255), primary_key=True)
    status = Column(String(24), nullable=False, default='queued')
    deleted_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    finished_at = Column(DateTime(timezone=True))


class Documentation(Base):
    __tablename__ = 'documentation'
    __table_args__ = {'schema': 'wevnsec'}
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    slug = Column(String(120), unique=True, nullable=False)
    title = Column(String(180), nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String(80), nullable=False)
    severity = Column(String(16), nullable=False)
    coverage = Column(String(24), nullable=False)
    check_ids = Column(JSONB, nullable=False, default=list)
    explanation = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    mitigation = Column(Text, nullable=False)
    validation = Column(Text, nullable=False)
    limitations = Column(Text, nullable=False)
    reference_url = Column(Text, nullable=False, default='')
    published = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
