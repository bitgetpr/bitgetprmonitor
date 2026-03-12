python
import json
import os

with open("data/dashboard_data.json") as f:
    d = json.load(f)

sov      = d["sov_pct"]
counts   = d["sov_counts"]
stats    = d["bitget_stats"]
market   = d["market"]
fg       = d["fear_greed"]
articles = d["bitget_articles"]
gen_at   = d["generated_at"]
total    = d["total_articles_scanned"]

EXCHANGE_ORDER = ["Bitget", "Binance", "OKX", "Bybit", "MEXC", "KuCoin"]
COLORS = {
    "Bitget":  "#00c4ff",
    "OKX":     "#ff4d6d",
    "Bybit":   "#ff9800",
    "MEXC":    "#ffd740",
    "KuCoin":  "#00e676",
    "Binance": "#7b61ff",
}

sov_labels = json.dumps(EXCHANGE_ORDER)
sov_data   = json.dumps([sov.get(e, 0) for e in EXCHANGE_ORDER])
sov_colors = json.dumps([COLORS[e] for e in EXCHANGE_ORDER])
sov_cnts   = json.dumps([counts.get(e, 0) for e in EXCHANGE_ORDER])

def delta_cls(val):
    try:
        return "up" if float(val) >= 0 else "down"
    except Exception:
        return "neutral"

def fmt_delta(val):
    try:
        v = float(val)
        sign = "+" if v >= 0 else ""
        return sign + str(round(v, 2)) + "%"
    except Exception:
        return "N/A"

news_html = ""
for art in articles[:8]:
    t   = art.get("title", "")
    lnk = art.get("link", "#")
    src = art.get("source", "News")
    pub = art.get("pub", "")[:16]
    news_html += (
        "<div class='news-item'>"
        "<div class='news-meta'>"
        "<span class='news-date'>" + pub + "</span>"
        "<span class='news-source'>" + src + "</span>"
        "<span class='news-tag'>Bitget</span>"
        "</div>"
        "<div class='news-title'>" + t + "</div>"
        "<a class='news-link' href='" + lnk + "' target='_blank'>Read full story</a>"
        "</div>"
    )

if not news_html:
    news_html = "<p style='color:#7986a3;font-size:13px;'>No Bitget articles found today.</p>"

sov_rows = ""
for e in EXCHANGE_ORDER:
    col   = COLORS[e]
    cnt   = counts.get(e, 0)
    pct   = sov.get(e, 0)
    sov_rows += (
        "<tr>"
        "<td><strong style='color:" + col + "'>" + e + "</strong></td>"
        "<td>" + str(cnt) + "</td>"
        "<td><strong>" + str(pct) + "%</strong></td>"
        "<td class='sov-bar-cell'><div class='sov-bar-bg'><div class='sov-bar' style='width:" + str(pct) + "%;background:" + col + "'></div></div></td>"
        "</tr>"
    )

btc_price  = market.get("btc_price", "N/A")
btc_chg    = market.get("btc_change_24h", 0)
fg_val     = fg.get("value", "N/A")
fg_cls     = fg.get("classification", "")
bitget_sov = sov.get("Bitget", 0)
bitget_cnt = counts.get("Bitget", 0)

if isinstance(btc_price, (int, float)):
    btc_display = "$" + "{:,}".format(int(btc_price))
else:
    btc_display = str(btc_price)
<div class="comp-deep high">
          <div class="comp-header">
            <div><div class="comp-name">MEXC</div><div class="comp-tagline">Zero-fee king entering tokenized stocks</div><div class="comp-badges"><span class="badge badge-rank">#2 Daily Vol</span><span class="badge badge-users">36M+ Users</span></div></div>
            <span class="threat threat-high">HIGH</span>
          </div>
          <div class="comp-section">Key Moves</div>
          <ul class="comp-bullets">
            <li><strong>$175M net inflows Feb 2026</strong> - razor thin gap vs Bitget $205M</li>
            <li>9th Ondo Finance collab: 17 tokenized US equity pairs, zero-fee 30 days</li>
            <li>$1.1B in user fee savings via zero-fee spot in 2025</li>
            <li>BTC reserve coverage 158-266% (bimonthly audits)</li>
          </ul>
          <div class="verdict"><div class="verdict-label">Verdict</div><div class="verdict-text">Most underrated threat. Zero-fee moat plus Ondo tokenized stocks = attacking Bitget on two fronts simultaneously.</div></div>
          <div class="comp-links">
            <a class="comp-link" href="https://coincentral.com/mexc-expands-zero-fee-tokenized-equities-with-ondo-batch/" target="_blank">Ondo Equities</a>
          </div>
        </div>

        <div class="comp-deep moderate">
          <div class="comp-header">
            <div><div class="comp-name">KuCoin</div><div class="comp-tagline">$2B compliance pivot</div><div class="comp-badges"><span class="badge badge-rank">#5 Volume</span><span class="badge badge-users">41M Users</span></div></div>
            <span class="threat threat-moderate">MODERATE</span>
          </div>
          <div class="comp-section">Key Moves</div>
          <ul class="comp-bullets">
            <li>$2B Trust Project over 2026-2028 for security and compliance</li>
            <li>Goal: most trusted global crypto exchange by 2028</li>
            <li>Compliance pivot is defensive - no TradFi product announced</li>
          </ul>
          <div class="verdict"><div class="verdict-label">Verdict</div><div class="verdict-text">Bitget's actual PoR numbers today beat KuCoin's future promise. Not a TradFi threat yet.</div></div>
          <div class="comp-links">
            <a class="comp-link" href="https://www.kucoin.com/news/articles/kucoin-invests-2-billion-building-the-world-s-most-trusted-crypto-exchange" target="_blank">KuCoin Official</a>
          </div>
        </div>

        <div class="comp-deep moderate">
          <div class="comp-header">
            <div><div class="comp-name">Binance</div><div class="comp-tagline">Volume leader with declining reserves</div><div class="comp-badges"><span class="badge badge-rank">#1 Volume</span></div></div>
            <span class="threat threat-moderate">MODERATE</span>
          </div>
          <div class="comp-section">Key Moves</div>
          <ul class="comp-bullets">
            <li><strong>BTC reserves down 1.25%</strong> to 631K BTC in latest PoR</li>
            <li>ETH down 7.35%, net outflows Feb-Mar</li>
            <li>No TradFi pivot - fee-cut strategy only</li>
          </ul>
          <div class="verdict"><div class="verdict-label">Verdict</div><div class="verdict-text">Every month Binance reserves decline, Bitget's transparency story grows stronger. Lean into this narrative.</div></div>
        </div>


</div>
    </div>
  </div>
</div>
<footer>
  <p>Bitget PR Monitor - Auto-generated - """ + gen_at + """</p>
  <p>Sources: 10 RSS feeds, CoinGecko, Alternative.me - """ + str(total) + """ articles scanned</p>
</footer>
<script>
const ctx = document.getElementById('sovChart').getContext('2d');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: """ + sov_labels + """,
    datasets: [{
      label: 'Share of Voice (%)',
      data: """ + sov_data + """,
      backgroundColor: """ + sov_colors + """,
      borderRadius: 6
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(c) {
            var cnts = """ + sov_cnts + """;
            return ' ' + c.parsed.y + '% (' + cnts[c.dataIndex] + ' mentions)';
          }
        }
      }
    },
    scales: {
      x: { ticks: { color: '#7986a3' }, grid: { color: '#2a2f3d' } },
      y: { ticks: { color: '#7986a3', callback: function(v){ return v + '%'; } }, grid: { color: '#2a2f3d' }, beginAtZero: true }
    }
  }
});
</script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(page)

print("index.html generated - " + str(len(page)) + " bytes")
print("SOV: " + str(sov))...
