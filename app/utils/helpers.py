from datetime import datetime

def format_time(timestamp):
    """Zaman damgasını formatlı bir şekilde döndür"""
    if isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return timestamp.strftime('%d-%m-%Y %H:%M:%S')

def change_region_tr(name):
    """Bölge adını Türkçeye çevir"""
    region_map = {
        'polish': 'cila',
        'melting': 'eritme',
        'saw': 'patlatma',
        'acid': 'boru',
        'safe': 'kasa',
        'table': 'masa'
    }
    return region_map.get(name, name)

def change_region_en(name):
    """Bölge adını İngilizceye çevir"""
    region_map = {
        'cila': 'polish',
        'eritme': 'melting',
        'patlatma': 'saw',
        'boru': 'acid',
        'kasa': 'safe',
        'masa': 'table'
    }
    return region_map.get(name, name)

def change_operation_tr(name):
    """İşlem adını Türkçeye çevir"""
    if name.upper() == 'ADD':
        return 'EKLEME'
    elif name.upper() == 'SUBTRACT':
        return 'ÇIKARMA'
    return name

def get_transaction_type_tr(transaction_type):
    """İşlem türünü Türkçeye çevir"""
    type_map = {
        'PRODUCT_IN': 'ÜRÜN GİRİŞ',
        'PRODUCT_OUT': 'ÜRÜN ÇIKIŞ',
        'SCRAP_IN': 'HURDA GİRİŞ',
        'SCRAP_OUT': 'HURDA ÇIKIŞ'
    }
    return type_map.get(transaction_type, transaction_type)