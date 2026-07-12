# JETBOX v3 — YouTube API Setup Guide

**by ENNYTANG**  
*Direct YouTube upload — no n8n, no extra services*

---

## Overview

JETBOX uploads videos directly to YouTube using the YouTube Data API v3. No n8n, no Docker, no extra services. Everything runs from your JETBOX folder.

```
Dashboard [Onayla] → Flask API → YouTube Data API v3 → Your Channel
```

One-time setup takes ~10 minutes. After that, uploads work automatically.

---

## Step 1: Google Cloud Console — Proje Oluştur

1. Aç: **https://console.cloud.google.com**
2. Sağ üstte Google hesabınla giriş yap (YouTube kanalının bağlı olduğu hesap)
3. Üst kısımda proje seçiciye tıkla → **"NEW PROJECT"**
4. Project name: **JETBOX**
5. **"CREATE"** butonuna bas
6. Projenin oluşturulmasını bekle (birkaç saniye), sonra üstten **JETBOX** projesini seç

---

## Step 2: YouTube Data API v3'ü Etkinleştir

1. Sol menüden: **APIs & Services → Library**
   - Direkt link: https://console.cloud.google.com/apis/library
2. Arama kutusuna yaz: **YouTube Data API v3**
3. Çıkan sonuca tıkla
4. Mavi **"ENABLE"** butonuna bas
5. API etkinleştirildi mesajını gör

---

## Step 3: OAuth Consent Screen

API'yi etkinleştirdikten sonra credential oluşturmadan önce "consent screen" ayarlanması gerekiyor:

1. Sol menüden: **APIs & Services → OAuth consent screen**
   - Direkt link: https://console.cloud.google.com/apis/credentials/consent
2. User Type: **External** seç → **"CREATE"**
3. Formu doldur:
   - App name: **JETBOX**
   - User support email: kendi email'in
   - Developer contact: kendi email'in
   - Diğer alanları boş bırak
4. **"SAVE AND CONTINUE"**
5. Scopes sayfasında: **"ADD OR REMOVE SCOPES"** tıkla
   - Filtrele: `youtube`
   - Seç: `youtube.upload` ve `youtube.force-ssl`
   - **"UPDATE"** → **"SAVE AND CONTINUE"**
6. Test users sayfasında: **"+ ADD USERS"**
   - Kendi Gmail adresini ekle (YouTube kanalının bağlı olduğu)
   - **"SAVE AND CONTINUE"**
7. Summary → **"BACK TO DASHBOARD"**

---

## Step 4: OAuth2 Credential Oluştur

1. Sol menüden: **APIs & Services → Credentials**
   - Direkt link: https://console.cloud.google.com/apis/credentials
2. Üstte **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **Desktop app**
4. Name: **JETBOX**
5. **"CREATE"**
6. Açılan popup'ta **"DOWNLOAD JSON"** butonuna bas (⬇️ ikonu)
7. İndirilen dosyanın adını **`client_secrets.json`** olarak değiştir
8. Bu dosyayı JETBOX ana klasörüne kopyala:
   ```
   JETBOX/
   ├── client_secrets.json  ← BURAYA
   ├── backend/
   ├── frontend/
   └── ...
   ```

---

## Step 5: İlk Kez Auth (Tarayıcıda Google Sign-In)

Terminal/CMD aç, JETBOX klasörüne git ve çalıştır:

```bash
cd JETBOX/backend
pip install -r ../requirements.txt
python youtube_upload.py --setup
```

Bu komut:
1. Tarayıcında Google sign-in sayfasını açar
2. YouTube kanalının bağlı olduğu hesapla giriş yap
3. "JETBOX wants to access your YouTube account" → **"Allow"**
4. "Google hasn't verified this app" uyarısı gelirse → **"Advanced"** → **"Go to JETBOX (unsafe)"** → **"Allow"**
5. Terminal'de "Authentication successful!" mesajını gör
6. `youtube_token.json` otomatik kaydedilir — bir daha sign-in gerekmez

---

## Step 6: Test Et

```bash
python youtube_upload.py --channel
```

Beklenen çıktı:
```
  channel_id: UCxxxxxxxxx
  title: ENNYTANG
  video_count: 42
  subscriber_count: 150
```

Eğer kanalın görünüyorsa, setup tamamdır.

---

## Step 7: JETBOX'u Başlat

```bash
cd JETBOX/backend
python app.py
```

Dashboard'da "Onayla & YouTube'a Yükle" butonu artık direkt YouTube'a yükler.

---

## Günlük Kullanım

Setup bir kere yapılır. Sonra:
1. BEATS/ klasörüne WAV at
2. Dashboard'da artist seç, artwork seç, beat name yaz
3. "Preview & Render" → MP4 oluşturulur
4. "Onayla & YouTube'a Yükle" → Direkt YouTube'a gider

Token otomatik yenilenir. Sadece 6+ ay kullanmamazsan tekrar sign-in gerekebilir.

---

## Önemli Notlar

- **Günlük kota:** YouTube API günde 10,000 birim verir. Her upload ~1,600 birim. Günde ~6 video yükleyebilirsin.
- **Unverified app:** Uygulamanız "testing" modunda kaldığı sürece sadece test user olarak eklediğiniz hesaplar kullanabilir. Bu senin için yeterli.
- **Custom thumbnail:** YouTube kanalının doğrulanmış (telefon numarası ile) olması gerekiyor. Yoksa thumbnail otomatik seçilir.
- **client_secrets.json** ve **youtube_token.json** dosyalarını asla paylaşma veya git repo'ya koyma.

---

## Sorun Giderme

| Problem | Çözüm |
|---------|-------|
| "Google API libraries not installed" | `pip install -r requirements.txt` |
| "client_secrets.json not found" | Step 4'ü tekrar yap, dosyayı JETBOX/ root'a koy |
| "Access blocked: app not verified" | Consent screen'de "Advanced" → "Go to JETBOX (unsafe)" tıkla |
| "Token expired" | `python youtube_upload.py --setup` tekrar çalıştır |
| "quotaExceeded" | Günlük 6 video limiti aşıldı, 24 saat bekle |
| Upload çalışıyor ama video private | `privacy_status: "public"` olduğundan emin ol |

---

## API Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/youtube/status` | GET | YouTube auth durumu |
| `/api/youtube/channel` | GET | Kanal bilgileri |
| `/api/upload/youtube` | POST | Video yükle |
