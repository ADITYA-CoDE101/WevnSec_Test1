from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from check_catalog import CHECK_CATALOG
from database import get_db
from models import Documentation


def serialize_article(article):
    fields = ('id','slug','title','summary','category','severity','coverage','check_ids','explanation','impact','mitigation','validation','limitations','reference_url','published','version')
    return {**{f: getattr(article, f) for f in fields}, 'created_at': article.created_at.isoformat(), 'updated_at': article.updated_at.isoformat()}


def documentation_router(get_current_user):
    router = APIRouter()

    @router.get('/docs/catalog')
    async def catalog():
        return CHECK_CATALOG

    @router.get('/docs')
    async def articles(q: str = Query('', max_length=200), coverage: Literal['automated','educational'] | None = None, db: AsyncSession = Depends(get_db)):
        query = select(Documentation).where(Documentation.published.is_(True))
        if coverage:
            query = query.where(Documentation.coverage == coverage)
        if q.strip():
            needle = '%' + q.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_','\\_') + '%'
            query = query.where(or_(*[getattr(Documentation, f).ilike(needle, escape='\\') for f in ('title','summary','category','explanation','mitigation')]))
        rows = (await db.execute(query.order_by(Documentation.title))).scalars().all()
        return [serialize_article(a) for a in rows]

    @router.get('/docs/{slug}')
    async def article(slug: str, db: AsyncSession = Depends(get_db)):
        row = (await db.execute(select(Documentation).where(Documentation.slug == slug, Documentation.published.is_(True)))).scalar_one_or_none()
        if not row:
            raise HTTPException(404, detail='This article is not available. It may have been unpublished or removed.')
        return serialize_article(row)

    return router