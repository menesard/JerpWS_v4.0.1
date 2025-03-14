from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from app import db
from flask_login import current_user
from app.models.database import User
from app.models.system_manager import SystemManager
from app.hardware.scale import ScaleManager
from werkzeug.security import check_password_hash

# Blueprint oluştur
api_bp = Blueprint('api', __name__)

# JWT Manager'ı initialize et
jwt = JWTManager()


@api_bp.route('/login', methods=['POST'])
def api_login():
    """API Giriş endpoint'i"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Eksik kullanıcı adı veya şifre"}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    return jsonify({"error": "Hatalı kullanıcı adı veya şifre"}), 401


@api_bp.route('/weight', methods=['GET'])
def get_weight():
    """Güncel ağırlık bilgisini döndür - JWT kimlik doğrulaması olmadan erişilebilir"""
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        scale_manager.initialize(simulation_mode=True)
        scale_manager.start_monitoring()

    weight, is_valid = scale_manager.get_current_weight()

    return jsonify({
        "weight": weight,
        "is_valid": is_valid
    }), 200

@api_bp.route('/tare', methods=['POST'])
@jwt_required()
def tare_scale():
    """Teraziyi sıfırla"""
    scale_manager = ScaleManager()
    if not scale_manager.scale:
        return jsonify({"error": "Terazi bağlantısı yok"}), 400

    result = scale_manager.tare()
    if result:
        return jsonify({"message": "Terazi sıfırlandı"}), 200

    return jsonify({"error": "Terazi sıfırlanamadı"}), 400


@api_bp.route('/status/<setting>', methods=['GET'])
def get_status(setting):
    """Belirli bir ayar için sistem durumunu döndür"""
    status = SystemManager.get_status(setting)
    return jsonify({"status": status}), 200


@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """İşlem kayıtlarını döndür"""
    limit = request.args.get('limit', 50, type=int)
    logs = SystemManager.get_logs(limit)
    return jsonify({"logs": logs}), 200


@api_bp.route('/add_item', methods=['POST'])
@jwt_required()
def add_item():
    """Manuel olarak altın ekle"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Geçersiz veri"}), 400

    region = data.get('region')
    setting = data.get('setting')
    gram = data.get('gram')

    if not region or not setting or not gram:
        return jsonify({"error": "Eksik parametreler"}), 400

    # Kullanıcı kimliğini al
    current_user = User.query.filter_by(username=get_jwt_identity()).first()

    if not current_user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401

    try:
        gram = float(gram)

        if region == 'safe':
            result = SystemManager.add_item_safe(setting, gram, current_user.id)
        else:
            result = SystemManager.add_item(region, setting, gram, current_user.id)

        if result:
            return jsonify({"message": "İşlem başarılı"}), 200
        else:
            return jsonify({"error": "İşlem başarısız"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/remove_item', methods=['POST'])
@jwt_required()
def remove_item():
    """Manuel olarak altın çıkar"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Geçersiz veri"}), 400

    region = data.get('region')
    setting = data.get('setting')
    gram = data.get('gram')

    if not region or not setting or not gram:
        return jsonify({"error": "Eksik parametreler"}), 400

    current_user = User.query.filter_by(username=get_jwt_identity()).first()

    if not current_user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 401

    try:
        gram = float(gram)

        if region == 'safe':
            result = SystemManager.remove_item_safe(setting, gram, current_user.id)
        else:
            result = SystemManager.remove_item(region, setting, gram, current_user.id)

        if result:
            return jsonify({"message": "İşlem başarılı"}), 200
        else:
            return jsonify({"error": "İşlem başarısız"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """Müşteri listesini döndür"""
    search = request.args.get('search')
    customers = SystemManager.get_customers(search)

    result = []
    for customer in customers:
        result.append({
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone or "",
            "email": customer.email or "",
            "address": customer.address or ""
        })

    return jsonify({"customers": result}), 200


@api_bp.route('/customers', methods=['POST'])
@jwt_required()
def add_customer():
    """Yeni müşteri ekle"""
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({"error": "Müşteri adı gereklidir"}), 400

    try:
        customer = SystemManager.add_customer(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address')
        )

        return jsonify({
            "message": "Müşteri başarıyla eklendi",
            "customer_id": customer.id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Müşteri detaylarını döndür"""
    customer = SystemManager.get_customer(customer_id)

    if not customer:
        return jsonify({"error": "Müşteri bulunamadı"}), 404

    result = {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone or "",
        "email": customer.email or "",
        "address": customer.address or "",
    }

    return jsonify({"customer": result}), 200


@api_bp.route('/customers/<int:customer_id>/balance', methods=['GET'])
@jwt_required()
def get_customer_balance(customer_id):
    """Müşteri bakiyesini döndür"""
    setting = request.args.get('setting')
    balance = SystemManager.get_customer_balance(customer_id, setting)

    if not balance:
        return jsonify({"error": "Müşteri veya ayar bulunamadı"}), 404

    return jsonify({"balance": balance}), 200


@api_bp.route('/customers/<int:customer_id>/transactions', methods=['GET'])
@jwt_required()
def get_customer_transactions(customer_id):
    """Müşteri işlemlerini döndür"""
    limit = request.args.get('limit', 50, type=int)
    transactions = SystemManager.get_customer_transactions(customer_id, limit)

    return jsonify({"transactions": transactions}), 200


@api_bp.route('/settings/<setting_name>/purity', methods=['GET'])
def get_setting_purity(setting_name):
    """Ayarın milyem değerini döndür - JWT kimlik doğrulaması olmadan erişilebilir"""
    setting = SystemManager.get_setting_with_purity(setting_name)

    if not setting:
        return jsonify({"error": "Ayar bulunamadı"}), 404

    return jsonify({
        "setting": setting.name,
        "purity_per_thousand": setting.purity_per_thousand
    }), 200


@api_bp.route('/customers/<int:customer_id>/pure_gold_balance', methods=['GET'])
@jwt_required()
def get_customer_pure_gold_balance(customer_id):
    """Müşteri has altın bakiyesini döndür"""
    customer = SystemManager.get_customer(customer_id)

    if not customer:
        return jsonify({"error": "Müşteri bulunamadı"}), 404

    pure_gold_balance = SystemManager.get_customer_pure_gold_balance(customer_id)

    return jsonify({"pure_gold_balance": pure_gold_balance}), 200


@api_bp.route('/calculate/pure_gold', methods=['POST'])
def calculate_pure_gold():
    """Has altın hesaplama - JWT kimlik doğrulaması olmadan erişilebilir"""
    data = request.get_json()

    if not data or 'gram' not in data or 'purity_per_thousand' not in data:
        return jsonify({"error": "Eksik parametreler"}), 400

    try:
        gram = float(data['gram'])
        purity = int(data['purity_per_thousand'])
        pure_gold = SystemManager.calculate_pure_gold_weight(gram, purity)

        return jsonify({
            "gram": gram,
            "purity_per_thousand": purity,
            "pure_gold_weight": pure_gold
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/calculate/labor_pure_gold', methods=['POST'])
def calculate_labor_pure_gold():
    """İşçilik has karşılığı hesaplama - JWT kimlik doğrulaması olmadan erişilebilir"""
    data = request.get_json()

    if not data or 'gram' not in data or 'labor_percentage' not in data:
        return jsonify({"error": "Eksik parametreler"}), 400

    try:
        gram = float(data['gram'])
        labor_percentage = float(data['labor_percentage'])
        labor_pure_gold = SystemManager.calculate_labor_pure_gold(gram, labor_percentage)

        return jsonify({
            "gram": gram,
            "labor_percentage": labor_percentage,
            "labor_pure_gold": labor_pure_gold
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route('/customers/<int:customer_id>/transactions', methods=['POST'])
@jwt_required()
def add_customer_transaction(customer_id):
    """Yeni müşteri işlemi ekle - tüm has değer hesaplamaları ile"""
    data = request.get_json()

    if not data or 'transaction_type' not in data or 'setting' not in data or 'gram' not in data:
        return jsonify({"error": "Eksik parametreler"}), 400

    try:
        # Setting bilgisini al ve varsayılan milyem değerini kullan
        setting = SystemManager.get_setting_with_purity(data.get('setting'))
        purity_per_thousand = data.get('purity_per_thousand', setting.purity_per_thousand if setting else 916)

        transaction = SystemManager.add_customer_transaction(
            customer_id=customer_id,
            transaction_type=data.get('transaction_type'),
            setting_name=data.get('setting'),
            gram=float(data.get('gram')),
            product_description=data.get('product_description'),
            unit_price=data.get('unit_price'),
            labor_cost=data.get('labor_cost', 0),
            purity_per_thousand=purity_per_thousand,
            labor_percentage=data.get('labor_percentage', 0),
            notes=data.get('notes')
        )

        if transaction:
            return jsonify({
                "message": "İşlem başarıyla eklendi",
                "transaction_id": transaction.id,
                "pure_gold_weight": transaction.pure_gold_weight,
                "labor_pure_gold": transaction.labor_pure_gold
            }), 201
        else:
            return jsonify({"error": "İşlem eklenemedi"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400