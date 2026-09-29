"""Authenticated platform cron; only never-verified expired domains are purged."""
import logging
import os
import secrets
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from database import AsyncSessionLocal
from models import CronDelivery, Domain, utcnow

router = APIRouter()
logger = logging.getLogger(__name__)


async def cleanup_expired(run_id):
    try:
        async with AsyncSessionLocal() as db:
            delivery = (await db.execute(select(CronDelivery).where(CronDelivery.run_id == run_id).with_for_update())).scalar_one()
            if delivery.status == 'completed':
                return
            result = await db.execute(delete(Domain).where(Domain.verified.is_(False), Domain.verified_at.is_(None), Domain.token_expires_at <= utcnow()))
            delivery.deleted_count = result.rowcount
            delivery.status, delivery.finished_at = 'completed', utcnow()
            await db.execute(delete(CronDelivery).where(CronDelivery.created_at < utcnow() - timedelta(days=30), CronDelivery.run_id != run_id))
            await db.commit()
            logger.info('Domain cleanup complete: %s expired unverified domains removed', result.rowcount)
    except Exception:
        logger.exception('Domain cleanup failed')
        async with AsyncSessionLocal() as db:
            delivery = await db.get(CronDelivery, run_id)
            if delivery:
                delivery.status = 'failed'
                await db.commit()


@router.post('/cron/domain-cleanup', status_code=202)
async def enqueue_cleanup(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    expected = os.environ['WEBHOOK_CRON_SECRET']
    provided = request.headers.get('authorization', '')
    if not provided.startswith('Bearer ') or not secrets.compare_digest(provided[7:].encode('utf-8'), expected.encode('utf-8')):
        raise HTTPException(401, detail='Invalid cron authorization')
    try:
        body = await request.json()
        if not isinstance(body, dict) or body.get('event') != 'schedule.triggered':
            raise ValueError()
        run_id = request.headers.get('x-webhook-id') or body.get('run_id')
        if not isinstance(run_id, str) or not run_id.strip() or len(run_id) > 255:
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(400, detail='Invalid schedule envelope')
    async with AsyncSessionLocal() as db:
        result = await db.execute(insert(CronDelivery).values(run_id=run_id, status='queued', deleted_count=0, created_at=utcnow()).on_conflict_do_nothing(index_elements=['run_id']).returning(CronDelivery.run_id))
        accepted = result.scalar_one_or_none() is not None
        if not accepted:
            delivery = await db.get(CronDelivery, run_id)
            accepted = delivery.status == 'failed' or (delivery.status == 'queued' and delivery.created_at < utcnow() - timedelta(minutes=10))
            if accepted:
                delivery.status, delivery.created_at = 'queued', utcnow()
        await db.commit()
    if accepted:
        background.add_task(cleanup_expired, run_id)
    return {'accepted': True, 'duplicate': not accepted}