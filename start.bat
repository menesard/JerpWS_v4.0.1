@echo off

REM Sanal ortam ve paketleri kontrol et
if not exist "venv" (
    echo Sanal ortam veya gerekli paketler eksik. Kurulum baslatiliyor...
    python setup.py
    if errorlevel 1 (
        echo Kurulum basarisiz oldu!
        pause
        exit /b 1
    )
)

REM Ortam değişkenlerini yükle
if exist .env (
    for /F "tokens=*" %%A in (.env) do set %%A
)

REM Python sanal ortamını etkinleştir
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Gunicorn ile uygulamayı başlat
python -m gunicorn ^
    --bind 0.0.0.0:5000 ^
    --workers 4 ^
    --worker-class gthread ^
    --threads 2 ^
    --timeout 120 ^
    --access-logfile logs/access.log ^
    --error-logfile logs/error.log ^
    --certfile ssl/cert.pem ^
    --keyfile ssl/key.pem ^
    wsgi:app

pause 