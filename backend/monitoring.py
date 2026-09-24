"""Postgres-backed leases and transactional alert outbox, shared by all workers."""
import asyncio
import logging
import uuid
from datetime import timedelta

import httpx
from sqlalchemy import select, or_

from database import AsyncSessionLocal
from models import Alert, Domain, Scan, utcnow
from email_service import grade_drop_template, send_email

logger = logging.getLogger(__name__)
GRADE_RANK = {grade: i for i, grade in enumerate(('A+', 'A', 'B', 'C', 'D', 'F'))}


async def record_scan(db, scan, *, domain_id=None, lease_token=None):
    """Serialize comparisons per watched domain; scan and alert commit together."""
    domain = None
    if scan.user_id:
        domain = (await db.execute(select(Domain).where(
            Domain.user_id == scan.user_id, Domain.domain == scan.target
        ).with_for_update())).scalar_one_or_none()
    if domain_id and (not domain or domain.id != domain_id or domain.scan_lock_token != lease_token or not domain.monitoring_enabled):
        return False
    if domain:
        previous = (await db.execute(select(Scan).where(
            Scan.user_id == scan.user_id, Scan.target == scan.target
        ).order_by(Scan.created_at.desc()).limit(1))).scalar_one_or_none()
        if previous and GRADE_RANK[scan.grade] > GRADE_RANK[previous.grade]:
            db.add(Alert(
                user_id=scan.user_id, domain=scan.target, scan_share_id=scan.share_id,
                delta=previous.score - scan.score, previous_grade=previous.grade, current_grade=scan.grade,
                previous_score=previous.score, current_score=scan.score,
                message=f'{scan.target} dropped from {previous.grade} to {scan.grade}.',
                email_status='pending' if domain.email_alerts_enabled else 'disabled',
                email_next_attempt_at=utcnow() if domain.email_alerts_enabled else None,
            ))
        if domain_id:
            domain.last_scheduled_at = utcnow()
            domain.next_scan_at = utcnow() + timedelta(days=1)
            domain.scan_lock_until = domain.scan_lock_token = domain.last_scan_error = None
    scan.created_at = utcnow()
    db.add(scan)
    await db.commit()
    return True


class MonitoringWorker:
    def __init__(self, scan_target, resolve_email):
        self.scan_target, self.resolve_email = scan_target, resolve_email
        self.task = None

    def start(self):
        self.task = asyncio.create_task(self.run())

    async def stop(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def claim_domain(self):
        async with AsyncSessionLocal() as db:
            now = utcnow()
            domain = (await db.execute(select(Domain).where(
                Domain.monitoring_enabled.is_(True), Domain.next_scan_at <= now,
                or_(Domain.scan_lock_until.is_(None), Domain.scan_lock_until < now)
            ).order_by(Domain.next_scan_at).limit(1).with_for_update(skip_locked=True))).scalar_one_or_none()
            if not domain:
                return None
            domain.scan_lock_token = str(uuid.uuid4())
            domain.scan_lock_until = now + timedelta(minutes=5)
            await db.commit()
            return domain

    async def scan_due_domain(self):
        domain = await self.claim_domain()
        if not domain:
            return False
        try:
            scan = await asyncio.wait_for(self.scan_target(domain.domain, domain.user_id, 'scheduled'), timeout=180)
            async with AsyncSessionLocal() as db:
                await record_scan(db, scan, domain_id=domain.id, lease_token=domain.scan_lock_token)
        except Exception as exc:
            logger.warning('Scheduled scan failed: %s', type(exc).__name__)
            async with AsyncSessionLocal() as db:
                current = (await db.execute(select(Domain).where(Domain.id == domain.id).with_for_update())).scalar_one_or_none()
                if current and current.scan_lock_token == domain.scan_lock_token:
                    current.last_scan_error = 'Scan could not complete; retry scheduled in one hour.'
                    current.next_scan_at = utcnow() + timedelta(hours=1)
                    current.scan_lock_until = current.scan_lock_token = None
                    await db.commit()
        return True

    async def deliver_one_alert(self):
        # Keep the row lock during delivery: concurrent workers cannot send this alert twice.
        # Ambiguous timeouts/crashes are not automatically retried (proxy has no documented idempotency).
        async with AsyncSessionLocal() as db:
            alert = (await db.execute(select(Alert).where(
                Alert.email_status.in_(('pending','retrying','sending')),
                Alert.email_next_attempt_at <= utcnow(),
            ).order_by(Alert.created_at).limit(1).with_for_update(skip_locked=True))).scalar_one_or_none()
            if not alert:
                return False
            if alert.email_status == 'sending':
                alert.email_status = 'uncertain'
                alert.email_error = 'Delivery interrupted; automatic retry withheld to prevent duplicates.'
                await db.commit()
                return True
            domain = (await db.execute(select(Domain).where(Domain.user_id == alert.user_id, Domain.domain == alert.domain))).scalar_one_or_none()
            if not domain or not domain.email_alerts_enabled:
                alert.email_status = 'disabled'
                await db.commit()
                return True
            alert.email_status = 'sending'
            alert.email_attempts += 1
            alert.email_next_attempt_at = utcnow() + timedelta(minutes=5)
            alert_id = alert.id
            # Durable pre-send marker distinguishes interrupted sends after process restarts.
            await db.commit()
            alert = (await db.execute(select(Alert).where(Alert.id == alert_id).with_for_update())).scalar_one_or_none()
            try:
                recipient = await self.resolve_email(alert.user_id)
                if not recipient:
                    raise ValueError('No account email')
                subject, html = grade_drop_template(alert)
                alert.email_provider_id = await send_email(to=recipient, subject=subject, html=html)
                alert.email_status = 'sent'
                alert.email_sent_at = utcnow()
                alert.email_error = None
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                retryable = code == 429 or code >= 500
                alert.email_status = 'retrying' if retryable and alert.email_attempts < 3 else 'failed'
                alert.email_next_attempt_at = utcnow() + timedelta(minutes=5 * alert.email_attempts)
                alert.email_error = f'Email service rejected the request (HTTP {code}).'
            except (httpx.TimeoutException, httpx.NetworkError):
                alert.email_status = 'uncertain'
                alert.email_error = 'Delivery could not be confirmed; not retried to avoid duplicate emails.'
            except Exception as exc:
                alert.email_status = 'failed'
                alert.email_error = 'Email could not be sent. Check account email and service configuration.'
                logger.warning('Email failed: %s', type(exc).__name__)
            await db.commit()
            return True

    async def run(self):
        while True:
            try:
                for _ in range(5):
                    if not await self.deliver_one_alert():
                        break
                for _ in range(3):
                    if not await self.scan_due_domain():
                        break
            except Exception as exc:
                logger.warning('Monitoring cycle failed: %s', type(exc).__name__)
            await asyncio.sleep(30)