import os
import logging
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time
import hashlib

# Load environment variables
load_dotenv()

# Configuration
WHALE_DISCORD_WEBHOOK_URL = os.getenv("WHALE_DISCORD_WEBHOOK_URL")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory sent whale alerts storage (SESSION BASED)
sent_whale_alerts_session = set()

# Top coins tracking
TOP_COINS = {
    "BTC": {"name": "Bitcoin", "threshold": 500000},
    "ETH": {"name": "Ethereum", "threshold": 500000},
    "SOL": {"name": "Solana", "threshold": 500000},
    "XRP": {"name": "Ripple", "threshold": 500000},
    "LTC": {"name": "Litecoin", "threshold": 500000},
    "USDT": {"name": "Tether", "threshold": 500000},
    "USDC": {"name": "USD Coin", "threshold": 500000},
    "BNB": {"name": "Binance Coin", "threshold": 500000},
    "ADA": {"name": "Cardano", "threshold": 500000},
    "DOGE": {"name": "Dogecoin", "threshold": 500000},
    "AVAX": {"name": "Avalanche", "threshold": 500000},
    "MATIC": {"name": "Polygon", "threshold": 500000},
    "LINK": {"name": "Chainlink", "threshold": 500000},
    "DOT": {"name": "Polkadot", "threshold": 500000},
    "TRX": {"name": "Tron", "threshold": 500000},
    "XLM": {"name": "Stellar", "threshold": 500000},
    "BCH": {"name": "Bitcoin Cash", "threshold": 500000},
    "NEAR": {"name": "NEAR Protocol", "threshold": 500000},
    "ICP": {"name": "Internet Computer", "threshold": 500000},
    "TAO": {"name": "Bittensor", "threshold": 500000},
}

def get_coin_price(coin_id):
    """Get coin price from CoinGecko (100% FREE)"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        price = data.get(coin_id, {}).get("usd", 0)
        return price if price > 0 else 1
    except Exception as e:
        logger.error(f"CoinGecko Price Error ({coin_id}): {e}")
        return 1

def get_bitcoin_large_transfers():
    """Get large BTC transfers from Blockchain.com (100% FREE - No API key)"""
    try:
        logger.info("🔗 Bitcoin large transfers kontrol ediliyor...")
        
        # blockchain.com - free API, no key needed
        url = "https://blockchain.info/unconfirmed/btc"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.warning("Blockchain.com API unavailable")
            return []
        
        data = response.json()
        transfers = []
        btc_price = get_coin_price("bitcoin")
        
        for tx in data.get("txs", [])[:50]:
            try:
                # Get transaction outputs (receivers)
                outputs = tx.get("out", [])
                inputs = tx.get("inputs", [])
                
                if not outputs or not inputs:
                    continue
                
                # Get largest output
                largest_output = max(outputs, key=lambda x: x.get("value", 0))
                largest_input = inputs[0] if inputs else {}
                
                amount_satoshi = largest_output.get("value", 0)
                amount_btc = amount_satoshi / 100000000
                usd_value = amount_btc * btc_price
                
                # Filter for $1M+
                if usd_value >= 1000000:
                    from_addr = largest_input.get("prev_out", {}).get("addr", "Unknown")
                    to_addr = largest_output.get("addr", "Unknown")
                    
                    transfers.append({
                        "symbol": "BTC",
                        "coin_name": "Bitcoin",
                        "from": from_addr,
                        "to": to_addr,
                        "amount": amount_btc,
                        "usd_value": usd_value,
                        "hash": tx.get("hash", ""),
                        "chain": "Bitcoin",
                        "timestamp": datetime.fromtimestamp(tx.get("time", 0)).isoformat(),
                        "explorer": "https://www.blockchain.com/btc/tx/"
                    })
            except Exception as e:
                logger.debug(f"BTC TX Parse Error: {e}")
                continue
        
        if transfers:
            logger.info(f"🐋 {len(transfers)} BTC whale transfer bulundu")
        return transfers
        
    except Exception as e:
        logger.error(f"Bitcoin API Error: {e}")
        return []

def get_ethereum_large_transfers():
    """Get large ETH transfers from Etherscan (Free public API)"""
    try:
        logger.info("📊 Ethereum large transfers kontrol ediliyor...")
        
        # Etherscan has free rate-limited endpoint for getting transactions
        # Alternative: Use Alchemy free tier or blockscout
        # For now, using Blockscout (public, no key needed)
        
        url = "https://eth.blockscout.com/api/v2/transactions?sort=desc"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.warning("Blockscout API unavailable")
            return []
        
        data = response.json()
        transfers = []
        eth_price = get_coin_price("ethereum")
        
        for tx in data.get("items", [])[:50]:
            try:
                if tx.get("status") != "ok":
                    continue
                
                # Get transaction value
                value_wei = int(tx.get("value", "0"))
                value_eth = value_wei / 1e18
                usd_value = value_eth * eth_price
                
                # Filter for $1M+
                if usd_value >= 1000000:
                    transfers.append({
                        "symbol": "ETH",
                        "coin_name": "Ethereum",
                        "from": tx.get("from", {}).get("hash", "Unknown"),
                        "to": tx.get("to", {}).get("hash", "Unknown"),
                        "amount": value_eth,
                        "usd_value": usd_value,
                        "hash": tx.get("hash", ""),
                        "chain": "Ethereum",
                        "timestamp": tx.get("timestamp", ""),
                        "explorer": "https://etherscan.io/tx/"
                    })
            except Exception as e:
                logger.debug(f"ETH TX Parse Error: {e}")
                continue
        
        if transfers:
            logger.info(f"🐋 {len(transfers)} ETH whale transfer bulundu")
        return transfers
        
    except Exception as e:
        logger.error(f"Ethereum API Error: {e}")
        return []

def get_solana_large_transfers():
    """Get large SOL transfers from Solscan (Free API)"""
    try:
        logger.info("🌞 Solana large transfers kontrol ediliyor...")
        
        # Solscan public API - no key needed
        url = "https://api.solscan.io/api/v2/transfer?fromAddress=&toAddress=&limit=50"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.warning("Solscan API unavailable")
            return []
        
        data = response.json()
        transfers = []
        sol_price = get_coin_price("solana")
        
        for tx in data.get("result", {}).get("data", [])[:50]:
            try:
                amount = float(tx.get("amount", 0))
                usd_value = amount * sol_price
                
                # Filter for $1M+
                if usd_value >= 1000000:
                    transfers.append({
                        "symbol": "SOL",
                        "coin_name": "Solana",
                        "from": tx.get("from", "Unknown"),
                        "to": tx.get("to", "Unknown"),
                        "amount": amount,
                        "usd_value": usd_value,
                        "hash": tx.get("signature", ""),
                        "chain": "Solana",
                        "timestamp": datetime.fromtimestamp(tx.get("blockTime", 0)).isoformat(),
                        "explorer": "https://solscan.io/tx/"
                    })
            except Exception as e:
                logger.debug(f"SOL TX Parse Error: {e}")
                continue
        
        if transfers:
            logger.info(f"🐋 {len(transfers)} SOL whale transfer bulundu")
        return transfers
        
    except Exception as e:
        logger.error(f"Solana API Error: {e}")
        return []

def get_multi_chain_transfers():
    """Get large transfers from multiple chains"""
    try:
        logger.info("\n🐋 Multi-Chain Whale Transfers kontrol ediliyor...")
        
        all_transfers = []
        
        # Bitcoin
        btc_transfers = get_bitcoin_large_transfers()
        all_transfers.extend(btc_transfers)
        
        # Ethereum
        eth_transfers = get_ethereum_large_transfers()
        all_transfers.extend(eth_transfers)
        
        # Solana
        sol_transfers = get_solana_large_transfers()
        all_transfers.extend(sol_transfers)
        
        total = len(all_transfers)
        if total > 0:
            logger.info(f"🐋 TOPLAM {total} whale transfer bulundu\n")
        else:
            logger.info("📡 Whale transfer bulunamadı (şimdilik $1M+ transfer yok)\n")
        
        return all_transfers
        
    except Exception as e:
        logger.error(f"Multi-Chain Error: {e}")
        return []

def create_unique_hash(tx_hash, symbol, amount):
    """Create unique hash from transaction"""
    combined = f"{tx_hash}:{symbol}:{amount}".lower().strip()
    return hashlib.md5(combined.encode()).hexdigest()

def format_address(address, chain="bitcoin"):
    """Format blockchain address"""
    if not address or address == "Unknown":
        return "Unknown"
    
    if len(address) > 16:
        return f"{address[:8]}...{address[-8:]}"
    return address

def send_whale_alert_to_discord(transfer):
    """Send whale transfer to Discord"""
    try:
        symbol = transfer.get("symbol", "")
        coin_name = transfer.get("coin_name", "")
        amount = transfer.get("amount", 0)
        usd_value = transfer.get("usd_value", 0)
        tx_hash = transfer.get("hash", "")
        chain = transfer.get("chain", "")
        from_addr = transfer.get("from", "Unknown")
        to_addr = transfer.get("to", "Unknown")
        timestamp = transfer.get("timestamp", "")
        explorer_base = transfer.get("explorer", "#")
        
        # Create blockchain explorer link
        explorer_url = f"{explorer_base}{tx_hash}"
        
        # Determine color based on amount
        if usd_value >= 10000000:
            color = 0xFF0000  # Red for huge transfers
        elif usd_value >= 5000000:
            color = 0xFF6600  # Orange
        elif usd_value >= 2000000:
            color = 0xFFCC00  # Yellow
        else:
            color = 0xFF6B9D  # Pink
        
        embed = {
            "title": f"🐋 {symbol} Whale Alert - {coin_name}",
            "description": f"**Large Transfer Detected**",
            "url": explorer_url,
            "color": color,
            "fields": [
                {
                    "name": "📊 Miktar",
                    "value": f"`{amount:.2f} {symbol}`",
                    "inline": True
                },
                {
                    "name": "💵 USD Değeri",
                    "value": f"`${usd_value:,.0f}`",
                    "inline": True
                },
                {
                    "name": "⛓️ Blockchain",
                    "value": f"`{chain}`",
                    "inline": True
                },
                {
                    "name": "📤 Gönderen",
                    "value": f"`{format_address(from_addr, chain)}`",
                    "inline": False
                },
                {
                    "name": "📥 Alan",
                    "value": f"`{format_address(to_addr, chain)}`",
                    "inline": False
                },
                {
                    "name": "🔗 İşlem Hash",
                    "value": f"[Görüntüle]({explorer_url})",
                    "inline": False
                },
                {
                    "name": "⏰ Zaman",
                    "value": f"`{timestamp}`",
                    "inline": True
                }
            ],
            "footer": {
                "text": "🔓 100% Free On-Chain Whale Alert Tracker v4.1"
            }
        }
        
        payload = {"embeds": [embed]}
        
        response = requests.post(WHALE_DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ Whale Alert gönderildi: {symbol} - ${usd_value:,.0f}")
            return True
        else:
            logger.error(f"Discord Error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Discord Send Error: {e}")
        return False

def check_whale_alerts():
    """Check for new whale transfers"""
    global sent_whale_alerts_session
    
    try:
        transfers = get_multi_chain_transfers()
        
        if not transfers:
            logger.info("⏭️  Whale alert bulunmadı\n")
            return
        
        for transfer in transfers:
            # Create unique hash
            tx_hash = transfer.get("hash", f"{transfer.get('symbol')}_{time.time()}")
            alert_hash = create_unique_hash(
                tx_hash,
                transfer.get("symbol", ""),
                transfer.get("amount", 0)
            )
            
            # Check if already sent in this session
            if alert_hash not in sent_whale_alerts_session:
                sent_whale_alerts_session.add(alert_hash)
                
                logger.info(f"\n🔔 Yeni Whale Transfer: {transfer.get('symbol')} - ${transfer.get('usd_value', 0):,.0f}")
                send_whale_alert_to_discord(transfer)
                
                time.sleep(1)
        
        logger.info(f"\n✅ Whale Alert kontrol tamamlandı (Bu session'da {len(sent_whale_alerts_session)} alert işlendi)\n")
        
    except Exception as e:
        logger.error(f"Check Whale Error: {e}")

def start_scheduler():
    """Start scheduler"""
    scheduler = BackgroundScheduler()
    
    # Check every 1 minute
    scheduler.add_job(
        check_whale_alerts,
        'interval',
        seconds=60,
        id='check_whale_job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("⏱️  On-Chain Whale Alert Şeduler başlatıldı - Her 1 dakikada kontrol\n")
    logger.info("🔓 100% Free APIs - No API Keys Required!\n")
    
    return scheduler

if __name__ == "__main__":
    logger.info("\n🐋 ON-CHAIN WHALE ALERT TRACKER BOTU v4.1 Başlatılıyor...\n")
    
    if not WHALE_DISCORD_WEBHOOK_URL:
        logger.error("❌ WHALE_DISCORD_WEBHOOK_URL variable'ı ayarlanmamış!")
        exit(1)
    
    scheduler = start_scheduler()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 On-Chain Whale Alert Bot durduruldu")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        scheduler.shutdown()

