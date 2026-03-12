<div class="comp-links"><a class="comp-link" href="https://www.kucoin.com/news/articles/kucoin-invests-2-billion-building-the-world-s-most-trusted-crypto-exchange" target="_blank">↗ KuCoin Official</a></div>
        </div>
        <div class="comp-deep moderate">
          <div class="comp-deep-header"><div><div class="comp-name">Binance</div><div class="comp-tagline">"Volume leader, declining reserves"</div><div class="comp-badges"><span class="badge badge-rank">#1 Volume</span></div></div><span class="threat-badge threat-moderate">● MODERATE</span></div>
          <ul class="comp-bullets"><li>BTC reserves <strong>down 1.25%</strong> → 631K BTC latest PoR</li><li>ETH down 7.35%, net outflows Feb–Mar</li><li>No TradFi pivot; fee-cut strategy only</li></ul>
          <div class="verdict-box"><div class="verdict-label">⚔️ Verdict</div><div class="verdict-text">Every month Binance's PoR declines, Bitget's transparency story grows stronger. Lean into this narrative.</div></div>
        </div>
      </div>
      <div class="panel">
        <div class="section-header"><span class="section-icon">👀</span><h2>Watchlist</h2></div>
        <div class="watch-item"><div class="watch-dot" style="background:#ff4d6d"></div><div><div class="watch-title">OKX NYSE Stocks Launch (H2 2026)</div><div class="watch-desc">When OKX goes live, Bitget's first-mover window closes. Track weekly.</div></div></div>
        <div class="watch-item"><div class="watch-dot" style="background:#ff9800"></div><div><div class="watch-title">Bybit MyBank + ByCustody AUM</div><div class="watch-desc">If custody crosses $10B, institutional optics shift against Bitget.</div></div></div>


<div class="watch-item"><div class="watch-dot" style="background:#ffd740"></div><div><div class="watch-title">MEXC × Ondo Next Batch</div><div class="watch-desc">Track how fast they close the tokenized stocks gap with Bitget.</div></div></div>


<div class="watch-item"><div class="watch-dot" style="background:#00e676"></div><div><div class="watch-title">Bitget × B2C2 Institutional Volume</div><div class="watch-desc">Counter to OKX's ICE story — watch for client win announcements.</div></div></div>
        <div class="watch-item"><div class="watch-dot" style="background:#7b61ff"></div><div><div class="watch-title">Bitget Data Credibility Play</div><div class="watch-desc">Bitget cited as Nasdaq ETHB data source. Build as a separate PR narrative.</div></div></div>
      </div>
    </div>
  </div>
</div>
<footer>
  <p>GetClaw × Bitget PR Monitor · Auto-generated · {generated_at}</p>
  <p>Sources: 10 RSS feeds · CoinGecko · Alternative.me · {total_scanned} articles scanned</p>
</footer>
<script>
const ctx = document.getElementById('sovChart').getContext('2d');
new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: {sov_labels},
    datasets: [{{
      label: 'Share of Voice (%)',
      data: {sov_data},
      backgroundColor: {sov_colors},
      borderColor: {sov_colors},
      borderWidth: 1,
      borderRadius: 6,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: function(ctx) {{
            const counts = {sov_counts_list};
            return  ${{ctx.parsed.y}}% (${{counts[ctx.dataIndex]}} mentions);
          }}
        }}
      }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#7986a3' }}, grid: {{ color: '#2a2f3d' }} }},
      y: {{ ticks: {{ color: '#7986a3', callback: v => v + '%' }}, grid: {{ color: '#2a2f3d' }}, beginAtZero: true }}
    }}
  }}
}});
</script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(html)

print(f"✓ index.html generated ({len(html):,} bytes)")
print(f"  SOV: {sov}")
print(f"  Articles scanned: {total_scanned}")
