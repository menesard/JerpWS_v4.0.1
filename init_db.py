#!/usr/bin/env python
from app import create_app, db
from app.models.database import init_db

app = create_app()

with app.app_context():
    # Veritabanı tablolarını oluştur
    db.create_all()

    # Başlangıç verilerini ekle
    init_db()

    print("Veritabanı başarıyla başlatıldı!")