import sqlite3
from contextlib import closing


DB_NAME = "stocktrader.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    balance REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock TEXT,
    quantity INTEGER,
    price REAL,
    type TEXT,
    timestamp TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""


def initialize_database(database_path=DB_NAME):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(SCHEMA)
        connection.commit()
