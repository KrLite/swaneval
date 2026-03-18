"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-03-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    user_role = postgresql.ENUM('admin', 'data_manager', 'evaluator', 'guest', name='userrole', create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)

    model_type = postgresql.ENUM('local', 'huggingface', 'api', name='modeltype', create_type=False)
    model_type.create(op.get_bind(), checkfirst=True)

    task_status = postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'paused', name='taskstatus', create_type=False)
    task_status.create(op.get_bind(), checkfirst=True)

    dataset_source = postgresql.ENUM('preset', 'huggingface', 'custom', 'server_path', name='datasetsource', create_type=False)
    dataset_source.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'data_manager', 'evaluator', 'guest', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create model_configs table
    op.create_table(
        'model_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('model_type', sa.Enum('local', 'huggingface', 'api', name='modeltype'), nullable=True),
        sa.Column('path', sa.Text(), nullable=True),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_configs_id'), 'model_configs', ['id'], unique=False)
    op.create_index(op.f('ix_model_configs_name'), 'model_configs', ['name'], unique=False)

    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('source', sa.Enum('preset', 'huggingface', 'custom', 'server_path', name='datasetsource'), nullable=True),
        sa.Column('path', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_datasets_id'), 'datasets', ['id'], unique=False)
    op.create_index(op.f('ix_datasets_name'), 'datasets', ['name'], unique=False)

    # Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_config_id', sa.Integer(), nullable=True),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('generation_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dataset_args', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('eval_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', 'paused', name='taskstatus'), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
        sa.ForeignKeyConstraint(['model_config_id'], ['model_configs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_id'), 'evaluations', ['id'], unique=False)

    # Create evaluation_results table
    op.create_table(
        'evaluation_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('expected_output', sa.Text(), nullable=True),
        sa.Column('actual_output', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_results_id'), 'evaluation_results', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_evaluation_results_id'), table_name='evaluation_results')
    op.drop_table('evaluation_results')
    op.drop_index(op.f('ix_evaluations_id'), table_name='evaluations')
    op.drop_table('evaluations')
    op.drop_index(op.f('ix_datasets_name'), table_name='datasets')
    op.drop_index(op.f('ix_datasets_id'), table_name='datasets')
    op.drop_table('datasets')
    op.drop_index(op.f('ix_model_configs_name'), table_name='model_configs')
    op.drop_index(op.f('ix_model_configs_id'), table_name='model_configs')
    op.drop_table('model_configs')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS datasetsource')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS modeltype')
    op.execute('DROP TYPE IF EXISTS userrole')