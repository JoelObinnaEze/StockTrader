import requests
from price import get_stock_price
import yfinance as yf

API_KEY = 'M63HE2XB7TVPNBVY'
BASE_URL = 'https://www.alphavantage.co/query'

class StockAPI:
    @staticmethod
    def get_stock(symbol):
        url = f"{BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()
        msft = yf.Ticker(symbol)

        if 'Global Quote' in data:
            quote = data['Global Quote']
            return {
                'symbol': quote['01. symbol'],
                'price': float(get_stock_price(symbol)),
                'name': msft.info['longName']
            }
        return None

if __name__ == "__main__":
    stock = StockAPI.get_stock('AAPL')
    print(stock)
