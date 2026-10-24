"""Create Phase 1 domain tables."""

from alembic import op
import sqlalchemy as sa

revision = "0001_phase1_domain"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Existing local databases are created by src/db/schema.sql. This migration
    # is the canonical schema for new environments and future migrations.
    op.create_table("transactions", sa.Column("id", sa.String(), primary_key=True), sa.Column("portfolio_id", sa.String(), nullable=False), sa.Column("symbol", sa.String(), nullable=False), sa.Column("side", sa.String(), nullable=False), sa.Column("quantity", sa.Float(), nullable=False), sa.Column("price", sa.Float(), nullable=False), sa.Column("executed_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"))
    op.create_table("notes", sa.Column("id", sa.String(), primary_key=True), sa.Column("user_id", sa.String(), nullable=False), sa.Column("symbol", sa.String()), sa.Column("body", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"))
    op.create_table("alerts", sa.Column("id", sa.String(), primary_key=True), sa.Column("user_id", sa.String(), nullable=False), sa.Column("symbol", sa.String(), nullable=False), sa.Column("rule", sa.String(), nullable=False), sa.Column("threshold", sa.Float(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"))


def downgrade():
    op.drop_table("alerts")
    op.drop_table("notes")
    op.drop_table("transactions")
