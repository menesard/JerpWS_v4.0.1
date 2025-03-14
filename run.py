#!/usr/bin/env python
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Geliştirme sunucusunu çalıştır
    # Production ortamında Gunicorn veya uWSGI gibi bir WSGI sunucusu kullanılmalıdır
    app.run(host='0.0.0.0', port=5000, debug=True)