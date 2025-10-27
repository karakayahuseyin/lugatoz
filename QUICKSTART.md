# 🚀 ÖzBilig - Hızlı Başlangıç

## 📱 Multiplayer Test için Hızlı Deployment

### 1️⃣ Tek Komutla Deploy

```bash
./deploy.sh
```

Bu komut:
- ✅ Development container'larını durdurur
- ✅ Production build yapar
- ✅ Container'ları başlatır
- ✅ IP adresinizi gösterir

### 2️⃣ Manuel Deploy

```bash
# Development'ı durdur
docker compose down

# Production build ve başlat
docker compose -f docker-compose.prod.yml up -d --build
```

### 3️⃣ IP Adresinizi Öğrenin

```bash
hostname -I
```

Çıktı örneği: `192.168.1.100`

### 4️⃣ Farklı Cihazlardan Bağlanın

#### Aynı WiFi Ağında
1. Telefonunuzu, tabletinizi veya başka bir bilgisayarınızı aynı WiFi'ye bağlayın
2. Tarayıcıdan `http://192.168.1.100` adresine gidin (IP'nizi kullanın)
3. İsminizi girin ve "Oyuna Katıl" butonuna basın

#### Mobil Cihazlar (Tavsiye)
- iOS: Safari kullanın
- Android: Chrome kullanın
- Responsive tasarım sayesinde mobilde mükemmel çalışır!

### 5️⃣ Oyunu Başlatın

1. **İlk Katılan = Host**
   - İlk oyuncu otomatik olarak host olur
   - Sadece host "Oyunu Başlat" butonunu görebilir

2. **2-4 Oyuncu Bekleyin**
   - En az 2 oyuncu gerekli
   - Maksimum 4 oyuncu oynayabilir

3. **Host Oyunu Başlatır**
   - Herkes hazır olduğunda host oyunu başlatır
   - Oyun tüm cihazlarda senkronize olarak başlar

### 🎮 Oyun Akışı

```
1. Oyuna Katıl (tüm oyuncular) 
   ↓
2. Lobby'de Bekle
   ↓
3. Host Oyunu Başlatır
   ↓
4. Soru → Yanlış Cevap Gir
   ↓
5. Oylama → Doğru Cevabı Seç
   ↓
6. Sonuçları Gör
   ↓
7. 10 Tur (4-6 tekrar)
   ↓
8. Final Testi (her oyuncu kendi hızında)
   ↓
9. Kazananı Gör!
```

### 🔧 Admin Paneli

Soru eklemek/silmek için:

```
http://IP-ADRESINIZ/#admin
```

Örnek: `http://192.168.1.100/#admin`

### 🐛 Sorun Giderme

#### WebSocket Bağlanamıyor
```bash
# Firewall'u kontrol et
sudo ufw status

# Port 80'i aç
sudo ufw allow 80/tcp
```

#### Container Çalışmıyor
```bash
# Durumu kontrol et
docker compose -f docker-compose.prod.yml ps

# Logları gör
docker compose -f docker-compose.prod.yml logs
```

#### Sorular Yüklenmiyor
```bash
# API'yi test et
curl http://localhost:8000/api/questions

# Backend'i restart et
docker compose -f docker-compose.prod.yml restart backend
```

### 🌐 İnternetten Erişim (Opsiyonel)

Arkadaşlarınız farklı ağlardaysa:

1. **Router Port Yönlendirme**
   - Router admin paneline girin
   - Port 80'i sunucu IP'nize yönlendirin

2. **Dış IP Öğrenin**
   ```bash
   curl ifconfig.me
   ```

3. **Firewall Ayarı**
   ```bash
   sudo ufw allow 80/tcp
   ```

4. **Paylaşın**
   - Arkadaşlarınıza dış IP'nizi verin
   - `http://DIŞ_IP` adresine gitsinler

### 📊 Performans İpuçları

- **Önerilen:** 4 oyuncu için en az 1GB RAM
- **Network:** WiFi yerine 5GHz kullanın
- **Tarayıcı:** Chrome/Safari önerili
- **Ping:** <50ms ideal

### 🎯 Test Senaryosu

1. **Bilgisayarınızda:**
   ```bash
   ./deploy.sh
   ```

2. **Telefonunuzda:**
   - WiFi'ye bağlanın
   - `http://IP-ADRESI` açın
   - İsim girin: "Oyuncu 1"

3. **Tabletinizde:**
   - Aynı WiFi'ye bağlanın
   - `http://IP-ADRESI` açın
   - İsim girin: "Oyuncu 2"

4. **Başka bir telefonda:**
   - İsim girin: "Oyuncu 3"

5. **İlk giren (Oyuncu 1) oyunu başlatır!** 🚀

### 💡 İpuçları

- ✅ Her oyuncu farklı cihazdan bağlanmalı
- ✅ İsimleri farklı yapın
- ✅ Tüm cihazlar aynı WiFi'de olmalı
- ✅ Host beklemeden oyunu başlatabilir (min 2 oyuncu)
- ✅ Final testinde her oyuncu kendi hızında ilerler

### 🎓 Eğitici Kullanım

- Okulda: Öğrencilerle sınıfta oynayın
- Evde: Aile üyeleriyle eğlenceli öğrenme
- Online: Arkadaşlarınızla uzaktan oyun

### 📞 Yardım

Sorun mu yaşıyorsunuz?
1. Logları kontrol edin
2. DEPLOYMENT.md'yi okuyun
3. README.md'de troubleshooting bölümüne bakın

---

**Hazır! Artık multiplayer oyununuzu farklı cihazlardan test edebilirsiniz! 🎮**
