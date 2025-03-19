from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, login_manager
from app.models.database import User, Setting, Operation, Region, FireDetail, Fire, DailyVault
from app.models.system_manager import SystemManager
from app.hardware.scale import ScaleManager
from app.utils.helpers import change_region_tr, change_operation_tr
from app.models.database import User, Setting, Customer, CustomerTransaction
from app.models.database import TRANSACTION_PRODUCT_IN, TRANSACTION_PRODUCT_OUT, TRANSACTION_SCRAP_IN, TRANSACTION_SCRAP_OUT
from datetime import datetime
# Blueprint oluştur
main_bp = Blueprint('main', __name__)


# Flask-Login için kullanıcı yükleme işlevi
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@main_bp.route('/')
def index():
    """Ana sayfa"""
    return redirect(url_for('main.dashboard'))


from flask_jwt_extended import create_access_token


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            # JWT token oluştur ve yanıta ekle
            access_token = create_access_token(identity=username)
            response = make_response(redirect(url_for('main.dashboard')))
            response.set_cookie('jwt_token', access_token, httponly=False)

            return response
        else:
            flash('Hatalı kullanıcı adı veya şifre!', 'danger')

    return render_template('login.html')


@main_bp.route('/logout')
@login_required
def logout():
    """Çıkış yap"""
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/select_setting', methods=['GET', 'POST'])
@login_required
def select_setting():
    """Ayar seçim sayfası"""
    if request.method == 'POST':
        setting = request.form.get('setting')
        if setting:
            session['selected_setting'] = setting
            return redirect(url_for('main.dashboard'))

    settings = Setting.query.all()
    return render_template('select_setting.html', settings=settings)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Kontrol paneli sayfası"""
    # Seçili ayar kontrol
    if 'selected_setting' not in session:
        return redirect(url_for('main.select_setting'))

    selected_setting = session['selected_setting']

    # Ağırlık bilgisini al
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        scale_manager.initialize(simulation_mode=True)
        scale_manager.start_monitoring()

    weight, is_valid = scale_manager.get_current_weight()

    # Bölge durumlarını al
    status = SystemManager.get_status(selected_setting)

    # Biraz format düzenlemesi
    formatted_status = []
    for region, setting_data in status.items():
        region_tr = change_region_tr(region)
        for setting, gram in setting_data.items():
            formatted_status.append({
                'region': region_tr,
                'region_en': region,
                'setting': setting,
                'gram': f"{gram:.2f}"
            })

    # Son işlemleri al
    logs = SystemManager.get_logs(10)  # Son 10 işlem

    return render_template(
        'dashboard.html',
        status=formatted_status,
        logs=logs,
        weight=weight,
        weight_valid=is_valid,
        selected_setting=selected_setting,
        change_region_tr=change_region_tr,  # Bu satırı ekleyin
        change_operation_tr=change_operation_tr  # Bu satırı ekleyin
    )


# İşlemler sayfasında sadece aktif bölgeleri gösterme

@main_bp.route('/operations', methods=['GET', 'POST'])
@login_required
def operations():
    """Manuel işlemler sayfası"""
    if 'selected_setting' not in session:
        return redirect(url_for('main.select_setting'))

    selected_setting = session['selected_setting']

    # Ağırlık bilgisini al
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        scale_manager.initialize(simulation_mode=True)
        scale_manager.start_monitoring()

    weight, is_valid = scale_manager.get_current_weight()

    if request.method == 'POST':
        operation_type = request.form.get('operation_type')
        region = request.form.get('region')
        gram = request.form.get('gram', type=float)

        # Kasa bölgesine manuel işlem yapılmasını engelle
        if region in ['safe', 'kasa']:
            flash('Kasa bölgesine manuel işlem yapılamaz!', 'danger')
            return redirect(url_for('main.operations'))

        if not gram:
            flash('Geçerli bir gram değeri giriniz!', 'danger')
        else:
            try:
                if operation_type == 'add':
                    result = SystemManager.add_item(region, selected_setting, gram, current_user.id)
                elif operation_type == 'subtract':
                    result = SystemManager.remove_item(region, selected_setting, gram, current_user.id)

                if result:
                    flash('İşlem başarıyla tamamlandı!', 'success')
                else:
                    flash('İşlem gerçekleştirilemedi!', 'danger')

            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'danger')

        return redirect(url_for('main.operations'))

    # Önce tüm aktif bölgeleri al
    all_regions = Region.query.filter_by(is_active=True).all()

    # Sonra kasa bölgesini filtrele (hem 'safe' hem de 'kasa' olabilir)
    regions = [{'name': region.name, 'name_tr': change_region_tr(region.name)}
               for region in all_regions
               if region.name not in ['safe', 'kasa']]

    return render_template(
        'operations.html',
        regions=regions,
        weight=weight,
        weight_valid=is_valid,
        selected_setting=selected_setting
    )


@main_bp.route('/history')
@login_required
def history():
    """İşlem geçmişi sayfası"""
    if 'selected_setting' not in session:
        return redirect(url_for('main.select_setting'))

    logs = SystemManager.get_logs(50)  # Son 50 işlem

    # İşlemleri formatla
    for log in logs:
        log['operation_type_tr'] = change_operation_tr(log['operation_type'])
        log['source_region_tr'] = change_region_tr(log['source_region'])
        log['target_region_tr'] = change_region_tr(log['target_region'])

    return render_template(
        'history.html',
        logs=logs,
        selected_setting=session['selected_setting']
    )


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Ayarlar sayfası"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Şifre değiştirme
        if 'change_password' in request.form:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not check_password_hash(current_user.password_hash, old_password):
                flash('Mevcut şifre yanlış!', 'danger')
            elif new_password != confirm_password:
                flash('Yeni şifreler eşleşmiyor!', 'danger')
            else:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Şifre başarıyla değiştirildi!', 'success')

        # Terazi ayarları
        elif 'scale_settings' in request.form:
            port = request.form.get('scale_port')
            simulation = 'simulation_mode' in request.form

            scale_manager = ScaleManager()
            scale_manager.close()
            result = scale_manager.initialize(port=port, simulation_mode=simulation)
            scale_manager.start_monitoring()

            if result:
                flash('Terazi ayarları güncellendi!', 'success')
            else:
                flash('Terazi bağlantısı kurulamadı!', 'danger')

    # Terazi durumunu al
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        scale_manager.initialize(simulation_mode=True)
        scale_manager.start_monitoring()

    scale_connected = scale_manager.scale.is_connected
    scale_simulation = scale_manager.scale.simulation_mode
    scale_port = scale_manager.scale.port

    return render_template(
        'settings.html',
        scale_connected=scale_connected,
        scale_simulation=scale_simulation,
        scale_port=scale_port
    )


@main_bp.route('/change_setting', methods=['POST'])
@login_required
def change_setting():
    """Ayar değiştirme"""
    setting = request.form.get('setting')
    if setting:
        session['selected_setting'] = setting
    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/tare_scale')
@login_required
def tare_scale():
    """Teraziyi sıfırla"""
    scale_manager = ScaleManager()
    if scale_manager.scale:
        result = scale_manager.tare()
        if result:
            flash('Terazi sıfırlandı!', 'success')
        else:
            flash('Terazi sıfırlanamadı!', 'danger')
    else:
        flash('Terazi bağlantısı yok!', 'danger')

    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/customers')
@login_required
def customers():
    """Müşteriler sayfası"""
    search = request.args.get('search', '')
    customers_list = SystemManager.get_customers(search)

    return render_template(
        'customers.html',
        customers=customers_list,
        search=search
    )


@main_bp.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """Müşteri ekleme sayfası"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')

        if not name:
            flash('Müşteri adı gereklidir!', 'danger')
        else:
            try:
                customer = SystemManager.add_customer(name, phone, email, address)
                flash('Müşteri başarıyla eklendi!', 'success')
                return redirect(url_for('main.customer_detail', customer_id=customer.id))
            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'danger')

    return render_template('customer_form.html')


@main_bp.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """Müşteri detay sayfası"""
    customer = SystemManager.get_customer(customer_id)
    if not customer:
        flash('Müşteri bulunamadı!', 'danger')
        return redirect(url_for('main.customers'))

    # Seçili ayar kontrolü
    if 'selected_setting' not in session:
        return redirect(url_for('main.select_setting'))

    selected_setting = session['selected_setting']

    # Müşteri bakiyesi
    balance = SystemManager.get_customer_balance(customer_id)

    # Has altın bakiyesi - sistem hazır değilse boş değer gönderin
    try:
        pure_gold_balance = SystemManager.get_customer_pure_gold_balance(customer_id)
    except (AttributeError, Exception):
        pure_gold_balance = {
            'pure_gold_inputs': 0.0,
            'pure_gold_outputs': 0.0,
            'net_pure_gold': 0.0,
            'labor_pure_gold_inputs': 0.0,
            'labor_pure_gold_outputs': 0.0,
            'net_labor_pure_gold': 0.0,
            'total_net_pure_gold': 0.0
        }

    # Müşteri işlemleri
    transactions = SystemManager.get_customer_transactions(customer_id)

    return render_template(
        'customer_detail.html',
        customer=customer,
        balance=balance,
        pure_gold_balance=pure_gold_balance,
        transactions=transactions,
        selected_setting=selected_setting,
        # transaction=??? eksik
    )


@main_bp.route('/customers/<int:customer_id>/add_transaction', methods=['GET', 'POST'])
@login_required
def add_customer_transaction(customer_id):
    """Müşteri işlemi ekleme sayfası"""
    customer = SystemManager.get_customer(customer_id)
    if not customer:
        flash('Müşteri bulunamadı!', 'danger')
        return redirect(url_for('main.customers'))

    # Seçili ayar kontrolü
    if 'selected_setting' not in session:
        return redirect(url_for('main.select_setting'))

    selected_setting = session['selected_setting']

    # Ayara göre milyem değerini al
    setting = Setting.query.filter_by(name=selected_setting).first()
    setting_purity = 916  # Varsayılan değer (22 ayar)

    # Setting modeli purity_per_thousand alanına sahipse kullan
    if hasattr(setting, 'purity_per_thousand'):
        setting_purity = setting.purity_per_thousand

    # Ağırlık bilgisini al
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        scale_manager.initialize(simulation_mode=True)
        scale_manager.start_monitoring()

    weight, is_valid = scale_manager.get_current_weight()

    if request.method == 'POST':
        transaction_type = request.form.get('transaction_type')
        product_description = request.form.get('product_description')
        gram = request.form.get('gram', type=float)
        purity_per_thousand = request.form.get('purity_per_thousand', type=int, default=setting_purity)
        labor_percentage = request.form.get('labor_percentage', type=float, default=0)
        notes = request.form.get('notes')

        # TL alanları kaldırıldı - varsayılan değerler atanıyor
        unit_price = None
        labor_cost = 0
        total_amount = 0

        if not transaction_type or not gram:
            flash('İşlem tipi ve gram değeri gereklidir!', 'danger')
        else:
            try:
                # Has değerleri için model uygunsa has hesaplamalarını kullan
                transaction = SystemManager.add_customer_transaction(
                    customer_id=customer_id,
                    transaction_type=transaction_type,
                    setting_name=selected_setting,
                    gram=gram,
                    user_id=current_user.id,
                    product_description=product_description,
                    unit_price=unit_price,
                    labor_cost=labor_cost,
                    purity_per_thousand=purity_per_thousand,
                    labor_percentage=labor_percentage,
                    notes=notes
                )

                if transaction:
                    flash('İşlem başarıyla eklendi!', 'success')
                    return redirect(url_for('main.customer_detail', customer_id=customer_id))
                else:
                    flash('İşlem eklenirken bir hata oluştu!', 'danger')

            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'danger')
                print(f"İşlem eklenirken hata: {str(e)}")

    # İşlem türleri
    transaction_types = [
        {'value': 'PRODUCT_IN', 'label': 'Ürün Giriş (Müşteriden Al)'},
        {'value': 'PRODUCT_OUT', 'label': 'Ürün Çıkış (Müşteriye Ver)'},
        {'value': 'SCRAP_IN', 'label': 'Hurda Giriş (Müşteriden Al)'},
        {'value': 'SCRAP_OUT', 'label': 'Hurda Çıkış (Müşteriye Ver)'}
    ]

    return render_template(
        'customer_transaction_form.html',
        customer=customer,
        transaction_types=transaction_types,
        selected_setting=selected_setting,
        setting_purity=setting_purity,
        weight=weight,
        weight_valid=is_valid
    )

@main_bp.route('/transactions/<int:transaction_id>')
@login_required
def transaction_detail(transaction_id):
    """İşlem detay sayfası"""
    transaction = SystemManager.get_transaction(transaction_id)

    if not transaction:
        flash('İşlem bulunamadı!', 'danger')
        return redirect(url_for('main.dashboard'))

    # İşlem geçmişini al
    transaction_history = SystemManager.get_transaction_history(transaction_id)

    # Müşteri bilgilerini al
    customer = Customer.query.get(transaction.customer_id)

    # İşlem türünü Türkçeye çevir
    transaction_type_tr = SystemManager.get_transaction_type_tr(transaction.transaction_type)

    return render_template(
        'transaction_detail.html',
        transaction=transaction,
        transaction_history=transaction_history,
        customer=customer,
        transaction_type_tr=transaction_type_tr
    )


@main_bp.route('/transactions/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    """İşlem düzenleme sayfası"""
    transaction = SystemManager.get_transaction(transaction_id)

    if not transaction:
        flash('İşlem bulunamadı!', 'danger')
        return redirect(url_for('main.dashboard'))

    # Ayarları al
    settings = Setting.query.all()

    # Mevcut ayarın milyem değerini al
    setting = Setting.query.get(transaction.setting_id)
    setting_purity = setting.purity_per_thousand if hasattr(setting, 'purity_per_thousand') else 916

    # Ağırlık bilgisini al
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        scale_manager.initialize(simulation_mode=True)
        scale_manager.start_monitoring()

    weight, is_valid = scale_manager.get_current_weight()

    if request.method == 'POST':
        transaction_type = request.form.get('transaction_type')
        product_description = request.form.get('product_description')
        gram = request.form.get('gram', type=float)
        setting_id = request.form.get('setting_id', type=int)
        purity_per_thousand = request.form.get('purity_per_thousand', type=int, default=setting_purity)
        labor_percentage = request.form.get('labor_percentage', type=float, default=0)
        notes = request.form.get('notes')

        if not transaction_type or not gram or not setting_id:
            flash('İşlem tipi, gram ve ayar değerleri gereklidir!', 'danger')
        else:
            try:
                # Has değeri hesapla
                pure_gold_weight = SystemManager.calculate_pure_gold_weight(gram, purity_per_thousand)

                # İşçilik has karşılığını hesapla
                labor_pure_gold = SystemManager.calculate_labor_pure_gold(gram, labor_percentage)

                # İşlemi düzenle
                edited_transaction = SystemManager.edit_customer_transaction(
                    transaction_id=transaction_id,
                    user_id=current_user.id,
                    transaction_type=transaction_type,
                    gram=gram,
                    setting_id=setting_id,
                    product_description=product_description,
                    purity_per_thousand=purity_per_thousand,
                    pure_gold_weight=pure_gold_weight,
                    labor_percentage=labor_percentage,
                    labor_pure_gold=labor_pure_gold,
                    notes=notes
                )

                if edited_transaction:
                    flash('İşlem başarıyla düzenlendi!', 'success')
                    return redirect(url_for('main.transaction_detail', transaction_id=edited_transaction.id))
                else:
                    flash('İşlem düzenlenemedi!', 'danger')

            except Exception as e:
                flash(f'Hata oluştu: {str(e)}', 'danger')
                print(f"İşlem düzenlenirken hata: {str(e)}")

    # İşlem türleri
    transaction_types = [
        {'value': 'PRODUCT_IN', 'label': 'Ürün Giriş (Müşteriden Al)'},
        {'value': 'PRODUCT_OUT', 'label': 'Ürün Çıkış (Müşteriye Ver)'},
        {'value': 'SCRAP_IN', 'label': 'Hurda Giriş (Müşteriden Al)'},
        {'value': 'SCRAP_OUT', 'label': 'Hurda Çıkış (Müşteriye Ver)'}
    ]

    return render_template(
        'transaction_edit.html',
        transaction=transaction,
        transaction_types=transaction_types,
        settings=settings,
        setting_purity=setting_purity,
        weight=weight,
        weight_valid=is_valid,
        now=datetime.utcnow()
    )


@main_bp.route('/users')
@login_required
def users():
    """Kullanıcılar sayfası - sadece admin ve yöneticiler görebilir"""
    if not current_user.has_role('manager'):
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.dashboard'))

    # Eğer yönetici ise, sadece kendi oluşturduğu veya admin değilse admin kullanıcıları hariç hepsini göster
    if current_user.is_admin:
        users_list = User.query.all()
    else:
        users_list = User.query.filter(
            db.or_(
                User.created_by_id == current_user.id,
                db.and_(User.role != 'admin', User.is_admin == False)
            )
        ).all()

    return render_template('users.html', users=users_list)


@main_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Kullanıcı ekleme sayfası - sadece admin ve yöneticiler"""
    if not current_user.has_role('manager'):
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        # Admin olmayan bir kullanıcı, kendinden daha yetkili bir kullanıcı ekleyemez
        if not current_user.is_admin and role == 'admin':
            flash('Admin kullanıcı ekleme yetkiniz yok!', 'danger')
            return redirect(url_for('main.users'))

        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor!', 'danger')
        elif password != confirm_password:
            flash('Şifreler eşleşmiyor!', 'danger')
        else:
            from werkzeug.security import generate_password_hash
            is_admin = role == 'admin'
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                is_admin=is_admin,
                role=role,
                created_by_id=current_user.id
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Kullanıcı başarıyla eklendi!', 'success')
            return redirect(url_for('main.users'))

    return render_template('user_form.html')


@main_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Kullanıcı düzenleme sayfası"""
    if not current_user.has_role('manager'):
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)

    # Kendinden daha yetkili kullanıcıyı düzenleyemez, kendini düzenleyebilir
    if not current_user.is_admin and (user.is_admin or (user.role == 'manager' and current_user.role != 'manager')):
        if user.id != current_user.id:
            flash('Bu kullanıcıyı düzenleme yetkiniz yok!', 'danger')
            return redirect(url_for('main.users'))

    if request.method == 'POST':
        role = request.form.get('role')
        password = request.form.get('password')

        # Rol değişikliği kontrolü
        if not current_user.is_admin and role == 'admin':
            flash('Admin rolü atama yetkiniz yok!', 'danger')
        else:
            if role and user.id != current_user.id:  # Kendi rolünü değiştiremez
                user.role = role
                user.is_admin = (role == 'admin')

            # Şifre değişikliği
            if password:
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash(password)

            db.session.commit()
            flash('Kullanıcı başarıyla güncellendi!', 'success')
            return redirect(url_for('main.users'))

    return render_template('user_edit.html', user=user)


@main_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Kullanıcı silme"""
    if not current_user.has_role('manager'):
        flash('Bu işlem için yetkiniz yok!', 'danger')
        return redirect(url_for('main.users'))

    user = User.query.get_or_404(user_id)

    # Kendini veya kendinden daha yetkili kullanıcıyı silemez
    if user.id == current_user.id:
        flash('Kendinizi silemezsiniz!', 'danger')
    elif not current_user.is_admin and (user.is_admin or (user.role == 'manager' and current_user.role != 'manager')):
        flash('Bu kullanıcıyı silme yetkiniz yok!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Kullanıcı başarıyla silindi!', 'success')

    return redirect(url_for('main.users'))


@main_bp.route('/users/<int:user_id>/operations')
@login_required
def user_operations(user_id):
    """Kullanıcı işlemleri sayfası"""
    user = User.query.get_or_404(user_id)

    # Yetkisiz erişim kontrolü
    if not current_user.has_role('manager') and current_user.id != user_id:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.dashboard'))

    # Son 20 işlemi göster
    operations = Operation.query.filter_by(user_id=user_id).order_by(Operation.timestamp.desc()).limit(20).all()

    return render_template('user_operations.html', user=user, operations=operations)


# main_bp.route('/stock') fonksiyonunda yapılacak değişiklikler

@main_bp.route('/stock')
@login_required
def stock():
    """Stok durumu sayfası"""
    if 'selected_setting' not in session:
        return redirect(url_for('main.select_setting'))

    # Tüm ayarları al
    settings = [setting.name for setting in Setting.query.all()]

    # Sadece aktif bölgeleri al
    regions = [{'name': region.name, 'name_tr': change_region_tr(region.name)}
               for region in Region.query.filter_by(is_active=True).all()]

    # Her ayar için stok durumunu al
    stock_data = []
    totals = {}
    total_pure_gold = 0

    for setting_name in settings:
        setting = Setting.query.filter_by(name=setting_name).first()
        status = SystemManager.get_status(setting_name)
        setting_total = 0

        for region, setting_data in status.items():
            # Sadece aktif bölgeleri göster
            region_obj = Region.query.filter_by(name=region).first()
            if region_obj and region_obj.is_active:
                region_tr = change_region_tr(region)
                for s, gram in setting_data.items():
                    stock_data.append({
                        'region': region_tr,
                        'region_en': region,
                        'setting': s,
                        'gram': f"{gram:.2f}"
                    })
                    # Toplam hesapla
                    setting_total += gram

        # Ayar için toplam ve has değer hesapla
        if setting_total > 0:
            totals[setting_name] = {
                'total': setting_total,
                'purity': setting.purity_per_thousand
            }
            # Has altın değeri hesapla ve toplama ekle
            total_pure_gold += setting_total * setting.purity_per_thousand / 1000

    return render_template(
        'stock.html',
        settings=settings,
        regions=regions,
        stock_data=stock_data,
        totals=totals,
        total_pure_gold=total_pure_gold
    )


@main_bp.route('/regions', methods=['GET', 'POST'])
@login_required
def manage_regions():
    """Bölge yönetim sayfası"""
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if 'add_region' in request.form:
            region_name = request.form.get('region_name')
            if region_name:
                success, message = SystemManager.add_region(region_name)
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'danger')
        elif 'delete_region' in request.form:
            region_id = request.form.get('region_id')
            if region_id:
                success, message = SystemManager.deactivate_region(int(region_id))
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'danger')
        elif 'restore_region' in request.form:
            region_id = request.form.get('region_id')
            if region_id:
                success, message = SystemManager.activate_region(int(region_id))
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'danger')

        return redirect(url_for('main.manage_regions'))

    # Aktif ve silinen bölgeleri ayrı ayrı getir
    active_regions = Region.query.filter_by(is_active=True).all()
    deleted_regions = Region.query.filter_by(is_active=False).all()

    # Her bölgedeki toplam altını hesapla
    region_totals = {}
    for region in active_regions:
        region_totals[region.id] = 0
        for setting in Setting.query.all():
            status = SystemManager.get_region_status(region.name, setting.name)
            region_totals[region.id] += status[setting.name] if setting.name in status else 0

    return render_template(
        'regions.html',
        active_regions=active_regions,
        deleted_regions=deleted_regions,
        region_totals=region_totals
    )


@main_bp.route('/ramat', methods=['GET', 'POST'])
@login_required
def ramat():
    """Ramat işlemi sayfası"""
    if not current_user.has_role('manager'):
        flash('Bu sayfaya erişim için yönetici yetkisi gereklidir!', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        actual_pure_gold = request.form.get('actual_pure_gold', type=float)
        notes = request.form.get('notes')

        if actual_pure_gold:
            success, message = SystemManager.create_ramat(current_user.id, actual_pure_gold, notes)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
        else:
            flash('Geçerli bir has değeri giriniz!', 'danger')

        return redirect(url_for('main.ramat'))

    # Bölge bazında has değerlerini hesapla
    regions = Region.query.filter_by(is_active=True).all()
    region_data = []
    total_pure_gold = 0

    for region in regions:
        if region.name == 'kasa':
            continue  # Kasa bölgesini ramat hesabına katmıyoruz

        region_pure_gold = 0
        setting_data = []

        for setting in Setting.query.all():
            status = SystemManager.get_region_status(region.name, setting.name)
            gram = status.get(setting.name, 0)

            if gram > 0:
                pure_gold = gram * (setting.purity_per_thousand / 1000)
                region_pure_gold += pure_gold

                setting_data.append({
                    'name': setting.name,
                    'gram': gram,
                    'purity': setting.purity_per_thousand,
                    'pure_gold': pure_gold
                })

        if region_pure_gold > 0:
            region_data.append({
                'name': region.name,
                'settings': setting_data,
                'total_pure_gold': region_pure_gold
            })
            total_pure_gold += region_pure_gold

    return render_template(
        'ramat.html',
        region_data=region_data,
        total_pure_gold=total_pure_gold
    )


@main_bp.route('/fires')
@login_required
def fires():
    """Fire kayıtları sayfası"""
    # Tüm fire kayıtlarını getir
    fires = Fire.query.order_by(Fire.timestamp.desc()).all()

    return render_template(
        'fires.html',
        fires=fires
    )


@main_bp.route('/fires/<int:fire_id>')
@login_required
def fire_detail(fire_id):
    """Fire detay sayfası"""
    fire = Fire.query.get_or_404(fire_id)

    # Fire detaylarını getir
    details = FireDetail.query.filter_by(fire_id=fire.id).all()

    # Detayları gruplama
    region_details = {}
    for detail in details:
        if detail.region.name not in region_details:
            region_details[detail.region.name] = []

        region_details[detail.region.name].append({
            'setting': detail.setting.name,
            'gram': detail.gram,
            'purity': detail.setting.purity_per_thousand,
            'pure_gold': detail.pure_gold
        })

    return render_template(
        'fire_detail.html',
        fire=fire,
        region_details=region_details
    )


@main_bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    """Masraflar sayfası"""
    if request.method == 'POST':
        description = request.form.get('description')
        amount_tl = request.form.get('amount_tl', type=float, default=0)
        amount_gold = request.form.get('amount_gold', type=float, default=0)
        gold_price = request.form.get('gold_price', type=float, default=0)

        if description:
            success, message = SystemManager.add_expense(
                description, amount_tl, amount_gold, gold_price, current_user.id
            )
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
        else:
            flash('Masraf açıklaması gereklidir!', 'danger')

        return redirect(url_for('main.expenses'))

    # Filtreleri al
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    include_used = request.args.get('include_used') == 'on'

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # Günün sonuna ayarla
        end_date = end_date.replace(hour=23, minute=59, second=59)

    expenses = SystemManager.get_expenses(start_date, end_date, include_used)

    return render_template(
        'expenses.html',
        expenses=expenses,
        start_date=start_date.strftime('%Y-%m-%d') if start_date else '',
        end_date=end_date.strftime('%Y-%m-%d') if end_date else '',
        include_used=include_used
    )


@main_bp.route('/transfers')
@login_required
def transfers():
    """Devir işlemleri sayfası"""
    transfers = SystemManager.get_transfers()

    return render_template(
        'transfers.html',
        transfers=transfers
    )


@main_bp.route('/transfers/new', methods=['GET', 'POST'])
@login_required
def new_transfer():
    """Yeni devir işlemi sayfası"""
    if not current_user.has_role('manager'):
        flash('Bu sayfaya erişim için yönetici yetkisi gereklidir!', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            success, message = SystemManager.create_transfer(current_user.id)

            if success:
                flash(message, 'success')
                return redirect(url_for('main.transfers'))
            else:
                flash(message, 'danger')
        except Exception as e:
            flash(f'Hata oluştu: {str(e)}', 'danger')

        return redirect(url_for('main.new_transfer'))

    # Devir hesapla
    transfer_data = SystemManager.calculate_transfer()

    return render_template(
        'new_transfer.html',
        transfer_data=transfer_data
    )


@main_bp.route('/transfers/<int:transfer_id>')
@login_required
def transfer_detail(transfer_id):
    """Devir detay sayfası"""
    transfer_details = SystemManager.get_transfer_details(transfer_id)

    if not transfer_details:
        flash('Devir işlemi bulunamadı!', 'danger')
        return redirect(url_for('main.transfers'))

    return render_template(
        'transfer_detail.html',
        transfer=transfer_details['transfer'],
        transactions=transfer_details['transactions'],
        expenses=transfer_details['expenses']
    )


@main_bp.route('/daily-vault', methods=['GET', 'POST'])
@login_required
def daily_vault():
    """Günlük kasa sayfası"""
    if request.method == 'POST':
        actual_grams = {}

        # Form'dan ayar bazında gramları al
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_id = key.replace('setting_', '')
                try:
                    actual_grams[setting_id] = float(value)
                except ValueError:
                    actual_grams[setting_id] = 0

        notes = request.form.get('notes')

        if actual_grams:
            success, message = SystemManager.create_daily_vault(current_user.id, actual_grams, notes)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
        else:
            flash('Geçerli veri girilmedi!', 'danger')

        return redirect(url_for('main.daily_vault_history'))

    # Beklenen değerleri hesapla
    expected_data = SystemManager.calculate_vault_expected()

    # Bugün kayıt yapılmış mı kontrol et
    today = datetime.utcnow().date()
    today_record = DailyVault.query.filter(DailyVault.date == today).first()

    return render_template(
        'daily_vault.html',
        expected_data=expected_data,
        today_record=today_record
    )


@main_bp.route('/daily-vault/history')
@login_required
def daily_vault_history():
    """Günlük kasa geçmişi sayfası"""
    # Filtreleri al
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    daily_vaults = SystemManager.get_daily_vaults(start_date, end_date)

    return render_template(
        'daily_vault_history.html',
        daily_vaults=daily_vaults,
        start_date=start_date.strftime('%Y-%m-%d') if start_date else '',
        end_date=end_date.strftime('%Y-%m-%d') if end_date else ''
    )


@main_bp.route('/daily-vault/<int:vault_id>')
@login_required
def daily_vault_detail(vault_id):
    """Günlük kasa detay sayfası"""
    daily_vault = DailyVault.query.get_or_404(vault_id)

    return render_template(
        'daily_vault_detail.html',
        daily_vault=daily_vault
    )