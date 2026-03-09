"""add progress tracking tables and fields

Revision ID: 2a3b4c5d6e7f
Revises: 1c05a24535a5
Create Date: 2026-01-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a3b4c5d6e7f'
down_revision = '1c05a24535a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建 path_modules 表
    op.create_table(
        'path_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learning_path_id', sa.Integer(), nullable=False),
        sa.Column('phase_index', sa.Integer(), nullable=False),
        sa.Column('phase_title', sa.String(200), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('module_key', sa.String(100), nullable=False),
        sa.Column('module_name', sa.String(200), nullable=False),
        sa.Column('estimated_hours', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_path_modules_id', 'path_modules', ['id'], unique=False)
    op.create_index('ix_path_modules_learning_path_id', 'path_modules', ['learning_path_id'], unique=False)

    # 2. 创建 progresstriggertype 枚举类型（如果不存在）
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE progresstriggertype AS ENUM ('manual', 'conversation', 'task', 'time', 'quiz', 'ai', 'system');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 3. 创建 progress_history 表（使用已存在的 progressstatus 枚举）
    op.execute("""
        CREATE TABLE progress_history (
            id SERIAL PRIMARY KEY,
            progress_id INTEGER NOT NULL REFERENCES learning_progress(id) ON DELETE CASCADE,
            old_percentage FLOAT NOT NULL,
            new_percentage FLOAT NOT NULL,
            old_status progressstatus,
            new_status progressstatus,
            trigger_type progresstriggertype NOT NULL,
            trigger_source VARCHAR(200),
            trigger_detail TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    op.create_index('ix_progress_history_id', 'progress_history', ['id'], unique=False)
    op.create_index('ix_progress_history_progress_id', 'progress_history', ['progress_id'], unique=False)

    # 4. 修改 learning_progress 表，添加新字段
    op.add_column('learning_progress', sa.Column('path_module_id', sa.Integer(), nullable=True))
    op.add_column('learning_progress', sa.Column('actual_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('learning_progress', sa.Column('notes', sa.Text(), nullable=True))

    # 添加外键约束
    op.create_foreign_key(
        'fk_learning_progress_path_module',
        'learning_progress',
        'path_modules',
        ['path_module_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_learning_progress_path_module_id', 'learning_progress', ['path_module_id'], unique=False)


def downgrade() -> None:
    # 删除外键和索引
    op.drop_index('ix_learning_progress_path_module_id', table_name='learning_progress')
    op.drop_constraint('fk_learning_progress_path_module', 'learning_progress', type_='foreignkey')

    # 删除 learning_progress 的新字段
    op.drop_column('learning_progress', 'notes')
    op.drop_column('learning_progress', 'actual_hours')
    op.drop_column('learning_progress', 'path_module_id')

    # 删除 progress_history 表
    op.drop_index('ix_progress_history_progress_id', table_name='progress_history')
    op.drop_index('ix_progress_history_id', table_name='progress_history')
    op.drop_table('progress_history')

    # 删除 path_modules 表
    op.drop_index('ix_path_modules_learning_path_id', table_name='path_modules')
    op.drop_index('ix_path_modules_id', table_name='path_modules')
    op.drop_table('path_modules')

    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS progresstriggertype')