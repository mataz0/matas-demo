#!/usr/bin/env python3
"""Money OS price feed: writes moneyos/prices.json (stocks/ETFs via Yahoo chart,
top-100 crypto via CoinGecko, USD->EUR/GBP via Frankfurter). Stdlib only."""
import json, time, urllib.request, sys

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
OUT = "moneyos/prices.json"

# display ticker -> yahoo symbol
STOCKS = {s: s for s in (
    "AAPL MSFT NVDA GOOGL AMZN META TSLA JPM V JNJ WMT XOM UNH MA PG HD COST "
    "ORCL CVX ABBV MRK KO PEP BAC AVGO LLY ADBE CRM NFLX AMD INTC CSCO TMO MCD "
    "DIS ABT NKE QCOM TXN IBM CAT GE AXP GS MS PM T VZ PFE UPS RTX HON BA SBUX "
    "LOW SPGI BLK PLTR UBER COIN PYPL SHOP MSTR HOOD SNOW ARM "
    "SPY QQQ VTI VOO IVV DIA IWM SCHD VYM VUG VTV GLD SLV ARKK"
).split()}
STOCKS.update({"BRK.B": "BRK-B", "VWCE": "VWCE.DE", "EUNL": "EUNL.DE",
               "VUAA": "VUAA.DE", "SXR8": "SXR8.DE", "IWDA": "IWDA.AS",
               "AGGH": "AGGH.MI", "IUSQ": "IUSQ.DE"})

def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1: return None
            time.sleep(1 + i)

def main():
    out = {"t": int(time.time()), "fx": {}, "stocks": {}, "crypto": {}}

    fx = get("https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,GBP")
    if fx and fx.get("rates"): out["fx"] = fx["rates"]

    for tick, ysym in STOCKS.items():
        d = get("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=1d&interval=1d" % ysym, tries=2)
        try:
            m = d["chart"]["result"][0]["meta"]
            p, c = m["regularMarketPrice"], m["currency"]
            if p and c in ("USD", "EUR", "GBP"):
                out["stocks"][tick] = {"p": round(float(p), 4), "c": c}
        except Exception:
            pass
        time.sleep(0.25)

    mk = get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1")
    if mk:
        for c in mk:
            sym = (c.get("symbol") or "").upper()
            p = c.get("current_price")
            if sym and p and sym not in out["crypto"]:
                out["crypto"][sym] = {"p": p, "c": "USD"}

    if len(out["stocks"]) < 30 or len(out["crypto"]) < 30 or not out["fx"]:
        print("REFUSING to write thin feed: stocks=%d crypto=%d fx=%s"
              % (len(out["stocks"]), len(out["crypto"]), bool(out["fx"])))
        sys.exit(1)

    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote %s: %d stocks, %d crypto, fx=%s" % (OUT, len(out["stocks"]), len(out["crypto"]), out["fx"]))

if __name__ == "__main__":
    main()
