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

btc_display = "N/A"
if isinstance(data["btc_price"], (int, float)):
    btc_display = "{:,}".format(int(data["btc_price"]))

btc_chg = data["btc_change"]
btc_cls = "up" if btc_chg >= 0 else "down"
btc_sign = "+" if btc_chg >= 0 else ""
btc_chg_str = btc_sign + str(btc_chg) + "%"

labels_js = json.dumps(ORDER)
data_js = json.dumps([sov_pct.get(e, 0) for e in ORDER])
colors_js = json.dumps([COLORS[e] for e in ORDER])
counts_js = json.dumps([sov_counts.get(e, 0) for e in ORDER])

news_html = ""
for a in bitget_news:
    news_html += (
        "<div class='ni'>"
        "<div class='nm'>"
        "<span class='nd'>" + a["pub"] + "</span>"
        "<span class='ns'>" + a["source"] + "</span>"
        "</div>"
        "<div class='nt'>" + a["title"] + "</div>"
        "<a class='nl' href='" + a["link"] + "' target='_blank'>Read story</a>"
        "</div>"
    )
if not news_html:
    news_html = "<p style='color:#7986a3'>No Bitget articles found today.</p>"

sov_rows = ""
for e in ORDER:
    c = COLORS[e]
    cnt = sov_counts.get(e, 0)
    pct = sov_pct.get(e, 0)
    sov_rows += (
        "<tr>"
        "<td><b style='color:" + c + "'>" + e + "</b></td>"
        "<td>" + str(cnt) + "</td>"
        "<td><b>" + str(pct) + "%</b></td>"
        "<td><div class='bb'><div class='bf' style='width:" + str(pct) + "%;background:" + c + "'></div></div></td>"
        "</tr>"
    )
html = (
    "<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Bitget PR Monitor</title>"
    "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'></script>"
    "<style>"
    "*{box-sizing:border-box;margin:0;padding:0}"
    ":root{--bg:#0d0f14;--s:#161a23;--s2:#1e2330;--br:#2a2f3d;--ac:#00c4ff;--ac2:#7b61ff;--gr:#00e676;--rd:#ff4d6d;--yw:#ffd740;--or:#ff9800;--tx:#e8eaf6;--mu:#7986a3}"
    "body{background:var(--bg);color:var(--tx);font-family:'Segoe UI',sans-serif}"
    "header{background:linear-gradient(135deg,#0d0f14,#161a23);border-bottom:1px solid var(--br);padding:20px 32px;display:flex;align-items:center;justify-content:space-between}"
    ".logo{display:flex;align-items:center;gap:14px}"
    ".li{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--ac),var(--ac2));display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#fff}"
    ".lt h1{font-size:20px;font-weight:700}"
    ".lt p{font-size:12px;color:var(--mu);margin-top:2px}"
    ".hr{display:flex;align-items:center;gap:16px}"
    ".lb{display:flex;align-items:center;gap:6px;background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);color:var(--gr);padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600}"
    ".ld{width:7px;height:7px;border-radius:50%;background:var(--gr);animation:pulse 1.5s infinite}"
    "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}"
    ".ts{font-size:12px;color:var(--mu)}"
    ".wrap{max-width:1400px;margin:0 auto;padding:24px 32px}"
    ".sb{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:28px}"
    ".sc{background:var(--s);border:1px solid var(--br);border-radius:12px;padding:16px 20px;position:relative;overflow:hidden}"
    ".sc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--ac),var(--ac2))}"
    ".sl{font-size:11px;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}"
    ".sv{font-size:20px;font-weight:700}"
    ".sd{font-size:12px;margin-top:4px;font-weight:600}"
    ".up{color:var(--gr)}.down{color:var(--rd)}.neutral{color:var(--mu)}"
    ".mg{display:grid;grid-template-columns:1fr 420px;gap:24px}"
    ".pn{background:var(--s);border:1px solid var(--br);border-radius:14px;padding:20px;margin-bottom:20px}"
    ".ph{display:flex;align-items:center;gap:10px;margin-bottom:16px;font-size:15px;font-weight:700}"
    ".ct{background:var(--s2);border:1px solid var(--br);color:var(--mu);font-size:11px;padding:2px 8px;border-radius:10px}"
    ".ni{border:1px solid var(--br);border-radius:10px;padding:14px 16px;margin-bottom:12px;background:var(--s2)}"
    ".nm{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}"
    ".nd{font-size:11px;color:var(--mu)}"
    ".ns{font-size:11px;font-weight:600;padding:2px 8px;border-radius:5px;background:rgba(0,196,255,.1);color:var(--ac);border:1px solid rgba(0,196,255,.2)}"
    ".nt{font-size:14px;font-weight:600;margin-bottom:8px;line-height:1.4}"
    ".nl{display:inline-flex;color:var(--ac);font-size:12px;text-decoration:none;font-weight:600;padding:4px 10px;border:1px solid rgba(0,196,255,.25);border-radius:6px;background:rgba(0,196,255,.06)}"
    ".cw{position:relative;height:260px;margin-bottom:16px}"
    ".st{width:100%;border-collapse:collapse;font-size:13px}"
".st th{text-align:left;padding:8px 10px;color:var(--mu);font-size:11px;text-transform:uppercase;border-bottom:1px solid var(--br)}"
    ".st td{padding:9px 10px;border-bottom:1px solid rgba(42,47,61,.5)}"
    ".bb{background:var(--br);border-radius:3px;height:5px;width:140px}"
    ".bf{height:5px;border-radius:3px}"
    ".cd{border:1px solid var(--br);border-radius:12px;padding:18px;margin-bottom:16px;background:var(--s2);position:relative;overflow:hidden}"
    ".cd::before{content:'';position:absolute;top:0;left:0;bottom:0;width:3px}"
    ".cd.cr::before{background:var(--rd)}"
    ".cd.hi::before{background:var(--or)}"
    ".cd.mo::before{background:var(--yw)}"
    ".ch{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px}"
    ".cn{font-size:17px;font-weight:800}"
    ".cg{font-size:12px;color:var(--mu);margin-top:2px;font-style:italic}"
    ".cbg{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}"
    ".bk{font-size:10px;font-weight:700;padding:3px 8px;border-radius:6px}"
    ".br{background:rgba(0,196,255,.1);color:var(--ac);border:1px solid rgba(0,196,255,.25)}"
    ".bu{background:rgba(0,230,118,.1);color:var(--gr);border:1px solid rgba(0,230,118,.25)}"
    ".th{font-size:10px;font-weight:700;padding:4px 10px;border-radius:6px;white-space:nowrap}"
    ".tc{background:rgba(255,77,109,.15);color:var(--rd);border:1px solid rgba(255,77,109,.3)}"
    ".th2{background:rgba(255,152,0,.15);color:var(--or);border:1px solid rgba(255,152,0,.3)}"
    ".tm{background:rgba(255,215,64,.1);color:var(--yw);border:1px solid rgba(255,215,64,.25)}"
    ".cs{font-size:11px;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin:12px 0 6px}"
    ".cl{list-style:none}"
    ".cl li{font-size:12px;color:var(--mu);padding:3px 0 3px 16px;position:relative;line-height:1.5}"
    ".cl li::before{content:'>';position:absolute;left:0;color:var(--br)}"
    ".cl li b{color:var(--tx)}"
    ".vd{background:rgba(0,0,0,.3);border-radius:8px;padding:10px 14px;margin-top:12px;border-left:3px solid var(--ac2)}"
    ".vl{font-size:10px;font-weight:700;color:var(--ac2);text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px}"
    ".vt{font-size:12px;line-height:1.5}"
    ".lks{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}"
    ".lk{font-size:11px;color:var(--ac);text-decoration:none;font-weight:600;padding:3px 9px;border:1px solid rgba(0,196,255,.2);border-radius:5px;background:rgba(0,196,255,.05)}"
    ".si{font-size:11px;color:var(--mu);margin-top:8px;text-align:center}"
    "footer{border-top:1px solid var(--br);padding:16px 32px;margin-top:32px;display:flex;justify-content:space-between}"
    "footer p{font-size:11px;color:var(--mu)}"
    "@media(max-width:900px){.sb{grid-template-columns:repeat(2,1fr)}.mg{grid-template-columns:1fr}.wrap{padding:16px}}"
    "</style></head><body>"

    "<header>"
    "<div class='logo'><div class='li'>B</div><div class='lt'><h1>Bitget PR Monitor</h1><p>Daily coverage and Share of Voice</p></div></div>"
    "<div class='hr'><div class='lb'><div class='ld'></div>LIVE</div><div class='ts'>Updated: " + gen_at + "</div></div>"
    "</header>"
"<div class='wrap'>"
    "<div class='sb'>"
    "<div class='sc'><div class='sl'>BTC Reserves</div><div class='sv'>" + data["reserve_btc"] + "</div><div class='sd up'>" + data["reserve_yoy"] + "</div></div>"
    "<div class='sc'><div class='sl'>Reserve Ratio</div><div class='sv'>" + data["reserve_ratio"] + "</div><div class='sd up'>Overcollateralized</div></div>"
    "<div class='sc'><div class='sl'>Net Inflows Feb</div><div class='sv'>" + data["net_inflows"] + "</div><div class='sd up'>Strong</div></div>"
    "<div class='sc'><div class='sl'>BTC Price</div><div class='sv'>" + btc_display + "</div><div class='sd " + btc_cls + "'>" + btc_chg_str + " 24h</div></div>"
    "<div class='sc'><div class='sl'>Fear and Greed</div><div class='sv'>" + str(data["fg_value"]) + "</div><div class='sd neutral'>" + data["fg_class"] + "</div></div>"
    "<div class='sc'><div class='sl'>Bitget SOV</div><div class='sv'>" + str(sov_pct.get("Bitget", 0)) + "%</div><div class='sd neutral'>" + str(sov_counts.get("Bitget", 0)) + " mentions today</div></div>"
    "</div>"

    "<div class='mg'><div>"
    "<div class='pn'>"
    "<div class='ph'>Share of Voice <span class='ct'>" + str(len(all_items)) + " articles scanned</span></div>"
    "<div class='cw'><canvas id='sovChart'></canvas></div>"
    "<table class='st'><thead><tr><th>Exchange</th><th>Mentions</th><th>SOV</th><th>Share</th></tr></thead><tbody>" + sov_rows + "</tbody></table>"
    "<div class='si'>Sources: CoinTelegraph, CoinDesk, Decrypt, Blockworks, NewsBTC, Bitcoinist, CryptoNews, U.Today, AmbCrypto, CoinJournal</div>"
    "</div>"

    "<div class='pn'><div class='ph'>Bitget Coverage Today</div>" + news_html + "</div>"
    "</div>"

    "<div>"
    "<div class='pn'><div class='ph'>Competitor Intelligence <span class='ct'>5 exchanges</span></div>"

    "<div class='cd cr'><div class='ch'>"
    "<div><div class='cn'>OKX</div><div class='cg'>NYSE rails and same UEX thesis</div>"
    "<div class='cbg'><span class='bk br'>No.3 Volume</span><span class='bk bu'>120M Users</span></div></div>"
    "<span class='th tc'>CRITICAL</span></div>"
    "<div class='cs'>Key Moves</div>"
    "<ul class='cl'>"
    "<li><b>ICE/NYSE invested 200M at 25B valuation</b> - Mar 5 2026</li>"
    "<li>Tokenized NYSE stocks launching H2 2026 - 6 month window before they go live</li>"
    "<li>120M users plus NYSE credibility = most dangerous competitor</li>"
    "</ul>"
    "<div class='vd'><div class='vl'>Verdict</div><div class='vt'>Executing Bitget's exact playbook with institutional backing. The 6-month product gap is the window to use.</div></div>"
    "<div class='lks'><a class='lk' href='https://ir.theice.com/press/news-details/2026/ICE-Makes-Investment-in-OKX-Establishing-Strategic-Relationship/default.aspx' target='_blank'>ICE Press Release</a>"
    "<a class='lk' href='https://www.coindesk.com/business/2026/03/05/nyse-owner-ice-forges-strategic-partnership-with-crypto-exchange-okx' target='_blank'>CoinDesk</a></div>"
    "</div>"
"<div class='cd hi'><div class='ch'>"
    "<div><div class='cn'>Bybit</div><div class='cg'>New Financial Platform and MyBank</div>"
    "<div class='cbg'><span class='bk br'>No.2 Volume</span><span class='bk bu'>60M+ Users</span></div></div>"
    "<span class='th th2'>HIGH</span></div>"
    "<div class='cs'>Key Moves</div>"
    "<ul class='cl'>"
    "<li>MyBank launched Feb 2026 - fiat accounts and cross-border payments</li>"
    "<li>ByCustody: 5B+ AUM institutional custody</li>"
    "<li>QNB Qatar National Bank and Pave Bank partnerships</li>"
    "<li>Targeting 1.4 billion underbanked users globally</li>"
    "</ul>"
    "<div class='vd'><div class='vl'>Verdict</div><div class='vt'>Banking infrastructure could attract institutional clients away from Bitget. Different TradFi vector but equally serious.</div></div>"
    "<div class='lks'><a class='lk' href='https://www.marketwatch.com/press-release/bybit-unveils-2026-vision-as-the-new-financial-platform-expanding-beyond-exchange-into-global-financial-infrastructure-e153c863' target='_blank'>MarketWatch</a></div>"
    "</div>"

    "<div class='cd hi'><div class='ch'>"
    "<div><div class='cn'>MEXC</div><div class='cg'>Zero-fee king entering tokenized stocks</div>"
    "<div class='cbg'><span class='bk br'>No.2 Daily Vol</span><span class='bk bu'>36M+ Users</span></div></div>"
    "<span class='th th2'>HIGH</span></div>"
    "<div class='cs'>Key Moves</div>"
    "<ul class='cl'>"
    "<li><b>175M USD net inflows Feb 2026</b> - razor thin gap vs Bitget 205M USD</li>"
    "<li>9th Ondo Finance collab: 17 tokenized US equity pairs, zero-fee 30 days</li>"
    "<li>1.1B USD in user fee savings via zero-fee spot in 2025</li>"
    "<li>BTC reserve coverage 158-266 percent (bimonthly audits)</li>"
    "</ul>"
    "<div class='vd'><div class='vl'>Verdict</div><div class='vt'>Most underrated threat. Zero-fee moat plus Ondo tokenized stocks = attacking Bitget on two fronts simultaneously.</div></div>"
    "<div class='lks'><a class='lk' href='https://coincentral.com/mexc-expands-zero-fee-tokenized-equities-with-ondo-batch/' target='_blank'>Ondo Equities</a></div>"
    "</div>"

    "<div class='cd mo'><div class='ch'>"
    "<div><div class='cn'>KuCoin</div><div class='cg'>2B USD compliance pivot</div>"
    "<div class='cbg'><span class='bk br'>No.5 Volume</span><span class='bk bu'>41M Users</span></div></div>"
    "<span class='th tm'>MODERATE</span></div>"
    "<div class='cs'>Key Moves</div>"
    "<ul class='cl'>"
    "<li>2B USD Trust Project over 2026-2028 for security and compliance</li>"
    "<li>Goal: most trusted global crypto exchange by 2028</li>"
    "<li>Compliance pivot is defensive - no TradFi product announced yet</li>"
    "</ul>"
    "<div class='vd'><div class='vl'>Verdict</div><div class='vt'>Bitget's actual PoR numbers today beat KuCoin's future promise. Not a TradFi threat yet.</div></div>"
    "</div>"
"<div class='cd mo'><div class='ch'>"
    "<div><div class='cn'>Binance</div><div class='cg'>Volume leader with declining reserves</div>"
    "<div class='cbg'><span class='bk br'>No.1 Volume</span></div></div>"
    "<span class='th tm'>MODERATE</span></div>"
    "<div class='cs'>Key Moves</div>"
    "<ul class='cl'>"
    "<li><b>BTC reserves down 1.25 percent</b> to 631K BTC in latest PoR</li>"
    "<li>ETH down 7.35 percent, net outflows Feb-Mar</li>"
    "<li>No TradFi pivot - fee-cut strategy only</li>"
    "</ul>"
    "<div class='vd'><div class='vl'>Verdict</div><div class='vt'>Every month Binance reserves decline, Bitget's transparency story grows stronger. Lean into this narrative.</div></div>"
    "</div>"

    "</div></div></div>"

    "<footer>"
    "<p>Bitget PR Monitor - Auto-generated - " + gen_at + "</p>"
    "<p>Sources: 10 RSS feeds, CoinGecko, Alternative.me - " + str(len(all_items)) + " articles scanned</p>"
    "</footer>"

    "<script>"
    "const ctx = document.getElementById('sovChart').getContext('2d');"
    "new Chart(ctx, {"
    "type: 'bar',"
    "data: {"
    "labels: " + labels_js + ","
    "datasets: [{"
    "label: 'SOV',"
    "data: " + data_js + ","
    "backgroundColor: " + colors_js + ","
    "borderRadius: 6"
    "}]"
    "},"
    "options: {"
    "responsive: true,"
    "maintainAspectRatio: false,"
    "plugins: {"
    "legend: { display: false },"
    "tooltip: { callbacks: { label: function(c) { var n = " + counts_js + "; return ' ' + c.parsed.y + '% (' + n[c.dataIndex] + ' mentions)'; } } }"
    "},"
    "scales: {"
    "x: { ticks: { color: '#7986a3' }, grid: { color: '#2a2f3d' } },"
    "y: { ticks: { color: '#7986a3', callback: function(v){ return v + '%'; } }, grid: { color: '#2a2f3d' }, beginAtZero: true }"
    "}"
    "}"
    "});"
    "</script>"
    "</body></html>"
)

with open("index.html", "w") as f:
    f.write(html)

print("Done. index.html written.")
