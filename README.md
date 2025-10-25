# 🤖 Crypto News AI Bot v14

Discord'a gerçek zamanlı kripto haber analizi yapan AI bot. Claude AI ile gelişmiş analiz ve piyasa psikolojisi tahmini.

## ✨ Özellikler

- 📰 **Çoklu Kaynak**: NewsAPI, RSS Feeds (CoinTelegraph, CoinDesk), Twitter
- 🧠 **Claude AI Analizi**: Piyasa psikolojisi, whale davranışı, risk analizi
- 🎯 **Risk Seviyesi**: HIGH, MEDIUM, LOW - En üstte görünür
- 💹 **Fiyat Tahmini**: Beklenen fiyat hareketi yüzdeleri
- 🚨 **Önem Seviyeleri**: CRITICAL, HIGH, MEDIUM, LOW, SKIPPABLE
- ⚙️ **Otomatik Kontrol**: Her 30 saniyede haberler taranır
- 🔄 **Çoğaltma Engelleme**: Aynı haberi birden fazla göndermez

## 📋 Gereksinimler

- Python 3.8+
- Discord Webhook URL
- NewsAPI Key
- Claude API Key
- Twitter Bearer Token (opsiyonel)

## 🚀 Hızlı Başlangıç

### Local Çalıştırma

```bash
# Klon
git clone https://github.com/kullaniciadi/cryptonewsaibot.git
cd cryptonewsaibot

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# .env dosyasını açıp API keylerinizi ekleyin

# Çalıştırma
python bot.py
```

### Railway'e Deploy

Detaylı rehber için: [RAILWAY_SETUP.md](RAILWAY_SETUP.md)

Kısaca:
1. GitHub'a push yapın
2. Railway.app'ta GitHub repo bağlayın
3. Environment variables ekleyin
4. Deploy yapın ✅

## 📊 Discord Embed Düzeni

Botun gönderdiği mesajlarda şu bilgiler bulunur:

```
[EMOJI] Haber Başlığı
├─ 🎯 Önem Seviyesi (CRITICAL/HIGH/MEDIUM/LOW)
├─ ⚠️ Risk Seviyesi (HIGH/MEDIUM/LOW)
├─ 💡 Tavsiye (BUY/SELL/WAIT/HOLD)
├─ 💭 Piyasanın Duygusu
├─ 💹 Piyasa Etkisi
├─ 📊 Fiyat Hareketi
├─ 🧠 Pazar Psikolojisi
├─ 🐋 Whale Davranışı
├─ 💬 Analiz
├─ 📌 Kaynak
└─ 📅 Yayın Zamanı
```

## 🔧 Yapılandırma

### Tarama Aralığı (bot.py satır 462-468)
```python
scheduler.add_job(
    check_news,
    'interval',
    seconds=30,  # ← Burayı değiştirin
    id='check_news_job',
)
```

### RSS Feeds (bot.py satır 33-36)
```python
RSS_FEEDS = [
    "https://cointelegraph.com/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    # Yeni feed ekleyin
]
```

## 📝 Logging

Bot çalıştığında terminal'de detaylı loglar görülür:

```
2024-01-15 10:30:45 - INFO - 🤖 KRİPTO HABER ANALIZ BOTU v14 Başlatılıyor...
2024-01-15 10:30:45 - INFO - ⏱️  Şeduler başlatıldı - Her 30 saniyede kontrol
2024-01-15 10:31:15 - INFO - 🔍 Haberler kontrol ediliyor...
```

## 🐛 Sorun Giderme

### Bot başlamıyor
- API keylerinizin doğru olup olmadığını kontrol edin
- Discord webhook URL'si aktif olduğundan emin olun

### Haberler gelmiyorsa
- Internet bağlantısını kontrol edin
- API rate limitini aşmadığınızdan emin olun
- Loglar'ı kontrol edin: `python bot.py`

### Claude analizi başarısız
- Claude API keyi geçerli mi?
- Rate limit aşıldı mı? (bkz: Anthropic docs)
- API yanıtını loglardan kontrol edin

## 📚 API Kaynakları

- [NewsAPI](https://newsapi.org)
- [Claude API](https://docs.anthropic.com)
- [Twitter API v2](https://developer.twitter.com/en/docs)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook)

## 📄 Lisans

MIT License - Özgürce kullanın!

## 👨‍💻 Geliştirme

Katkı yapmak ister misiniz? Pull request gönderin!

---

**Bot Sürümü**: v14  
**Son Güncelleme**: 25 Ekim 2024  
**Durum**: ✅ Aktif & Çalışan
