# StockTrader

A desktop paper-trading workstation for testing market ideas with virtual capital. It combines quote lookup, guarded buy and sell orders, portfolio analysis, an execution ledger, and price research in one focused interface.

## What changed

- Persistent workstation navigation instead of disconnected screens
- Overview with net worth, cash, exposure, unrealized P/L, allocation, and local portfolio signals
- Non-blocking market-data requests so the UI stays responsive
- Weighted average cost, validated order sizes, and atomic cash/position updates
- Scrypt password hashing with automatic upgrade when a legacy account signs in
- One yfinance market-data path; no embedded API key
- Private local SQLite data instead of a populated database committed to Git

The signal brief is deterministic portfolio analysis, not an LLM and not investment advice. Market data may be delayed.

## Run

Requires Python 3.9+.

```powershell
python -m pip install -r requirements.txt
python gui.py
```

The app creates a fresh, ignored `stocktrader.db` on first launch.

## Verify

```powershell
python -m unittest -v
python -m compileall -q database.py gui.py insights.py portfolio.py stock.py stock_api.py transaction.py user.py
```

## Structure

| File | Responsibility |
|---|---|
| `gui.py` | Authentication, workstation shell, and five product views |
| `database.py` | Local schema and first-run initialization |
| `user.py` | Authentication and atomic trade execution |
| `portfolio.py` | Portfolio position reads |
| `transaction.py` | Execution-ledger access |
| `stock_api.py` | Validated quote and history boundary |
| `insights.py` | Deterministic portfolio analysis |
| `test_core.py` | Money-path, account, market-data, and analysis checks |

## Data and security

`stocktrader.db`, environment files, key files, and generated Python artifacts are ignored. The original GitHub history contained a populated database and an AlphaVantage key; if either held real credentials, rotate them and purge that history before treating the repository as private or secure.
