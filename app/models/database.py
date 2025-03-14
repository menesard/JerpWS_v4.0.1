from flask_login import UserMixin

from app import db
from datetime import datetime

# İşlem türleri için sabitler
OPERATION_ADD = 'ADD'
OPERATION_SUBTRACT = 'SUBTRACT'


class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    purity_per_thousand = db.Column(db.Integer, nullable=False, default=916)  # Varsayılan değer 22 ayar için

    def __repr__(self):
        return f"<Setting {self.name}>"


class Region(db.Model):
    __tablename__ = 'regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"<Region {self.name}>"


class Operation(db.Model):
    __tablename__ = 'operations'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    source_region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))
    target_region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))
    setting_id = db.Column(db.Integer, db.ForeignKey('settings.id'), nullable=False)
    gram = db.Column(db.Float, nullable=False)


    # İlişkiler

    source_region = db.relationship('Region', foreign_keys=[source_region_id])
    target_region = db.relationship('Region', foreign_keys=[target_region_id])
    setting = db.relationship('Setting')
    user = db.relationship('User', backref=db.backref('operations', lazy='dynamic'))

    def __repr__(self):
        return f"<Operation {self.operation_type} {self.gram}g>"


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='staff')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    created_by = db.relationship('User', remote_side=[id], backref=db.backref('created_users', lazy='dynamic'))

    def has_role(self, role):
        if self.is_admin:
            return True
        if role == 'manager' and self.role == 'manager':
            return True
        if role == 'staff' and (self.role == 'manager' or self.role == 'staff'):
            return True
        return False

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    transactions = db.relationship('CustomerTransaction', backref='customer', lazy='dynamic')

    def __repr__(self):
        return f"<Customer {self.name}>"


# İşlem türleri için sabitler
TRANSACTION_PRODUCT_IN = 'PRODUCT_IN'
TRANSACTION_PRODUCT_OUT = 'PRODUCT_OUT'
TRANSACTION_SCRAP_IN = 'SCRAP_IN'
TRANSACTION_SCRAP_OUT = 'SCRAP_OUT'


class CustomerTransaction(db.Model):
    __tablename__ = 'customer_transactions'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    product_description = db.Column(db.String(200))
    setting_id = db.Column(db.Integer, db.ForeignKey('settings.id'), nullable=False)
    gram = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float)  # Gram başına fiyat
    labor_cost = db.Column(db.Float, default=0)  # İşçilik bedeli (TL)
    total_amount = db.Column(db.Float)  # Toplam tutar
    purity_per_thousand = db.Column(db.Integer, default=916)  # Milyem (ayara göre otomatik belirlenecek)
    pure_gold_weight = db.Column(db.Float)  # Has altın değeri (gram)
    labor_percentage = db.Column(db.Float, default=0)  # İşçilik yüzdesi (%)
    labor_pure_gold = db.Column(db.Float, default=0)  # İşçilik has altın karşılığı
    notes = db.Column(db.Text)

    # Düzenleme ile ilgili yeni alanlar
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    is_edited = db.Column(db.Boolean, default=False)  # Düzenlenip düzenlenmediği
    edited_date = db.Column(db.DateTime)  # Düzenlenme tarihi
    edited_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Düzenleyen kullanıcı
    original_transaction_id = db.Column(db.Integer, db.ForeignKey('customer_transactions.id'))  # Orijinal işlem ID'si

    # İlişkiler
    setting = db.relationship('Setting')
    edited_by = db.relationship('User', foreign_keys=[edited_by_user_id])
    original_transaction = db.relationship('CustomerTransaction', remote_side=[id],
                                           backref=db.backref('edited_versions', lazy='dynamic'),
                                           foreign_keys=[original_transaction_id])


    def __repr__(self):
        return f"<CustomerTransaction {self.transaction_type} {self.gram}g>"


def init_db():
    """Veritabanını başlangıç verileriyle doldur"""
    # Bölgeler

    global TRANSACTION_PRODUCT_IN, TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_IN, TRANSACTION_SCRAP_OUT
    TRANSACTION_PRODUCT_IN = 'PRODUCT_IN'
    TRANSACTION_PRODUCT_OUT = 'PRODUCT_OUT'
    TRANSACTION_SCRAP_IN = 'SCRAP_IN'
    TRANSACTION_SCRAP_OUT = 'SCRAP_OUT'

    regions = ['safe', 'table', 'polish', 'melting', 'saw', 'acid']
    for region_name in regions:
        if not Region.query.filter_by(name=region_name).first():
            region = Region(name=region_name)
            db.session.add(region)

    # Ayarlar ve milyem değerleri
    settings_data = [
        {'name': '8', 'purity_per_thousand': 333},
        {'name': '14', 'purity_per_thousand': 585},
        {'name': '18', 'purity_per_thousand': 750},
        {'name': '21', 'purity_per_thousand': 875},
        {'name': '22', 'purity_per_thousand': 916}
    ]

    for setting_data in settings_data:
        if not Setting.query.filter_by(name=setting_data['name']).first():
            setting = Setting(name=setting_data['name'],
                              purity_per_thousand=setting_data['purity_per_thousand'])
            db.session.add(setting)

    # Admin kullanıcı
    if not User.query.filter_by(username='admin').first():
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin'),
            is_admin=True
        )
        db.session.add(admin)

    db.session.commit()