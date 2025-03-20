#!/usr/bin/env python
# JerpWS (Jewelry ERP - Workshop)
# Copyright (c) 2025 ARD INC. Tüm hakları saklıdır.
# Sürüm: 1.0.0

import os
from app import create_app
from app.config import APP_NAME, APP_VERSION, APP_COMPANY

# Çalışma ortamını al (varsayılan: production)
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == "__main__":
    # Başlangıç bilgisi göster
    print(f"**** {APP_NAME} v{APP_VERSION} ****")
    print(f"Geliştirici: {APP_COMPANY}")
    print(f"Çalışma modu: {env}")

    # Geliştirme sunucusunu çalıştır
    # Production ortamında Gunicorn veya uWSGI gibi bir WSGI sunucusu kullanılmalıdır
    if env == 'development':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # Prodüksiyon modunda sınırlı erişim
        app.run(host='localhost', port=5000, debug=False)