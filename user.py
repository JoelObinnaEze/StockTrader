import hashlib
import hmac
import math
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime

from database import DB_NAME
from portfolio import Portfolio
from transaction import Transaction


PASSWORD_SCHEME = "scrypt"
MAX_USERNAME_LENGTH = 40
MAX_PASSWORD_LENGTH = 256
MAX_SHARES = 1_000_000


def _hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1, dklen=32
    ).hex()
    return f"{PASSWORD_SCHEME}$16384$8$1${salt}${digest}"


def _password_matches(password, stored_password):
    if not stored_password.startswith(f"{PASSWORD_SCHEME}$"):
        return hmac.compare_digest(password, stored_password)
    try:
        _, work_factor, block_size, parallelism, salt, expected = (
            stored_password.split("$", 5)
        )
        actual = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt),
            n=int(work_factor),
            r=int(block_size),
            p=int(parallelism),
            dklen=32,
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


class User:
    def __init__(self, id, username, _password, balance=10_000):
        self.id = id
        self.username = username
        self.balance = balance
        self.portfolio = Portfolio(self.id)
        self.transaction_history = Transaction(self.id)

    @classmethod
    def register(cls, username, password):
        username = username.strip().lower()
        valid_username = 1 <= len(username) <= MAX_USERNAME_LENGTH
        valid_password = 8 <= len(password) <= MAX_PASSWORD_LENGTH
        if not valid_username or not valid_password:
            return False

        try:
            with closing(sqlite3.connect(DB_NAME)) as connection:
                cursor = connection.cursor()
                stored_password = _hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                    (username, stored_password, 10_000),
                )
                connection.commit()
                return cls(cursor.lastrowid, username, stored_password, 10_000)
        except sqlite3.IntegrityError:
            return False

    @classmethod
    def login(cls, username, password):
        username = username.strip().lower()
        valid_username = 1 <= len(username) <= MAX_USERNAME_LENGTH
        valid_password = 1 <= len(password) <= MAX_PASSWORD_LENGTH
        if not valid_username or not valid_password:
            return False
        with closing(sqlite3.connect(DB_NAME)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, username, password, balance FROM users "
                "WHERE LOWER(username) = ?",
                (username,),
            )
            user_data = cursor.fetchone()
            if not user_data or not _password_matches(password, user_data[2]):
                return False

            if not user_data[2].startswith(f"{PASSWORD_SCHEME}$"):
                stored_password = _hash_password(password)
                cursor.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (stored_password, user_data[0]),
                )
                connection.commit()
                user_data = (*user_data[:2], stored_password, user_data[3])
            return cls(*user_data)

    def buy_stock(self, stock, quantity):
        if not _valid_trade(stock, quantity):
            return False
        total_price = stock.price * quantity
        if total_price > self.balance:
            return False

        with closing(sqlite3.connect(DB_NAME)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT quantity, price FROM portfolio WHERE user_id = ? AND symbol = ?",
                (self.id, stock.symbol),
            )
            existing = cursor.fetchone()
            if existing:
                new_quantity = existing[0] + quantity
                average_price = (
                    existing[0] * existing[1] + quantity * stock.price
                ) / new_quantity
                cursor.execute(
                    "UPDATE portfolio SET quantity = ?, price = ?, name = ? "
                    "WHERE user_id = ? AND symbol = ?",
                    (new_quantity, average_price, stock.name, self.id, stock.symbol),
                )
            else:
                cursor.execute(
                    "INSERT INTO portfolio (user_id, symbol, name, quantity, price) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (self.id, stock.symbol, stock.name, quantity, stock.price),
                )

            new_balance = self.balance - total_price
            cursor.execute(
                "UPDATE users SET balance = ? WHERE id = ?", (new_balance, self.id)
            )
            _record_transaction(cursor, self.id, stock, quantity, "BUY")
            connection.commit()

        self.balance = new_balance
        return True

    def sell_stock(self, stock, quantity):
        if not _valid_trade(stock, quantity):
            return False

        with closing(sqlite3.connect(DB_NAME)) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?",
                (self.id, stock.symbol),
            )
            existing = cursor.fetchone()
            if not existing or quantity > existing[0]:
                return False

            remaining = existing[0] - quantity
            if remaining:
                cursor.execute(
                    "UPDATE portfolio SET quantity = ? WHERE user_id = ? AND symbol = ?",
                    (remaining, self.id, stock.symbol),
                )
            else:
                cursor.execute(
                    "DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                    (self.id, stock.symbol),
                )

            new_balance = self.balance + stock.price * quantity
            cursor.execute(
                "UPDATE users SET balance = ? WHERE id = ?", (new_balance, self.id)
            )
            _record_transaction(cursor, self.id, stock, quantity, "SELL")
            connection.commit()

        self.balance = new_balance
        return True

def _valid_trade(stock, quantity):
    return (
        isinstance(quantity, int)
        and not isinstance(quantity, bool)
        and 0 < quantity <= MAX_SHARES
        and isinstance(stock.price, (int, float))
        and math.isfinite(stock.price)
        and stock.price > 0
    )


def _record_transaction(cursor, user_id, stock, quantity, transaction_type):
    cursor.execute(
        "INSERT INTO transactions (user_id, stock, quantity, price, type, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            user_id,
            stock.symbol,
            quantity,
            stock.price,
            transaction_type,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
