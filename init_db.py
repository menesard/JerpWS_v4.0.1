#!/usr/bin/env python
# JerpWS (Jewelry ERP - Workshop)
# Copyright (c) 2025 ARD INC. Tüm hakları saklıdır.
# Sürüm: 1.0.0

from app import create_app, db
from app.models.database import init_db
import os

app = create_app('production')  # Production modunda başlat

with app.app_context():
    # Veritabanı dosyasını kontrol et ve gerekirse sil
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'jewelry.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Mevcut veritabanı silindi: {db_path}")

    # Instance klasörünü oluştur (yoksa)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Veritabanı tablolarını oluştur
    db.create_all()

    # Başlangıç verilerini ekle
    init_db()

    print("Veritabanı başarıyla başlatıldı!")
    print("Admin kullanıcısı oluşturuldu:")
    print("Kullanıcı adı: admin")
    print("Şifre: admin")
    print("ÖNEMLİ: İlk girişten sonra admin şifresini değiştirmeyi unutmayın!")