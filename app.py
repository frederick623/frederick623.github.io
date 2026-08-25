import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)


@app.route("/")
def dashboard():
    """Serve the dashboard from the same origin as its API."""
    return send_from_directory(app.root_path, "index.html")


def _ticker_info(symbol):
    t = yf.Ticker(symbol)
    info = t.info
    return info


@app.route("/api/search")
def search():
    """Return info + sector peers for a ticker symbol."""
    symbol = request.args.get("symbol", "").upper().strip()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    try:
        info = _ticker_info(symbol)
    except Exception:
        app.logger.exception("Request error")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500

    sector = info.get("sector", "")
    industry = info.get("industry", "")

    # Collect a handful of peer tickers from the same sector/industry using
    # Yahoo Finance's recommendations endpoint, falling back gracefully.
    peers = []
    try:
        t = yf.Ticker(symbol)
        recs = t.recommendations
        if recs is not None and not recs.empty:
            # recommendations df has an index of dates; latest rows first
            firms = recs.tail(10)
            # grab the ticker column if available, otherwise use a dummy list
            if "To Grade" in firms.columns:
                pass  # recommendations don't contain peer tickers this way
        # Use the similar tickers if available
        peer_tickers = []

        # Best effort: use the sector/industry to build a small hardcoded map
        # of representative stocks, since Yahoo Finance API doesn't expose a
        # "sector peers" endpoint directly.
        sector_peers_map = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA", "AMD", "INTC", "CRM"],
            "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP", "SCHW", "USB"],
            "Healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK", "TMO", "ABT", "LLY", "BMY", "AMGN"],
            "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "SBUX", "MCD", "TGT", "LOW", "BKNG", "F"],
            "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "CL", "GIS", "KHC"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO", "PSX", "OXY", "HAL"],
            "Industrials": ["BA", "CAT", "GE", "HON", "UPS", "RTX", "LMT", "MMM", "EMR", "ITW"],
            "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "SNAP", "WBD"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "ED", "WEC"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "SPG", "PSA", "O", "DLR", "WELL", "AVB"],
            "Basic Materials": ["LIN", "APD", "SHW", "ECL", "NEM", "FCX", "DOW", "DD", "NUE", "CF"],
        }

        if sector in sector_peers_map:
            candidates = [s for s in sector_peers_map[sector] if s != symbol]
            peer_tickers = candidates[:6]
        else:
            peer_tickers = []

        for pt in peer_tickers:
            try:
                pi = yf.Ticker(pt).info
                peers.append({
                    "symbol": pt,
                    "name": pi.get("shortName", pt),
                    "sector": pi.get("sector", ""),
                    "industry": pi.get("industry", ""),
                    "currentPrice": pi.get("currentPrice") or pi.get("regularMarketPrice"),
                })
            except Exception:
                peers.append({"symbol": pt, "name": pt, "sector": sector, "industry": industry})

    except Exception:
        pass

    return jsonify({
        "symbol": symbol,
        "name": info.get("shortName", symbol),
        "sector": sector,
        "industry": industry,
        "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
        "peers": peers,
    })


@app.route("/api/quote")
def quote():
    """Return last price + OHLC summary for a ticker."""
    symbol = request.args.get("symbol", "").upper().strip()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    try:
        t = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period="1d")
        last_row = hist.iloc[-1] if not hist.empty else None

        return jsonify({
            "symbol": symbol,
            "name": info.get("shortName", symbol),
            "currency": info.get("currency", "USD"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "open": float(last_row["Open"]) if last_row is not None else info.get("open"),
            "high": float(last_row["High"]) if last_row is not None else info.get("dayHigh"),
            "low": float(last_row["Low"]) if last_row is not None else info.get("dayLow"),
            "close": float(last_row["Close"]) if last_row is not None else info.get("previousClose"),
            "volume": int(last_row["Volume"]) if last_row is not None else info.get("volume"),
            "previousClose": info.get("previousClose"),
            "marketCap": info.get("marketCap"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
        })
    except Exception:
        app.logger.exception("Request error")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500


@app.route("/api/history")
def history():
    """Return OHLCV candlestick history for a ticker."""
    symbol = request.args.get("symbol", "").upper().strip()
    period = request.args.get("period", "3mo")
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        hist.index = hist.index.strftime("%Y-%m-%d")
        candles = [
            {
                "date": idx,
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]
        return jsonify({"symbol": symbol, "candles": candles})
    except Exception:
        app.logger.exception("Request error")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500


INDICATOR_MAP = {
    "pe_ratio": "trailingPE",
    "eps": "trailingEps",
    "revenue": "totalRevenue",
    "gross_profit": "grossProfits",
    "operating_cash_flow": "operatingCashflow",
    "free_cash_flow": "freeCashflow",
    "debt_to_equity": "debtToEquity",
    "roe": "returnOnEquity",
    "roa": "returnOnAssets",
    "profit_margin": "profitMargins",
    "dividend_yield": "dividendYield",
    "beta": "beta",
    "52w_high": "fiftyTwoWeekHigh",
    "52w_low": "fiftyTwoWeekLow",
}


@app.route("/api/indicators")
def indicators():
    """Return list of available indicator keys."""
    return jsonify({"indicators": list(INDICATOR_MAP.keys())})


@app.route("/api/indicator_series")
def indicator_series():
    """Return a time-series of a financial indicator for the optional y-axis."""
    symbol = request.args.get("symbol", "").upper().strip()
    indicator = request.args.get("indicator", "pe_ratio")
    period = request.args.get("period", "3mo")
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    try:
        t = yf.Ticker(symbol)

        # For indicators that can be derived from financials / history:
        if indicator == "volume":
            hist = t.history(period=period)
            hist.index = hist.index.strftime("%Y-%m-%d")
            series = [{"date": idx, "value": int(row["Volume"])} for idx, row in hist.iterrows()]
            return jsonify({"symbol": symbol, "indicator": indicator, "series": series})

        # For many static indicators (e.g. P/E, Beta), Yahoo Finance only
        # provides the current snapshot value, not a historical time-series.
        # We repeat that single value across all dates so it appears as a
        # reference line on the chart; the indicator title in the chart legend
        # makes clear it is a current-snapshot value.
        info = t.info
        yf_key = INDICATOR_MAP.get(indicator, indicator)
        value = info.get(yf_key)

        hist = t.history(period=period)
        hist.index = hist.index.strftime("%Y-%m-%d")
        series = [{"date": idx, "value": value} for idx in hist.index]
        return jsonify({"symbol": symbol, "indicator": indicator, "snapshot": True, "series": series})
    except Exception:
        app.logger.exception("Request error")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500


@app.route("/api/news")
def news():
    """Return news for a ticker from Yahoo Finance."""
    symbol = request.args.get("symbol", "").upper().strip()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400

    try:
        t = yf.Ticker(symbol)
        raw_news = t.news or []
        items = []
        for article in raw_news:
            # yfinance returns a list of dicts with keys: uuid, title, publisher,
            # link, providerPublishTime, type, thumbnail, relatedTickers
            pub_ts = article.get("providerPublishTime", 0)
            pub_date = datetime.datetime.utcfromtimestamp(pub_ts).strftime("%Y-%m-%d %H:%M") if pub_ts else ""
            items.append({
                "date": pub_date,
                "title": article.get("title", ""),
                "publisher": article.get("publisher", ""),
                "type": article.get("type", "STORY"),
                "link": article.get("link", ""),
                "relatedTickers": article.get("relatedTickers", []),
            })
        return jsonify({"symbol": symbol, "news": items})
    except Exception:
        app.logger.exception("Request error")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
