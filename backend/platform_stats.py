from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from check_catalog import CHECK_CATALOG
from database import get_db
from models import utcnow

router = APIRouter()


@router.get('/stats')
async def stats(response: Response, db: AsyncSession = Depends(get_db)):
    # One statement gives a consistent snapshot; findings are observations, not
    # unique CVEs, customers, or remediations. A repeat scan may repeat a finding.
    row = (await db.execute(text('''
        SELECT s.*, f.*, d.* FROM
        (SELECT count(*) AS scans, count(DISTINCT target) AS unique_domains,
                max(created_at) AS last_scan_at FROM wevnsec.scans) s
        CROSS JOIN (SELECT count(*) FILTER (WHERE c->>'status' IN ('fail','warn')) AS findings,
                           count(*) FILTER (WHERE c->>'status' = 'fail') AS vulns,
                           count(*) FILTER (WHERE c->>'status' = 'warn') AS warnings
                    FROM wevnsec.scans, jsonb_array_elements(checks) AS c) f
        CROSS JOIN (SELECT count(*) AS docs_count,
                           count(*) FILTER (WHERE coverage='automated') AS automated_docs_count,
                           count(*) FILTER (WHERE coverage='educational') AS educational_docs_count
                    FROM wevnsec.documentation WHERE published=true) d
    '''))).mappings().one()
    result = dict(row)
    result['last_scan_at'] = row['last_scan_at'].isoformat() if row['last_scan_at'] else None
    result.update(checks_supported=len(CHECK_CATALOG), updated_at=utcnow().isoformat())
    response.headers['Cache-Control'] = 'no-store'
    return result