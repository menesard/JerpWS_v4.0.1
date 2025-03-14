"""Add pure gold and labor calculations fields

Revision ID: pure_gold_calculations
Revises: e4e2cc1dfc0c
Create Date: 2025-03-11 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pure_gold_calculations'
down_revision = 'e4e2cc1dfc0c'
branch_labels = None
depends_on = None


def upgrade():
    # Setting tablosuna milyem değeri ekle
    op.add_column('settings', sa.Column('purity_per_thousand', sa.Integer(), nullable=False, server_default='916'))

    # CustomerTransaction tablosuna has değer alanları ekle
    op.add_column('customer_transactions', sa.Column('purity_per_thousand', sa.Integer(), nullable=True, server_default='916'))
    op.add_column('customer_transactions', sa.Column('pure_gold_weight', sa.Float(), nullable=True))
    op.add_column('customer_transactions', sa.Column('labor_percentage', sa.Float(), nullable=True, server_default='0'))
    op.add_column('customer_transactions', sa.Column('labor_pure_gold', sa.Float(), nullable=True, server_default='0'))

    # Mevcut değerleri güncelle
    # Alembic üzerinden veri güncellemesi yapmak yerine, aşağıdaki SQL sorgularını kullanın:

    # 1. 8 ayar için milyem değerini 333 olarak güncelle
    op.execute("UPDATE settings SET purity_per_thousand = 333 WHERE name = '8'")

    # 2. 14 ayar için milyem değerini 585 olarak güncelle
    op.execute("UPDATE settings SET purity_per_thousand = 585 WHERE name = '14'")

    # 3. 18 ayar için milyem değerini 750 olarak güncelle
    op.execute("UPDATE settings SET purity_per_thousand = 750 WHERE name = '18'")

    # 4. 21 ayar için milyem değerini 875 olarak güncelle
    op.execute("UPDATE settings SET purity_per_thousand = 875 WHERE name = '21'")

    # 5. 22 ayar için milyem değerini 916 olarak güncelle
    op.execute("UPDATE settings SET purity_per_thousand = 916 WHERE name = '22'")

    # 6. Mevcut müşteri işlemleri için has altın değerlerini hesapla
    op.execute("""
    UPDATE customer_transactions AS ct
    SET purity_per_thousand = s.purity_per_thousand,
        pure_gold_weight = ct.gram * (s.purity_per_thousand / 1000)
    FROM settings AS s
    WHERE ct.setting_id = s.id
    """)


def downgrade():
    # Has değer alanlarını kaldır
    op.drop_column('customer_transactions', 'labor_pure_gold')
    op.drop_column('customer_transactions', 'labor_percentage')
    op.drop_column('customer_transactions', 'pure_gold_weight')
    op.drop_column('customer_transactions', 'purity_per_thousand')

    # Setting tablosundan milyem değerini kaldır
    op.drop_column('settings', 'purity_per_thousand')