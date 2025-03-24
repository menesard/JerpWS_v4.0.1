#!/usr/bin/env python
from app import create_app

application = create_app('production')

# Bu satır, 'python wsgi.py' ile çalıştırıldığında kullanılır
if __name__ == "__main__":
    application.run()