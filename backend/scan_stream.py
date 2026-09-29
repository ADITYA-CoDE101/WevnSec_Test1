"""Request-scoped live scan events, emitted only when real probes return."""
import asyncio
import json
import logging
from contextvars import ContextVar

from fastapi import HTTPException

from database import AsyncSessionLocal
from monitoring import record_scan

reporter = ContextVar('scan_reporter', default=None)


def emit_check(check):
    queue = reporter.get()
    if queue is not None:
        queue.put_nowait({'type': 'check', 'check': check})


async def stream_scan(host, user_id, advanced, run_scan, serialize_scan):
    queue = asyncio.Queue()

    async def execute():
        token = reporter.set(queue)
        try:
            scan = await run_scan(host, user_id, advanced=advanced)
            async with AsyncSessionLocal() as db:
                await record_scan(db, scan)
            queue.put_nowait({'type': 'complete', 'report': serialize_scan(scan)})
        except HTTPException as exc:
            queue.put_nowait({'type': 'error', 'message': exc.detail if isinstance(exc.detail, str) else exc.detail.get('message', 'Scan could not complete.')})
        except Exception:
            logging.getLogger(__name__).exception('Live scan failed')
            queue.put_nowait({'type': 'error', 'message': 'The scan could not be completed or saved. Please try again.'})
        finally:
            reporter.reset(token)

    task = asyncio.create_task(execute())
    try:
        yield json.dumps({'type': 'started', 'target': host, 'message': 'Running TLS and HTTP probes'}) + '\n'
        while True:
            event = await queue.get()
            yield json.dumps(event) + '\n'
            if event['type'] in ('complete', 'error'):
                break
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)