
# 💸 StockTrader - Stock Trading Simulator

A GUI-based stock trading simulator built with `customtkinter` that allows users to register, buy/sell stocks, view their portfolio, track transaction history, and analyze stock growth trends. It's a self-contained educational tool that mimics the experience of trading in the stock market using real-time financial data.

---

## 🚀 Features

- 🔐 **User Authentication**  
  Register and log in with a secure interface that includes caps lock detection and error handling.

- 📈 **Live Stock Search & Purchase**  
  Search for real-time stock data using APIs and purchase shares directly from the interface.

- 💼 **Portfolio Management**  
  View your holdings, including quantities, buy price, live price, and calculated profit/loss.

- 🕰️ **Transaction History**  
  Review a detailed history of all stock purchases and sales with timestamps.

- 📊 **Growth Analytics**  
  Visualize the last month's price trends of a stock using interactive Matplotlib charts.

- 🧾 **Clean UI**  
  Built using `customtkinter` with a modern dark theme and structured navigation bar.

---

## 🛠️ Tech Stack

| Layer              | Technology         |
|--------------------|--------------------|
| GUI Framework      | `customtkinter`    |
| Data Fetching      | `yfinance`, AlphaVantage API (`StockAPI`) |
| Charting           | `matplotlib`       |
| Backend Logic      | OOP-based modules (`User`, `Stock`, `Portfolio`, etc.) |
| Additional Tools   | `FigureCanvasTkAgg` for embedding charts |

---


## 📁 Project Structure

```
StockTrader/
│
├── data.db                  # Database for user info
├── gui.py                   # Main GUI application
├── user.py                  # User class: login, registration
├── stock_api.py             # Handles API calls to fetch stock data
├── stock.py                 # Stock object representation
├── portfolio.py             # Manages user portfolios
├── price.py                 # Fetches live prices
├── transaction.py           # Transaction class: buying, selling
└── README.md                # Project documentation
```

---

## 🧪 How to Run

### Requirements:
- Python 3.9+
- `yfinance`
- `matplotlib`
- `customtkinter`

### Installation:

1. **Clone the Repository**
```bash
git clone https://github.com/JoelObinnaEze/StockTrader.git
cd StockTrader
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the App**
```bash
python gui.py
```

---

## 👨‍💻 Author

**Joel Obinna-Eze**  
*Software Engineering Student | Full-stack Developer*  
[GitHub](https://github.com/JoelObinnaEze)

---

## 📝 License

This project is for educational purposes only.  
Feel free to fork or contribute!
