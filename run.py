import json
import time
import os
import difflib
import re
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
os.makedirs("data", exist_ok=True)
**EXCHANGE KEYWORD CONFIG**
**─────────────────────────────────────────────**
EXCHANGES = {
    "Bitget": ["bitget", "bitget exchange", "bitget token", "bitget UEX", "BGB token", "bitget wallet"],
    "Binance": ["binance", "binance exchange", "BNB", "binance.com", "CZ Binance"],
    "OKX": ["okx exchange", "okx token", "okx crypto", "okx wallet"],
    "Bybit": ["bybit", "bybit exchange", "bybit crypto", "bybit wallet"],
    "MEXC": ["mexc", "mexc exchange", "mexc crypto", "mexc global"],
    "KuCoin": ["kucoin", "kucoin exchange", "kcs token", "kucoin crypto"],
}
**─────────────────────────────────────────────**
**SENTIMENT KEYWORDS**
**─────────────────────────────────────────────**
POSITIVE_KEYWORDS = [
    "partnership", "launch", "record", "growth", "wins", "expands", "raises", "integrates",
    "bullish", "milestone", "surpasses", "achieves", "leading", "innovation", "approved",
    "listed", "gains", "tops", "rally", "best", "secured", "trusted", "compliant",
    "regulation approved", "new feature", "upgrade", "award"
]
NEGATIVE_KEYWORDS = [
    "hack", "scam", "fraud", "down", "outage", "crash", "lawsuit", "fined", "breach",
    "exploit", "stolen", "arrested", "investigation", "ban", "suspended", "halted",
    "loss", "penalty", "delisted", "warning", "risk", "bearish", "collapse", "scandal",
    "charges", "seizure", "blocked"
]
def score_sentiment(text):
    text_lower = text.lower()
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    else:
        return "neutral"
**─────────────────────────────────────────────**
**GOOGLE NEWS RSS FEEDS (per-exchange queries)**
**─────────────────────────────────────────────**
GOOGLE_FEEDS = {
    # Base searches
    "https://news.google.com/rss/search?q=bitget+exchange&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=binance+exchange&hl=en-US&gl=US&ceid=US:en": "Binance",
    "https://news.google.com/rss/search?q=OKX+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "OKX",
    "https://news.google.com/rss/search?q=Bybit+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "Bybit",
    "https://news.google.com/rss/search?q=MEXC+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "MEXC",
    "https://news.google.com/rss/search?q=KuCoin+crypto+exchange&hl=en-US&gl=US&ceid=US:en": "KuCoin",
    # Binance extras
    "https://news.google.com/rss/search?q=BNB+token+binance&hl=en-US&gl=US&ceid=US:en": "Binance",
    "https://news.google.com/rss/search?q=binance+reserve+proof&hl=en-US&gl=US&ceid=US:en": "Binance",
    "https://news.google.com/rss/search?q=binance+US+regulation&hl=en-US&gl=US&ceid=US:en": "Binance",
    # OKX extras
    "https://news.google.com/rss/search?q=OKX+NYSE+ICE&hl=en-US&gl=US&ceid=US:en": "OKX",
    "https://news.google.com/rss/search?q=OKX+tokenized+stocks&hl=en-US&gl=US&ceid=US:en": "OKX",
    "https://news.google.com/rss/search?q=OKX+institutional&hl=en-US&gl=US&ceid=US:en": "OKX",
    # Bybit extras
    "https://news.google.com/rss/search?q=Bybit+MyBank&hl=en-US&gl=US&ceid=US:en": "Bybit",
    "https://news.google.com/rss/search?q=Bybit+custody+AUM&hl=en-US&gl=US&ceid=US:en": "Bybit",
    "https://news.google.com/rss/search?q=Bybit+underbanked&hl=en-US&gl=US&ceid=US:en": "Bybit",
    # MEXC extras
    "https://news.google.com/rss/search?q=MEXC+Ondo+tokenized&hl=en-US&gl=US&ceid=US:en": "MEXC",
    "https://news.google.com/rss/search?q=MEXC+zero+fee&hl=en-US&gl=US&ceid=US:en": "MEXC",
    "https://news.google.com/rss/search?q=MEXC+reserve+audit&hl=en-US&gl=US&ceid=US:en": "MEXC",
    # KuCoin extras
    "https://news.google.com/rss/search?q=KuCoin+compliance+trust&hl=en-US&gl=US&ceid=US:en": "KuCoin",
    "https://news.google.com/rss/search?q=KuCoin+KCS+token&hl=en-US&gl=US&ceid=US:en": "KuCoin",
    "https://news.google.com/rss/search?q=KuCoin+security+update&hl=en-US&gl=US&ceid=US:en": "KuCoin",
    # Bitget extras
    "https://news.google.com/rss/search?q=bitget+UEX+universal+exchange&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=bitget+tokenized+stocks&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=bitget+reserves+transparency&hl=en-US&gl=US&ceid=US:en": "Bitget",
}
**─────────────────────────────────────────────**
**NEW: DIRECT MEDIA OUTLET RSS FEEDS**
**Scans all exchanges simultaneously from authoritative sources.**
**Value = "all" means detect exchange from article content.**
**─────────────────────────────────────────────**
DIRECT_FEEDS = {
    # Institutional / research-grade
    "https://www.theblock.co/rss.xml": "all",
    "https://messari.io/rss": "all",
    # High-traffic crypto media
    "https://cointelegraph.com/rss": "all",
    "https://www.coindesk.com/arc/outboundfeeds/rss/": "all",
    "https://decrypt.co/feed": "all",
    "https://blockworks.co/feed": "all",
    "https://beincrypto.com/feed/": "all",
    "https://cryptoslate.com/feed/": "all",
    "https://watcher.guru/news/feed": "all",
    "https://coingape.com/feed/": "all",
    "https://crypto.news/feed/": "all",
    # Established outlets
    "https://protos.com/feed/": "all",
    "https://thedefiant.io/api/feed": "all",
    "https://bitcoinist.com/feed/": "all",
    "https://ambcrypto.com/feed/": "all",
}
**─────────────────────────────────────────────**
**FUZZY DEDUPLICATION (replaces URL-based dedup)**
**─────────────────────────────────────────────**
def normalize_title(title):
    """Lowercase + strip punctuation for fuzzy comparison."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title
def is_duplicate(new_title, seen_titles, threshold=0.85):
    """
    Return True if new_title is >= threshold similar to any seen title.
    85% catches near-duplicates (same story, slightly different headline).
    """
    norm_new = normalize_title(new_title)
    for seen in seen_titles:
        ratio = difflib.SequenceMatcher(None, norm_new, seen).ratio()
        if ratio >= threshold:
            return True
    return False
**─────────────────────────────────────────────**
**FETCH WITH EXPONENTIAL BACKOFF RETRY**
**─────────────────────────────────────────────**
def fetch_with_retry(url, max_retries=3, base_delay=1.0, timeout=15):
    """
    Fetch URL with exponential backoff: waits 1s, 2s, 4s between attempts.
    Returns raw bytes on success, None after all retries exhausted.
    """
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PRMonitor/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            wait = base_delay * (2 ** attempt)
            print(f"  [WARN] Attempt {attempt + 1}/{max_retries} failed for {url[:60]}: {e}")
            if attempt < max_retries - 1:
                print(f"         Retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"  [ERROR] All retries exhausted for {url[:60]}")
    return None
**─────────────────────────────────────────────**
**PARSE A SINGLE RSS FEED**
**─────────────────────────────────────────────**
def parse_feed(url, assigned_exchange=None):
    """
    Parse one RSS feed. Returns list of article dicts.
    - assigned_exchange="all"    → detect exchange from content
    - assigned_exchange="Bitget" → assign all articles to Bitget
    Includes 0.5s rate-limit sleep after every fetch.
    """
    print(f"  Fetching: {url[:80]}...")
    data = fetch_with_retry(url)
    # Rate limiting: prevents Google soft-blocks on rapid sequential requests
    time.sleep(0.5)
    if data is None:
        return []
    articles = []
    try:
        root = ET.fromstring(data)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            title_el  = item.find("title")
            link_el   = item.find("link")
            pub_el    = item.find("pubDate")
            desc_el   = item.find("description")
            title      = (title_el.text  or "").strip() if title_el  is not None else ""
            link       = (link_el.text   or "").strip() if link_el   is not None else ""
            pub_date   = (pub_el.text    or "").strip() if pub_el    is not None else ""
            description= (desc_el.text   or "").strip() if desc_el   is not None else ""
            if not title:
                continue
            full_text = f"{title} {description}".lower()
            # Determine matched exchanges
            if assigned_exchange == "all":
                matched_exchanges = [
                    ex for ex, keywords in EXCHANGES.items()
                    if any(kw.lower() in full_text for kw in keywords)
                ]
            else:
                matched_exchanges = [assigned_exchange]
            if not matched_exchanges:
                continue
            sentiment = score_sentiment(full_text)
            for ex in matched_exchanges:
                articles.append({
                    "exchange":    ex,
                    "title":       title,
                    "link":        link,
                    "pub_date":    pub_date,
                    "sentiment":   sentiment,
                    "source_feed": url,
                })
    except ET.ParseError as e:
        print(f"  [ERROR] XML parse error for {url[:60]}: {e}")
    return articles
**─────────────────────────────────────────────**
**WEEK-OVER-WEEK SOV HELPERS**
**─────────────────────────────────────────────**
LAST_WEEK_SOV_PATH = "data/last_week_sov.json"
def load_last_week_sov():
    if os.path.exists(LAST_WEEK_SOV_PATH):
        try:
            with open(LAST_WEEK_SOV_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}
def save_current_sov(sov_map):
    with open(LAST_WEEK_SOV_PATH, "w") as f:
        json.dump(sov_map, f, indent=2)
**─────────────────────────────────────────────**
**MAIN**
**─────────────────────────────────────────────**
def main():
    print("=" * 60)
    print(f"Bitget PR Monitor — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    all_articles = []
    seen_titles  = []  # normalized titles for fuzzy dedup
    # ── Step 1: Google News RSS feeds ──
    print(f"\n[1/2] Fetching {len(GOOGLE_FEEDS)} Google News feeds...")
    for url, exchange in GOOGLE_FEEDS.items():
        for article in parse_feed(url, assigned_exchange=exchange):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)
    # ── Step 2: Direct media outlet feeds ──
    print(f"\n[2/2] Fetching {len(DIRECT_FEEDS)} direct media outlet feeds...")
    for url, exchange in DIRECT_FEEDS.items():
        for article in parse_feed(url, assigned_exchange=exchange):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)
    print(f"\nTotal unique articles collected: {len(all_articles)}")
    # ── Step 3: Aggregate mentions + sentiment per exchange ──
    mention_counts  = defaultdict(int)
    sentiment_counts = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for article in all_articles:
        ex = article["exchange"]
        mention_counts[ex] += 1
        sentiment_counts[ex][article["sentiment"]] += 1
    total_mentions = sum(mention_counts.values())
    # ── Step 4: Compute SOV ──
    sov_map = {
        ex: round(mention_counts.get(ex, 0) / total_mentions * 100, 2)
        if total_mentions > 0 else 0.0
        for ex in EXCHANGES
    }
    # ── Step 5: WoW delta ──
    last_week_sov = load_last_week_sov()
    sov_delta = {
        ex: round(sov_map[ex] - last_week_sov[ex], 2)
        if ex in last_week_sov else None
        for ex in EXCHANGES
    }
    save_current_sov(sov_map)  # persist for next week
    # ── Step 6: Build output JSON ──
    exchange_data = {}
    for ex in EXCHANGES:
        delta = sov_delta.get(ex)
        exchange_data[ex] = {
            "mentions":      mention_counts.get(ex, 0),
            "sov":           sov_map[ex],
            "sov_delta_wow": delta,  # None = first run (show as n/a in dashboard)
            "sentiment": {
                "positive": sentiment_counts[ex]["positive"],
                "negative": sentiment_counts[ex]["negative"],
                "neutral":  sentiment_counts[ex]["neutral"],
            },
        }
    output = {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "total_articles": len(all_articles),
        "total_mentions": total_mentions,
        "exchanges":      exchange_data,
        "articles":       all_articles,
    }
    # ── Step 7: Write output ──
    output_path = "data/latest.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    # ── Step 8: Console summary ──
    print(f"\n✅ Done. Written to {output_path}")
    print("\n── Share of Voice Summary ──")
    for ex, data in sorted(exchange_data.items(), key=lambda x: -x[1]["sov"]):
        delta = data["sov_delta_wow"]
        if delta is not None:
            delta_str = f"({'+' if delta >= 0 else ''}{delta}% WoW)"
        else:
            delta_str = "(first run)"
        s = data["sentiment"]
        print(
            f"  {ex:8s}: {data['mentions']:4d} mentions | "
            f"SOV {data['sov']:5.1f}% {delta_str} | "
            f"😊{s['positive']} 😐{s['neutral']} 😟{s['negative']}"
        )
if __name__ == "__main__":
    main()
