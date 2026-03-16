import json
import time
import os
import re
import difflib
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

os.makedirs("data", exist_ok=True)

EXCHANGES = {
    "Bitget":  ["bitget", "bgb token", "bitget wallet", "bitget exchange", "gracy bitget"],
    "Binance": ["binance", "bnb token", "binance.com", "cz binance", "richard binance"],
    "OKX":     ["okx", "okx exchange", "okb token", "okx crypto", "okx star"],
    "Bybit":   ["bybit", "bybit exchange", "bybit crypto", "bit token"],
    "MEXC":    ["mexc", "mexc exchange", "mexc global", "mx token"],
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

POSITIVE_KEYWORDS = [
    "partnership", "launch", "record", "growth", "wins", "expands", "raises",
    "integrates", "bullish", "milestone", "surpasses", "achieves", "leading",
    "innovation", "approved", "listed", "gains", "tops", "rally", "best",
    "secured", "trusted", "compliant", "new feature", "upgrade", "award",
    "investment", "funding", "expansion",
]

NEGATIVE_KEYWORDS = [
    "hack", "scam", "fraud", "down", "outage", "crash", "lawsuit", "fined",
    "breach", "exploit", "stolen", "arrested", "investigation", "ban",
    "suspended", "halted", "loss", "penalty", "delisted", "warning", "risk",
    "bearish", "collapse", "scandal", "charges", "seizure", "blocked", "attack",
]

def score_sentiment(text):
    t = text.lower()
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in t)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in t)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    else:
        return "neutral"

GOOGLE_FEEDS = {
    "https://news.google.com/rss/search?q=bitget+exchange&hl=en-US&gl=US&ceid=US:en":         "Bitget",
    "https://news.google.com/rss/search?q=bitget+crypto+exchange&hl=en-US&gl=US&ceid=US:en":  "Bitget",
    "https://news.google.com/rss/search?q=bitget+tokenized+stocks&hl=en-US&gl=US&ceid=US:en": "Bitget",
    "https://news.google.com/rss/search?q=binance+exchange&hl=en-US&gl=US&ceid=US:en":        "Binance",
    "https://news.google.com/rss/search?q=BNB+token+binance&hl=en-US&gl=US&ceid=US:en":       "Binance",
    "https://news.google.com/rss/search?q=binance+US+regulation&hl=en-US&gl=US&ceid=US:en":   "Binance",
    "https://news.google.com/rss/search?q=OKX+crypto+exchange&hl=en-US&gl=US&ceid=US:en":     "OKX",
    "https://news.google.com/rss/search?q=OKX+institutional&hl=en-US&gl=US&ceid=US:en":       "OKX",
    "https://news.google.com/rss/search?q=Bybit+crypto+exchange&hl=en-US&gl=US&ceid=US:en":   "Bybit",
    "https://news.google.com/rss/search?q=Bybit+custody+AUM&hl=en-US&gl=US&ceid=US:en":       "Bybit",
    "https://news.google.com/rss/search?q=MEXC+crypto+exchange&hl=en-US&gl=US&ceid=US:en":    "MEXC",
    "https://news.google.com/rss/search?q=MEXC+zero+fee&hl=en-US&gl=US&ceid=US:en":           "MEXC",
    "https://news.google.com/rss/search?q=KuCoin+crypto+exchange&hl=en-US&gl=US&ceid=US:en":  "KuCoin",
    "https://news.google.com/rss/search?q=KuCoin+KCS+token&hl=en-US&gl=US&ceid=US:en":        "KuCoin",
}

DIRECT_FEEDS = {
    "https://www.theblock.co/rss.xml":                 "all",
    "https://messari.io/rss":                           "all",
    "https://cointelegraph.com/rss":                    "all",
    "https://www.coindesk.com/arc/outboundfeeds/rss/": "all",
    "https://decrypt.co/feed":                          "all",
    "https://blockworks.co/feed":                       "all",
    "https://beincrypto.com/feed/":                     "all",
    "https://cryptoslate.com/feed/":                    "all",
    "https://watcher.guru/news/feed":                   "all",
    "https://coingape.com/feed/":                       "all",
    "https://crypto.news/feed/":                        "all",
    "https://protos.com/feed/":                         "all",
    "https://thedefiant.io/api/feed":                   "all",
    "https://bitcoinist.com/feed/":                     "all",
    "https://ambcrypto.com/feed/":                      "all",
}

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

def fetch_with_retry(url, max_retries=3, base_delay=1.0, timeout=15, headers=None):
    default_headers = {"User-Agent": "Mozilla/5.0 (compatible; PRMonitor/2.0)"}
    if headers:
        default_headers.update(headers)
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=default_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            wait = base_delay * (2 ** attempt)
            print("  [WARN] Attempt {}/{} failed: {} -- {}".format(
                attempt + 1, max_retries, url[:60], e))
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                print("  [ERROR] Giving up on: {}".format(url[:60]))
    return None

def parse_feed(url, assigned_exchange=None):
    print("  Fetching: {}...".format(url[:80]))
    data = fetch_with_retry(url)
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
            title_el = item.find("title")
            link_el  = item.find("link")
            pub_el   = item.find("pubDate")
            desc_el  = item.find("description")
            title = (title_el.text or "").strip() if title_el is not None else ""
            link  = (link_el.text  or "").strip() if link_el  is not None else ""
            pub   = (pub_el.text   or "").strip() if pub_el   is not None else ""
            desc  = (desc_el.text  or "").strip() if desc_el  is not None else ""
            if not title:
                continue
            full_text = "{} {}".format(title, desc).lower()
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
                    "source":    "rss",
                })
    except ET.ParseError as e:
        print("  [ERROR] XML parse error: {} -- {}".format(url[:60], e))
    return articles

def fetch_meltwater(api_key, saved_search_ids, exchange_map, lookback_days=7):
    if not api_key:
        print("  [SKIP] No Meltwater API key set.")
        return []
    base_url  = "https://api.meltwater.com"
    end_dt    = datetime.now(timezone.utc)
    start_dt  = end_dt - timedelta(days=lookback_days)
    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_iso   = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    articles = []
    auth_headers = {
        "apikey": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    for search_id, exchange in saved_search_ids.items():
        print("  [Meltwater] Fetching search {} for {}...".format(search_id, exchange))
        try:
            url = base_url + "/v3/search/" + search_id
            payload = json.dumps({
                "start":     start_iso,
                "end":       end_iso,
                "page":      1,
                "page_size": 50,
                "sort_by":   "date",
                "sort_order":"desc",
                "tz":        "UTC",
                "template":  {"name": "api.json"},
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers=auth_headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
            data = json.loads(raw)
            print("  [DEBUG] Meltwater keys: {}".format(list(data.keys())))
            mentions = data.get("result", {}).get("documents", [])
            for m in mentions:
                title   = m.get("content", "")[:120]
                link    = m.get("url", "")
                pub     = m.get("published_date", "")
                enrich  = m.get("enrichments", {})
                mw_sent = str(enrich.get("sentiment", {}).get("label", "") if isinstance(enrich.get("sentiment"), dict) else enrich.get("sentiment", "")).lower()
                if mw_sent in ("positive", "negative", "neutral"):
                    sentiment = mw_sent
                else:
                    sentiment = score_sentiment(title)
                if not title:
                    continue
                articles.append({
                    "exchange":  exchange,
                    "title":     title,
                    "link":      link,
                    "pub_date":  pub[:16] if pub else "",
                    "sentiment": sentiment,
                    "source":    "meltwater",
                })
        except Exception as e:
            print("  [ERROR] Meltwater fetch failed for {}: {}".format(exchange, e))
        time.sleep(0.3)
    print("  [Meltwater] {} articles fetched.".format(len(articles)))
    return articles

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

def get_top_articles(articles, exchange, n=3):
    hits = [a for a in articles if a["exchange"] == exchange]
    return hits[:n]

def build_competitor_card(name, subtitle, badges, threat_label, threat_class, articles, verdict, links, card_class):
    badge_html = ""
    for label, cls in badges:
        badge_html += "<span class='bk " + cls + "'>" + label + "</span>"

    link_html = ""
    for text, url in links:
        link_html += "<a class='lk' href='" + url + "' target='_blank'>" + text + "</a>"
    if link_html:
        link_html = "<div class='lks'>" + link_html + "</div>"

    news_html = ""
    if articles:
        news_html += "<div class='cs'>This Week</div><ul class='cl'>"
        for a in articles:
            pub = a["pub_date"][:10] if a["pub_date"] else ""
            sent = a["sentiment"]
            sent_color = "#00e676" if sent == "positive" else "#ff4d6d" if sent == "negative" else "#7986a3"
            src_badge = "<span style='font-size:9px;color:#7b61ff;margin-left:4px'>[MW]</span>" if a.get("source") == "meltwater" else ""
            news_html += (
                "<li><span style='color:" + sent_color + ";font-size:10px;margin-right:4px'>*</span>"
                "<a href='" + a["link"] + "' target='_blank' style='color:var(--tx)'>"
                + a["title"][:90] + ("..." if len(a["title"]) > 90 else "") +
                "</a>" + src_badge +
                "<span class='muted'> - " + pub + "</span></li>"
            )
        news_html += "</ul>"
    else:
        news_html = "<div class='cs'>This Week</div><p style='font-size:12px;color:var(--mu);padding:4px 0'>No articles found this run</p>"

    return (
        "<div class='cd " + card_class + "'>"
        "<div class='ch'><div>"
        "<div class='cn'>" + name + "</div>"
        "<div class='cg'>" + subtitle + "</div>"
        "<div class='cbg'>" + badge_html + "</div>"
        "</div><span class='th-badge " + threat_class + "'>" + threat_label + "</span></div>"
        + news_html +
        "<div class='vd'><div class='vl'>Verdict</div>"
        "<div class='vt'>" + verdict + "</div></div>"
        + link_html +
        "</div>"
    )

def generate_html(output):
    exchanges    = output["exchanges"]
    articles     = output["articles"]
    generated    = output["generated_at"][:16].replace("T", " ") + " UTC"
    total_art    = output["total_articles"]
    total_men    = output["total_mentions"]
    top_articles = output.get("top_articles", {})
    ex_order     = list(EXCHANGES.keys())
    colors       = [EXCHANGE_COLORS[e] for e in ex_order]
    sov_values   = [exchanges[e]["sov"] for e in ex_order]

    cards_html = ""
    for ex in sorted(exchanges, key=lambda x: -exchanges[x]["sov"]):
        d     = exchanges[ex]
        delta = d["sov_delta_wow"]
        color = EXCHANGE_COLORS[ex]
        if delta is None:
            delta_html = "<span class='sd neutral'>first run</span>"
        elif delta >= 0:
            delta_html = "<span class='sd up'>+" + str(delta) + "% WoW</span>"
        else:
            delta_html = "<span class='sd down'>" + str(delta) + "% WoW</span>"
        s = d["sentiment"]
        cards_html += (
            "<div class='sc' style='--accent:" + color + "'>"
            "<div class='sl ex-link' data-ex='" + ex.lower() + "' style='cursor:pointer;text-decoration:underline dotted'>" + ex + "</div>"
            "<div class='sv' style='color:" + color + "'>" + str(d["sov"]) + "%</div>"
            + delta_html +
            "<div class='sm'>" + str(d["mentions"]) + " mentions</div>"
            "<div class='sent'>"
            "<span class='pos'>+" + str(s["positive"]) + "</span>"
            "<span class='neu'>~" + str(s["neutral"]) + "</span>"
            "<span class='neg'>-" + str(s["negative"]) + "</span>"
            "</div></div>"
        )

    table_rows = ""
    for ex in sorted(exchanges, key=lambda x: -exchanges[x]["sov"]):
        d     = exchanges[ex]
        color = EXCHANGE_COLORS[ex]
        delta = d["sov_delta_wow"]
        if delta is None:
            delta_str = "--"
        elif delta >= 0:
            delta_str = "<span class='up'>+" + str(delta) + "%</span>"
        else:
            delta_str = "<span class='down'>" + str(delta) + "%</span>"
        s = d["sentiment"]
        table_rows += (
            "<tr>"
            "<td><b style='color:" + color + "'>"
            "<span class='ex-link' data-ex='" + ex.lower() + "' style='cursor:pointer;text-decoration:underline dotted'>" + ex + "</span>"
            "</b></td>"
            "<td>" + str(d["mentions"]) + "</td>"
            "<td><b>" + str(d["sov"]) + "%</b></td>"
            "<td>" + delta_str + "</td>"
            "<td><div class='bb'><div class='bf' style='width:" + str(d["sov"]) + "%;background:" + color + "'></div></div></td>"
            "<td>"
            "<span class='badge pos-b'>" + str(s["positive"]) + "</span>"
            "<span class='badge neu-b'>" + str(s["neutral"]) + "</span>"
            "<span class='badge neg-b'>" + str(s["negative"]) + "</span>"
            "</td></tr>"
        )

    art_rows = ""
    for a in articles[:80]:
        color = EXCHANGE_COLORS.get(a["exchange"], "#aaa")
        pub   = a["pub_date"][:16] if a["pub_date"] else "--"
        sent  = a["sentiment"]
        src_tag = " [MW]" if a.get("source") == "meltwater" else ""
        art_rows += (
            "<tr><td><b style='color:" + color + "'>" + a["exchange"] + "</b></td>"
            "<td><a href='" + a["link"] + "' target='_blank'>" + a["title"] + src_tag + "</a></td>"
            "<td><span class='badge " + sent + "-b'>" + sent + "</span></td>"
            "<td class='muted'>" + pub + "</td></tr>"
        )

    bg = exchanges.get("Bitget", {}).get("sentiment", {"positive": 0, "neutral": 0, "negative": 0})
    mw_count = sum(1 for a in articles if a.get("source") == "meltwater")
    rss_count = total_art - mw_count

    css = (
        "*{box-sizing:border-box;margin:0;padding:0}"
        ":root{--bg:#0d0f14;--s:#161a23;--s2:#1e2330;--br:#2a2f3d;--tx:#e8eaf6;--mu:#7986a3}"
        "body{background:var(--bg);color:var(--tx);font-family:'Segoe UI',sans-serif}"
        "header{background:linear-gradient(135deg,#0d0f14,#161a23);border-bottom:1px solid var(--br);padding:20px 32px;display:flex;align-items:center;justify-content:space-between}"
        ".logo{display:flex;align-items:center;gap:14px}"
        ".li{width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,#00c4ff,#7b61ff);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#fff}"
        ".lt h1{font-size:20px;font-weight:700}"
        ".lt p{font-size:12px;color:var(--mu);margin-top:2px}"
        ".hr{display:flex;align-items:center;gap:16px}"
        ".lb{display:flex;align-items:center;gap:6px;background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);color:#00e676;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600}"
        ".ld{width:7px;height:7px;border-radius:50%;background:#00e676;animation:pulse 1.5s infinite}"
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}"
        ".ts{font-size:12px;color:var(--mu)}"
        ".wrap{max-width:1400px;margin:0 auto;padding:24px 32px}"
        ".sb{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:28px}"
        ".sc{background:var(--s);border:1px solid var(--br);border-radius:12px;padding:16px 20px;position:relative;overflow:hidden}"
        ".sc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent,#00c4ff)}"
        ".sl{font-size:11px;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}"
        ".sv{font-size:28px;font-weight:700}"
        ".sd{font-size:12px;margin-top:4px;font-weight:600}"
        ".sm{font-size:11px;color:var(--mu);margin-top:4px}"
        ".sent{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;font-size:11px}"
        ".pos{background:rgba(0,230,118,.1);color:#00e676;padding:2px 6px;border-radius:10px}"
        ".neu{background:rgba(121,134,163,.1);color:var(--mu);padding:2px 6px;border-radius:10px}"
        ".neg{background:rgba(255,77,109,.1);color:#ff4d6d;padding:2px 6px;border-radius:10px}"
        ".up{color:#00e676}.down{color:#ff4d6d}.neutral{color:var(--mu)}"
        ".mg{display:grid;grid-template-columns:1fr 360px;gap:24px}"

".pn{background:var(--s);border:1px solid var(--br);border-radius:14px;padding:20px;margin-bottom:20px}"
        ".ph{font-size:15px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:10px}"
        ".ct{background:var(--s2);border:1px solid var(--br);color:var(--mu);font-size:11px;padding:2px 8px;border-radius:10px}"
        ".cw{position:relative;height:240px;margin-bottom:16px}"
        "table{width:100%;border-collapse:collapse;font-size:13px}"
        "th{text-align:left;padding:8px 10px;color:var(--mu);font-size:11px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--br)}"
        "td{padding:9px 10px;border-bottom:1px solid rgba(42,47,61,.5);vertical-align:middle}"
        "tr:hover td{background:rgba(255,255,255,.02)}"
        "a{color:#00c4ff;text-decoration:none}a:hover{text-decoration:underline}"
        ".muted{color:var(--mu);font-size:12px}"
        ".bb{background:var(--br);border-radius:3px;height:5px;width:120px}"
        ".bf{height:5px;border-radius:3px}"
        ".badge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:8px;margin-right:2px;display:inline-block}"
        ".positive-b{background:rgba(0,230,118,.1);color:#00e676}"
        ".neutral-b{background:rgba(121,134,163,.1);color:var(--mu)}"
        ".negative-b{background:rgba(255,77,109,.1);color:#ff4d6d}"
        ".pos-b{background:rgba(0,230,118,.1);color:#00e676}"
        ".neu-b{background:rgba(121,134,163,.1);color:var(--mu)}"
        ".neg-b{background:rgba(255,77,109,.1);color:#ff4d6d}"
        ".src{font-size:11px;color:var(--mu);margin-top:12px;text-align:center}"
        ".cd{border:1px solid var(--br);border-radius:12px;padding:18px;margin-bottom:16px;background:var(--s2);position:relative;overflow:hidden}"
        ".cd::before{content:'';position:absolute;top:0;left:0;bottom:0;width:3px}"
        ".cd.cr::before{background:#ff4d6d}"
        ".cd.hi::before{background:#ff9800}"
        ".cd.mo::before{background:#ffd740}"
        ".ch{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px}"
        ".cn{font-size:17px;font-weight:800}"
        ".cg{font-size:12px;color:var(--mu);margin-top:2px;font-style:italic}"
        ".cbg{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}"
        ".bk{font-size:10px;font-weight:700;padding:3px 8px;border-radius:6px}"
        ".bkr{background:rgba(0,196,255,.1);color:#00c4ff;border:1px solid rgba(0,196,255,.25)}"

".bku{background:rgba(0,230,118,.1);color:#00e676;border:1px solid rgba(0,230,118,.25)}"
        ".th-badge{font-size:10px;font-weight:700;padding:4px 10px;border-radius:6px;white-space:nowrap}"
        ".tc{background:rgba(255,77,109,.15);color:#ff4d6d;border:1px solid rgba(255,77,109,.3)}"
        ".th2{background:rgba(255,152,0,.15);color:#ff9800;border:1px solid rgba(255,152,0,.3)}"
        ".tm{background:rgba(255,215,64,.1);color:#ffd740;border:1px solid rgba(255,215,64,.25)}"
        ".cs{font-size:11px;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin:12px 0 6px}"
        ".cl{list-style:none}"
        ".cl li{font-size:12px;color:var(--mu);padding:3px 0 3px 16px;position:relative;line-height:1.5}"
        ".cl li::before{content:'';position:absolute;left:0}"
        ".cl li b{color:var(--tx)}"
        ".vd{background:rgba(0,0,0,.3);border-radius:8px;padding:10px 14px;margin-top:12px;border-left:3px solid #7b61ff}"
        ".vl{font-size:10px;font-weight:700;color:#7b61ff;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px}"
        ".vt{font-size:12px;line-height:1.5}"
        ".lks{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}"
        ".lk{font-size:11px;color:#00c4ff;text-decoration:none;font-weight:600;padding:3px 9px;border:1px solid rgba(0,196,255,.2);border-radius:5px;background:rgba(0,196,255,.05)}"
        ".modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;align-items:center;justify-content:center}"
        ".modal-overlay.open{display:flex}"
        ".modal{background:var(--s);border:1px solid var(--br);border-radius:16px;width:90%;max-width:860px;max-height:80vh;overflow:hidden;display:flex;flex-direction:column}"
        ".modal-head{padding:20px 24px;border-bottom:1px solid var(--br);display:flex;align-items:center;justify-content:space-between}"
        ".modal-head h2{font-size:16px;font-weight:700}"
        ".modal-close{background:none;border:none;color:var(--mu);font-size:22px;cursor:pointer;line-height:1}"
        ".modal-body{overflow-y:auto;padding:20px 24px}"
        ".week-block{margin-bottom:24px}"
        ".week-label{font-size:11px;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid var(--br)}"
        ".news-item{padding:8px 0;border-bottom:1px solid rgba(42,47,61,.4)}"
        ".news-item:last-child{border-bottom:none}"

".news-title{font-size:13px;line-height:1.5}"
        ".news-meta{font-size:11px;color:var(--mu);margin-top:2px}"
        "footer{border-top:1px solid var(--br);padding:16px 32px;margin-top:32px;display:flex;justify-content:space-between}"
        "footer p{font-size:11px;color:var(--mu)}"
        "@media(max-width:900px){.sb{grid-template-columns:repeat(2,1fr)}.mg{grid-template-columns:1fr}.wrap{padding:16px}}"
    )

    page = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Bitget PR Monitor</title>"
        "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'></script>"
        "<style>" + css + "</style>"
        "</head><body>"
        "<header>"
        "<div class='logo'><div class='li'>B</div>"
        "<div class='lt'><h1>Bitget PR Monitor</h1><p>Daily coverage and Share of Voice</p></div></div>"
        "<div class='hr'><div class='lb'><div class='ld'></div>LIVE</div>"
        "<div class='ts'>Updated: " + generated + "</div></div>"
        "</header>"
        "<div class='wrap'>"
        "<div class='sb'>" + cards_html + "</div>"
        "<div class='mg'><div>"
        "<div class='pn'>"
        "<div class='ph'>Share of Voice <span class='ct'>" + str(total_art) + " articles</span></div>"
        "<div class='cw'><canvas id='sovChart'></canvas></div>"
        "<table><thead><tr><th>Exchange</th><th>Mentions</th><th>SOV</th><th>WoW</th><th>Share</th><th>Sentiment</th></tr></thead>"
        "<tbody>" + table_rows + "</tbody></table>"
        "<div class='src'>CoinTelegraph - CoinDesk - Decrypt - Blockworks - The Block - Messari - BeInCrypto - CryptoSlate - Watcher.Guru - Protos - The Defiant - Bitcoinist - AmbCrypto + Google News"
        + (" + Meltwater [" + str(mw_count) + " articles]" if mw_count > 0 else "") +
        "</div>"
        "</div>"
        "<div class='pn'>"
        "<div class='ph'>Recent Coverage <span class='ct'>" + str(min(80, len(articles))) + " articles</span></div>"
        "<table><thead><tr><th>Exchange</th><th>Headline</th><th>Sentiment</th><th>Date</th></tr></thead>"
        "<tbody>" + art_rows + "</tbody></table>"
        "</div></div>"
        "<div>"
        "<div class='pn'><div class='ph'>Summary</div>"
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>"
        "<tr><td>Total articles</td><td>" + str(total_art) + "</td></tr>"
        "<tr><td>RSS articles</td><td>" + str(rss_count) + "</td></tr>"
        "<tr><td>Meltwater articles</td><td>" + str(mw_count) + "</td></tr>"
        "<tr><td>Total mentions</td><td>" + str(total_men) + "</td></tr>"
        "<tr><td>Exchanges tracked</td><td>" + str(len(exchanges)) + "</td></tr>"
        "<tr><td>Last updated</td><td class='muted'>" + generated + "</td></tr>"

"</tbody></table></div>"
        "<div class='pn'><div class='ph'>Bitget Sentiment</div>"
        "<table><thead><tr><th>Type</th><th>Count</th></tr></thead><tbody>"
        "<tr><td>Positive</td><td><b style='color:#00e676'>" + str(bg["positive"]) + "</b></td></tr>"
        "<tr><td>Neutral</td><td><b style='color:var(--mu)'>" + str(bg["neutral"]) + "</b></td></tr>"
        "<tr><td>Negative</td><td><b style='color:#ff4d6d'>" + str(bg["negative"]) + "</b></td></tr>"
        "</tbody></table></div>"
        "<div class='pn'>"
        "<div class='ph'>Competitor Intelligence <span class='ct'>auto-updated</span></div>"
        + build_competitor_card(
            "OKX", "NYSE rails and same UEX thesis",
            [("No.3 Volume", "bkr"), ("120M Users", "bku")],
            "CRITICAL", "tc",
            top_articles.get("OKX", []),
            "Executing Bitget exact playbook with institutional backing. 6-month product gap is the window.",
            [
                ("ICE Press Release", "https://ir.theice.com/press/news-details/2026/ICE-Makes-Investment-in-OKX-Establishing-Strategic-Relationship/default.aspx"),
                ("CoinDesk", "https://www.coindesk.com/business/2026/03/05/nyse-owner-ice-forges-strategic-partnership-with-crypto-exchange-okx"),
            ],
            "cr"
        )
        + build_competitor_card(
            "Bybit", "New Financial Platform and MyBank",
            [("No.2 Volume", "bkr"), ("60M+ Users", "bku")],
            "HIGH", "th2",
            top_articles.get("Bybit", []),
            "Recovered faster than expected from the Feb hack. MyBank is a direct threat to Bitget fiat strategy.",
            [],
            "hi"
        )
        + build_competitor_card(
            "Binance", "Regulatory normalization play",
            [("No.1 Volume", "bkr"), ("200M+ Users", "bku")],
            "MONITOR", "tm",
            top_articles.get("Binance", []),
            "Still market leader by distance. Watch for CZ re-engagement and new product launches.",
            [],
            "mo"
        )
        + "</div>"
        "</div></div></div>"
        "<div class='modal-overlay' id='newsModal'>"
        "<div class='modal'>"
        "<div class='modal-head'>"
        "<h2 id='modal-title'>News History</h2>"
        "<button class='modal-close' onclick=\"document.getElementById('newsModal').classList.remove('open')\">x</button>"
        "</div>"
        "<div class='modal-body' id='modal-body'>Loading...</div>"

"</div></div>"
        "<footer>"
        "<p>Bitget PR Monitor - auto-generated by GitHub Actions</p>"
        "<p>Refreshed daily at 01:00 UTC</p>"
        "</footer>"
        "<script>"
        "new Chart(document.getElementById('sovChart').getContext('2d'),{"
        "type:'bar',"
        "data:{labels:" + json.dumps(ex_order) + ","
        "datasets:[{label:'SOV %',data:" + json.dumps(sov_values) + ","
        "backgroundColor:" + json.dumps(colors) + ",borderRadius:6}]},"
        "options:{responsive:true,maintainAspectRatio:false,"
        "plugins:{legend:{display:false}},"
        "scales:{x:{ticks:{color:'#7986a3'},grid:{color:'#2a2f3d'}},"
        "y:{ticks:{color:'#7986a3',callback:function(v){return v+'%'}},grid:{color:'#2a2f3d'},beginAtZero:true}}}});"
        "document.querySelectorAll('.ex-link').forEach(function(el){"
        "el.addEventListener('click',function(){"
        "var ex=this.getAttribute('data-ex');"
        "var modal=document.getElementById('newsModal');"
        "var title=document.getElementById('modal-title');"
        "var body=document.getElementById('modal-body');"
        "title.textContent=ex.charAt(0).toUpperCase()+ex.slice(1)+' - News History';"
        "body.innerHTML='Loading...';"
        "modal.classList.add('open');"
        "fetch('data/'+ex+'_news.json')"
        ".then(function(r){return r.json();})"
        ".then(function(weeks){"
        "if(!weeks.length){body.innerHTML='<p style=\"color:var(--mu)\">No history yet.</p>';return;}"
        "var html='';"
        "weeks.slice().reverse().forEach(function(w){"
        "html+='<div class=\"week-block\">';"
        "html+='<div class=\"week-label\">'+w.week+' - '+w.generated_at.slice(0,10)+' - '+w.articles.length+' articles</div>';"
        "w.articles.forEach(function(a){"
        "var sc=a.sentiment==='positive'?'#00e676':a.sentiment==='negative'?'#ff4d6d':'#7986a3';"
        "var mw=a.source==='meltwater'?' <span style=\"color:#7b61ff;font-size:10px\">[MW]</span>':'';"
        "html+='<div class=\"news-item\">';"
        "html+='<div class=\"news-title\"><span style=\"color:'+sc+';margin-right:6px\">*</span>';"
        "html+='<a href=\"'+a.link+'\" target=\"_blank\">'+a.title+'</a>'+mw+'</div>';"
        "html+='<div class=\"news-meta\">'+(a.pub_date?a.pub_date.slice(0,16):'')+' '+a.exchange+'</div>';"
        "html+='</div>';"
        "});"
        "html+='</div>';"
        "});"
        "body.innerHTML=html;"
        "})"

".catch(function(){body.innerHTML='<p style=\"color:#ff4d6d\">Failed to load. Run the workflow once to generate history.</p>';});"
        "});"
        "});"
        "document.getElementById('newsModal').addEventListener('click',function(e){"
        "if(e.target===this)this.classList.remove('open');"
        "});"
        "</script></body></html>"
    )
    return page

def main():
    print("=" * 60)
    print("Bitget PR Monitor -- {}".format(
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")))
    print("=" * 60)

    MELTWATER_API_KEY = os.environ.get("MELTWATER_API_KEY", "")
    MELTWATER_SEARCHES = {
        "26257006": "Binance",
        "26256926": "Bitget",
        "26256928": "Bybit",
        "26256978": "OKX",
    }
    MELTWATER_SEARCHES = {k: v for k, v in MELTWATER_SEARCHES.items() if k}

    all_articles = []
    seen_titles  = []

    print("\n[1/3] Fetching {} Google News feeds...".format(len(GOOGLE_FEEDS)))
    for url, exchange in GOOGLE_FEEDS.items():
        for article in parse_feed(url, assigned_exchange=exchange):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)

    print("\n[2/3] Fetching {} direct media feeds...".format(len(DIRECT_FEEDS)))
    for url, exchange in DIRECT_FEEDS.items():
        for article in parse_feed(url, assigned_exchange=exchange):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)

    print("\n[3/3] Fetching Meltwater...")
    if MELTWATER_API_KEY and MELTWATER_SEARCHES:
        for article in fetch_meltwater(MELTWATER_API_KEY, MELTWATER_SEARCHES, EXCHANGES):
            if not is_duplicate(article["title"], seen_titles):
                seen_titles.append(normalize_title(article["title"]))
                all_articles.append(article)
    else:
        print("  [SKIP] Set MELTWATER_API_KEY + search IDs to enable.")

    print("\nTotal unique articles: {}".format(len(all_articles)))

    mention_counts   = defaultdict(int)
    sentiment_counts = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for a in all_articles:
        ex = a["exchange"]
        mention_counts[ex] += 1
        sentiment_counts[ex][a["sentiment"]] += 1

    total_mentions = sum(mention_counts.values())

    sov_map = {
        ex: round(mention_counts.get(ex, 0) / total_mentions * 100, 1) if total_mentions > 0 else 0.0
        for ex in EXCHANGES
    }

    last_week = load_last_week_sov()
    sov_delta = {
        ex: round(sov_map[ex] - last_week[ex], 1) if ex in last_week else None
        for ex in EXCHANGES
    }
    save_sov(sov_map)

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
        "sov_pct":        {ex: sov_map[ex] for ex in EXCHANGES},
        "top_articles":   {ex: get_top_articles(all_articles, ex) for ex in EXCHANGES},
    }

    with open("data/dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("data/dashboard_data.json written.")

    for ex in EXCHANGES:
        ex_articles = [a for a in all_articles if a["exchange"] == ex]
        ex_path = "data/" + ex.lower() + "_news.json"
        history = []
        if os.path.exists(ex_path):
            try:
                with open(ex_path) as f:
                    history = json.load(f)
            except Exception:
                history = []
        week_entry = {
            "week":         datetime.now(timezone.utc).strftime("%Y-W%V"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "articles":     ex_articles,
        }
        history = [w for w in history if w["week"] != week_entry["week"]]
        history.append(week_entry)
        history = history[-8:]
        with open(ex_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    print("Per-exchange news history written.")

    html = generate_html(output)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html generated.")

    print("\n-- Share of Voice --")
    for ex, d in sorted(exchange_data.items(), key=lambda x: -x[1]["sov"]):
        delta = d["sov_delta_wow"]
        if delta is None:
            dstr = "(first run)"
        else:
            dstr = "({}{}% WoW)".format("+" if delta >= 0 else "", delta)
        s = d["sentiment"]
        print("  {:8s}: {:4d} mentions | SOV {:5.1f}% {} | +{} ~{} -{}".format(
            ex, d["mentions"], d["sov"], dstr,
            s["positive"], s["neutral"], s["negative"]
        ))

if __name__ == "__main__":
    main()
