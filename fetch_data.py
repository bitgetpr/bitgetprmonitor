--- Assemble Output ---
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

print(f"\nData saved to {OUTPUT_FILE}")
print(f"Generated at: {output['generated_at']}")
```

