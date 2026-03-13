import json
import time
import os
import re
import difflib
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request
import xml.etree.ElementTree as ET
os.makedirs("data", exist_ok=True)
**─────────────────────────────────────────────**
**EXCHANGE KEYWORDS**
**─────────────────────────────────────────────**
EXCHANGES = {
    "Bitget":  ["bitget", "bgb token", "bitget wallet", "bitget exchange"],
    "Binance": ["binance", "bnb", "binance.com", "cz binance"],
    "OKX":     ["okx", "okx exchange", "okx crypto", "okx wallet"],
    "Bybit":   ["bybit", "bybit exchange", "bybit crypto"],
    "MEXC":    ["mexc", "mexc exchange", "mexc global"],
    "KuCoin":  ["kucoin", "kcs token", "kucoin exchange"],
}
EXCHANGE_COLORS = {
    "Bitget":  "#00c4ff",
    "Binance": "#7b61ff",
    "OKX":     "#ff4d6d",
    "Bybit":   "#ff9800",
    "MEXC":    "#ffd740",
    "KuCoin":  "#00e676",
}
**─────────────────────────────────────────────**
**SENTIMENT KEYWORDS**
**─────────────────────────────────────────────**
POSITIVE_KEYWORDS = [
    "partnership", "launch", "record", "growth", "wins", "expands", "raises",
    "integrates", "bullish", "milestone", "surpasses", "achieves", "leading",
    "innovation", "approved", "listed", "gains", "tops", "rally", "best",
    "secured", "trusted", "compliant", "new feature", "upgrade", "award",
    "investment", "funding", "expansion"
]
NEGATIVE_KEYWORDS = [
    "hack", "scam", "fraud", "down", "outage", "crash", "lawsuit", "fined",
    "breach", "exploit", "stolen", "arrested", "investigation", "ban",
    "suspended", "halted", "loss", "penalty", "delisted", "warning", "risk",
    "bearish", "collapse", "scandal", "charges", "seizure", "blocked", "attack"
]
def score_sentiment(text):
    t = text.lower()
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in t)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in t)
    if pos > neg:   return "positive"
    elif neg > pos: return "negative"
    else:           return "neutral"
**─────────────────────────────────────────────**
**RSS FEEDS**
**─────────────────────────────────────────────**
GOOGLE_FEEDS = {
    "https://news.google.com/rss/search?q=bitget+exchange&hl=en-US&gl=US&ceid=US:en":          "Bitget",
    "https://news.google.com/rss/search?q=bitget+crypto+exchange&hl=en-US&gl=US&ceid=US:en":   "Bitget",
    "https://news.google.com/rss/search?q=bitget+tokenized+stocks&hl=en-US&gl=US&ceid=US:en":  "Bitget",
    "https://news.google.com/rss/search?q=binance+exchange&hl=en-US&gl=US&ceid=US:en":         "Binance",
    "https://news.google.com/rss/search?q=BNB+token+binance&hl=en-US&gl=US&ceid=US:en":        "Binance",
    "https://news.google.com/rss/search?q=binance+US+regulation&hl=en-US&gl=US&ceid=US:en":    "Binance",
    "https://news.google.com/rss/search?q=OKX+crypto+exchange&hl=en-US&gl=US&ceid=US:en":      "OKX",
    "https://news.google.com/rss/search?q=OKX+institutional&hl=en-US&gl=US&ceid=US:en":        "OKX",
    "https://news.google.com/rss/search?q=Bybit+crypto+exchange&hl=en-US&gl=US&ceid=US:en":    "Bybit",
    "https://news.google.com/rss/search?q=Bybit+custody+AUM&hl=en-US&gl=US&ceid=US:en":        "Bybit",
    "https://news.google.com/rss/search?q=MEXC+crypto+exchange&hl=en-US&gl=US&ceid=US:en":     "MEXC",
    "https://news.google.com/rss/search?q=MEXC+zero+fee&hl=en-US&gl=US&ceid=US:en":            "MEXC",
    "https://news.google.com/rss/search?q=KuCoin+crypto+exchange&hl=en-US&gl=US&ceid=US:en":   "KuCoin",
    "https://news.google.com/rss/search?q=KuCoin+KCS+token&hl=en-US&gl=US&ceid=US:en":         "KuCoin",
}
DIRECT_FEEDS = {
    "https://www.theblock.co/rss.xml":                   "all",
    "https://messari.io/rss":                             "all",
    "https://cointelegraph.com/rss":                      "all",
    "https://www.coindesk.com/arc/outboundfeeds/rss/":   "all",
    "https://decrypt.co/feed":                            "all",
    "https://blockworks.co/feed":                         "all",
    "https://beincrypto.com/feed/":                       "all",
    "https://cryptoslate.com/feed/":                      "all",
    "https://watcher.guru/news/feed":                     "all",
    "https://coingape.com/feed/":                         "all",
    "https://crypto.news/feed/":                          "all",
    "https://protos.com/feed/":                           "all",
    "https://thedefiant.io/api/feed":                     "all",
    "https://bitcoinist.com/feed/":                       "all",
    "https://ambcrypto.com/feed/":                        "all",
}
**─────────────────────────────────────────────**
**FUZZY DEDUPLICATION**
**─────────────────────────────────────────────**
def normalize_title(title):
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title
def is_duplicate(new_title, seen_titles, threshold=0.85):
    norm = normalize_title(new_title)
    for seen in seen_titles:
        if difflib.SequenceMatcher(None, norm, seen).ratio() >= threshold:
            return True
    return False
**─────────────────────────────────────────────**
**FETCH WITH RETRY**
**─────────────────────────────────────────────**
def fetch_with_retry(url, max_retries=3, base_delay=1.0, timeout=15):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; PRMonitor/2.0)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            wait = base_delay * (2 ** attempt)
            print(f"  [WARN] Attempt {attempt+1}/{max_retries} failed: {url[:60]} — {e}")
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                print(f"  [ERROR] Giving up on: {url[:60]}")
    return None
**─────────────────────────────────────────────**
**PARSE RSS FEED**
**─────────────────────────────────────────────**
def parse_feed(url, assigned_exchange=None):
    print(f"  Fetching: {url[:80]}...")
    data = fetch_with_retry(url)
    time.sleep(0.5)  # rate limiting
    if data is None:
        return []
    articles = []
    try:
        root    = ET.fromstring(data)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            title_el = item.find("title")
            link_el  = item.find("link")
            pub_el   = item.find("pubDate")
            desc_el  = item.find("description")
            title   = (title_el.text or "").strip() if title_el is not None else ""
            link    = (link_el.text  or "").strip() if link_el  is not None else ""
            pub     = (pub_el.text   or "").strip() if pub_el   is not None else ""
            desc    = (desc_el.text  or "").strip() if desc_el  is not None else ""
            if not title:
                continue
            full_text = f"{title} {desc}".lower()
            if assigned_exchange == "all":
                matched = [
                    ex for ex, kws in EXCHANGES.items()
                    if any(kw in full_text for kw in kws)
                ]
            else:
                matched = [assigned_exchange]
            if not matched:
                continue
            sentiment = score_sentiment(full_text)
            for ex in matched:
                articles.append({
                    "exchange":  ex,
                    "title":     title,
                    "link":      link,
                    "pub_date":  pub,
                    "sentiment": sentiment,
                })
    except ET.ParseError as e:
        print(f"  [ERROR] XML parse error: {url[:60]} — {e}")
    return articles
**─────────────────────────────────────────────**
**WEEK-OVER-WEEK SOV**
**─────────────────────────────────────────────**
LAST_WEEK_PATH = "data/last_week_sov.json"
def load_last_week_sov():
    if os.path.exists(LAST_WEEK_PATH):
        try:
            with open(LAST_WEEK_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}
def save_sov(sov_map):
    with open(LAST_WEEK_PATH, "w") as f:
        json.dump(sov_map, f, indent=2)
**─────────────────────────────────────────────**
**GENERATE index.html**
**─────────────────────────────────────────────**
def generate_html(output):
    exchanges   = output["exchanges"]
    articles    = output["articles"]
    generated   = output["generated_at"][:16].replace("T", " ") + " UTC"
    total_art   = output["total_articles"]
    total_men   = output["total_mentions"]
    # Build SOV bar data for Chart.js
    ex_order    = list(EXCHANGES.keys())
    colors      = [EXCHANGE_COLORS[e] for e in ex_order]
    sov_values  = [exchanges[e]["sov"]      for e in ex_order]
    men_values  = [exchanges[e]["mentions"] for e in ex_order]
    # SOV cards
    cards_html = ""
    for ex in sorted(exchanges, key=lambda x: -exchanges[x]["sov"]):
        d     = exchanges[ex]
        delta = d["sov_delta_wow"]
        color = EXCHANGE_COLORS[ex]
        if delta is None:
            delta_html = '<span class="sd neutral">first run</span>'
        elif delta >= 0:
            delta_html = f'<span class="sd up">▲ +{delta}% WoW</span>'
        else:
            delta_html = f'<span class="sd down">▼ {delta}% WoW</span>'
        s = d["sentiment"]
        cards_html += f"""
        <div class="sc" style="--accent:{color}">
          <div class="sl">{ex}</div>
          <div class="sv" style="color:{color}">{d['sov']}%</div>
          {delta_html}
          <div class="sm">{d['mentions']} mentions</div>
          <div class="sent">
            <span class="pos">😊 {s['positive']}</span>
            <span class="neu">😐 {s['neutral']}</span>
            <span class="neg">😟 {s['negative']}</span>
          </div>
        </div>"""
    # SOV table rows
    table_rows = ""
    for ex in sorted(exchanges, key=lambda x: -exchanges[x]["sov"]):
        d     = exchanges[ex]
        color = EXCHANGE_COLORS[ex]
        bar   = d["sov"]
        delta = d["sov_delta_wow"]
        if delta is None:
            delta_str = "—"
        elif delta >= 0:
            delta_str = f'<span class="up">+{delta}%</span>'
        else:
            delta_str = f'<span class="down">{delta}%</span>'
        s = d["sentiment"]
        table_rows += f"""
          <tr>
            <td><b style="color:{color}">{ex}</b></td>
            <td>{d['mentions']}</td>
            <td><b>{d['sov']}%</b></td>
            <td>{delta_str}</td>
            <td>
              <div class="bb"><div class="bf" style="width:{bar}%;background:{color}"></div></div>
            </td>
            <td>
              <span class="badge pos-b">😊 {s['positive']}</span>
              <span class="badge neu-b">😐 {s['neutral']}</span>
              <span class="badge neg-b">😟 {s['negative']}</span>
            </td>
          </tr>"""
    # Articles (top 80)
    art_rows = ""
    for a in articles[:80]:
        color = EXCHANGE_COLORS.get(a["exchange"], "#aaa")
        pub   = a["pub_date"][:16] if a["pub_date"] else "—"
        sent  = a["sentiment"]
        art_rows += f"""
          <tr>
            <td><b style="color:{color}">{a['exchange']}</b></td>
            <td><a href="{a['link']}" target="_blank">{a['title']}</a></td>
            <td><span class="badge {sent}-b">{sent}</span></td>
            <td class="muted">{pub}</td>
          </tr>"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Bitget PR Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#0d0f14;--s:#161a23;--s2:#1e2330;--br:#2a2f3d;--tx:#e8eaf6;--mu:#7986a3}}
    body{{background:var(--bg);color:var(--tx);font-family:'Segoe UI',sans-serif;min-height:100vh}}
    header{{background:linear-gradient(135deg,#0d0f14,#161a23);border-bottom:1px solid var(--br);
            padding:20px 32px;display:flex;align-items:center;justify-content:space-between}}
    .logo{{display:flex;align-items:center;gap:14px}}
    .li{{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,#00c4ff,#7b61ff);
         display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#fff}}
    .lt h1{{font-size:20px;font-weight:700}}
    .lt p{{font-size:12px;color:var(--mu);margin-top:2px}}
    .hr{{display:flex;align-items:center;gap:16px}}
    .lb{{display:flex;align-items:center;gap:6px;background:rgba(0,230,118,.1);
         border:1px solid rgba(0,230,118,.3);color:#00e676;padding:5px 12px;
         border-radius:20px;font-size:12px;font-weight:600}}
    .ld{{width:7px;height:7px;border-radius:50%;background:#00e676;animation:pulse 1.5s infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
    .ts{{font-size:12px;color:var(--mu)}}
    .wrap{{max-width:1400px;margin:0 auto;padding:24px 32px}}
    /* SOV Cards */
    .sb{{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:28px}}
    .sc{{background:var(--s);border:1px solid var(--br);border-radius:12px;padding:16px 20px;
         position:relative;overflow:hidden}}
    .sc::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent,#00c4ff)}}
    .sl{{font-size:11px;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}}
    .sv{{font-size:28px;font-weight:700}}
    .sd{{font-size:12px;margin-top:4px;font-weight:600}}
    .sm{{font-size:11px;color:var(--mu);margin-top:4px}}
    .sent{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}}
    .sent span{{font-size:11px;padding:2px 6px;border-radius:10px}}
    .pos{{background:rgba(0,230,118,.1);color:#00e676}}
    .neu{{background:rgba(121,134,163,.1);color:var(--mu)}}
    .neg{{background:rgba(255,77,109,.1);color:#ff4d6d}}
    .up{{color:#00e676}}
    .down{{color:#ff4d6d}}
    .neutral{{color:var(--mu)}}
    /* Main grid */
    .mg{{display:grid;grid-template-columns:1fr 380px;gap:24px}}
    .pn{{background:var(--s);border:1px solid var(--br);border-radius:14px;padding:20px;margin-bottom:20px}}
    .ph{{font-size:15px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:10px}}
    .ct{{background:var(--s2);border:1px solid var(--br);color:var(--mu);font-size:11px;
         padding:2px 8px;border-radius:10px}}
    /* Chart */
    .cw{{position:relative;height:240px;margin-bottom:16px}}
    /* Table */
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    th{{text-align:left;padding:8px 10px;color:var(--mu);font-size:11px;
        text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--br)}}
    td{{padding:9px 10px;border-bottom:1px solid rgba(42,47,61,.5);vertical-align:middle}}
    tr:hover td{{background:rgba(255,255,255,.02)}}
    a{{color:#00c4ff;text-decoration:none}}
    a:hover{{text-decoration:underline}}
    .muted{{color:var(--mu);font-size:12px}}
    .bb{{background:var(--br);border-radius:3px;height:5px;width:120px}}
    .bf{{height:5px;border-radius:3px}}
    .badge{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:8px;margin-right:2px;
            display:inline-block}}
    .positive-b{{background:rgba(0,230,118,.1);color:#00e676;border:1px solid rgba(0,230,118,.2)}}
    .neutral-b{{background:rgba(121,134,163,.1);color:var(--mu);border:1px solid rgba(121,134,163,.2)}}
    .negative-b{{background:rgba(255,77,109,.1);color:#ff4d6d;border:1px solid rgba(255,77,109,.2)}}
    .pos-b{{background:rgba(0,230,118,.1);color:#00e676}}
    .neu-b{{background:rgba(121,134,163,.1);color:var(--mu)}}
    .neg-b{{background:rgba(255,77,109,.1);color:#ff4d6d}}
    .src{{font-size:11px;color:var(--mu);margin-top:12px;text-align:center}}
    footer{{border-top:1px solid var(--br);padding:16px 32px;margin-top:32px;
            display:flex;justify-content:space-between}}
    footer p{{font-size:11px;color:var(--mu)}}
    @media(max-width:900px){{
      .sb{{grid-template-columns:repeat(2,1fr)}}
      .mg{{grid-template-columns:1fr}}
      .wrap{{padding:16px}}
    }}
  </style>
</head>
<body>
<header>
  <div class="logo">
    <div class="li">B</div>
    <div class="lt">
      <h1>Bitget PR Monitor</h1>
      <p>Daily coverage and Share of Voice</p>
    </div>
  </div>
  <div class="hr">
    <div class="lb"><div class="ld"></div>LIVE</div>
    <div class="ts">Updated: {generated}</div>
  </div>
</header>
<div class="wrap">
  <!-- SOV Cards -->
  <div class="sb">{cards_html}</div>
  <div class="mg">
    <div>
      <!-- SOV Chart + Table -->
      <div class="pn">
        <div class="ph">Share of Voice <span class="ct">{total_art} articles scanned</span></div>
        <div class="cw">
          <canvas id="sovChart"></canvas>
        </div>
        <table>
          <thead>
            <tr>
              <th>Exchange</th>
              <th>Mentions</th>
              <th>SOV</th>
              <th>WoW</th>
              <th>Share</th>
              <th>Sentiment</th>
            </tr>
          </thead>
          <tbody>{table_rows}</tbody>
        </table>
        <div class="src">Sources: CoinTelegraph · CoinDesk · Decrypt · Blockworks · The Block · Messari · BeInCrypto · CryptoSlate · Watcher.Guru · CoinGape · Protos · The Defiant · Bitcoinist · AmbCrypto + Google News</div>
      </div>
      <!-- Articles Table -->
      <div class="pn">
        <div class="ph">Recent Coverage <span class="ct">{min(80, len(articles))} articles</span></div>
        <table>
          <thead>
            <tr><th>Exchange</th><th>Headline</th><th>Sentiment</th><th>Date</th></tr>
          </thead>
          <tbody>{art_rows}</tbody>
        </table>
      </div>
    </div>
    <!-- Right sidebar: stats -->
    <div>
      <div class="pn">
        <div class="ph">Summary</div>
        <table>
          <thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Total articles</td><td><b>{total_art}</b></td></tr>
            <tr><td>Total mentions</td><td><b>{total_men}</b></td></tr>
            <tr><td>Exchanges tracked</td><td><b>{len(exchanges)}</b></td></tr>
            <tr><td>Last updated</td><td class="muted">{generated}</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pn">
        <div class="ph">Bitget Sentiment</div>
        <table>
          <thead><tr><th>Type</th><th>Count</th></tr></thead>
          <tbody>
            <tr><td>😊 Positive</td><td><b style="color:#00e676">{exchanges['Bitget']['sentiment']['positive']}</b></td></tr>
            <tr><td>😐 Neutral</td><td><b style="color:var(--mu)">{exchanges['Bitget']['sentiment']['neutral']}</b></td></tr>
            <tr><td>😟 Negative</td><td><b style="color:#ff4d6d">{exchanges['Bitget']['sentiment']['negative']}</b></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
<footer>
  <p>Bitget PR Monitor — auto-generated by GitHub Actions</p>
  <p>Data refreshed daily at 01:00 UTC</p>
</footer>
<script>
  new Chart(document.getElementById("sovChart").getContext("2d"), {{
    type: "bar",
    data: {{
      labels: {json.dumps(ex_order)},
      datasets: [{{
        label: "SOV %",
        data: {json.dumps(sov_values)},
        backgroundColor: {json.dumps(colors)},
        borderRadius: 6
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: "#7986a3" }}, grid: {{ color: "#2a2f3d" }} }},
        y: {{
          ticks: {{ color: "#7986a3", callback: v => v + "%" }},
          grid:  {{ color: "#2a2f3d" }},
          beginAtZero: true
        }}
      }}
    }}
  }});
</script>
</body>
</html>"""
    return html
**─────────────────────────────────────────────**
**MAIN**
**─────────────────────────────────────────────**
def main():
    print("=" * 60)
    print(f"Bitget PR Monitor — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    all_articles = []
    seen_titles  = []
    # Step 1: Google News feeds
    print(f"\n[1/2] Fetching {len(GOOGLE_FEEDS)} Google News feeds...")
    for url, exchange in GOOGLE_FEEDS.items():
        for article in parse_feed(url, assigned_exchange=exchange):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)
    # Step 2: Direct media feeds
    print(f"\n[2/2] Fetching {len(DIRECT_FEEDS)} direct media feeds...")
    for url, exchange in DIRECT_FEEDS.items():
        for article in parse_feed(url, assigned_exchange=exchange):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)
    print(f"\nTotal unique articles: {len(all_articles)}")
    # Step 3: Aggregate
    mention_counts   = defaultdict(int)
    sentiment_counts = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for a in all_articles:
        ex = a["exchange"]
        mention_counts[ex] += 1
        sentiment_counts[ex][a["sentiment"]] += 1
    total_mentions = sum(mention_counts.values())
    # Step 4: SOV
    sov_map = {
        ex: round(mention_counts.get(ex, 0) / total_mentions * 100, 1) if total_mentions > 0 else 0.0
        for ex in EXCHANGES
    }
    # Step 5: WoW delta
    last_week   = load_last_week_sov()
    sov_delta   = {
        ex: round(sov_map[ex] - last_week[ex], 1) if ex in last_week else None
        for ex in EXCHANGES
    }
    save_sov(sov_map)
    # Step 6: Build output
    exchange_data = {
        ex: {
            "mentions":      mention_counts.get(ex, 0),
            "sov":           sov_map[ex],
            "sov_delta_wow": sov_delta.get(ex),
            "sentiment":     dict(sentiment_counts[ex]),
        }
        for ex in EXCHANGES
    }
    output = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "total_articles": len(all_articles),
        "total_mentions": total_mentions,
        "exchanges":      exchange_data,
        "articles":       all_articles,
        "sov_pct":        {ex: sov_map[ex] for ex in EXCHANGES},  # chart.js compat
    }
    # Step 7: Write JSON
    with open("data/dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("✅ data/dashboard_data.json written.")
    # Step 8: Generate index.html
    html = generate_html(output)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ index.html generated.")
    # Step 9: Console summary
    print("\n── Share of Voice ──")
    for ex, d in sorted(exchange_data.items(), key=lambda x: -x[1]["sov"]):
        delta = d["sov_delta_wow"]
        dstr  = f"({'+' if delta and delta >= 0 else ''}{delta}% WoW)" if delta is not None else "(first run)"
        s     = d["sentiment"]
        print(f"  {ex:8s}: {d['mentions']:4d} mentions | SOV {d['sov']:5.1f}% {dstr} | 😊{s['positive']} 😐{s['neutral']} 😟{s['negative']}")
if __name__ == "__main__":
    main()
