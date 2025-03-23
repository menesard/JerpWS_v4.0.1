#!/usr/bin/env python
from app import create_app, db
from app.models.database import init_db
import os

app = create_app('production')  # Production modunda başlat

with app.app_context():
    # Veritabanı dizininin izinlerini kontrol et ve ayarla
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(db_path, exist_ok=True)

    # Veritabanı dosyasını oluştur
    db_file = os.path.join(db_path, 'jewelry.db')

    # Veritabanı tablolarını oluştur
    db.create_all()

    # Başlangıç verilerini ekle
    try:
        init_db()
        print("Veritabanı başlangıç verileri başarıyla eklendi!")
    except Exception as e:
        print(f"Başlangıç verileri eklenirken hata oluştu: {e}")

    print("Veritabanı başarıyla başlatıldı!")