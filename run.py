import json
import time
import os
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

os.makedirs("data", exist_ok=True)

# IMPROVED: More specific search queries for each exchange
EXCHANGES = {
    "Bitget": ["bitget", "bitget exchange", "bitget token", "bitget UEX", "BGB token", "bitget wallet"],
    "Binance": ["binance", "binance exchange", "BNB", "binance.com", "CZ Binance"],
    "OKX": ["okx exchange", "okx token", "okx crypto", "okx wallet"],
    "Bybit": ["bybit", "bybit exchange", "bybit crypto", "bybit wallet"],
    "MEXC": ["mexc", "mexc exchange", "mexc crypto", "mexc global"],
    "KuCoin": ["kucoin", "kucoin exchange", "kcs token", "kucoin crypto"]
}

# IMPROVED: More comprehensive Google News queries
GOOGLE_FEEDS = {
    # Specific brand searches
    "https://news.google.com/rss/search?q=bitget+exchange&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=binance+exchange&hl=en-US&gl=US&ceid=US:en": "Binance",
    "https://news.google.com/rss/search?q=OKX+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "OKX",
    "https://news.google.com/rss/search?q=Bybit+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "Bybit",
    "https://news.google.com/rss/search?q=MEXC+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "MEXC",
    "https://news.google.com/rss/search?q=KuCoin+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "KuCoin",
    
    # Additional specific searches for Bitget (to boost coverage)
    "https://news.google.com/rss/search?q=bitget+UEX+universal+exchange&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=bitget+tokenized+stocks&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=bitget+reserves+transparency&hl=en-US&gl=US&ceid=US:en": "Bitget",
}

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://blockworks.co/feed",
    "https://bitcoinist.com/feed/",
    "https://newsbtc.com/feed/",
    "https://cryptonews.com/news/feed/",
    "https://coinjournal.net/feed/",
    "https://cryptobriefing.com/feed/",
    "https://beincrypto.com/feed/",
]

COLORS = {
    "Bitget": "#00c4ff",
    "OKX": "#ff4d6d",
    "Bybit": "#ff9800",
    "MEXC": "#ffd740",
    "KuCoin": "#00e676",
    "Binance": "#7b61ff",
}

ORDER = ["Bitget", "Binance", "OKX", "Bybit", "MEXC", "KuCoin"]

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print("Fetch failed " + url + " : " + str(e))
        return ""

def parse_rss(xml_text):
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.iter("item"):
            items.append({
                "title": item.findtext("title", "").strip(),
                "link": item.findtext("link", "").strip(),
                "desc": item.findtext("description", "").strip(),
                "pub": item.findtext("pubDate", "").strip(),
            })
    except Exception as e:
        print("Parse error: " + str(e))
    return items

def has_mention(text, keywords):
    t = text.lower()
    # Count matches - if multiple keywords match, count as 1
    return any(k in t for k in keywords)

def fetch_price(coin_id):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=" + coin_id + "&vs_currencies=usd&include_24hr_change=true"
    raw = fetch_url(url)
    if raw:
        try:
            return json.loads(raw).get(coin_id, {})
        except Exception:
            pass
    return {}

def fetch_fg():
    raw = fetch_url("https://api.alternative.me/fng/?limit=1")
    if raw:
        try:
            d = json.loads(raw)["data"][0]
            return {"value": d["value"], "classification": d["value_classification"]}
        except Exception:
            pass
    return {"value": "N/A", "classification": "Unknown"}

# Process Google News feeds
print("Fetching Google News feeds...")
sov_counts = defaultdict(int)
bitget_news = []

for feed_url, exchange in GOOGLE_FEEDS.items():
    xml = fetch_url(feed_url)
    if xml:
        items = parse_rss(xml)
        # Only count unique articles per exchange
        new_count = 0
        for item in items:
            # Skip duplicates within same exchange
            if item["link"] not in [i["link"] for i in bitget_news]:
                new_count += 1
                if exchange == "Bitget":
                    src = urllib.parse.urlparse(item["link"]).netloc.replace("www.", "")
                    bitget_news.append({
                        "title": item["title"],
                        "link": item["link"],
                        "source": src,
                        "pub": item["pub"][:16] if item["pub"] else "",
                    })
        sov_counts[exchange] += new_count
        print(f"  {exchange}: {new_count} new articles")
    time.sleep(0.3)

print(f"Total Bitget articles found: {len(bitget_news)}")

# Process general RSS feeds
print("Fetching general RSS feeds...")
all_items = []
for feed in RSS_FEEDS:
    xml = fetch_url(feed)
    if xml:
        parsed = parse_rss(xml)
        all_items.extend(parsed)
    time.sleep(0.3)

print("Total RSS articles: " + str(len(all_items)))

# Count mentions from RSS (excluding Google News results to avoid dupes)
google_links = set()
for feed_url, exchange in GOOGLE_FEEDS.items():
    xml = fetch_url(feed_url)
    if xml:
        items = parse_rss(xml)
        for item in items:
            google_links.add(item["link"])

rss_only_count = defaultdict(int)
for item in all_items:
    # Skip if already in Google News
    if item["link"] in google_links:
        continue
    text = (item["title"] + " " + item["desc"]).lower()
    for ex, kw in EXCHANGES.items():
        if has_mention(text, kw):
            rss_only_count[ex] += 1

# Merge counts (avoid double counting)
for ex, cnt in rss_only_count.items():
    sov_counts[ex] = sov_counts.get(ex, 0) + cnt

print("Final SOV counts:")
for ex in ORDER:
    print(f"  {ex}: {sov_counts.get(ex, 0)}")

total_m = sum(sov_counts.values()) or 1
sov_pct = {ex: round(cnt / total_m * 100, 1) for ex, cnt in sov_counts.items()}

# Deduplicate Bitget news
seen_links = set()
unique_bitget_news = []
for item in bitget_news:
    if item["link"] not in seen_links:
        seen_links.add(item["link"])
        unique_bitget_news.append(item)
bitget_news = unique_bitget_news[:10]  # Keep max 10

print("Fetching market data...")
btc = fetch_price("bitcoin")
eth = fetch_price("ethereum")
fg = fetch_fg()

gen_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

data = {
    "generated_at": gen_at,
    "sov_counts": dict(sov_counts),
    "sov_pct": sov_pct,
    "total_scanned": len(all_items) + sum(sov_counts.values()),
    "bitget_news": bitget_news,
    "btc_price": btc.get("usd", "N/A"),
    "btc_change": round(btc.get("usd_24h_change", 0), 2),
    "eth_price": eth.get("usd", "N/A"),
    "eth_change": round(eth.get("usd_24h_change", 0), 2),
    "fg_value": fg["value"],
    "fg_class": fg["classification"],
    "reserve_btc": "36,700",
    "reserve_ratio": "169%",
    "reserve_yoy": "+86% YoY",
    "net_inflows": "205M USD",
}

with open("data/dashboard_data.json", "w") as f:
    json.dump(data, f, indent=2)

print("Data saved to data/dashboard_data.json")