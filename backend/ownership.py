from fastapi import HTTPException
from sqlalchemy import select

from domain_validation import apex_domain
from models import Domain


async def require_ownership(db, user_id, host):
    """A previously verified apex authorizes its entire subdomain tree."""
    apex = apex_domain(host)
    domain = (await db.execute(select(Domain).where(
        Domain.user_id == user_id, Domain.domain == apex, Domain.verified.is_(True)
    ))).scalar_one_or_none() if user_id else None
    if not domain:
        raise HTTPException(403, detail={'reason': 'ownership_required', 'message': f'Verify ownership of {apex} to run advanced scans. Instant Scan remains available.'})
    return domain