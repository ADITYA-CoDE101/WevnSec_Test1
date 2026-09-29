"""Editable reference library and protected administrative roles."""
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = 'f1a5b7c9d014'
down_revision = 'e0f4a6b8c013'
branch_labels = depends_on = None


def upgrade():
    table = op.create_table('documentation',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('slug', sa.String(120), nullable=False, unique=True),
        sa.Column('title', sa.String(180), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('category', sa.String(80), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('coverage', sa.String(24), nullable=False),
        sa.Column('check_ids', JSONB(), nullable=False),
        *[sa.Column(field, sa.Text(), nullable=False) for field in ('explanation','impact','mitigation','validation','limitations','reference_url')],
        sa.Column('published', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), schema='wevnsec')
    op.create_index('ix_documentation_published', 'documentation', ['published'], schema='wevnsec')
    op.execute('ALTER TABLE wevnsec.documentation ENABLE ROW LEVEL SECURITY')
    op.execute('REVOKE ALL ON wevnsec.documentation FROM anon, authenticated')
    # Roles protecting documentation must not be writable via browser Supabase keys.
    op.execute('REVOKE UPDATE ON wevnsec.profiles FROM anon, authenticated')
    op.execute('GRANT UPDATE (name) ON wevnsec.profiles TO authenticated')
    from docs_seed import ARTICLES
    now = datetime.now(timezone.utc)
    op.bulk_insert(table, [dict(a, id=str(uuid.uuid4()), version=1, created_at=now, updated_at=now) for a in ARTICLES])


def downgrade():
    op.drop_index('ix_documentation_published', table_name='documentation', schema='wevnsec')
    op.drop_table('documentation', schema='wevnsec')
    # Keep role-write protection; rollback must not reopen privilege escalation.