#!/bin/bash

# Sanal ortam ve paketleri kontrol et
if [ ! -d "venv" ] || [ ! -f "venv/bin/gunicorn" ]; then
    echo "Sanal ortam veya gerekli paketler eksik. Kurulum başlatılıyor..."
    python3 setup.py
fi

# Ortam değişkenlerini yükle
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Python sanal ortamını etkinleştir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Gunicorn ile uygulamayı başlat
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --certfile ssl/cert.pem \
    --keyfile ssl/key.pem \
    wsgi:app 