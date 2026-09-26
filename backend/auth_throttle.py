"""Supabase credential verification remains authoritative; PostgreSQL serializes attempts."""
import hashlib
import hmac
import math
import os
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select, text

from models import LoginThrottle, utcnow


async def lock_attempt(db, email):
    # Account-wide limit cannot be bypassed by rotating ingress peers or forged IP headers.
    identifier = hmac.new(os.environ['JWT_SECRET'].encode(), email.encode(), hashlib.sha256).hexdigest()
    await db.execute(text('''INSERT INTO wevnsec.login_throttle (identifier, failed_attempts, updated_at)
        VALUES (:id, 0, now()) ON CONFLICT (identifier) DO NOTHING'''), {'id': identifier})
    row = (await db.execute(select(LoginThrottle).where(LoginThrottle.identifier == identifier).with_for_update())).scalar_one()
    now = utcnow()
    if row.cooldown_until and row.cooldown_until > now:
        retry = max(1, math.ceil((row.cooldown_until-now).total_seconds()))
        raise HTTPException(status_code=429, detail='Too many sign-in attempts. Try again in 15 minutes.', headers={'Retry-After':str(retry)})
    if row.cooldown_until or row.updated_at < now-timedelta(minutes=15):
        row.failed_attempts, row.cooldown_until = 0, None
    row.updated_at = now
    return row


async def failed_attempt(db, row):
    row.failed_attempts += 1
    row.updated_at = utcnow()
    if row.failed_attempts >= 5:
        row.cooldown_until = utcnow()+timedelta(minutes=15)
    # Commit BEFORE raising HTTPException in the caller; otherwise rollback erases failures.
    await db.commit()


async def successful_attempt(db, row):
    row.failed_attempts, row.cooldown_until = 0, None
    row.updated_at = utcnow()
    await db.commit()