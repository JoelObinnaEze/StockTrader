import math

import yfinance as yf


class StockAPI:
    @staticmethod
    def get_stock(symbol):
        symbol = _normalize_symbol(symbol)
        if not symbol:
            return None

        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period="5d")
            if history.empty:
                return None
            price = float(history["Close"].iloc[-1])
        except Exception:
            return None
        if not math.isfinite(price) or price <= 0:
            return None
        try:
            info = ticker.get_info()
        except Exception:
            info = {}
        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "price": price,
        }

    @staticmethod
    def get_history(symbol, period="1mo"):
        symbol = _normalize_symbol(symbol)
        if not symbol:
            return None
        try:
            history = yf.Ticker(symbol).history(period=period)
            return None if history.empty else history
        except Exception:
            return None


def _normalize_symbol(symbol):
    if not isinstance(symbol, str):
        return None
    symbol = symbol.strip().upper()
    allowed = set(".-^=")
    valid = 1 <= len(symbol) <= 15 and all(
        character.isalnum() or character in allowed for character in symbol
    )
    return symbol if valid else None
