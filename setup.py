import os
import secrets
import subprocess
from pathlib import Path
import sys
import venv

def create_env_file():
    """Ortam değişkenleri dosyasını oluştur"""
    env_content = f"""FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY={secrets.token_hex(32)}
JWT_SECRET_KEY={secrets.token_hex(32)}
DATABASE_URL=sqlite:///instance/kuyumcu.db
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✓ .env dosyası oluşturuldu")

def create_directories():
    """Gerekli dizinleri oluştur"""
    directories = [
        'instance',
        'logs',
        'backups/daily',
        'backups/weekly',
        'backups/monthly',
        'ssl'
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✓ Dizin yapısı oluşturuldu")

def setup_database():
    """Veritabanını oluştur ve ilk migration'ı yap"""
    try:
        subprocess.run(['flask', 'db', 'upgrade'], check=True)
        print("✓ Veritabanı oluşturuldu ve migration'lar uygulandı")
    except subprocess.CalledProcessError:
        print("! Veritabanı kurulumu başarısız oldu")
        return False
    return True

def create_ssl_cert():
    """Self-signed SSL sertifikası oluştur"""
    if not os.path.exists('ssl/cert.pem') or not os.path.exists('ssl/key.pem'):
        try:
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-nodes',
                '-out', 'ssl/cert.pem',
                '-keyout', 'ssl/key.pem',
                '-days', '365',
                '-subj', '/CN=localhost'
            ], check=True)
            print("✓ SSL sertifikaları oluşturuldu")
        except subprocess.CalledProcessError:
            print("! SSL sertifikası oluşturulamadı")
            return False
    return True

def setup_virtual_env():
    """Python sanal ortamı oluştur ve etkinleştir"""
    if not os.path.exists('venv'):
        print("Python sanal ortamı oluşturuluyor...")
        venv.create('venv', with_pip=True)
        print("✓ Sanal ortam oluşturuldu")
    
    # Sanal ortam yolunu belirle
    if sys.platform == 'win32':
        python_path = os.path.join('venv', 'Scripts', 'python')
        pip_path = os.path.join('venv', 'Scripts', 'pip')
    else:
        python_path = os.path.join('venv', 'bin', 'python')
        pip_path = os.path.join('venv', 'bin', 'pip')
    
    return python_path, pip_path

def install_requirements(pip_path):
    """Gerekli paketleri yükle"""
    if os.path.exists('requirements.txt'):
        print("Gerekli paketler yükleniyor...")
        try:
            subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
            print("✓ Paketler başarıyla yüklendi")
            return True
        except subprocess.CalledProcessError:
            print("! Paket yükleme başarısız oldu")
            return False
    else:
        print("! requirements.txt dosyası bulunamadı")
        return False

def main():
    print("JerpWS Kurulum Başlatılıyor...")
    
    # Python sanal ortamını oluştur
    python_path, pip_path = setup_virtual_env()
    
    # Gerekli paketleri yükle
    if not install_requirements(pip_path):
        print("! Kurulum tamamlanamadı: Paket yükleme hatası")
        return
    
    # Ortam değişkenleri dosyasını oluştur
    create_env_file()
    
    # Dizinleri oluştur
    create_directories()
    
    # Veritabanını kur
    if not setup_database():
        print("! Kurulum tamamlanamadı: Veritabanı hatası")
        return
    
    # SSL sertifikalarını oluştur
    if not create_ssl_cert():
        print("! SSL sertifikaları oluşturulamadı, HTTP kullanılacak")
    
    print("\nKurulum tamamlandı!")
    print("""
Sistemi başlatmak için:
Linux: ./start.sh
Windows: start.bat

Not: Production ortamında çalıştırmadan önce .env dosyasındaki anahtarları güncelleyin.
    """)

if __name__ == "__main__":
    main() 