"""Persistent auth cooldown, isolated from application/public records."""
from alembic import op
import sqlalchemy as sa

revision = 'd9e3f5a7b012'
down_revision = 'c8d2e4f6a901'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('login_throttle',
        sa.Column('identifier', sa.String(64), primary_key=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cooldown_until', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='wevnsec')
    op.execute('ALTER TABLE wevnsec.login_throttle ENABLE ROW LEVEL SECURITY')
    # No client policies: only the backend database role may access throttles.
    op.create_index('ix_login_throttle_updated', 'login_throttle', ['updated_at'], schema='wevnsec')


def downgrade():
    op.drop_table('login_throttle', schema='wevnsec')