from datetime import datetime

from app import db
from app.models.database import Region, Setting, Operation, Customer, CustomerTransaction, User, Expense, Transfer, \
    Fire, FireDetail, DailyVaultDetail, DailyVault
from app.models.database import OPERATION_ADD, OPERATION_SUBTRACT
from app.models.database import TRANSACTION_PRODUCT_IN, TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_IN, TRANSACTION_SCRAP_OUT
from sqlalchemy import func

class SystemManager:
    @staticmethod
    def get_region_id(region_name):
        """Bölge adından ID'yi al (sadece aktif bölgeler)"""
        print(f"DEBUG: get_region_id çağrıldı: {region_name}")

        # Giriş verisi kontrolü
        if not region_name:
            print("DEBUG: Bölge adı boş!")
            return None

        # 'kasa' ve 'safe' bölgelerini standartlaştırma
        if region_name.lower() in ['kasa', 'safe']:
            # Hem 'kasa' hem de 'safe' adlarına bakalım
            region = Region.query.filter(
                Region.is_active == True,
                db.or_(
                    db.func.lower(Region.name) == 'kasa',
                    db.func.lower(Region.name) == 'safe'
                )
            ).first()
        elif region_name.lower() in ['masa', 'table']:
            # Hem 'masa' hem de 'table' adlarına bakalım
            region = Region.query.filter(
                Region.is_active == True,
                db.or_(
                    db.func.lower(Region.name) == 'masa',
                    db.func.lower(Region.name) == 'table'
                )
            ).first()
        else:
            # Normal bölge araması
            region = Region.query.filter(
                Region.is_active == True,
                db.func.lower(Region.name) == region_name.lower()
            ).first()

        if region:
            print(f"DEBUG: Bölge bulundu - {region.name} (ID: {region.id})")
            return region.id
        else:
            print(f"DEBUG: Bölge bulunamadı - {region_name}")
            return None

    @staticmethod
    def get_region_status(region_name, setting_name):
        """Belirli bir bölgedeki belirli bir ayarın stok durumunu hesapla"""
        print(f"DEBUG: get_region_status çağrıldı: {region_name}, {setting_name}")

        # Region ID'yi al
        region_id = SystemManager.get_region_id(region_name)
        if not region_id:
            print(f"DEBUG: '{region_name}' bölgesi bulunamadı, 0 dönülüyor")
            return {setting_name: 0}

        # Setting ID'yi al
        setting = Setting.query.filter_by(name=setting_name).first()
        if not setting:
            print(f"DEBUG: '{setting_name}' ayarı bulunamadı, 0 dönülüyor")
            return {setting_name: 0}

        try:
            # Eklenen toplam
            added = db.session.query(func.coalesce(func.sum(Operation.gram), 0)).filter(
                Operation.target_region_id == region_id,
                Operation.setting_id == setting.id,
                Operation.operation_type == OPERATION_ADD
            ).scalar()

            # Çıkarılan toplam
            subtracted = db.session.query(func.coalesce(func.sum(Operation.gram), 0)).filter(
                Operation.source_region_id == region_id,
                Operation.setting_id == setting.id,
                Operation.operation_type == OPERATION_SUBTRACT
            ).scalar()

            # Net stok miktarını hesapla
            net_stock = float(added - subtracted)
            print(
                f"DEBUG: {region_name} bölgesindeki {setting_name} ayarı stok: {net_stock}g (Eklenen: {added}g, Çıkarılan: {subtracted}g)")

            return {setting_name: net_stock}
        except Exception as e:
            import traceback
            print(f"DEBUG Stok hesaplama hatası: {traceback.format_exc()}")
            return {setting_name: 0}

    @staticmethod
    def get_setting_id(setting_name):
        """Ayar adından ID'yi al"""
        setting = Setting.query.filter_by(name=setting_name).first()
        return setting.id if setting else None

    @staticmethod
    def add_item_safe(setting_name, gram, user_id=None):
        """Kasaya altın ekle"""
        setting_id = SystemManager.get_setting_id(setting_name)
        safe_id = SystemManager.get_region_id('safe')

        if setting_id and safe_id:
            operation = Operation(
                operation_type=OPERATION_ADD,
                target_region_id=safe_id,
                setting_id=setting_id,
                gram=float(gram),
                user_id=user_id  # Kullanıcı ID'si eklendi
            )
            db.session.add(operation)
            db.session.commit()
            return True
        return False

    @staticmethod
    def remove_item_safe(setting_name, gram, user_id=None):
        """Kasadan altın çıkar"""
        setting_id = SystemManager.get_setting_id(setting_name)
        safe_id = SystemManager.get_region_id('safe')

        if setting_id and safe_id:
            operation = Operation(
                operation_type=OPERATION_SUBTRACT,
                source_region_id=safe_id,
                setting_id=setting_id,
                gram=float(gram),
                user_id=user_id  # Kullanıcı ID'si eklendi
            )
            db.session.add(operation)
            db.session.commit()
            return True
        return False

    @staticmethod
    def add_item(region_name, setting_name, gram, user_id=None):
        """Bölgeye altın ekle (masa üzerinden)"""
        print(f"DEBUG: add_item başladı: {region_name}, {setting_name}, {gram}")
        region_id = SystemManager.get_region_id(region_name)
        setting_id = SystemManager.get_setting_id(setting_name)
        table_id = SystemManager.get_region_id('table')  # masa bölgesi ID'si
        safe_id = SystemManager.get_region_id('safe')  # kasa bölgesi ID'si

        # Debug
        print(f"DEBUG ID'ler: region_id={region_id}, setting_id={setting_id}, table_id={table_id}, safe_id={safe_id}")

        # ID kontrol
        if not region_id:
            print(f"DEBUG: '{region_name}' bölgesi bulunamadı")
            return False
        if not setting_id:
            print(f"DEBUG: '{setting_name}' ayarı bulunamadı")
            return False
        if not table_id:
            print("DEBUG: 'table/masa' bölgesi bulunamadı")
            return False
        if not safe_id:
            print("DEBUG: 'safe/kasa' bölgesi bulunamadı")
            return False

        try:
            if region_name == 'table' or region_name == 'masa':
                # Kasadan masaya transfer
                # 1. Kasadan çıkar
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=safe_id,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                # 2. Masaya ekle
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    source_region_id=safe_id,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(subtract_op)
                db.session.add(add_op)
                print(f"DEBUG: Kasadan masaya işlem eklendi: {gram}g {setting_name}")
            else:
                # Masadan diğer bölgeye transfer
                # 1. Masadan çıkar
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=table_id,
                    target_region_id=region_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                # 2. Hedef bölgeye ekle
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    source_region_id=table_id,
                    target_region_id=region_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(subtract_op)
                db.session.add(add_op)
                print(f"DEBUG: Masadan {region_name} bölgesine işlem eklendi: {gram}g {setting_name}")

            db.session.commit()
            print("DEBUG: İşlem başarıyla tamamlandı")
            return True
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"DEBUG HATA: {traceback.format_exc()}")
            print(f"DEBUG: İşlem hatası: {str(e)}")
            return False

    @staticmethod
    def remove_item(region_name, setting_name, gram, user_id=None):
        """Bölgeden altın çıkar (masa üzerinden)"""
        print(f"DEBUG: remove_item başladı: {region_name}, {setting_name}, {gram}")
        region_id = SystemManager.get_region_id(region_name)
        setting_id = SystemManager.get_setting_id(setting_name)
        table_id = SystemManager.get_region_id('table')  # masa bölgesi ID'si
        safe_id = SystemManager.get_region_id('safe')  # kasa bölgesi ID'si

        # Debug
        print(f"DEBUG ID'ler: region_id={region_id}, setting_id={setting_id}, table_id={table_id}, safe_id={safe_id}")

        # ID kontrol
        if not region_id:
            print(f"DEBUG: '{region_name}' bölgesi bulunamadı")
            return False
        if not setting_id:
            print(f"DEBUG: '{setting_name}' ayarı bulunamadı")
            return False
        if not table_id:
            print("DEBUG: 'table/masa' bölgesi bulunamadı")
            return False
        if not safe_id:
            print("DEBUG: 'safe/kasa' bölgesi bulunamadı")
            return False

        # Bölgedeki mevcut stok kontrolü
        region_status = SystemManager.get_region_status(region_name, setting_name)
        current_stock = region_status.get(setting_name, 0)
        print(f"DEBUG: '{region_name}' bölgesindeki mevcut stok: {current_stock}g")

        if current_stock < float(gram):
            print(f"DEBUG: Yetersiz stok! İstenilen: {gram}g, Mevcut: {current_stock}g")
            return False

        try:
            if region_name == 'table' or region_name == 'masa':
                # Masadan kasaya transfer
                # 1. Masadan çıkar
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=table_id,
                    target_region_id=safe_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                # 2. Kasaya ekle
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    source_region_id=table_id,
                    target_region_id=safe_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(subtract_op)
                db.session.add(add_op)
                print(f"DEBUG: Masadan kasaya işlem eklendi: {gram}g {setting_name}")
            else:
                # Diğer bölgeden masaya transfer
                # 1. Bölgeden çıkar
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=region_id,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                # 2. Masaya ekle
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    source_region_id=region_id,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(subtract_op)
                db.session.add(add_op)
                print(f"DEBUG: {region_name} bölgesinden masaya işlem eklendi: {gram}g {setting_name}")

            db.session.commit()
            print("DEBUG: İşlem başarıyla tamamlandı")
            return True
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"DEBUG HATA: {traceback.format_exc()}")
            print(f"DEBUG: İşlem hatası: {str(e)}")
            return False

    @staticmethod
    def get_status(setting_name):
        """Tüm bölgelerin durumunu döndür"""
        setting_id = SystemManager.get_setting_id(setting_name)
        if not setting_id:
            return {}

        status = {}
        # Sadece aktif bölgeleri al
        regions = Region.query.filter_by(is_active=True).all()

        for region in regions:
            region_name = region.name
            region_id = region.id

            # Eklenen toplam
            added = db.session.query(func.coalesce(func.sum(Operation.gram), 0)).filter(
                Operation.target_region_id == region_id,
                Operation.setting_id == setting_id,
                Operation.operation_type == OPERATION_ADD
            ).scalar()

            # Çıkarılan toplam
            subtracted = db.session.query(func.coalesce(func.sum(Operation.gram), 0)).filter(
                Operation.source_region_id == region_id,
                Operation.setting_id == setting_id,
                Operation.operation_type == OPERATION_SUBTRACT
            ).scalar()

            status[region_name] = {setting_name: float(added - subtracted)}

        return status

    @staticmethod
    def get_logs(limit=50):
        """Son işlemleri döndür (daha okunabilir formatta)"""
        # Sadece ekleme işlemlerini al (her transfer için bir kayıt)
        operations = Operation.query.filter_by(operation_type=OPERATION_ADD).order_by(Operation.timestamp.desc()).limit(
            limit).all()
        logs = []

        for op in operations:
            source_region = op.source_region.name if op.source_region else ""
            target_region = op.target_region.name if op.target_region else ""

            # Kullanıcı bilgisini kontrol et
            username = "Bilinmeyen"
            if op.user_id:
                user = User.query.get(op.user_id)
                if user:
                    username = user.username

            # Daha açıklayıcı bir işlem açıklaması
            operation_description = "EKLEME"
            if source_region and target_region:
                operation_description = f"TRANSFER ({source_region} → {target_region})"
            elif not source_region and target_region:
                operation_description = f"EKLEME ({target_region})"

            logs.append({
                "time": op.timestamp.strftime('%d-%m-%Y %H:%M:%S'),
                "operation_type": operation_description,  # Değiştirilmiş işlem açıklaması
                "source_region": source_region,
                "target_region": target_region,
                "setting": op.setting.name,
                "gram": f"{op.gram:.2f}",
                "username": username
            })

        return logs
    @staticmethod
    def add_customer(name, phone=None, email=None, address=None):
        """Yeni müşteri ekle"""
        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            address=address
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def get_customers(search=None, limit=100):
        """Müşterileri listele, opsiyonel arama ile"""
        query = Customer.query

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Customer.name.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Customer.email.ilike(search_term)
                )
            )

        return query.order_by(Customer.name).limit(limit).all()

    @staticmethod
    def get_customer(customer_id):
        """Müşteri detaylarını getir"""
        return Customer.query.get(customer_id)

    @staticmethod
    def get_setting_with_purity(setting_name):
        """Ayar adından ayar ve milyem bilgilerini al"""
        setting = Setting.query.filter_by(name=setting_name).first()
        return setting

    @staticmethod
    def calculate_pure_gold_weight(gram, purity_per_thousand):
        """Has altın ağırlığını hesapla"""
        return gram * (purity_per_thousand / 1000)

    @staticmethod
    def calculate_labor_pure_gold(gram, labor_percentage):
        """İşçilik has altın karşılığını hesapla"""
        return gram * (labor_percentage / 1000)

    @staticmethod
    def add_customer_transaction(customer_id, transaction_type, setting_name, gram,
                                 product_description=None, unit_price=None, labor_cost=0,
                                 purity_per_thousand=None, labor_percentage=0, notes=None, user_id=None,
                                 used_in_transfer=False, transfer_id=None):
        """Müşteri işlemi ekle - has değer hesaplamalı ve kasaya etkili"""
        customer = Customer.query.get(customer_id)
        setting = SystemManager.get_setting_with_purity(setting_name)

        if not customer or not setting:
            return False

        # Milyem değerini kontrol et, belirtilmemişse ayardan al
        if purity_per_thousand is None:
            purity_per_thousand = setting.purity_per_thousand

        # Has altın ağırlığını hesapla
        pure_gold_weight = SystemManager.calculate_pure_gold_weight(float(gram), purity_per_thousand)

        # İşçilik has karşılığını hesapla
        labor_pure_gold = SystemManager.calculate_labor_pure_gold(float(gram), labor_percentage)

        # Toplam tutarı hesapla
        total_amount = 0
        if unit_price is not None:
            total_amount = (gram * unit_price) + (labor_cost or 0)

        transaction = CustomerTransaction(
            customer_id=customer_id,
            transaction_type=transaction_type,
            setting_id=setting.id,
            gram=float(gram),
            product_description=product_description,
            unit_price=unit_price,
            labor_cost=labor_cost,
            total_amount=total_amount,
            purity_per_thousand=purity_per_thousand,
            pure_gold_weight=pure_gold_weight,
            labor_percentage=labor_percentage,
            labor_pure_gold=labor_pure_gold,
            notes=notes,
            created_by_user_id=user_id,
            used_in_transfer=used_in_transfer,
            transfer_id=transfer_id
        )

        db.session.add(transaction)
        db.session.flush()  # ID ataması için

        try:
            # Kasa bölgesini al
            safe_region = Region.query.filter_by(name='kasa', is_active=True).first()
            if not safe_region:
                # Eğer "kasa" bulunamazsa, "safe" olarak da dene
                safe_region = Region.query.filter_by(name='safe', is_active=True).first()

            if not safe_region:
                # Yine bulunamazsa hata döndür
                db.session.rollback()
                return False

            safe_id = safe_region.id

            # Ürün çıkışı veya hurda çıkışı için kasa stokunu güncelle
            if transaction_type in [TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT]:
                # Müşteriye ürün/hurda veriliyor - kasadan çıkarılır
                operation = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=safe_id,
                    setting_id=setting.id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(operation)

            # Ürün girişi veya hurda girişi için kasa stokunu güncelle
            elif transaction_type in [TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN]:
                # Müşteriden ürün/hurda alınıyor - kasaya eklenir
                operation = Operation(
                    operation_type=OPERATION_ADD,
                    target_region_id=safe_id,
                    setting_id=setting.id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(operation)

            db.session.commit()
            return transaction
        except Exception as e:
            # Hata durumunda işlemi geri al
            db.session.rollback()
            print(f"Müşteri işlemi eklerken hata: {str(e)}")
            return False

    @staticmethod
    def get_customer_balance(customer_id, setting_name=None):
        """Müşteri bakiyesini hesapla"""
        setting_id = None
        if setting_name:
            setting_id = SystemManager.get_setting_id(setting_name)

        balances = {}

        # Tüm ayarlar için veya belirli bir ayar için sorgu yap
        settings = [Setting.query.get(setting_id)] if setting_id else Setting.query.all()

        for setting in settings:
            # Ürün ve hurda girişleri (müşteriden alınanlar)
            inputs = db.session.query(func.coalesce(func.sum(CustomerTransaction.gram), 0)).filter(
                CustomerTransaction.customer_id == customer_id,
                CustomerTransaction.setting_id == setting.id,
                CustomerTransaction.transaction_type.in_([TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN])
            ).scalar()

            # Ürün ve hurda çıkışları (müşteriye verilenler)
            outputs = db.session.query(func.coalesce(func.sum(CustomerTransaction.gram), 0)).filter(
                CustomerTransaction.customer_id == customer_id,
                CustomerTransaction.setting_id == setting.id,
                CustomerTransaction.transaction_type.in_([TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT])
            ).scalar()

            # Net bakiye
            net = inputs - outputs

            balances[setting.name] = {
                'inputs': inputs,
                'outputs': outputs,
                'net': net
            }

        return balances

    @staticmethod
    def get_customer_pure_gold_balance(customer_id):
        """Müşteri has altın bakiyesini hesapla"""

        # Varsayılan değerler
        pure_gold_balance = {
            'pure_gold_inputs': 0.0,
            'pure_gold_outputs': 0.0,
            'net_pure_gold': 0.0,
            'labor_pure_gold_inputs': 0.0,
            'labor_pure_gold_outputs': 0.0,
            'net_labor_pure_gold': 0.0,
            'total_net_pure_gold': 0.0
        }

        # CustomerTransaction tablosunda has altın ve işçilik alanları henüz yoksa
        # sadece varsayılan değerleri döndür
        if not hasattr(CustomerTransaction, 'pure_gold_weight'):
            return pure_gold_balance

        # Toplam has altın girişleri (müşteriden alınanlar)
        inputs = db.session.query(func.coalesce(func.sum(CustomerTransaction.pure_gold_weight), 0)).filter(
            CustomerTransaction.customer_id == customer_id,
            CustomerTransaction.transaction_type.in_([TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN])
        ).scalar()

        # İşçilik has altın girişleri
        labor_inputs = db.session.query(func.coalesce(func.sum(CustomerTransaction.labor_pure_gold), 0)).filter(
            CustomerTransaction.customer_id == customer_id,
            CustomerTransaction.transaction_type.in_([TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN])
        ).scalar()

        # Toplam has altın çıkışları (müşteriye verilenler)
        outputs = db.session.query(func.coalesce(func.sum(CustomerTransaction.pure_gold_weight), 0)).filter(
            CustomerTransaction.customer_id == customer_id,
            CustomerTransaction.transaction_type.in_([TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT])
        ).scalar()

        # İşçilik has altın çıkışları
        labor_outputs = db.session.query(func.coalesce(func.sum(CustomerTransaction.labor_pure_gold), 0)).filter(
            CustomerTransaction.customer_id == customer_id,
            CustomerTransaction.transaction_type.in_([TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT])
        ).scalar()

        # Net bakiyeler
        net_pure_gold = inputs - outputs
        net_labor_pure_gold = labor_inputs - labor_outputs
        total_net = net_pure_gold + net_labor_pure_gold

        return {
            'pure_gold_inputs': inputs,
            'pure_gold_outputs': outputs,
            'net_pure_gold': net_pure_gold,
            'labor_pure_gold_inputs': labor_inputs,
            'labor_pure_gold_outputs': labor_outputs,
            'net_labor_pure_gold': net_labor_pure_gold,
            'total_net_pure_gold': total_net
        }

    @staticmethod
    def get_transaction_type_tr(transaction_type):
        """İşlem türünü Türkçeye çevir"""
        type_map = {
            TRANSACTION_PRODUCT_IN: "ÜRÜN GİRİŞ",
            TRANSACTION_PRODUCT_OUT: "ÜRÜN ÇIKIŞ",
            TRANSACTION_SCRAP_IN: "HURDA GİRİŞ",
            TRANSACTION_SCRAP_OUT: "HURDA ÇIKIŞ"
        }
        return type_map.get(transaction_type, transaction_type)

    @staticmethod
    def get_transaction(transaction_id):
        """Belirli bir işlemin detaylarını getir"""
        return CustomerTransaction.query.get(transaction_id)

    @staticmethod
    def edit_customer_transaction(transaction_id, user_id, **kwargs):
        """
        Müşteri işlemini düzenle ve orijinal işlemi koruyarak yeni işlem oluştur

        Args:
            transaction_id: Düzenlenecek işlem ID'si
            user_id: Düzenleyen kullanıcı ID'si
            **kwargs: Değişecek alanlar (transaction_type, gram, product_description, vs.)

        Returns:
            Yeni oluşturulan işlem
        """
        # Orijinal işlemi bul
        original_transaction = CustomerTransaction.query.get(transaction_id)

        if not original_transaction:
            return None

        # Orijinal işlemden yeni işlem oluştur
        new_transaction = CustomerTransaction(
            customer_id=original_transaction.customer_id,
            transaction_type=kwargs.get('transaction_type', original_transaction.transaction_type),
            transaction_date=datetime.utcnow(),
            product_description=kwargs.get('product_description', original_transaction.product_description),
            setting_id=kwargs.get('setting_id', original_transaction.setting_id),
            gram=kwargs.get('gram', original_transaction.gram),
            unit_price=kwargs.get('unit_price', original_transaction.unit_price),
            labor_cost=kwargs.get('labor_cost', original_transaction.labor_cost),
            total_amount=kwargs.get('total_amount', original_transaction.total_amount),
            purity_per_thousand=kwargs.get('purity_per_thousand', original_transaction.purity_per_thousand),
            pure_gold_weight=kwargs.get('pure_gold_weight', original_transaction.pure_gold_weight),
            labor_percentage=kwargs.get('labor_percentage', original_transaction.labor_percentage),
            labor_pure_gold=kwargs.get('labor_pure_gold', original_transaction.labor_pure_gold),
            notes=kwargs.get('notes', original_transaction.notes),
            is_edited=True,
            edited_date=datetime.utcnow(),
            edited_by_user_id=user_id,
            original_transaction_id=original_transaction.id
        )

        # Has değerini hesapla (değişmiş olabilir)
        if 'gram' in kwargs or 'purity_per_thousand' in kwargs:
            new_transaction.pure_gold_weight = SystemManager.calculate_pure_gold_weight(
                new_transaction.gram,
                new_transaction.purity_per_thousand
            )

        # İşçilik has karşılığını hesapla (değişmiş olabilir)
        if 'gram' in kwargs or 'labor_percentage' in kwargs:
            new_transaction.labor_pure_gold = SystemManager.calculate_labor_pure_gold(
                new_transaction.gram,
                new_transaction.labor_percentage
            )

        db.session.add(new_transaction)

        # Stok durumunu güncelle (önceki işlemin etkilerini geri al, yeni işlemin etkilerini uygula)
        # Önceki işlem türüne göre tersine işlem yap
        if original_transaction.transaction_type in [TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT]:
            # Önceki işlem çıkış ise, stoğa geri ekle
            setting = Setting.query.get(original_transaction.setting_id)
            SystemManager.add_item_safe(setting.name, original_transaction.gram)
        elif original_transaction.transaction_type in [TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN]:
            # Önceki işlem giriş ise, stoktan düş
            setting = Setting.query.get(original_transaction.setting_id)
            SystemManager.remove_item_safe(setting.name, original_transaction.gram)

        # Yeni işlem türüne göre işlem yap
        if new_transaction.transaction_type in [TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT]:
            # Yeni işlem çıkış ise, stoktan düş
            setting = Setting.query.get(new_transaction.setting_id)
            SystemManager.remove_item_safe(setting.name, new_transaction.gram)
        elif new_transaction.transaction_type in [TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN]:
            # Yeni işlem giriş ise, stoğa ekle
            setting = Setting.query.get(new_transaction.setting_id)
            SystemManager.add_item_safe(setting.name, new_transaction.gram)

        db.session.commit()
        return new_transaction

    @staticmethod
    def get_transaction_history(transaction_id):
        """
        Bir işlemin tüm düzenleme geçmişini getir

        Args:
            transaction_id: İşlem ID'si

        Returns:
            İşlem ve tüm düzenleme geçmişi
        """
        # İlk olarak, bu işlemin orijinal mi yoksa düzenlenmiş bir işlem mi olduğunu kontrol et
        transaction = CustomerTransaction.query.get(transaction_id)

        if not transaction:
            return []

        # Eğer bu bir düzenlenmiş işlemse, orijinalini bul
        if transaction.original_transaction_id:
            original_id = transaction.original_transaction_id
            while original_id:
                original = CustomerTransaction.query.get(original_id)
                if not original.original_transaction_id:
                    # En baştaki orijinal işleme ulaştık
                    break
                original_id = original.original_transaction_id

            # Şimdi orijinal işlemi ve tüm düzenlemelerini al
            history = [original]
            history.extend(original.edited_versions.order_by(CustomerTransaction.edited_date).all())

        else:
            # Bu zaten orijinal işlem, kendisini ve düzenlemelerini al
            history = [transaction]
            history.extend(transaction.edited_versions.order_by(CustomerTransaction.edited_date).all())

        return history

    @staticmethod
    def get_customer_transactions(customer_id, limit=50, include_edited=True):
        """
        Müşteri işlemlerini getir - has değerleriyle birlikte

        Args:
            customer_id: Müşteri ID'si
            limit: Maksimum işlem sayısı
            include_edited: Düzenlenmiş işlemleri dahil et (True) veya sadece en son halleri göster (False)
        """
        if include_edited:
            # Tüm işlemleri getir
            transactions = CustomerTransaction.query.filter_by(customer_id=customer_id) \
                .order_by(CustomerTransaction.transaction_date.desc()) \
                .limit(limit).all()
        else:
            # Sadece düzenlenmemiş veya en son düzenlenmiş işlemleri getir (orijinal işlemleri atla)
            # Karmaşık bir sorgu gerekiyor, SQLAlchemy ile
            # 1. Düzenlenmemiş işlemler (is_edited=False ve edited_versions boş)
            # 2. En son düzenlenmiş işlemler (herhangi bir işlemin edited_versions'ında en son tarihli olanlar)

            # Önce orijinal işlemleri bulalım
            originals = db.session.query(CustomerTransaction.id).filter(
                CustomerTransaction.customer_id == customer_id,
                CustomerTransaction.original_transaction_id == None
            ).all()

            original_ids = [o[0] for o in originals]

            # Düzenlenen işlemlerin en son versiyonlarını bulalım
            subquery = db.session.query(
                CustomerTransaction.original_transaction_id,
                func.max(CustomerTransaction.edited_date).label('max_date')
            ).filter(
                CustomerTransaction.customer_id == customer_id,
                CustomerTransaction.is_edited == True
            ).group_by(CustomerTransaction.original_transaction_id).subquery()

            edited_latest = db.session.query(CustomerTransaction).join(
                subquery,
                db.and_(
                    CustomerTransaction.original_transaction_id == subquery.c.original_transaction_id,
                    CustomerTransaction.edited_date == subquery.c.max_date
                )
            ).all()

            # Düzenlenmemiş işlemleri bulalım (orijinal ama düzenlenme geçmişi olmayan)
            unedited = db.session.query(CustomerTransaction).filter(
                CustomerTransaction.customer_id == customer_id,
                CustomerTransaction.is_edited == False,
                ~CustomerTransaction.id.in_(
                    [e.original_transaction_id for e in edited_latest if e.original_transaction_id])
            ).all()

            # İkisini birleştirip sıralayalım
            transactions = edited_latest + unedited
            transactions.sort(key=lambda x: x.transaction_date, reverse=True)

            # Limit uygula
            transactions = transactions[:limit]

        result = []
        for tx in transactions:
            transaction_data = {
                "id": tx.id,
                "date": tx.transaction_date.strftime('%d-%m-%Y %H:%M:%S'),
                "type": tx.transaction_type,
                "type_tr": SystemManager.get_transaction_type_tr(tx.transaction_type),
                "setting": tx.setting.name,
                "gram": f"{tx.gram:.2f}",
                "is_edited": tx.is_edited,
                "notes": tx.notes or ""
            }

            # Has değeri alanları varsa ekle
            if hasattr(tx, 'purity_per_thousand') and tx.purity_per_thousand:
                transaction_data.update({
                    "purity": f"{tx.purity_per_thousand}",
                    "pure_gold": f"{tx.pure_gold_weight:.4f}" if tx.pure_gold_weight else "-",
                    "labor_percentage": f"{tx.labor_percentage:.2f}" if tx.labor_percentage else "-",
                    "labor_pure_gold": f"{tx.labor_pure_gold:.4f}" if tx.labor_pure_gold else "-",
                })

            # Ürün açıklaması varsa ekle
            if tx.product_description:
                transaction_data["product"] = tx.product_description

            # Düzenlenme bilgileri varsa ekle
            if tx.is_edited:
                transaction_data["edited_date"] = tx.edited_date.strftime(
                    '%d-%m-%Y %H:%M:%S') if tx.edited_date else "-"
                if tx.edited_by:
                    transaction_data["edited_by"] = tx.edited_by.username

            result.append(transaction_data)

        return result

    @staticmethod
    def add_region(name):
        """Yeni bölge ekle"""
        if Region.query.filter_by(name=name).first():
            return False, "Bu isimde bir bölge zaten var"

        region = Region(name=name, is_active=True)
        db.session.add(region)
        db.session.commit()
        return True, "Bölge başarıyla eklendi"

    @staticmethod
    def deactivate_region(region_id):
        """Bölgeyi pasif duruma getir (silmiş gibi)"""
        region = Region.query.get(region_id)
        if not region:
            return False, "Bölge bulunamadı"

        # Varsayılan bölgeyi silemeyiz
        if region.is_default:
            return False, "Varsayılan bölgeler silinemez"

        # Bölgedeki tüm altınları kontrol et
        total_gold = 0
        for setting in Setting.query.all():
            status = SystemManager.get_region_status(region.name, setting.name)
            total_gold += status[setting.name] if setting.name in status else 0

        # Bölgede altın varsa silemeyiz
        if total_gold > 0:
            return False, f"Bölgede {total_gold}g altın bulunduğu için silinemez"

        region.is_active = False
        db.session.commit()
        return True, "Bölge başarıyla silindi"

    @staticmethod
    def activate_region(region_id):
        """Silinmiş bölgeyi aktif et"""
        region = Region.query.get(region_id)
        if not region:
            return False, "Bölge bulunamadı"

        # Bölge zaten aktif mi kontrol et
        if region.is_active:
            return False, "Bölge zaten aktif durumda"

        # Aynı isimde aktif bölge var mı kontrol et
        if Region.query.filter_by(name=region.name, is_active=True).first():
            return False, "Bu isimde aktif bir bölge zaten var"

        region.is_active = True
        db.session.commit()
        return True, "Bölge başarıyla geri yüklendi"

    @staticmethod
    def create_ramat(user_id, actual_pure_gold, notes=None):
        """Ramat işlemi oluştur ve fire hesapla"""
        # Tüm bölgelerdeki altınları topla
        total_pure_gold = 0
        fire_details = []

        # Sadece aktif bölgeleri al
        regions = Region.query.filter_by(is_active=True).all()

        # Her bölge için ayar bazında detayları hesapla
        for region in regions:
            if region.name == 'kasa':
                continue  # Kasa bölgesini ramat hesabına katmıyoruz

            for setting in Setting.query.all():
                status = SystemManager.get_region_status(region.name, setting.name)
                gram = status.get(setting.name, 0)

                if gram > 0:
                    # Has değerini hesapla
                    pure_gold = gram * (setting.purity_per_thousand / 1000)
                    total_pure_gold += pure_gold

                    fire_details.append({
                        'region_id': region.id,
                        'setting_id': setting.id,
                        'gram': gram,
                        'pure_gold': pure_gold
                    })

        if total_pure_gold <= 0:
            return False, "Bölgelerde ramat için altın bulunmuyor"

        # Gerçek has değer beklenen değerden büyük olamaz
        if float(actual_pure_gold) > total_pure_gold:
            return False, f"Gerçek has değer ({actual_pure_gold}g), beklenen değerden ({total_pure_gold:.2f}g) büyük olamaz"

        # Fire miktarını hesapla
        fire_amount = total_pure_gold - float(actual_pure_gold)

        # Fire kaydı oluştur
        fire = Fire(
            expected_pure_gold=total_pure_gold,
            actual_pure_gold=float(actual_pure_gold),
            fire_amount=fire_amount,
            notes=notes,
            user_id=user_id
        )
        db.session.add(fire)
        db.session.flush()  # ID ataması için

        # Fire detaylarını ekle
        for detail in fire_details:
            fire_detail = FireDetail(
                fire_id=fire.id,
                region_id=detail['region_id'],
                setting_id=detail['setting_id'],
                gram=detail['gram'],
                pure_gold=detail['pure_gold']
            )
            db.session.add(fire_detail)

        # Ramat sonrası bölgelerden altınları çıkar ve kasaya ekle
        # Her bölgeyi temizle (kasa hariç)
        for region in regions:
            if region.name == 'kasa':
                continue

            for setting in Setting.query.all():
                status = SystemManager.get_region_status(region.name, setting.name)
                gram = status.get(setting.name, 0)

                if gram > 0:
                    # Bölgeden çıkar
                    SystemManager.remove_item(region.name, setting.name, gram, user_id)

        # Kasaya gerçek has değeri ekle
        setting_22 = Setting.query.filter_by(name='22').first()
        if setting_22:
            # Gerçek değeri 22 ayar olarak kasaya ekle
            gold_equivalent = float(actual_pure_gold) / (setting_22.purity_per_thousand / 1000)
            SystemManager.add_item_safe(setting_22.name, gold_equivalent, user_id)

        db.session.commit()
        return True, f"Ramat işlemi başarılı. Fire: {fire_amount:.2f}g"

    @staticmethod
    def add_expense(description, amount_tl=0, amount_gold=0, gold_price=0, user_id=None):
        """Masraf ekle"""
        if amount_tl <= 0 and amount_gold <= 0:
            return False, "TL veya altın miktarından en az biri pozitif olmalıdır"

        expense = Expense(
            description=description,
            amount_tl=amount_tl,
            amount_gold=amount_gold,
            gold_price=gold_price,
            user_id=user_id
        )

        db.session.add(expense)
        db.session.commit()
        return True, "Masraf başarıyla eklendi"

    @staticmethod
    def get_expenses(start_date=None, end_date=None, include_used=False):
        """Masrafları listele"""
        query = Expense.query

        if start_date:
            query = query.filter(Expense.date >= start_date)

        if end_date:
            query = query.filter(Expense.date <= end_date)

        if not include_used:
            query = query.filter(Expense.used_in_transfer == False)

        return query.order_by(Expense.date.desc()).all()

    @staticmethod
    def calculate_transfer():
        """Devir hesapla - henüz devir işlemi oluşturmaz"""
        # Müşteri işlemlerini al (devirde henüz kullanılmamış)
        customer_transactions = CustomerTransaction.query.filter_by(used_in_transfer=False).all()

        # Müşteri işlemlerini topla
        customer_total = 0
        labor_total = 0

        for tx in customer_transactions:
            # Has değerler üzerinden hesapla
            if tx.transaction_type in [TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT]:
                # Müşteriye verilen
                customer_total += tx.pure_gold_weight
                labor_total += tx.labor_pure_gold
            elif tx.transaction_type in [TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN]:
                # Müşteriden alınan
                customer_total -= tx.pure_gold_weight
                labor_total -= tx.labor_pure_gold

        # Masrafları al (devirde henüz kullanılmamış)
        expenses = Expense.query.filter_by(used_in_transfer=False).all()
        expense_total = sum(expense.amount_gold for expense in expenses)

        # Devir formülü: Devir = (Müşterilere verilenler + İşçilik) - (Müşterilerden alınanlar + İşçilik) - Masraf
        transfer_amount = customer_total + labor_total - expense_total

        return {
            'customer_total': customer_total,
            'labor_total': labor_total,
            'expense_total': expense_total,
            'transfer_amount': transfer_amount,
            'transactions': customer_transactions,
            'expenses': expenses
        }

    @staticmethod
    def create_transfer(user_id):
        """Devir işlemi oluştur"""
        # Devir hesapla
        transfer_data = SystemManager.calculate_transfer()

        if transfer_data['transfer_amount'] <= 0:
            return False, "Devir miktarı sıfır veya negatif olamaz"

        # Devir kaydı oluştur
        transfer = Transfer(
            customer_total=transfer_data['customer_total'],
            labor_total=transfer_data['labor_total'],
            expense_total=transfer_data['expense_total'],
            transfer_amount=transfer_data['transfer_amount'],
            user_id=user_id
        )

        db.session.add(transfer)
        db.session.flush()  # ID için

        # İşlemleri ve masrafları kullanıldı olarak işaretle
        for tx in transfer_data['transactions']:
            tx.used_in_transfer = True
            tx.transfer_id = transfer.id

        for expense in transfer_data['expenses']:
            expense.used_in_transfer = True
            expense.transfer_id = transfer.id

        db.session.commit()
        return True, f"Devir işlemi başarıyla tamamlandı. Devir miktarı: {transfer_data['transfer_amount']:.4f} g"

    @staticmethod
    def get_transfers():
        """Devir işlemlerini listele"""
        return Transfer.query.order_by(Transfer.date.desc()).all()

    @staticmethod
    def get_transfer_details(transfer_id):
        """Devir detaylarını getir"""
        transfer = Transfer.query.get(transfer_id)
        if not transfer:
            return None

        # Bu devirde kullanılan işlemler
        transactions = CustomerTransaction.query.filter_by(transfer_id=transfer_id).all()

        # Bu devirde kullanılan masraflar
        expenses = Expense.query.filter_by(transfer_id=transfer_id).all()

        return {
            'transfer': transfer,
            'transactions': transactions,
            'expenses': expenses
        }

    @staticmethod
    def calculate_vault_expected():
        """Kasada beklenen değerleri hesapla"""
        # Kasa bölgesi
        safe_region = Region.query.filter_by(name='kasa').first()
        if not safe_region:
            return None

        result = {}
        total_gram = 0

        # Her ayar için kasadaki miktarı hesapla
        for setting in Setting.query.all():
            status = SystemManager.get_region_status('kasa', setting.name)
            gram = status.get(setting.name, 0)

            result[setting.id] = {
                'setting': setting,
                'gram': gram
            }

            total_gram += gram

        return {
            'details': result,
            'total': total_gram
        }

    @staticmethod
    def create_daily_vault(user_id, actual_grams, notes=None):
        """Günlük kasa kaydı oluştur"""
        # Beklenen değerleri hesapla
        expected_data = SystemManager.calculate_vault_expected()
        if not expected_data:
            return False, "Kasa bölgesi bulunamadı"

        # Girilen değerleri kontrol et
        if not actual_grams or not isinstance(actual_grams, dict):
            return False, "Geçersiz veri formatı"

        # Toplam değerleri hesapla
        actual_total = 0
        for setting_id, gram in actual_grams.items():
            actual_total += float(gram)

        # Fark hesapla
        difference = actual_total - expected_data['total']

        # Günlük kasa kaydı oluştur
        daily_vault = DailyVault(
            expected_total=expected_data['total'],
            actual_total=actual_total,
            difference=difference,
            user_id=user_id,
            notes=notes
        )

        db.session.add(daily_vault)
        db.session.flush()  # ID için

        # Detayları ekle
        for setting_id, gram in actual_grams.items():
            setting_id = int(setting_id)
            expected_gram = expected_data['details'].get(setting_id, {}).get('gram', 0)

            detail = DailyVaultDetail(
                daily_vault_id=daily_vault.id,
                setting_id=setting_id,
                expected_gram=expected_gram,
                actual_gram=float(gram)
            )

            db.session.add(detail)

        db.session.commit()
        return True, f"Günlük kasa kaydı oluşturuldu. Fark: {difference:.2f}g"

    @staticmethod
    def get_daily_vaults(start_date=None, end_date=None):
        """Günlük kasa kayıtlarını listele"""
        query = DailyVault.query

        if start_date:
            query = query.filter(DailyVault.date >= start_date)

        if end_date:
            query = query.filter(DailyVault.date <= end_date)

        return query.order_by(DailyVault.date.desc()).all()

    @staticmethod
    def get_region_status(region_name, setting_name):
        """Belirli bir bölgedeki belirli bir ayarın stok durumunu hesapla"""
        region = Region.query.filter_by(name=region_name).first()
        setting = Setting.query.filter_by(name=setting_name).first()

        if not region or not setting:
            return {setting_name: 0}

        # Eklenen toplam
        added = db.session.query(func.coalesce(func.sum(Operation.gram), 0)).filter(
            Operation.target_region_id == region.id,
            Operation.setting_id == setting.id,
            Operation.operation_type == OPERATION_ADD
        ).scalar()

        # Çıkarılan toplam
        subtracted = db.session.query(func.coalesce(func.sum(Operation.gram), 0)).filter(
            Operation.source_region_id == region.id,
            Operation.setting_id == setting.id,
            Operation.operation_type == OPERATION_SUBTRACT
        ).scalar()

        # Net stok miktarını hesapla
        net_stock = float(added - subtracted)

        return {setting_name: net_stock}