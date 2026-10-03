# Spec: StockTrader Workstation Remake

## Objective
Rebuild StockTrader as a focused desktop market workstation while preserving its core simulator loop: create an account, research a symbol, trade with virtual cash, and understand portfolio performance. The experience should feel deliberate and technical, not like a generic dashboard.

## Tech Stack
- Python 3.9+
- CustomTkinter 5
- SQLite via the standard library
- yfinance for quotes and history
- Matplotlib for charts

## Commands
- Run: `python gui.py`
- Test: `python -m unittest -v`
- Build check: `python -m compileall -q database.py gui.py user.py portfolio.py transaction.py stock_api.py stock.py insights.py`

## Project Structure
- `gui.py` — application shell and views
- `database.py` — schema and first-run database initialization
- `user.py`, `portfolio.py`, `transaction.py` — account and trade persistence
- `stock_api.py`, `stock.py` — market data boundary
- `insights.py` — deterministic portfolio signals used by the UI
- `test_core.py` — focused money-path and insight checks

## Code Style
Use small, named functions and semantic UI helpers; prefer the standard library and existing dependencies.

```python
def format_money(value):
    return f"${value:,.2f}"
```

## Testing Strategy
Use `unittest` with a temporary SQLite database for account and trade behavior. Keep UI validation to a launch smoke check plus visual inspection because widget appearance is not meaningfully proven by unit tests.

## Boundaries
- Always: validate quantities, preserve existing account data, keep network failures recoverable, and run tests before handoff.
- Ask first: database schema changes, new dependencies, or a switch away from the Python desktop stack.
- Never: hardcode credentials, make real-money claims, or present deterministic insights as financial advice.

## Success Criteria
- Login and registration work by mouse and keyboard with useful error states.
- A signed-in user can navigate Overview, Trade, Portfolio, Activity, and Research without rebuilding the application shell.
- Overview shows cash, holdings value, net worth, unrealized P/L, positions, allocation, and an honest local signal brief.
- Quote lookup runs without freezing the UI and supports validated virtual buy orders.
- Portfolio supports validated sells; failed trades never change cash or history.
- Research renders recent price history and handles missing/network data cleanly.
- Source contains no API key; tests and compile checks pass.
- The UI remains usable at the documented minimum window size and uses visible focus, readable contrast, and native controls.

## Open Questions
None. The user explicitly allowed a full reskin and broad design discretion.
