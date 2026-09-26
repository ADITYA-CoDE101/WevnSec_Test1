"""enable row level security + auth.users FK

Revision ID: b7c1f0a2d3e4
Revises: 9aa95ee97a93
Create Date: 2026-07-24
"""
from alembic import op

revision = "b7c1f0a2d3e4"
down_revision = "9aa95ee97a93"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE wevnsec.profiles ADD CONSTRAINT fk_profiles_auth_user "
        "FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE"
    )

    op.execute("ALTER TABLE wevnsec.profiles ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY profiles_select_own ON wevnsec.profiles FOR SELECT TO authenticated USING (auth.uid() = id)")
    op.execute("CREATE POLICY profiles_update_own ON wevnsec.profiles FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id)")

    op.execute("ALTER TABLE wevnsec.scans ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY scans_select_own ON wevnsec.scans FOR SELECT TO authenticated USING (auth.uid() = user_id)")
    op.execute("CREATE POLICY scans_insert_own ON wevnsec.scans FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id)")

    op.execute("ALTER TABLE wevnsec.domains ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY domains_all_own ON wevnsec.domains FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)")

    op.execute("ALTER TABLE wevnsec.alerts ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY alerts_select_own ON wevnsec.alerts FOR SELECT TO authenticated USING (auth.uid() = user_id)")
    op.execute("CREATE POLICY alerts_update_own ON wevnsec.alerts FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)")


def downgrade() -> None:
    for table, policies in {
        "profiles": ["profiles_select_own", "profiles_update_own"],
        "scans": ["scans_select_own", "scans_insert_own"],
        "domains": ["domains_all_own"],
        "alerts": ["alerts_select_own", "alerts_update_own"],
    }.items():
        for p in policies:
            op.execute(f"DROP POLICY IF EXISTS {p} ON wevnsec.{table}")
        op.execute(f"ALTER TABLE wevnsec.{table} DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE wevnsec.profiles DROP CONSTRAINT IF EXISTS fk_profiles_auth_user")
