from datetime import datetime

def format_time(timestamp):
    """Zaman damgasını formatlı bir şekilde döndür"""
    if isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return timestamp.strftime('%d-%m-%Y %H:%M:%S')

def change_region_tr(region_name):
    """İngilizce bölge adını Türkçeye çevir"""
    region_map = {
        'safe': 'Kasa',
        'table': 'Masa',
        'polish': 'Cila',
        'melting': 'Eritme',
        'saw': 'Testere',
        'acid': 'Asit',
        'kasa': 'Kasa',
        'masa': 'Masa',
        'yer': 'Yer'
    }
    return region_map.get(region_name, region_name.capitalize() if region_name else '-')

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

def change_operation_tr(operation_type):
    """İngilizce işlem türünü Türkçeye çevir"""
    operation_map = {
        'ADD': 'EKLEME',
        'SUBTRACT': 'ÇIKARMA'
    }
    return operation_map.get(operation_type, operation_type)

def get_transaction_type_tr(transaction_type):
    """İşlem türünü Türkçeye çevir"""
    type_map = {
        'PRODUCT_IN': 'ÜRÜN GİRİŞ',
        'PRODUCT_OUT': 'ÜRÜN ÇIKIŞ',
        'SCRAP_IN': 'HURDA GİRİŞ',
        'SCRAP_OUT': 'HURDA ÇIKIŞ'
    }
    return type_map.get(transaction_type, transaction_type)