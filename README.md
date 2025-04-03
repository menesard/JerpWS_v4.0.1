# JerpWS (Jewelry ERP - Workshop)

Modern kuyumcu atölyesi yönetim sistemi.

## Özellikler

- Kullanıcı yönetimi ve yetkilendirme
- Ürün ve stok takibi
- Müşteri yönetimi
- Sipariş takibi
- Raporlama
- HTTPS güvenliği
- RESTful API

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
sudo apt-get update
sudo apt-get install python3-venv nginx
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

4. Veritabanını oluşturun:
```bash
python init_db.py
```

5. Admin kullanıcısı oluşturun:
```bash
python create_admin.py
```

6. SSL sertifikalarını oluşturun:
```bash
mkdir ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365
```

7. Nginx yapılandırmasını kopyalayın:
```bash
sudo cp nginx.conf /etc/nginx/sites-enabled/jerpws.conf
sudo systemctl restart nginx
```

8. Uygulamayı başlatın:
```bash
gunicorn -c gunicorn.conf.py wsgi:application
```

## Dizin Yapısı

```
.
├── app/                # Ana uygulama kodu
├── instance/          # Veritabanı ve geçici dosyalar
├── logs/             # Log dosyaları
├── migrations/       # Veritabanı migrasyonları
├── ssl/             # SSL sertifikaları
├── .venv/           # Sanal ortam
├── gunicorn.conf.py # Gunicorn yapılandırması
├── nginx.conf       # Nginx yapılandırması
├── wsgi.py          # WSGI uygulaması
└── requirements.txt # Bağımlılıklar
```

## Güvenlik

- HTTPS üzerinden güvenli iletişim
- JWT tabanlı kimlik doğrulama
- Rol tabanlı yetkilendirme
- Güvenli şifre hashleme

## Lisans

Copyright (c) 2025 ARD INC. Tüm hakları saklıdır.

## İletişim

Sorularınız veya önerileriniz için:
- E-posta: ornek@email.com
- GitHub Issues: [Proje Issues](https://github.com/kullaniciadi/JerpWS_v3.2/issues)

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir özellik dalı oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Dalınıza push yapın (`git push origin yeni-ozellik`)
5. Bir Pull Request oluşturun
