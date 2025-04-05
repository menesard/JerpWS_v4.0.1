#!/bin/bash

echo "JerpWS Linux Servis Kurulumu"

# Root yetkisi kontrolü
if [ "$EUID" -ne 0 ]; then
    echo "Bu betik root yetkisi gerektirir. Lütfen sudo ile çalıştırın."
    exit 1
fi

# Mevcut dizini al
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Servis dosyasını sistemd dizinine kopyala
cp "$SCRIPT_DIR/jerpws.service" /etc/systemd/system/

# Servis dosyasındaki yolları güncelle
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" /etc/systemd/system/jerpws.service
sed -i "s|Environment=\"PATH=.*|Environment=\"PATH=$SCRIPT_DIR/venv/bin\"|" /etc/systemd/system/jerpws.service
sed -i "s|Environment=\"PYTHONPATH=.*|Environment=\"PYTHONPATH=$SCRIPT_DIR\"|" /etc/systemd/system/jerpws.service

# Systemd'yi yeniden yükle
systemctl daemon-reload

# Servisi etkinleştir ve başlat
systemctl enable jerpws
systemctl start jerpws

echo -e "\nKurulum tamamlandı!"
echo "Servis durumunu kontrol etmek için: systemctl status jerpws"
echo "Servisi manuel başlatmak için: sudo systemctl start jerpws"
echo "Servisi durdurmak için: sudo systemctl stop jerpws"
echo "Servis loglarını görüntülemek için: sudo journalctl -u jerpws" 