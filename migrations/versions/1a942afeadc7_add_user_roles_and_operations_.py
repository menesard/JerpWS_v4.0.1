"""Add user roles and operations relationships

Revision ID: 1a942afeadc7
Revises: transaction_editing_fields
Create Date: [otomatik_tarih]

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '1a942afeadc7'
down_revision = 'transaction_editing_fields'
branch_labels = None
depends_on = None

def upgrade():
    # SQLAlchemy 1.4+ ile uyumlu sütun kontrolü
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # User tablosuna rol alanını ekleyin
    user_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'role' not in user_columns:
        op.add_column('users', sa.Column('role', sa.String(20), server_default='staff', nullable=False))

    if 'created_by_id' not in user_columns:
        op.add_column('users', sa.Column('created_by_id', sa.Integer(), nullable=True))

    if 'created_at' not in user_columns:
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Operation tablosuna user_id alanını ekleyin
    operation_columns = [c['name'] for c in inspector.get_columns('operations')]
    if 'user_id' not in operation_columns:
        op.add_column('operations', sa.Column('user_id', sa.Integer(), nullable=True))

    # CustomerTransaction tablosuna created_by_user_id alanını ekleyin
    transaction_columns = [c['name'] for c in inspector.get_columns('customer_transactions')]
    if 'created_by_user_id' not in transaction_columns:
        op.add_column('customer_transactions', sa.Column('created_by_user_id', sa.Integer(), nullable=True))

    # Admin kullanıcıların rolünü güncelle
    op.execute("UPDATE users SET role = 'admin' WHERE is_admin = 1")

def downgrade():
    # SQLite'ta ALTER TABLE DROP COLUMN desteklenmiyor
    # Değişiklikleri geri almak için tabloyu yeniden oluşturmak gerekir
    pass