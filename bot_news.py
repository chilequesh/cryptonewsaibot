import os
import logging
import requests
import tweepy
import json
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time
import hashlib

# Load environment variables
load_dotenv()

# Configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory sent news storage (SESSION BASED - reset on restart is OK)
# Bu session'da atılan haberler tekrar gelmez
sent_news_session = set()

# RSS Feeds
RSS_FEEDS = [
    "https://cointelegraph.com/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

# Twitter Keywords
TWITTER_KEYWORDS = ["bitcoin", "ethereum", "crypto", "cryptocurrency", "blockchain", "NFT", "DeFi", "altcoin", "BTC", "ETH"]

def parse_rss_feed(feed_url):
    """Parse RSS feed"""
    articles = []
    try:
        import xml.etree.ElementTree as ET
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        
        for item in items[:3]:
            title_elem = item.find('title')
            desc_elem = item.find('description')
            link_elem = item.find('link')
            pub_date = item.find('pubDate')
            
            if title_elem is None:
                title_elem = item.find('{http://www.w3.org/2005/Atom}title')
            if desc_elem is None:
                desc_elem = item.find('{http://www.w3.org/2005/Atom}summary')
            if link_elem is None:
                link_elem = item.find('{http://www.w3.org/2005/Atom}link')
            if pub_date is None:
                pub_date = item.find('{http://www.w3.org/2005/Atom}published')
            
            title = title_elem.text if title_elem is not None else ""
            description = desc_elem.text if desc_elem is not None else ""
            link = link_elem.text if link_elem is not None else ""
            published_time = pub_date.text if pub_date is not None else datetime.now().isoformat()
            
            if link_elem is not None and link_elem.get('href'):
                link = link_elem.get('href')
            
            if title and link:
                articles.append({
                    "title": title,
                    "description": description[:300] if description else "",
                    "url": link,
                    "source": "RSS Feed",
                    "type": "rss",
                    "published_at": published_time
                })
    except Exception as e:
        logger.error(f"RSS Parse Error: {e}")
    
    return articles

def get_newsapi_news():
    """Fetch from NewsAPI"""
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "cryptocurrency OR bitcoin OR ethereum OR crypto",
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": NEWSAPI_KEY,
            "pageSize": 5,
        }
        response = requests.get(url, params=params, timeout=10)
        articles = response.json().get("articles", [])
        
        formatted = []
        for article in articles:
            formatted.append({
                "title": article.get("title", ""),
                "description": article.get("description", "")[:300],
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "type": "newsapi",
                "published_at": article.get("publishedAt", datetime.now().isoformat())
            })
        return formatted
    except Exception as e:
        logger.error(f"NewsAPI Error: {e}")
        return []

def get_twitter_news():
    """Fetch from Twitter"""
    try:
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        query = " OR ".join(TWITTER_KEYWORDS) + " -is:retweet lang:en"
        
        tweets = client.search_recent_tweets(
            query=query,
            max_results=10,
            tweet_fields=['created_at', 'public_metrics'],
            expansions=['author_id'],
            user_fields=['username']
        )
        
        if not tweets.data:
            return []
        
        users = {user.id: user for user in tweets.includes['users']} if tweets.includes else {}
        formatted = []
        
        for tweet in tweets.data:
            user = users.get(tweet.author_id, {})
            formatted.append({
                "title": f"Tweet from @{getattr(user, 'username', 'unknown')}",
                "description": tweet.text[:300],
                "url": f"https://twitter.com/{getattr(user, 'username', 'crypto')}/status/{tweet.id}",
                "source": "Twitter",
                "type": "twitter",
                "published_at": tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat()
            })
        return formatted
    except Exception as e:
        logger.error(f"Twitter Error: {e}")
        return []

def create_unique_hash(title, description):
    """Create unique hash from title and description"""
    combined = f"{title}:{description}".lower().strip()
    return hashlib.md5(combined.encode()).hexdigest()

def analyze_with_claude(title, description):
    """Advanced analysis with Claude - Psychology & Market Behavior"""
    try:
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        prompt = f"""Sen bir uzman kripto para analisti ve pazar psikologusun.

GÖREVIN:
1. Haberin GERÇEK piyasa psikolojisine etkisini anlamak
2. Fiyat hareketleri öncesi işaret olup olmadığını tespit etmek
3. Sadece KAYDA DEĞER haberleri seç, önemsiz olanları göz ardı et
4. Yatırımcı davranışını ne şekilde etkileyeceğini analiz etmek

HABER:
Başlık: {title}
Özet: {description}

ANALIZ KRİTERLERİ:
- Fear & Greed Index etkisi nedir?
- Whale/Büyük yatırımcıları hareket ettirir mi?
- Retail yatırımcı paniğine neden olur mu?
- Fiyat hareketinin büyüklüğü ne olabilir?
- Haberin gerçekliği ne kadar kesin?

ÖNEMLİLİK FİLTRESİ:
- CRITICAL: Devasa hareket yaratabilecek (Fiyat %10+)
- HIGH: Büyük hareket yaratabilecek (Fiyat %5-10)
- MEDIUM: Dikkate alınması gereken (Fiyat %2-5)
- LOW: Bilgilendirici (Fiyat <2%)
- SKIPPABLE: Önemsiz haber

RİSK SEVİYESİ:
- HIGH: Çok yüksek volatilite ve belirsizlik
- MEDIUM: Normal volatilite
- LOW: Düşük volatilite

ÖNERİ:
- BUY: Satın alma sinyali
- SELL: Satış sinyali
- WAIT: Bekleme önerisi
- HOLD: Tutma önerisi

SADECE bu JSON formatında cevap ver:
{{"title_tr": "Türkçe başlık", "summary_tr": "Türkçe özet (max 150 karakter)", "sentiment": "POSITIVE/NEGATIVE/NEUTRAL", "market_impact": "HIGH/MEDIUM/LOW", "news_importance": "CRITICAL/HIGH/MEDIUM/LOW/SKIPPABLE", "price_movement": "Beklenen fiyat hareketi (ör: +3-5%)", "risk_level": "HIGH/MEDIUM/LOW", "recommendation": "BUY/SELL/WAIT/HOLD", "psychology": "Pazar psikolojisi (max 80 karakter)", "whale_behavior": "Whale davranışı (max 80 karakter)", "analysis_tr": "Kısa analiz (max 100 karakter)", "emoji": "Uygun emoji"}}"""
        
        payload = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 800,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result['content'][0]['text'].strip()
            
            logger.info(f"Claude: {text[:80]}")
            
            if "null" in text.lower() or "skip" in text.lower():
                logger.info(f"⏭️  Haber atlandı (önemsiz)")
                return None
            
            try:
                start = text.find('{')
                end = text.rfind('}') + 1
                
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    analysis = json.loads(json_str)
                    
                    if analysis.get("news_importance") == "SKIPPABLE":
                        logger.info(f"⏭️  Filtrelen: SKIPPABLE")
                        return None
                    
                    logger.info(f"✅ {analysis.get('sentiment')} | {analysis.get('news_importance')}")
                    return analysis
                else:
                    logger.error(f"JSON not found in response")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON Parse Error: {e}")
                return None
        else:
            logger.error(f"Claude API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return None

def get_sentiment_color(sentiment):
    """Get color for sentiment"""
    colors = {
        "POSITIVE": 0x00FF00,
        "NEGATIVE": 0xFF0000,
        "NEUTRAL": 0x808080
    }
    return colors.get(sentiment, 0x808080)

def get_emoji_for_sentiment(sentiment):
    """Get emoji for sentiment"""
    emojis = {
        "POSITIVE": "🟢",
        "NEGATIVE": "🔴",
        "NEUTRAL": "⚪"
    }
    return emojis.get(sentiment, "⚪")

def get_urgency_badge(importance):
    """Get urgency badge"""
    badges = {
        "CRITICAL": "🚨 KRİTİK",
        "HIGH": "⚠️ YÜKSEK",
        "MEDIUM": "ℹ️ ORTA",
        "LOW": "💡 DÜŞÜK"
    }
    return badges.get(importance, "ℹ️ ORTA")

def format_published_time(iso_time):
    """Format published time"""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return "Zaman bilinmiyor"

def send_to_discord(news_item, analysis):
    """Send analyzed news to Discord"""
    try:
        if not analysis:
            return False
        
        if analysis.get("news_importance") == "SKIPPABLE":
            logger.info(f"⏭️  Gönderilmedi (önemsiz)")
            return False
        
        title_tr = analysis.get("title_tr", "")
        summary_tr = analysis.get("summary_tr", "")
        sentiment = analysis.get("sentiment", "NEUTRAL")
        market_impact = analysis.get("market_impact", "MEDIUM")
        analysis_text = analysis.get("analysis_tr", "")
        psychology = analysis.get("psychology", "")
        whale_behavior = analysis.get("whale_behavior", "")
        news_importance = analysis.get("news_importance", "MEDIUM")
        price_movement = analysis.get("price_movement", "Bilinmiyor")
        risk_level = analysis.get("risk_level", "MEDIUM")
        recommendation = analysis.get("recommendation", "WAIT")
        published_time = format_published_time(news_item.get("published_at", ""))
        
        emoji_sentiment = get_emoji_for_sentiment(sentiment)
        color = get_sentiment_color(sentiment)
        urgency_badge = get_urgency_badge(news_importance)
        
        sentiment_labels = {
            "POSITIVE": "Pozitif 📈",
            "NEGATIVE": "Negatif 📉",
            "NEUTRAL": "Nötr ➡️"
        }
        
        impact_labels = {
            "HIGH": "Yüksek 🔥",
            "MEDIUM": "Orta ⚡",
            "LOW": "Düşük 💤"
        }
        
        risk_labels = {
            "HIGH": "Yüksek 🔴",
            "MEDIUM": "Orta 🟡",
            "LOW": "Düşük 🟢"
        }
        
        rec_labels = {
            "BUY": "🟢 AL",
            "SELL": "🔴 SAT",
            "WAIT": "🟡 BEKLE",
            "HOLD": "🔵 TART"
        }
        
        embed = {
            "title": f"{emoji_sentiment} {title_tr}",
            "description": summary_tr,
            "url": news_item.get("url", ""),
            "color": color,
            "fields": [
                {
                    "name": f"{urgency_badge}",
                    "value": f"Önem Seviyesi",
                    "inline": True
                },
                {
                    "name": "⚠️ Risk Seviyesi",
                    "value": risk_labels.get(risk_level, "Orta"),
                    "inline": True
                },
                {
                    "name": "💡 Tavsiye",
                    "value": rec_labels.get(recommendation, "BEKLE"),
                    "inline": True
                },
                {
                    "name": "💭 Piyasanın Duygusu",
                    "value": sentiment_labels.get(sentiment, "Nötr"),
                    "inline": True
                },
                {
                    "name": "💹 Piyasa Etkisi",
                    "value": impact_labels.get(market_impact, "Orta"),
                    "inline": True
                },
                {
                    "name": "📊 Fiyat Hareketi",
                    "value": price_movement,
                    "inline": True
                },
                {
                    "name": "🧠 Pazar Psikolojisi",
                    "value": psychology if psychology else "Analiz yapılamadı",
                    "inline": False
                },
                {
                    "name": "🐋 Whale Davranışı",
                    "value": whale_behavior if whale_behavior else "Tahmin yapılamadı",
                    "inline": False
                },
                {
                    "name": "💬 Analiz",
                    "value": analysis_text if analysis_text else "Analiz yapılamadı",
                    "inline": False
                },
                {
                    "name": "📌 Kaynak",
                    "value": news_item.get("source", "Unknown"),
                    "inline": True
                },
                {
                    "name": "📅 Yayın Zamanı",
                    "value": published_time,
                    "inline": True
                }
            ],
            "footer": {
                "text": "Kripto Haber Analiz Botu v3"
            }
        }
        
        payload = {"embeds": [embed]}
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ Discord'a gönderildi: {title_tr[:40]}")
            return True
        else:
            logger.error(f"Discord Error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Send Error: {e}")
        return False

def check_news():
    """Check all news sources"""
    global sent_news_session
    
    try:
        logger.info("\n🔍 Haberler kontrol ediliyor...")
        
        all_articles = []
        all_articles.extend(get_newsapi_news())
        all_articles.extend(get_twitter_news())
        all_articles.extend(parse_rss_feed_all())
        
        logger.info(f"📰 {len(all_articles)} haber bulundu")
        
        for article in all_articles:
            title = article.get("title", "").strip()
            description = article.get("description", "").strip()
            
            # Create unique hash
            news_hash = create_unique_hash(title, description)
            
            if news_hash not in sent_news_session:
                sent_news_session.add(news_hash)
                
                logger.info(f"\n🔄 Analiz: {title[:50]}")
                analysis = analyze_with_claude(title, description)
                
                if analysis:
                    send_to_discord(article, analysis)
                
                time.sleep(2)
        
        logger.info(f"\n✅ Kontrol tamamlandı (Bu session'da {len(sent_news_session)} haber işlendi)\n")
    except Exception as e:
        logger.error(f"Check Error: {e}")

def parse_rss_feed_all():
    """Get all RSS feeds"""
    articles = []
    for feed_url in RSS_FEEDS:
        articles.extend(parse_rss_feed(feed_url))
    return articles

def start_scheduler():
    """Start scheduler"""
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        check_news,
        'interval',
        seconds=30,
        id='check_news_job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("⏱️  Şeduler başlatıldı - Her 30 saniyede kontrol\n")
    
    return scheduler

if __name__ == "__main__":
    logger.info("\n🤖 KRİPTO HABER ANALIZ BOTU v3 Başlatılıyor...\n")
    
    scheduler = start_scheduler()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot durduruldu")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        scheduler.shutdown()
