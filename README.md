# Kuyumcu Takip Sistemi (JerpWS v3.2)

Bu proje, kuyumcular için geliştirilmiş bir takip sistemidir. Müşteri yönetimi, terazi entegrasyonu ve stok takibi gibi temel özellikleri içerir.

## Özellikler

- 🔐 Güvenli kullanıcı girişi ve yetkilendirme sistemi
- 👥 Müşteri yönetimi ve takibi
- 💍 Ürün yönetimi ve stok takibi
- ⚖️ Terazi entegrasyonu
- 📊 Raporlama sistemi
- 🔄 Veritabanı yedekleme ve geri yükleme
- 📱 Mobil uyumlu arayüz

## Gereksinimler

- Python 3.8 veya üzeri
- SQLite veritabanı
- Seri port bağlantısı (terazi için)

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/kullaniciadi/JerpWS_v3.2.git
cd JerpWS_v3.2
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac için
# veya
venv\Scripts\activate  # Windows için
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Veritabanını oluşturun:
```bash
flask db upgrade
```

5. Uygulamayı başlatın:
```bash
flask run
```

## Yapılandırma

1. `.env` dosyasını oluşturun ve aşağıdaki değişkenleri ayarlayın:
```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///jerp.db
SCALE_PORT=COM5  # Terazi port ayarı
```

2. Terazi ayarlarını yapılandırın:
- Terazinin bağlı olduğu port numarasını ayarlayın
- Terazi bağlantı hızını (baudrate) ayarlayın

## Kullanım

1. Tarayıcınızda `http://localhost:5000` adresine gidin
2. Varsayılan kullanıcı bilgileri:
   - Kullanıcı adı: admin
   - Şifre: admin123

## Güvenlik

- İlk girişten sonra varsayılan şifreyi değiştirmeniz önerilir
- Düzenli olarak veritabanı yedeği alın
- Güvenlik güncellemelerini takip edin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## İletişim

Sorularınız veya önerileriniz için:
- E-posta: ornek@email.com
- GitHub Issues: [Proje Issues](https://github.com/kullaniciadi/JerpWS_v3.2/issues)

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir özellik dalı oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Dalınıza push yapın (`git push origin yeni-ozellik`)
5. Bir Pull Request oluşturun
