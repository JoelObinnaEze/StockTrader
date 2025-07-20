import yfinance as yf

def get_stock_price(symbol):
    """Fetch real-time stock price from Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        return "{:.2f}".format(stock.history(period="1d")["Close"].iloc[-1])  # Last closing price
    except Exception:
        return "N/A"
