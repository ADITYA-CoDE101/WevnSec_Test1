import uuid
from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from check_catalog import CHECK_CATALOG, CHECK_IDS
from database import get_db
from models import Documentation, utcnow


class ArticleInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    slug: str = Field(pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', max_length=120)
    title: str = Field(min_length=3, max_length=180)
    summary: str = Field(min_length=10, max_length=600)
    category: str = Field(min_length=2, max_length=80)
    severity: Literal['info','low','medium','high','critical']
    coverage: Literal['automated','educational']
    check_ids: list[str] = Field(default_factory=list, max_length=30)
    explanation: str = Field(min_length=10, max_length=20000)
    impact: str = Field(min_length=5, max_length=10000)
    mitigation: str = Field(min_length=10, max_length=20000)
    validation: str = Field(min_length=5, max_length=10000)
    limitations: str = Field(min_length=5, max_length=10000)
    reference_url: str = Field(default='', max_length=2000)
    published: bool = False
    version: int | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def validate_coverage(self):
        if self.slug in {'manage', 'catalog'}:
            raise ValueError('That URL slug is reserved. Choose another slug.')
        if len(set(self.check_ids)) != len(self.check_ids) or any(c not in CHECK_IDS for c in self.check_ids):
            raise ValueError('Choose unique check IDs from the implemented scanner catalog.')
        if self.coverage == 'automated' and not self.check_ids:
            raise ValueError('Automated coverage requires at least one implemented check.')
        if self.coverage == 'educational' and self.check_ids:
            raise ValueError('Reference-only articles cannot claim automated check coverage.')
        if self.reference_url:
            try:
                url = urlsplit(self.reference_url)
                if url.scheme != 'https' or not url.hostname or url.username or url.password:
                    raise ValueError()
            except ValueError:
                raise ValueError('Reference links must be valid public HTTPS URLs without credentials.')
        return self


def serialize_article(article):
    fields = ('id','slug','title','summary','category','severity','coverage','check_ids','explanation','impact','mitigation','validation','limitations','reference_url','published','version')
    return {**{f: getattr(article, f) for f in fields}, 'created_at': article.created_at.isoformat(), 'updated_at': article.updated_at.isoformat()}


def documentation_router(get_current_user):
    router = APIRouter()

    async def admin(user=Depends(get_current_user)):
        if user['profile'].role != 'admin':
            raise HTTPException(403, detail='Administrator access is required to manage documentation.')
        return user

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

    @router.get('/admin/docs')
    async def admin_list(user=Depends(admin), db: AsyncSession = Depends(get_db)):
        rows = (await db.execute(select(Documentation).order_by(Documentation.updated_at.desc()))).scalars().all()
        return [serialize_article(a) for a in rows]

    @router.get('/admin/docs/{article_id}')
    async def admin_get(article_id: uuid.UUID, user=Depends(admin), db: AsyncSession = Depends(get_db)):
        row = await db.get(Documentation, str(article_id))
        if not row:
            raise HTTPException(404, detail='Article not found')
        return serialize_article(row)

    async def save(db, article):
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(409, detail='That article URL is already used. Choose a different slug.')
        return serialize_article(article)

    @router.post('/admin/docs', status_code=201)
    async def create(body: ArticleInput, user=Depends(admin), db: AsyncSession = Depends(get_db)):
        row = Documentation(**body.model_dump(exclude={'version'}))
        db.add(row)
        return await save(db, row)

    @router.put('/admin/docs/{article_id}')
    async def update(article_id: uuid.UUID, body: ArticleInput, user=Depends(admin), db: AsyncSession = Depends(get_db)):
        row = (await db.execute(select(Documentation).where(Documentation.id == str(article_id)).with_for_update())).scalar_one_or_none()
        if not row:
            raise HTTPException(404, detail='Article not found')
        if body.version != row.version:
            raise HTTPException(409, detail='This article changed since you opened it. Reload before saving to avoid overwriting another edit.')
        for field, value in body.model_dump(exclude={'version'}).items():
            setattr(row, field, value)
        row.version += 1
        row.updated_at = utcnow()
        return await save(db, row)

    @router.delete('/admin/docs/{article_id}')
    async def remove(article_id: uuid.UUID, user=Depends(admin), db: AsyncSession = Depends(get_db)):
        row = await db.get(Documentation, str(article_id))
        if not row:
            raise HTTPException(404, detail='Article not found')
        await db.delete(row)
        await db.commit()
        return {'ok': True}

    return router