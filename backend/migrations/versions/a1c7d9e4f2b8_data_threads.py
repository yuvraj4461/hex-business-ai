"""data threads for "Ask Your Data"

Revision ID: a1c7d9e4f2b8
Revises: 08e41455a428
Create Date: 2026-09-01 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c7d9e4f2b8'
down_revision: Union[str, Sequence[str], None] = '08e41455a428'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'data_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_data_threads_id'), 'data_threads', ['id'], unique=False)
    op.create_index(
        op.f('ix_data_threads_organization_id'),
        'data_threads', ['organization_id'], unique=False,
    )
    op.create_index(
        op.f('ix_data_threads_user_id'), 'data_threads', ['user_id'], unique=False,
    )

    op.create_table(
        'data_thread_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('spec', sa.JSON(), nullable=True),
        sa.Column('spec_label', sa.String(length=200), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('degraded', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['thread_id'], ['data_threads.id'], ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_data_thread_messages_id'),
        'data_thread_messages', ['id'], unique=False,
    )
    op.create_index(
        op.f('ix_data_thread_messages_thread_id'),
        'data_thread_messages', ['thread_id'], unique=False,
    )
    op.create_index(
        op.f('ix_data_thread_messages_organization_id'),
        'data_thread_messages', ['organization_id'], unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_data_thread_messages_organization_id'),
        table_name='data_thread_messages',
    )
    op.drop_index(
        op.f('ix_data_thread_messages_thread_id'),
        table_name='data_thread_messages',
    )
    op.drop_index(
        op.f('ix_data_thread_messages_id'), table_name='data_thread_messages',
    )
    op.drop_table('data_thread_messages')
    op.drop_index(op.f('ix_data_threads_user_id'), table_name='data_threads')
    op.drop_index(
        op.f('ix_data_threads_organization_id'), table_name='data_threads',
    )
    op.drop_index(op.f('ix_data_threads_id'), table_name='data_threads')
    op.drop_table('data_threads')
