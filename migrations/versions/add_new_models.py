"""Add new models for regions, fires, expenses, transfers and daily vault

Revision ID: add_new_models
Revises: 1a942afeadc7
Create Date: 2025-03-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'add_new_models'
down_revision = '1a942afeadc7'
branch_labels = None
depends_on = None


def upgrade():
    # Region modeli güncellemesi
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Region tablosundaki sütunları kontrol et
    region_columns = [c['name'] for c in inspector.get_columns('regions')]

    # Yeni alanları ekle
    if 'is_active' not in region_columns:
        op.add_column('regions', sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))

    if 'is_default' not in region_columns:
        op.add_column('regions', sa.Column('is_default', sa.Boolean(), server_default='0', nullable=False))

    if 'created_at' not in region_columns:
        op.add_column('regions', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Varsayılan bölgeleri işaretle
    op.execute("UPDATE regions SET is_default = 1 WHERE name IN ('kasa', 'masa', 'yer')")

    # CustomerTransaction modeli güncellemesi
    tx_columns = [c['name'] for c in inspector.get_columns('customer_transactions')]

    if 'used_in_transfer' not in tx_columns:
        op.add_column('customer_transactions',
                      sa.Column('used_in_transfer', sa.Boolean(), server_default='0', nullable=False))

    if 'transfer_id' not in tx_columns:
        op.add_column('customer_transactions', sa.Column('transfer_id', sa.Integer(), nullable=True))

    # Yeni tablolar oluştur
    # Fire tablosu
    op.create_table('fires',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('timestamp', sa.DateTime(), nullable=False),
                    sa.Column('expected_pure_gold', sa.Float(), nullable=False),
                    sa.Column('actual_pure_gold', sa.Float(), nullable=False),
                    sa.Column('fire_amount', sa.Float(), nullable=False),
                    sa.Column('notes', sa.Text(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Fire detay tablosu
    op.create_table('fire_details',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('fire_id', sa.Integer(), nullable=False),
                    sa.Column('region_id', sa.Integer(), nullable=False),
                    sa.Column('setting_id', sa.Integer(), nullable=False),
                    sa.Column('gram', sa.Float(), nullable=False),
                    sa.Column('pure_gold', sa.Float(), nullable=False),
                    sa.ForeignKeyConstraint(['fire_id'], ['fires.id'], ),
                    sa.ForeignKeyConstraint(['region_id'], ['regions.id'], ),
                    sa.ForeignKeyConstraint(['setting_id'], ['settings.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Transfer tablosu
    op.create_table('transfers',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('date', sa.DateTime(), nullable=False),
                    sa.Column('customer_total', sa.Float(), nullable=False),
                    sa.Column('labor_total', sa.Float(), nullable=False),
                    sa.Column('expense_total', sa.Float(), nullable=False),
                    sa.Column('transfer_amount', sa.Float(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Masraf tablosu
    op.create_table('expenses',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('date', sa.DateTime(), nullable=False),
                    sa.Column('description', sa.String(200), nullable=False),
                    sa.Column('amount_tl', sa.Float(), server_default='0', nullable=False),
                    sa.Column('amount_gold', sa.Float(), server_default='0', nullable=False),
                    sa.Column('gold_price', sa.Float(), server_default='0', nullable=False),
                    sa.Column('used_in_transfer', sa.Boolean(), server_default='0', nullable=False),
                    sa.Column('transfer_id', sa.Integer(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Günlük kasa tablosu
    op.create_table('daily_vaults',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('date', sa.Date(), nullable=False),
                    sa.Column('expected_total', sa.Float(), nullable=False),
                    sa.Column('actual_total', sa.Float(), nullable=False),
                    sa.Column('difference', sa.Float(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('notes', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Günlük kasa detay tablosu
    op.create_table('daily_vault_details',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('daily_vault_id', sa.Integer(), nullable=False),
                    sa.Column('setting_id', sa.Integer(), nullable=False),
                    sa.Column('expected_gram', sa.Float(), nullable=False),
                    sa.Column('actual_gram', sa.Float(), nullable=False),
                    sa.ForeignKeyConstraint(['daily_vault_id'], ['daily_vaults.id'], ),
                    sa.ForeignKeyConstraint(['setting_id'], ['settings.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    # Tabloları sil
    op.drop_table('daily_vault_details')
    op.drop_table('daily_vaults')
    op.drop_table('expenses')
    op.drop_table('transfers')
    op.drop_table('fire_details')
    op.drop_table('fires')

    # Sütunları kaldır
    op.drop_column('customer_transactions', 'transfer_id')
    op.drop_column('customer_transactions', 'used_in_transfer')
    op.drop_column('regions', 'created_at')
    op.drop_column('regions', 'is_default')
    op.drop_column('regions', 'is_active')