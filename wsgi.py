#!/usr/bin/env python
from app import create_app

application = create_app()
app = application  # Gunicorn için app değişkeni

# Bu satır, 'python wsgi.py' ile çalıştırıldığında kullanılır
if __name__ == "__main__":
    application.run(debug=True, use_reloader=True)