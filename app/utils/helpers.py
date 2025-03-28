from datetime import datetime
import requests
import pytz

def format_time(timestamp, timezone_str=None):
    """Zaman damgasını formatlı bir şekilde döndür"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return timestamp
    
    # Zaman dilimi dönüşümü yap (eğer belirtilmişse)
    if timezone_str and timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=pytz.UTC)
        local_timezone = pytz.timezone(timezone_str)
        timestamp = timestamp.astimezone(local_timezone)
    
    # Türkçe tarih formatı: gün-ay-yıl saat:dakika:saniye
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

def get_timezone_from_ip(ip_address):
    """
    IP adresinden zaman dilimini tespit eder.
    Ücretsiz ipinfo.io servisi kullanılıyor.
    """
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            data = response.json()
            timezone = data.get('timezone')
            if timezone:
                return timezone
    except Exception as e:
        print(f"IP zaman dilimi tespitinde hata: {e}")
    
    return 'UTC'  # Varsayılan olarak UTC döndür

def convert_utc_to_local(utc_time, timezone_str):
    """
    UTC zamanını verilen zaman dilimine çevirir
    """
    if not utc_time:
        return None
        
    if isinstance(utc_time, str):
        try:
            utc_time = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
        except ValueError:
            try:
                utc_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return utc_time
    
    if not isinstance(utc_time, datetime):
        return utc_time
        
    utc_time = utc_time.replace(tzinfo=pytz.UTC)
    local_timezone = pytz.timezone(timezone_str)
    local_time = utc_time.astimezone(local_timezone)
    
    return local_time