"""baseline users table

Revision ID: 7c9e6b2eb1b4
Revises: 
Create Date: 2026-06-15 12:53:35.063632

"""
# flake8: noqa
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c9e6b2eb1b4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Baseline: erzeugt die bestehende users-Tabelle. Auf bereits
    # vorhandenen Datenbanken (Dev/Prod) wird diese Revision nur
    # gestampt (flask db stamp), nicht ausgeführt. Frische
    # Installationen legen die Tabelle hierüber an.
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("first_name", sa.String(length=15), nullable=True),
        sa.Column("last_name", sa.String(length=15), nullable=True),
        sa.Column("password_hash", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )


def downgrade():
    op.drop_table("users")
