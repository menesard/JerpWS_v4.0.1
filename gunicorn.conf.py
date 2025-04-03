import multiprocessing

# Sunucu yapılandırması
bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Log yapılandırması
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Güvenlik yapılandırması
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190 