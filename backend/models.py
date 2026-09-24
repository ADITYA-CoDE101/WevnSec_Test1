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
    verified = Column(Boolean, nullable=False, default=False)
    monitoring_enabled = Column(Boolean, nullable=False, default=True)
    email_alerts_enabled = Column(Boolean, nullable=False, default=False)
    next_scan_at = Column(DateTime(timezone=True), default=utcnow)
    last_scheduled_at = Column(DateTime(timezone=True))
    scan_lock_until = Column(DateTime(timezone=True))
    scan_lock_token = Column(String(36))
    last_scan_error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "domain", name="uq_domains_user_domain"), {"schema": "wevnsec"})


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
