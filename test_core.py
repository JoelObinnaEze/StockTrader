import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import portfolio
import stock_api
import transaction
import user
from database import initialize_database
from insights import analyse_portfolio
from stock import Stock
from stock_api import StockAPI
from user import User


SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    balance REAL NOT NULL
);
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL
);
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock TEXT,
    quantity INTEGER,
    price REAL,
    type TEXT,
    timestamp TEXT
);
"""


class CoreTradingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        connection = sqlite3.connect(self.db_path)
        try:
            connection.executescript(SCHEMA)
        finally:
            connection.close()

        self.patches = [
            patch.object(user, "DB_NAME", self.db_path, create=True),
            patch.object(portfolio, "DB_NAME", self.db_path),
            patch.object(transaction, "DB_NAME", self.db_path),
        ]
        for db_patch in self.patches:
            db_patch.start()

    def tearDown(self):
        for db_patch in reversed(self.patches):
            db_patch.stop()
        self.temp_dir.cleanup()

    def test_registration_hashes_password_and_login_ignores_username_case(self):
        registered = User.register("Ada", "focused-builder")

        connection = sqlite3.connect(self.db_path)
        try:
            stored_password = connection.execute(
                "SELECT password FROM users WHERE username = 'ada'"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertTrue(stored_password.startswith("scrypt$"))
        self.assertNotEqual(stored_password, "focused-builder")
        self.assertEqual(User.login("ADA", "focused-builder").id, registered.id)

    def test_login_upgrades_a_legacy_plaintext_password(self):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                ("legacy", "old-password", 10_000),
            )
            connection.commit()
        finally:
            connection.close()

        self.assertTrue(User.login("legacy", "old-password"))

        connection = sqlite3.connect(self.db_path)
        try:
            upgraded = connection.execute(
                "SELECT password FROM users WHERE username = 'legacy'"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertTrue(upgraded.startswith("scrypt$"))

    def test_registration_rejects_oversized_credentials(self):
        self.assertFalse(User.register("x" * 41, "focused-builder"))
        self.assertFalse(User.register("ada", "x" * 257))

    def test_invalid_trade_quantities_do_not_change_account_state(self):
        trader = User.register("grace", "correct-horse")
        stock = Stock("NVDA", "NVIDIA", 100)

        self.assertFalse(trader.buy_stock(stock, 0))
        self.assertFalse(trader.buy_stock(stock, -4))
        self.assertFalse(trader.buy_stock(Stock("PENNY", "Penny Stock", 0.001), 1_000_001))
        self.assertFalse(trader.buy_stock(Stock("NVDA", "NVIDIA", float("nan")), 1))
        self.assertFalse(trader.sell_stock(stock, 1))

        self.assertEqual(trader.balance, 10_000)
        self.assertEqual(trader.portfolio.get_portfolio(), [])
        self.assertEqual(trader.transaction_history.get_transactions(), [])

    def test_trades_use_weighted_cost_and_failed_sell_has_no_side_effects(self):
        trader = User.register("linus", "kernel-mode")
        trader.buy_stock(Stock("AMD", "AMD", 100), 10)
        trader.buy_stock(Stock("AMD", "AMD", 200), 10)

        holding = trader.portfolio.get_portfolio()[0]
        self.assertEqual(holding[2], 20)
        self.assertEqual(holding[3], 150)

        balance_before_failed_sell = trader.balance
        history_before_failed_sell = trader.transaction_history.get_transactions()
        self.assertFalse(trader.sell_stock(Stock("AMD", "AMD", 250), 21))
        self.assertEqual(trader.balance, balance_before_failed_sell)
        self.assertEqual(
            trader.transaction_history.get_transactions(), history_before_failed_sell
        )

        self.assertTrue(trader.sell_stock(Stock("AMD", "AMD", 250), 5))
        self.assertEqual(trader.balance, balance_before_failed_sell + 1_250)
        self.assertEqual(trader.portfolio.get_portfolio()[0][2], 15)


class DatabaseTests(unittest.TestCase):
    def test_fresh_database_creates_the_required_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = str(Path(temp_dir) / "fresh.db")

            initialize_database(database_path)

            connection = sqlite3.connect(database_path)
            try:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
            finally:
                connection.close()
        self.assertTrue({"users", "portfolio", "transactions"}.issubset(tables))


class MarketDataTests(unittest.TestCase):
    @patch("stock_api.yf.Ticker")
    def test_quote_normalizes_symbol_and_uses_latest_close(self, ticker_factory):
        ticker = ticker_factory.return_value
        ticker.history.return_value = pd.DataFrame({"Close": [178.25]})
        ticker.get_info.return_value = {"longName": "Apple Inc."}

        quote = StockAPI.get_stock(" aapl ")

        ticker_factory.assert_called_once_with("AAPL")
        self.assertEqual(
            quote, {"symbol": "AAPL", "name": "Apple Inc.", "price": 178.25}
        )

    @patch("stock_api.yf.Ticker")
    def test_empty_symbol_is_a_recoverable_miss(self, ticker_factory):
        self.assertIsNone(StockAPI.get_stock("  "))
        self.assertIsNone(StockAPI.get_stock(None))
        self.assertIsNone(StockAPI.get_stock("AAPL; DROP TABLE"))
        ticker_factory.assert_not_called()

    @patch("stock_api.yf.Ticker")
    def test_non_finite_quote_is_a_recoverable_miss(self, ticker_factory):
        ticker_factory.return_value.history.return_value = pd.DataFrame(
            {"Close": [float("nan")]}
        )

        self.assertIsNone(StockAPI.get_stock("AAPL"))


class PortfolioInsightTests(unittest.TestCase):
    def test_analysis_calculates_value_profit_and_concentration(self):
        holdings = [
            ("AMD", "AMD", 4, 100),
            ("AAPL", "Apple", 2, 150),
        ]

        analysis = analyse_portfolio(holdings, 500, {"AMD": 125, "AAPL": 140})

        self.assertEqual(analysis["invested"], 780)
        self.assertEqual(analysis["net_worth"], 1_280)
        self.assertEqual(analysis["unrealized_pl"], 80)
        self.assertEqual(analysis["allocation"][0][0], "AMD")
        self.assertAlmostEqual(analysis["concentration"], 500 / 780)

    def test_empty_portfolio_returns_a_useful_cash_only_state(self):
        analysis = analyse_portfolio([], 10_000, {})

        self.assertEqual(analysis["net_worth"], 10_000)
        self.assertEqual(analysis["concentration"], 0)
        self.assertIn("deploy", analysis["brief"].lower())


if __name__ == "__main__":
    unittest.main()
