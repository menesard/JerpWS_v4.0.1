from datetime import datetime

from app import db
from app.models.database import Region, Setting, Operation, Customer, CustomerTransaction, User
from app.models.database import OPERATION_ADD, OPERATION_SUBTRACT
from app.models.database import TRANSACTION_PRODUCT_IN, TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_IN, TRANSACTION_SCRAP_OUT
from sqlalchemy import func

class SystemManager:
    @staticmethod
    def get_region_id(region_name):
        """Bölge adından ID'yi al"""
        region = Region.query.filter_by(name=region_name).first()
        return region.id if region else None

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
        region_id = SystemManager.get_region_id(region_name)
        setting_id = SystemManager.get_setting_id(setting_name)
        table_id = SystemManager.get_region_id('table')
        safe_id = SystemManager.get_region_id('safe')

        if region_id and setting_id:
            if region_name != 'table':
                # Masadan bölgeye transfer
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=table_id,
                    target_region_id=region_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id  # Kullanıcı ID'si eklendi
                )
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    target_region_id=region_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id  # Kullanıcı ID'si eklendi
                )
                db.session.add(subtract_op)
                db.session.add(add_op)
            else:
                # Kasadan masaya transfer
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=safe_id,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id  # Kullanıcı ID'si eklendi
                )
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id  # Kullanıcı ID'si eklendi
                )
                db.session.add(subtract_op)
                db.session.add(add_op)

            db.session.commit()
            return True
        return False

    @staticmethod
    def remove_item(region_name, setting_name, gram, user_id=None):
        """Bölgeden altın çıkar (masa üzerinden)"""
        region_id = SystemManager.get_region_id(region_name)
        setting_id = SystemManager.get_setting_id(setting_name)
        table_id = SystemManager.get_region_id('table')
        safe_id = SystemManager.get_region_id('safe')

        if region_id and setting_id:
            if region_name != 'table':
                # Bölgeden masaya transfer
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=region_id,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    target_region_id=table_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(subtract_op)
                db.session.add(add_op)
            else:
                # Masadan kasaya transfer
                subtract_op = Operation(
                    operation_type=OPERATION_SUBTRACT,
                    source_region_id=table_id,
                    target_region_id=safe_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id

                )
                add_op = Operation(
                    operation_type=OPERATION_ADD,
                    target_region_id=safe_id,
                    setting_id=setting_id,
                    gram=float(gram),
                    user_id=user_id
                )
                db.session.add(subtract_op)
                db.session.add(add_op)

            db.session.commit()
            return True
        return False

    @staticmethod
    def get_status(setting_name):
        """Tüm bölgelerin durumunu döndür"""
        setting_id = SystemManager.get_setting_id(setting_name)
        if not setting_id:
            return {}

        status = {}
        regions = Region.query.all()

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

            status[region_name] = {setting_name: added - subtracted}

        return status

    @staticmethod
    def get_logs(limit=50):
        """Son işlemleri döndür (kullanıcı bilgisi eklendi)"""
        operations = Operation.query.order_by(Operation.timestamp.desc()).limit(limit).all()
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

            logs.append({
                "time": op.timestamp.strftime('%d-%m-%Y %H:%M:%S'),
                "operation_type": op.operation_type,
                "source_region": source_region,
                "target_region": target_region,
                "setting": op.setting.name,
                "gram": f"{op.gram:.2f}",
                "username": username  # Kullanıcı bilgisi eklendi
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
                                 purity_per_thousand=None, labor_percentage=0, notes=None, user_id=None):
        """Müşteri işlemi ekle - has değer hesaplamalı"""
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
            created_by_user_id=user_id  # Kullanıcı ID'si eklendi
        )

        db.session.add(transaction)

        # Kasadan ürün çıkışı veya hurda çıkışı için kasa stokunu güncelle
        if transaction_type in [TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_OUT]:
            SystemManager.remove_item_safe(setting_name, gram, user_id=user_id)

        # Ürün girişi veya hurda girişi için kasa stokunu güncelle
        elif transaction_type in [TRANSACTION_PRODUCT_IN, TRANSACTION_SCRAP_IN]:
            SystemManager.add_item_safe(setting_name, gram, user_id=user_id)

        db.session.commit()
        return transaction

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