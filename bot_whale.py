import os
import logging
import requests
import tweepy
import json
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time

# Load environment variables
load_dotenv()

# Configuration
WHALE_DISCORD_WEBHOOK_URL = os.getenv("WHALE_DISCORD_WEBHOOK_URL")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Persistent sent whale alerts storage
SENT_WHALE_FILE = "sent_whale_alerts.json"

def load_sent_whale_alerts():
    """Load sent whale alerts from JSON file"""
    try:
        if os.path.exists(SENT_WHALE_FILE):
            with open(SENT_WHALE_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        logger.error(f"Error loading sent_whale_alerts: {e}")
    return set()

def save_sent_whale_alerts(sent_alerts):
    """Save sent whale alerts to JSON file"""
    try:
        with open(SENT_WHALE_FILE, 'w') as f:
            json.dump(list(sent_alerts), f)
    except Exception as e:
        logger.error(f"Error saving sent_whale_alerts: {e}")

# Load sent alerts at startup
sent_whale_alerts = load_sent_whale_alerts()
logger.info(f"🐋 {len(sent_whale_alerts)} whale alert hafızaya yüklendi")

def get_whale_alerts():
    """Fetch from Whale Alert Twitter Account (@whale_alert)"""
    try:
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        
        # Get tweets from @whale_alert
        tweets = client.search_recent_tweets(
            query="from:whale_alert",
            max_results=10,
            tweet_fields=['created_at']
        )
        
        if not tweets.data:
            logger.info("📡 Whale Alert tweet bulunamadı")
            return []
        
        formatted = []
        for tweet in tweets.data:
            formatted.append({
                "title": "🐋 Whale Alert",
                "description": tweet.text[:500],
                "url": f"https://twitter.com/whale_alert/status/{tweet.id}",
                "source": "Whale Alert (@whale_alert)",
                "type": "whale_alert",
                "published_at": tweet.created_at.isoformat() if tweet.created_at else datetime.now().isoformat(),
                "tweet_id": tweet.id
            })
        
        logger.info(f"🐋 {len(formatted)} whale alert bulundu")
        return formatted
        
    except Exception as e:
        logger.error(f"Whale Alert Fetch Error: {e}")
        return []

def send_whale_alert_to_discord(whale_alert):
    """Send whale alert to whale-alerts channel"""
    try:
        description = whale_alert.get("description", "")
        url = whale_alert.get("url", "")
        
        # Parse whale alert info
        embed = {
            "title": "🐋 Whale Alert - Büyük Cüzdan Hareketi",
            "description": description,
            "url": url,
            "color": 0xFF6B9D,  # Pink color
            "fields": [
                {
                    "name": "📊 Kaynak",
                    "value": whale_alert.get("source", "Whale Alert"),
                    "inline": True
                },
                {
                    "name": "⏰ Zaman",
                    "value": format_time(whale_alert.get("published_at", "")),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Whale Alert Tracker v2"
            }
        }
        
        payload = {"embeds": [embed]}
        
        response = requests.post(WHALE_DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ Whale Alert gönderildi")
            return True
        else:
            logger.error(f"Discord Error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Whale Send Error: {e}")
        return False

def format_time(iso_time):
    """Format published time"""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return "Zaman bilinmiyor"

def check_whale_alerts():
    """Check for new whale alerts"""
    global sent_whale_alerts
    
    try:
        logger.info("\n🐋 Whale Alert'ler kontrol ediliyor...")
        
        alerts = get_whale_alerts()
        
        for alert in alerts:
            # Create unique ID using tweet_id
            alert_id = str(alert.get('tweet_id', f"{alert.get('title')}:{alert.get('url')}"))
            
            # Check if already sent
            if alert_id not in sent_whale_alerts:
                sent_whale_alerts.add(alert_id)
                save_sent_whale_alerts(sent_whale_alerts)  # Save immediately
                
                logger.info(f"\n🔔 Yeni Whale Alert: {alert.get('description')[:60]}")
                send_whale_alert_to_discord(alert)
                
                time.sleep(1)
        
        logger.info(f"\n✅ Whale Alert kontrol tamamlandı (Hafızada {len(sent_whale_alerts)} alert)\n")
        
    except Exception as e:
        logger.error(f"Check Whale Error: {e}")

def start_scheduler():
    """Start scheduler"""
    scheduler = BackgroundScheduler()
    
    # Check whale alerts every 2 minutes
    scheduler.add_job(
        check_whale_alerts,
        'interval',
        seconds=120,
        id='check_whale_job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("⏱️  Whale Alert Şeduler başlatıldı - Her 2 dakikada kontrol\n")
    
    return scheduler

if __name__ == "__main__":
    logger.info("\n🐋 WHALE ALERT TRACKER BOTU v2 Başlatılıyor...\n")
    
    scheduler = start_scheduler()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Whale Alert Bot durduruldu")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        scheduler.shutdown()
