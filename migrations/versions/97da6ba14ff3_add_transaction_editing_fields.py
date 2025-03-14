"""Add transaction editing fields

Revision ID: transaction_editing_fields
Revises: pure_gold_calculations
Create Date: 2025-03-11 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlite3

# revision identifiers, used by Alembic.
revision = 'transaction_editing_fields'
down_revision = 'pure_gold_calculations'
branch_labels = None
depends_on = None

def column_exists(table_name, column_name):
    """Sütunun var olup olmadığını kontrol eder"""
    conn = op.get_bind()
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())

def upgrade():
    # Sütunları tek tek kontrol ederek ekle
    if not column_exists('customer_transactions', 'is_edited'):
        op.add_column('customer_transactions', sa.Column('is_edited', sa.Boolean(), nullable=True))

    if not column_exists('customer_transactions', 'edited_date'):
        op.add_column('customer_transactions', sa.Column('edited_date', sa.DateTime(), nullable=True))

    if not column_exists('customer_transactions', 'edited_by_user_id'):
        op.add_column('customer_transactions', sa.Column('edited_by_user_id', sa.Integer(), nullable=True))

    if not column_exists('customer_transactions', 'original_transaction_id'):
        op.add_column('customer_transactions', sa.Column('original_transaction_id', sa.Integer(), nullable=True))

    # Foreign key kısıtlamaları - SQLite'ta ALTER TABLE ile foreign key ekleyemiyoruz
    # Bu nedenle tablonun yeniden oluşturulması gerekebilir, ancak veri kaybını önlemek için
    # şimdilik sadece sütunları ekleyelim ve sonraki migration adımlarında ilişkileri düzenleyelim

def downgrade():
    # SQLite'ta ALTER TABLE DROP COLUMN desteklenmiyor
    # Değişiklikleri geri almak için tabloyu yeniden oluşturmak gerekir
    # Veri kaybını önlemek için bu işlemi manuel olarak yapmanız önerilir
    pass