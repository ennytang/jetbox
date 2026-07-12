# JETBOX v3 — Arkadaşına Gönderme Rehberi

## 📦 Projeyi Paketleme

Arkadaşına göndermeden **önce** şu klasörleri sil (gereksiz, çok yer kaplar):

```
❌ frontend/node_modules/     (npm install tekrar yükler)
❌ backend/__pycache__/       (Python otomatik oluşturur)
❌ OUTPUT/ içindeki dosyalar   (render çıktıları)
❌ youtube_token.json          (senin YouTube hesabın, paylaşma!)
```

Sonra klasörü ZİP'le ve gönder (WeTransfer, Google Drive, USB vb.)

---

## 🖥️ Arkadaşının Kurması Gerekenler

### 1. Python (3.10+)
- İndir: https://www.python.org/downloads/
- Kurulum sırasında **"Add Python to PATH"** kutusunu işaretle! ⚠️

### 2. Node.js (18+)
- İndir: https://nodejs.org/ (LTS sürümünü seç)
- Kurulumda varsayılanları kabul et

### 3. FFmpeg
- İndir: https://www.gyan.dev/ffmpeg/builds/ → `ffmpeg-release-essentials.zip`
- ZIP içinden `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` dosyalarını çıkar
- Dosyaları `C:\ffmpeg\bin\` klasörüne koy
- **Sistem PATH'e ekle:**
  1. Windows Arama → "Ortam değişkenleri" (Environment Variables)
  2. "Path" → Düzenle → Yeni → `C:\ffmpeg\bin` ekle
  3. Yeni bir CMD aç → `ffmpeg -version` yazarak test et

---

## 🚀 Çalıştırma

1. JETBOX klasörüne gir
2. `START.bat` dosyasına çift tıkla
3. Otomatik olarak:
   - Python paketleri kurulur
   - Node paketleri kurulur
   - Backend başlar (port 5001)
   - Frontend başlar (port 5173)
   - Tarayıcı açılır → http://localhost:5173
4. `BEATS/` klasörüne WAV dosyası at → Dashboard'dan "Scan BEATS/" tıkla

---

## 🔧 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `python bulunamadı` | Python PATH'e eklenmemiş → yeniden kur, "Add to PATH" işaretle |
| `npm bulunamadı` | Node.js kurulu değil veya CMD yeniden açılmadı |
| `FFmpeg: ✗` gösteriliyor | FFmpeg PATH'e eklenmemiş → yukarıdaki adımları uygula |
| `localhost bağlanmayı reddetti` | Backend başlamadı → `cd backend && python app.py` ile hatayı gör |
| Port 5001/5173 meşgul | Önceki JETBOX hala çalışıyor → Görev Yöneticisi'nden kapat |

---

## 📺 YouTube Yükleme (Opsiyonel)

YouTube'a otomatik yüklemek isteyen kişi kendi Google Cloud hesabıyla kurulum yapmalı:

1. https://console.cloud.google.com → Proje oluştur
2. YouTube Data API v3'ü etkinleştir
3. OAuth2 credentials oluştur (Desktop app)
4. `client_secrets.json` dosyasını JETBOX klasörüne koy
5. Terminal'de: `cd backend && python youtube_upload.py --setup`
