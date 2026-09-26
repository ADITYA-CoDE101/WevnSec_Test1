"""Complete ownership verification, global uniqueness, and cleanup deliveries.

Existing records receive a fresh seven-day window, not immediate deletion.
Duplicate claims must be resolved explicitly before this migration is run.
"""
import secrets
from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa

revision = 'e0f4a6b8c013'
down_revision = 'd9e3f5a7b012'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    duplicates = bind.execute(sa.text('SELECT domain FROM wevnsec.domains GROUP BY domain HAVING count(*) > 1')).scalars().all()
    if duplicates:
        raise RuntimeError('Resolve duplicate domain claims with the owner before migrating: ' + ', '.join(duplicates))
    columns = {c['name'] for c in sa.inspect(bind).get_columns('domains', schema='wevnsec')}
    additions = [
        sa.Column('verification_method', sa.String(32)), sa.Column('verification_token', sa.String(128)),
        sa.Column('verified_at', sa.DateTime(timezone=True)), sa.Column('verification_status', sa.String(32)),
        sa.Column('token_expires_at', sa.DateTime(timezone=True)), sa.Column('last_verification_at', sa.DateTime(timezone=True)),
        sa.Column('last_verification_error', sa.Text()),
    ]
    for column in additions:
        if column.name not in columns:
            op.add_column('domains', column, schema='wevnsec')
    now = datetime.now(timezone.utc)
    for row in bind.execute(sa.text('SELECT id, verified, verification_token, token_expires_at FROM wevnsec.domains')).mappings():
        bind.execute(sa.text('UPDATE wevnsec.domains SET verification_token=:token, token_expires_at=:expiry, verification_status=:status, verified_at=CASE WHEN verified THEN COALESCE(verified_at,:now) ELSE verified_at END WHERE id=:id'),
            {'token': row['verification_token'] or secrets.token_urlsafe(32), 'expiry': row['token_expires_at'] or now + timedelta(days=7),
             'status': 'verified' if row['verified'] else 'pending', 'id': row['id'], 'now': now})
    for name in ('verification_token', 'verification_status', 'token_expires_at'):
        op.alter_column('domains', name, nullable=False, schema='wevnsec')
    constraints = {c['name'] for c in sa.inspect(bind).get_unique_constraints('domains', schema='wevnsec')}
    if 'uq_domains_domain' not in constraints:
        op.create_unique_constraint('uq_domains_domain', 'domains', ['domain'], schema='wevnsec')
    op.create_check_constraint('ck_domains_verification_status', 'domains', "verification_status IN ('pending','verified','failed','needs_reverification')", schema='wevnsec')
    op.create_index('ix_domains_unverified_expiry', 'domains', ['token_expires_at'], schema='wevnsec', postgresql_where=sa.text('verified = false'))
    # Browser credentials may read their own rows, but must not self-assert proof.
    op.execute('DROP POLICY IF EXISTS domains_all_own ON wevnsec.domains')
    op.execute('CREATE POLICY domains_select_own ON wevnsec.domains FOR SELECT TO authenticated USING (auth.uid() = user_id)')
    op.execute('REVOKE INSERT, UPDATE, DELETE ON wevnsec.domains FROM anon, authenticated')
    op.create_table('cron_deliveries', sa.Column('run_id', sa.String(255), primary_key=True),
        sa.Column('status', sa.String(24), nullable=False), sa.Column('deleted_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('finished_at', sa.DateTime(timezone=True)), schema='wevnsec')
    op.execute('ALTER TABLE wevnsec.cron_deliveries ENABLE ROW LEVEL SECURITY')
    op.execute('REVOKE ALL ON wevnsec.cron_deliveries FROM anon, authenticated')


def downgrade():
    op.drop_table('cron_deliveries', schema='wevnsec')
    op.execute('DROP POLICY IF EXISTS domains_select_own ON wevnsec.domains')
    op.execute('CREATE POLICY domains_all_own ON wevnsec.domains FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)')
    op.drop_index('ix_domains_unverified_expiry', table_name='domains', schema='wevnsec')
    op.drop_constraint('ck_domains_verification_status', 'domains', schema='wevnsec')
    op.drop_constraint('uq_domains_domain', 'domains', schema='wevnsec')
    for name in ('verification_method','verification_token','verified_at','verification_status','token_expires_at','last_verification_at','last_verification_error'):
        op.drop_column('domains', name, schema='wevnsec')