## 🚀 Railway Deployment Rehberi

### Adım 1: Railway Hesabı Oluştur
1. https://railway.app adresine git
2. GitHub hesabınızla giriş yapın
3. Yeni project oluşturun

### Adım 2: GitHub Repository'ye Yükleme
```bash
git init
git add .
git commit -m "Crypto News AI Bot v14 - Railway Ready"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADI/cryptonewsaibot.git
git push -u origin main
```

### Adım 3: Railway Ayarları
1. Railway dashboard'ta "New Project" → "Deploy from GitHub" seçin
2. cryptonewsaibot repository'nizi seçin
3. **Environment Variables** ekleyin:
   - `DISCORD_WEBHOOK_URL` = (Discord webhook URL'niz)
   - `NEWSAPI_KEY` = (NewsAPI anahtarı)
   - `CLAUDE_API_KEY` = (Claude API anahtarı)
   - `TWITTER_BEARER_TOKEN` = (Twitter Bearer token)

### Adım 4: Deployment
1. "Deploy" butonuna tıklayın
2. Railway otomatik olarak Procfile'ı okuyacak
3. Bot sürekli çalışacak ✅

### Önemli Notlar:
- Procfile, bot'u "worker" olarak tanımlıyor (24/7 çalışacak)
- Environment variables güvenli şekilde şifrelenmiş
- Bot her 30 saniyede haberleri kontrol edecek
- Railway free tier'da 500 saate kadar çalıştırabilirsiniz

### Troubleshooting:
Eğer bot sorun yaşarsa:
```bash
# Railway logs'u kontrol edin
# Dashboard → Project → Logs seçeneğinden hataları görebilirsiniz
```

### Durdurmak:
Railway dashboard'tan "Pause" butonuyla bot'u durdurabilirsiniz.

---
Hazır mısınız? GitHub'a push yapmaya başlayabilirsiniz! 🚀
