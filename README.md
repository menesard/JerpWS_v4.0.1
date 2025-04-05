# JerpWS - Kuyumcu Yönetim Sistemi

JerpWS, kuyumcular için geliştirilmiş modern bir web tabanlı yönetim sistemidir. Sistem hem Windows hem de Linux işletim sistemlerinde çalışabilir şekilde tasarlanmıştır.

## Sistem Gereksinimleri

### Windows için:
- Python 3.8 veya üzeri
- NSSM (Non-Sucking Service Manager)
- Git (opsiyonel)

### Linux için:
- Python 3.8 veya üzeri
- systemd
- Git (opsiyonel)

## Kurulum

### Windows'ta Kurulum

1. Python'u yükleyin:
   - [Python'un resmi sitesinden](https://www.python.org/downloads/) Python 3.8 veya üzerini indirin
   - Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin

2. NSSM'i yükleyin:
   - [NSSM'in resmi sitesinden](https://nssm.cc/download) son sürümü indirin
   - Zip dosyasını açın
   - `nssm.exe` dosyasını `C:\Windows\System32` dizinine kopyalayın veya PATH'e ekleyin

3. Uygulamayı indirin:
   ```batch
   git clone https://github.com/user/JerpWS.git
   cd JerpWS
   ```
   veya zip olarak indirip açın.

4. Servisi kurun:
   ```batch
   install_windows_service.bat
   ```
   
   Bu komut otomatik olarak:
   - Python sanal ortamını oluşturacak
   - Gerekli paketleri yükleyecek
   - Veritabanını oluşturacak
   - Windows servisi olarak sistemi kuracak
   - Servisi başlatacak

### Linux'ta Kurulum

1. Gerekli paketleri yükleyin:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. Uygulamayı indirin:
   ```bash
   git clone https://github.com/user/JerpWS.git
   cd JerpWS
   ```
   veya zip olarak indirip açın.

3. Servisi kurun:
   ```bash
   sudo ./install_linux_service.sh
   ```

   Bu komut otomatik olarak:
   - Python sanal ortamını oluşturacak
   - Gerekli paketleri yükleyecek
   - Veritabanını oluşturacak
   - systemd servisi olarak sistemi kuracak
   - Servisi başlatacak

## Servis Yönetimi

### Windows'ta Servis Yönetimi

```batch
# Servis durumunu kontrol et
sc query JerpWS

# Servisi başlat
net start JerpWS

# Servisi durdur
net stop JerpWS

# Servisi yeniden başlat
net stop JerpWS && net start JerpWS

# Logları görüntüle
type logs\service.log
```

### Linux'ta Servis Yönetimi

```bash
# Servis durumunu kontrol et
sudo systemctl status jerpws

# Servisi başlat
sudo systemctl start jerpws

# Servisi durdur
sudo systemctl stop jerpws

# Servisi yeniden başlat
sudo systemctl restart jerpws

# Logları görüntüle
sudo journalctl -u jerpws
```

## SSL Sertifikaları

Sistem varsayılan olarak self-signed SSL sertifikaları ile gelir. Production ortamında kullanmadan önce:

1. Güvenilir bir sertifika sağlayıcısından SSL sertifikası alın
2. Sertifikaları `ssl` dizinine yerleştirin:
   - `ssl/cert.pem`: Sertifika dosyası
   - `ssl/key.pem`: Özel anahtar dosyası

## Güvenlik Ayarları

Production ortamında kullanmadan önce:

1. `.env` dosyasındaki güvenlik anahtarlarını değiştirin:
   ```
   SECRET_KEY=<güvenli-rastgele-anahtar>
   JWT_SECRET_KEY=<güvenli-rastgele-anahtar>
   ```

2. Veritabanı yedeklemelerini düzenli kontrol edin:
   - Günlük yedekler: `backups/daily`
   - Haftalık yedekler: `backups/weekly`
   - Aylık yedekler: `backups/monthly`

## Sorun Giderme

### Windows'ta Sık Karşılaşılan Sorunlar

1. "NSSM bulunamadı" hatası:
   - NSSM'in doğru yüklendiğinden emin olun
   - PATH'e eklendiğini kontrol edin

2. Servis başlatılamıyor:
   - Logları kontrol edin: `logs\service.log`
   - Python'un PATH'te olduğunu kontrol edin
   - Yönetici olarak cmd açıp tekrar deneyin

### Linux'ta Sık Karşılaşılan Sorunlar

1. Servis başlatılamıyor:
   - Logları kontrol edin: `sudo journalctl -u jerpws`
   - Dizin izinlerini kontrol edin
   - Python sanal ortamını kontrol edin

2. Port hatası:
   - 5000 portunun kullanılabilir olduğunu kontrol edin
   - Gerekirse portu değiştirin: `gunicorn --bind 0.0.0.0:5001`

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## İletişim

Sorunlar ve öneriler için:
- GitHub Issues
- E-posta: destek@jerpws.com
