import secrets
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from domain_validation import VerificationError, normalize_domain
from domain_verification import DomainIn, VerifyIn, check_proof, domain_view
from models import Domain, Scan, utcnow


def failure(status, reason, message):
    return HTTPException(status, detail={'reason': reason, 'message': message})


async def owned_domain(db, domain_id, user_id, *, lock=False):
    query = select(Domain).where(Domain.id == str(domain_id), Domain.user_id == user_id)
    if lock:
        query = query.with_for_update()
    domain = (await db.execute(query)).scalar_one_or_none()
    if not domain:
        raise HTTPException(404, detail='Domain not found')
    return domain


async def attempt(db, domain, method, *, reverify=False):
    # Keep the row lock until proof commits so a duplicate verify/reverify/delete
    # cannot overwrite a more recent result or resurrect a removed domain.
    if domain.verified and not reverify:
        return {**domain_view(domain), 'success': True, 'reason': None, 'message': 'Already verified. Use Re-verify for a fresh check.'}
    if reverify and not domain.verified:
        raise failure(409, 'verification_required', 'Verify this domain first before requesting a recheck.')
    if not domain.verified and domain.token_expires_at <= utcnow():
        raise failure(410, 'token_expired', 'This verification token has expired. Remove this domain and add it again for a fresh token.')
    domain.verification_method = method
    domain.last_verification_at = utcnow()
    try:
        await check_proof(domain, method)
    except VerificationError as exc:
        domain.verification_status = 'needs_reverification' if domain.verified else 'failed'
        domain.last_verification_error = exc.reason
        await db.commit()
        return {**domain_view(domain), 'success': False, 'reason': exc.reason, 'message': exc.message}
    domain.verified = True
    domain.verification_status = 'verified'
    domain.verified_at = domain.verified_at or utcnow()
    domain.last_verification_error = None
    if domain.monitoring_enabled and not domain.next_scan_at:
        domain.next_scan_at = utcnow()
    await db.commit()
    return {**domain_view(domain), 'success': True, 'reason': None, 'message': 'Ownership verified. Advanced scans are unlocked for this domain and its subdomains.'}


def domain_router(get_current_user, serialize_scan):
    router = APIRouter()

    @router.post('/domains', status_code=201)
    async def add_domain(body: DomainIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        try:
            host = normalize_domain(body.domain, apex_only=True)
        except VerificationError as exc:
            raise failure(400, exc.reason, exc.message)
        domain = Domain(user_id=user['id'], domain=host, verification_token=secrets.token_urlsafe(32),
            verification_status='pending', token_expires_at=utcnow() + timedelta(days=7),
            monitoring_enabled=False, next_scan_at=None)
        db.add(domain)
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            if getattr(exc.orig, 'sqlstate', None) == '23505' or getattr(exc.orig, 'pgcode', None) == '23505':
                raise failure(409, 'domain_already_claimed', 'This domain has already been added or claimed by another account. Each domain can have only one owner.')
            raise
        return domain_view(domain)

    @router.get('/domains')
    async def list_domains(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        domains = (await db.execute(select(Domain).where(Domain.user_id == user['id']).order_by(Domain.domain))).scalars().all()
        out = []
        for d in domains:
            scan = (await db.execute(select(Scan).where(Scan.user_id == user['id'], Scan.target == d.domain).order_by(Scan.created_at.desc()).limit(1))).scalar_one_or_none()
            out.append({**domain_view(d), 'monitoring_enabled': d.monitoring_enabled,
                'email_alerts_enabled': d.email_alerts_enabled,
                'next_scan_at': d.next_scan_at.isoformat() if d.verified and d.monitoring_enabled and d.next_scan_at else None,
                'last_scheduled_at': d.last_scheduled_at.isoformat() if d.last_scheduled_at else None,
                'scan_in_progress': bool(d.scan_lock_until and d.scan_lock_until > utcnow()),
                'last_scan_error': d.last_scan_error,
                'last_scan': serialize_scan(scan, include_checks=True) if scan else None})
        return out

    @router.get('/domains/{domain_id}')
    async def get_domain(domain_id: uuid.UUID, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        return domain_view(await owned_domain(db, domain_id, user['id']))

    @router.post('/domains/{domain_id}/verify')
    async def verify(domain_id: uuid.UUID, body: VerifyIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        return await attempt(db, await owned_domain(db, domain_id, user['id'], lock=True), body.method)

    @router.post('/domains/{domain_id}/reverify')
    async def reverify(domain_id: uuid.UUID, body: VerifyIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        return await attempt(db, await owned_domain(db, domain_id, user['id'], lock=True), body.method, reverify=True)

    @router.delete('/domains/{domain_id}')
    async def remove(domain_id: uuid.UUID, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        await db.delete(await owned_domain(db, domain_id, user['id'], lock=True))
        await db.commit()
        return {'ok': True}

    return router