#!/usr/bin/env python3
import os
import shutil
import datetime
import tarfile
import gzip
from pathlib import Path
import subprocess
import platform

# Yedekleme dizinleri
BACKUP_DIR = Path("backups")
DAILY_DIR = BACKUP_DIR / "daily"
WEEKLY_DIR = BACKUP_DIR / "weekly"
MONTHLY_DIR = BACKUP_DIR / "monthly"

# Yedeklenecek dosyalar ve dizinler
BACKUP_ITEMS = [
    Path("instance") / "jewelry.db",  # Veritabanı
    Path("logs"),                     # Log dosyaları
]

def copy_file(source, dest):
    """Platform bağımsız dosya kopyalama"""
    try:
        if platform.system() == "Linux":
            # Linux'ta sudo kullan
            try:
                subprocess.run(['sudo', 'cp', '-r', str(source), str(dest)], check=True)
            except subprocess.CalledProcessError:
                # Sudo başarısız olursa normal kopyalama dene
                shutil.copy2(str(source), str(dest))
        else:
            # Windows ve diğer sistemlerde normal kopyalama
            shutil.copy2(str(source), str(dest))
        return True
    except Exception as e:
        print(f"Hata: {source} kopyalanamadı: {e}")
        return False

def create_backup(backup_type="daily"):
    """Belirtilen tipte yedek oluşturur"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"jerpws_backup_{backup_type}_{timestamp}"
    
    # Yedekleme dizinini belirle
    target_dir = {
        "daily": DAILY_DIR,
        "weekly": WEEKLY_DIR,
        "monthly": MONTHLY_DIR
    }[backup_type]
    
    # Geçici dizin oluştur
    temp_dir = BACKUP_DIR / "temp"
    temp_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        # Dosyaları kopyala
        for item in BACKUP_ITEMS:
            source = Path(item)
            if source.exists():
                dest = temp_dir / source.name
                if source.is_file():
                    copy_file(source, dest)
                else:
                    shutil.copytree(source, dest, dirs_exist_ok=True)
        
        # SSL sertifikalarını ayrıca kopyala
        ssl_source = Path("ssl")
        if ssl_source.exists():
            ssl_temp = temp_dir / "ssl"
            ssl_temp.mkdir(exist_ok=True)
            copy_file(ssl_source / "cert.pem", ssl_temp / "cert.pem")
            copy_file(ssl_source / "key.pem", ssl_temp / "key.pem")
        
        # Yedek dosyasını oluştur
        backup_path = target_dir / f"{backup_name}.tar.gz"
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(temp_dir, arcname="")
        
        print(f"Yedek oluşturuldu: {backup_path}")
        
        # Eski yedekleri temizle
        cleanup_old_backups(target_dir, backup_type)
        
    finally:
        # Geçici dizini temizle
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def cleanup_old_backups(backup_dir, backup_type):
    """Eski yedekleri temizler"""
    max_backups = {
        "daily": 7,    # Son 7 gün
        "weekly": 4,   # Son 4 hafta
        "monthly": 12  # Son 12 ay
    }[backup_type]
    
    backups = sorted(backup_dir.glob("*.tar.gz"))
    if len(backups) > max_backups:
        for old_backup in backups[:-max_backups]:
            old_backup.unlink()
            print(f"Eski yedek silindi: {old_backup}")

def main():
    # Dizinleri oluştur
    for dir_path in [BACKUP_DIR, DAILY_DIR, WEEKLY_DIR, MONTHLY_DIR]:
        dir_path.mkdir(exist_ok=True)
    
    # Günlük yedek oluştur
    create_backup("daily")
    
    # Haftalık yedek (Pazar günleri)
    if datetime.datetime.now().weekday() == 6:  # 6 = Pazar
        create_backup("weekly")
    
    # Aylık yedek (Ayın 1'i)
    if datetime.datetime.now().day == 1:
        create_backup("monthly")

if __name__ == "__main__":
    main() 