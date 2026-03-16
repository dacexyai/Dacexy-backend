"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('organizations',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('plan_tier', sa.String(50), default='free'),
        sa.Column('credits_balance', sa.BigInteger(), default=0),
        sa.Column('monthly_ai_calls', sa.Integer(), default=0),
        sa.Column('monthly_ai_calls_reset', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('api_keys',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.Text(), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('refresh_tokens',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=False), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token_hash', sa.Text(), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('conversation_sessions',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(500), default='New Chat'),
        sa.Column('messages', sa.JSON(), default=list),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('audit_events',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('subscriptions',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), unique=True),
        sa.Column('plan_tier', sa.String(50), default='free'),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('razorpay_subscription_id', sa.String(255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('invoices',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(10), default='INR'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('razorpay_order_id', sa.String(255), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('usage_records',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('feature', sa.String(100), nullable=False),
        sa.Column('quantity', sa.Integer(), default=1),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('generated_images',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('generated_videos',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('generated_websites',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('memory_entries',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table('ai_tasks',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=False), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), nullable=True),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('input_data', sa.JSON(), default=dict),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    for table in ['ai_tasks', 'memory_entries', 'generated_websites', 'generated_videos',
                  'generated_images', 'usage_records', 'invoices', 'subscriptions',
                  'audit_events', 'conversation_sessions', 'refresh_tokens',
                  'api_keys', 'users', 'organizations']:
        op.drop_table(table)
