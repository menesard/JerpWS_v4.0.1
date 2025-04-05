@echo off
echo JerpWS Windows Servis Kurulumu

REM NSSM'in yüklü olup olmadığını kontrol et
where nssm >nul 2>nul
if %errorlevel% neq 0 (
    echo NSSM bulunamadi. Lutfen NSSM'i yukleyin ve PATH'e ekleyin.
    echo https://nssm.cc/download adresinden indirebilirsiniz.
    pause
    exit /b 1
)

REM Mevcut dizini al
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Servis adını belirle
set "SERVICE_NAME=JerpWS"

REM Önce varolan servisi kaldır
nssm stop %SERVICE_NAME% >nul 2>nul
nssm remove %SERVICE_NAME% confirm >nul 2>nul

REM Yeni servisi kur
echo Servis kuruluyor...
nssm install %SERVICE_NAME% "%SCRIPT_DIR%\start.bat"
nssm set %SERVICE_NAME% AppDirectory "%SCRIPT_DIR%"
nssm set %SERVICE_NAME% DisplayName "JerpWS Flask Application"
nssm set %SERVICE_NAME% Description "JerpWS Flask Web Uygulamasi"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START
nssm set %SERVICE_NAME% AppStdout "%SCRIPT_DIR%\logs\service.log"
nssm set %SERVICE_NAME% AppStderr "%SCRIPT_DIR%\logs\service.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateBytes 1048576
nssm set %SERVICE_NAME% AppRotateOnline 1

REM Servisi başlat
echo Servis baslatiliyor...
nssm start %SERVICE_NAME%

echo.
echo Kurulum tamamlandi!
echo Servis durumunu kontrol etmek icin: sc query %SERVICE_NAME%
echo Servisi manuel baslatmak icin: net start %SERVICE_NAME%
echo Servisi durdurmak icin: net stop %SERVICE_NAME%
echo.
pause 