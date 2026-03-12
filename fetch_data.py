#!/usr/bin/env python3
import json, re, time, os
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

OUTPUT_FILE = "data/dashboard_data.json"
os.makedirs("data", exist_ok=True)

EXCHANGES = {
    "Bitget":  ["bitget", "bgb"],
    "OKX":     ["okx", "okex"],
    "Bybit":   ["bybit"],
    "MEXC":    ["mexc"],
    "KuCoin":  ["kucoin", "kcs"],
    "Binance": ["binance", "bnb"],
}

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://blockworks.co/feed",
    "https://bitcoinist.com/feed/",
    "https://newsbtc.com/feed/",
    "https://ambcrypto.com/feed/",
    "https://cryptonews.com/news/feed/",
    "https://u.today/rss",
    "https://coinjournal.net/feed/",
]
def fetch_rss(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  RSS fetch failed {url}: {e}")
        return ""

def parse_rss(xml_text):
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            desc  = item.findtext("description", "").strip()
            pub   = item.findtext("pubDate", "").strip()
            items.append({"title": title, "link": link, "desc": desc, "pub": pub})
    except Exception as e:
        print(f"  Parse error: {e}")
    return items

def mentions(text, keywords):
    text = text.lower()
    return any(k in text for k in keywords)

def fetch_coingecko_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get(coin_id, {})
    except Exception as e:
        print(f"  CoinGecko error: {e}")
        return {}

def fetch_fear_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            d = data["data"][0]
            return {"value": d["value"], "classification": d["value_classification"]}
    except Exception as e:
        print(f"  Fear&Greed error: {e}")
        return {"value": "N/A", "classification": "Unknown"}

# --- Main ---
print("Fetching RSS feeds...")
all_items = []
for feed_url in RSS_FEEDS:
    print(f"  {feed_url}")
    xml = fetch_rss(feed_url)
    if xml:
        items = parse_rss(xml)
        all_items.extend(items)
        print(f"    -> {len(items)} articles")
    time.sleep(0.5)

print(f"Total articles fetched: {len(all_items)}")

# --- SOV Counting ---
print("Counting share of voice...")
sov_counts = defaultdict(int)
exchange_articles = defaultdict(list)

for item in all_items:
    full_text = (item["title"] + " " + item["desc"]).lower()
    for exchange, keywords in EXCHANGES.items():
        if mentions(full_text, keywords):
            sov_counts[exchange] += 1
            if exchange == "Bitget" and len(exchange_articles["Bitget"]) < 10:
                exchange_articles["Bitget"].append({
                    "title": item["title"],
                    "link": item["link"],
                    "source": urllib.parse.urlparse(item["link"]).netloc.replace("www.", ""),
                    "pub": item["pub"]
                })

total_mentions = sum(sov_counts.values()) or 1
sov_pct = {ex: round(cnt / total_mentions * 100, 1) for ex, cnt in sov_counts.items()}

print("SOV results:")
for ex, cnt in sorted(sov_counts.items(), key=lambda x: -x[1]):
    print(f"  {ex}: {cnt} mentions ({sov_pct.get(ex, 0)}%)")

# --- Market Data ---
print("Fetching market data...")
btc = fetch_coingecko_price("bitcoin")
eth = fetch_coingecko_price("ethereum")
fg  = fetch_fear_greed()


# --- Assemble Output ---
output = {
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "sov_counts": dict(sov_counts),
    "sov_pct": sov_pct,
    "total_articles_scanned": len(all_items),
    "bitget_articles": exchange_articles["Bitget"],
    "market": {
        "btc_price": btc.get("usd", "N/A"),
        "btc_change_24h": round(btc.get("usd_24h_change", 0), 2),
        "eth_price": eth.get("usd", "N/A"),
        "eth_change_24h": round(eth.get("usd_24h_change", 0), 2),
    },
    "fear_greed": fg,
    "bitget_stats": {
        "btc_reserves": "36,700",
        "reserve_ratio": "169%",
        "reserve_yoy": "+86% YoY",
        "net_inflows": "$205M",
        "tokenized_stocks_vol": "$1B+",
        "global_rank": "#6",
    }
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f, indent=2)

generated = output["generated_at"]
print("\nData saved to " + OUTPUT_FILE)
print("Generated at: " + generated)
