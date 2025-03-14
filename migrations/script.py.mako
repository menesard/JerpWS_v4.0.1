"""Add user roles and operation relationships

Revision ID: user_roles_and_operations
Revises: transaction_editing_fields
Create Date: 2025-03-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'user_roles_and_operations'
down_revision = 'transaction_editing_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Migration kontrolü için tablo yapısını kontrol et
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # User tablosu sütunlarını kontrol et
    user_columns = [column['name'] for column in inspector.get_columns('users')]

    # User tablosuna role alanı ekleme
    if 'role' not in user_columns:
        op.add_column('users', sa.Column('role', sa.String(20), server_default='staff', nullable=False))

    if 'created_by_id' not in user_columns:
        op.add_column('users', sa.Column('created_by_id', sa.Integer(), nullable=True))

    if 'created_at' not in user_columns:
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Foreign key oluştur (self-referential)
    try:
        op.create_foreign_key('fk_users_created_by', 'users', 'users', ['created_by_id'], ['id'])
    except Exception:
        pass  # Foreign key zaten varsa hata vermesin

    # Operation tablosu sütunlarını kontrol et
    operation_columns = [column['name'] for column in inspector.get_columns('operations')]

    # Operation tablosuna user_id alanı ekleme
    if 'user_id' not in operation_columns:
        op.add_column('operations', sa.Column('user_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key('fk_operations_user', 'operations', 'users', ['user_id'], ['id'])
        except Exception:
            pass  # Foreign key zaten varsa hata vermesin

    # CustomerTransaction tablosu sütunlarını kontrol et
    transaction_columns = [column['name'] for column in inspector.get_columns('customer_transactions')]

    # CustomerTransaction tablosuna created_by_user_id alanı ekleme
    if 'created_by_user_id' not in transaction_columns:
        op.add_column('customer_transactions', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key('fk_transactions_created_by', 'customer_transactions', 'users', ['created_by_user_id'], ['id'])
        except Exception:
            pass  # Foreign key zaten varsa hata vermesin

    # Admin kullanıcıların rolünü 'admin' olarak güncelle
    op.execute("UPDATE users SET role = 'admin' WHERE is_admin = true")

def downgrade():
    # Değişiklikleri geri alma işlemleri burada olacak
    # Foreign key'leri kaldır
    try:
        op.drop_constraint('fk_transactions_created_by', 'customer_transactions', type_='foreignkey')
    except Exception:
        pass

    try:
        op.drop_constraint('fk_operations_user', 'operations', type_='foreignkey')
    except Exception:
        pass

    try:
        op.drop_constraint('fk_users_created_by', 'users', type_='foreignkey')
    except Exception:
        pass

    # Alanları kaldır
    op.drop_column('customer_transactions', 'created_by_user_id')
    op.drop_column('operations', 'user_id')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'created_by_id')
    op.drop_column('users', 'role')