"""Initial migration with Users, Reports, ReportImages

Revision ID: 357b0adffc5f
Revises:
Create Date: 2026-01-10 16:32:15.165719

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '357b0adffc5f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users Tabelle erstellen (mit is_admin)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('first_name', sa.String(length=15), nullable=True),
        sa.Column('last_name', sa.String(length=15), nullable=True),
        sa.Column('password_hash', sa.String(length=128), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Reports Tabelle erstellen
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # ReportImages Tabelle erstellen
    op.create_table('report_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('report_images')
    op.drop_table('reports')
    op.drop_table('users')
