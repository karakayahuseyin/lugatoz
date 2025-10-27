# ÖzBilig Deployment Rehberi

## 🚀 Production Deployment

### Gereksinimler
- Docker ve Docker Compose yüklü olmalı
- Sunucuda 80 portu açık olmalı
- En az 1GB RAM ve 10GB disk alanı

### Deployment Adımları

#### 1. Repository'yi Klonlayın
```bash
git clone <repository-url>
cd ozbilig
```

#### 2. Production Build ve Deploy
```bash
# Production container'larını başlat
docker compose -f docker-compose.prod.yml up -d --build

# Logları kontrol et
docker compose -f docker-compose.prod.yml logs -f
```

#### 3. Erişim
- **Ana Oyun:** http://sunucu-ip-adresi
- **Admin Paneli:** http://sunucu-ip-adresi/#admin

### 🔧 Yönetim Komutları

#### Container'ları Durdur
```bash
docker compose -f docker-compose.prod.yml down
```

#### Container'ları Yeniden Başlat
```bash
docker compose -f docker-compose.prod.yml restart
```

#### Logları Görüntüle
```bash
# Tüm loglar
docker compose -f docker-compose.prod.yml logs -f

# Sadece backend
docker compose -f docker-compose.prod.yml logs -f backend

# Sadece frontend
docker compose -f docker-compose.prod.yml logs -f frontend
```

#### Veritabanını Yedekle
```bash
docker run --rm \
  -v ozbilig_backend-db:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/ozbilig-db-backup-$(date +%Y%m%d).tar.gz -C /data .
```

#### Veritabanını Geri Yükle
```bash
docker run --rm \
  -v ozbilig_backend-db:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/ozbilig-db-backup-YYYYMMDD.tar.gz"
```

### 📊 Admin Paneli Kullanımı

1. **Admin Paneline Erişim:** http://sunucu-ip/#admin
2. **Yeni Soru Ekleme:**
   - "Yeni Soru Ekle" butonuna tıklayın
   - Soru metnini, doğru cevabı, kategoriyi ve zorluk seviyesini girin
   - "Soruyu Ekle" butonuna basın
3. **Soru Silme:**
   - Sorunun yanındaki "Sil" butonuna tıklayın
   - Onaylayın

### 🌐 Multiplayer Test

#### Farklı Cihazlardan Bağlanma
1. Sunucu IP adresinizi öğrenin:
   ```bash
   hostname -I
   ```
2. Diğer cihazlardan `http://sunucu-ip` adresine gidin
3. Her cihazda farklı bir isim ile "Oyuna Katıl" butonuna basın
4. Host (ilk katılan) oyunu başlatabilir

#### Port Yönlendirme (Router)
Eğer internetten erişim istiyorsanız:
1. Router ayarlarına girin
2. Port 80'i sunucu IP'sine yönlendirin
3. Dış IP adresinizi öğrenin: https://whatismyipaddress.com
4. Dış IP adresiyle erişim sağlayın

### 🔒 Güvenlik Önerileri

#### Firewall Ayarları (Ubuntu/Debian)
```bash
# UFW kurulu değilse
sudo apt install ufw

# 80 portunu aç
sudo ufw allow 80/tcp

# SSH'ı kapat (opsiyonel)
sudo ufw allow 22/tcp

# Firewall'u etkinleştir
sudo ufw enable
```

#### HTTPS ile Çalıştırma (Nginx + Let's Encrypt)
```bash
# Certbot kur
sudo apt install certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d yourdomain.com
```

### 📈 Performans İzleme

#### Resource Kullanımı
```bash
# Container'ların kaynak kullanımı
docker stats
```

#### Aktif Oyuncu Sayısı
Backend loglarında "joined game" mesajlarını sayın:
```bash
docker compose -f docker-compose.prod.yml logs backend | grep "joined game" | wc -l
```

### 🐛 Troubleshooting

#### Problem: Container başlamıyor
```bash
# Container durumunu kontrol et
docker compose -f docker-compose.prod.yml ps

# Detaylı hata logları
docker compose -f docker-compose.prod.yml logs --tail=100
```

#### Problem: WebSocket bağlanamıyor
- Firewall'da 80 portu açık mı kontrol edin
- Nginx loglarını kontrol edin
- Browser console'da hata var mı bakın

#### Problem: Sorular yüklenmiyor
```bash
# Backend API'yi test et
curl http://localhost:8000/api/questions

# Database volume'ü kontrol et
docker volume ls | grep ozbilig
```

### 🔄 Güncelleme

```bash
# Yeni kodu çek
git pull

# Container'ları yeniden build et ve başlat
docker compose -f docker-compose.prod.yml up -d --build

# Eski image'leri temizle
docker image prune -f
```

### 📱 Mobil Erişim

Oyun mobil cihazlarda responsive olarak çalışır. Tarayıcıdan erişim yeterlidir.

### 🎮 Oyun Kuralları

1. **Maksimum 4 oyuncu** aynı anda oynayabilir
2. **10 soru** + **Final Testi**
3. Puanlama:
   - Doğru cevap: +1000 puan
   - Başkalarını aldatma: Her aldatılan için +500 puan
   - Final testi: Doğru cevap başına +500 puan

### 💾 Backup Stratejisi

Otomatik backup için crontab ekleyin:
```bash
# Crontab'ı düzenle
crontab -e

# Her gece saat 3'te backup al
0 3 * * * cd /path/to/ozbilig && docker run --rm -v ozbilig_backend-db:/data -v $(pwd):/backup alpine tar czf /backup/ozbilig-db-backup-$(date +\%Y\%m\%d).tar.gz -C /data .
```

### 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin
2. Issue açın: [GitHub Issues]
3. Documentation'ı okuyun: README.md

---

**Not:** Development için `docker-compose.yml` kullanın, production için `docker-compose.prod.yml` kullanın.
