#!/usr/bin/env python
from app import create_app, db
from app.models.database import init_db
import os

app = create_app('production')  # Production modunda başlat

with app.app_context():
    # Veritabanı dizininin izinlerini kontrol et ve ayarla
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(db_path, exist_ok=True)

    # Dizin izinlerini ayarla
    # os.chmod(db_path, 0o777)

    # Veritabanı dosyasını oluştur ve izinlerini ayarla
    db_file = os.path.join(db_path, 'jewelry.db')

    # Eğer dosya zaten varsa izinlerini değiştir
    # if os.path.exists(db_file):
    #    os.chmod(db_file, 0o666)

    # Veritabanı tablolarını oluştur
    db.create_all()

    # Başlangıç verilerini ekle
    init_db()

    print("Veritabanı başarıyla başlatıldı!")