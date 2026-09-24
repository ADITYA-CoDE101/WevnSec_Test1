"""Durable daily monitoring and grade-drop email outbox. Public data untouched."""
from alembic import op
import sqlalchemy as sa

revision = 'c8d2e4f6a901'
down_revision = 'b7c1f0a2d3e4'
branch_labels = None
depends_on = None


def upgrade():
    domain_columns = [
        sa.Column('monitoring_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('email_alerts_enabled', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('next_scan_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now() + interval '24 hours'")),
        sa.Column('last_scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('scan_lock_until', sa.DateTime(timezone=True)),
        sa.Column('scan_lock_token', sa.String(36)),
        sa.Column('last_scan_error', sa.Text()),
    ]
    for column in domain_columns:
        op.add_column('domains', column, schema='wevnsec')
    op.create_index('ix_domains_schedule_due', 'domains', ['monitoring_enabled','next_scan_at'], schema='wevnsec')
    op.add_column('scans', sa.Column('source', sa.String(16), nullable=False, server_default='manual'), schema='wevnsec')
    alert_columns = [
        sa.Column('previous_grade', sa.String(4)), sa.Column('current_grade', sa.String(4)),
        sa.Column('previous_score', sa.Integer()), sa.Column('current_score', sa.Integer()),
        sa.Column('email_status', sa.String(24), nullable=False, server_default='disabled'),
        sa.Column('email_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('email_next_attempt_at', sa.DateTime(timezone=True)),
        sa.Column('email_sent_at', sa.DateTime(timezone=True)),
        sa.Column('email_provider_id', sa.String(255)),
        sa.Column('email_error', sa.Text()),
    ]
    for column in alert_columns:
        op.add_column('alerts', column, schema='wevnsec')
    op.create_index('ix_alerts_email_due', 'alerts', ['email_status','email_next_attempt_at'], schema='wevnsec')


def downgrade():
    op.drop_index('ix_alerts_email_due', table_name='alerts', schema='wevnsec')
    for name in ('email_error','email_provider_id','email_sent_at','email_next_attempt_at','email_attempts','email_status','current_score','previous_score','current_grade','previous_grade'):
        op.drop_column('alerts', name, schema='wevnsec')
    op.drop_column('scans', 'source', schema='wevnsec')
    op.drop_index('ix_domains_schedule_due', table_name='domains', schema='wevnsec')
    for name in ('last_scan_error','scan_lock_token','scan_lock_until','last_scheduled_at','next_scan_at','email_alerts_enabled','monitoring_enabled'):
        op.drop_column('domains', name, schema='wevnsec')