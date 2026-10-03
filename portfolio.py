import sqlite3
from contextlib import closing

from database import DB_NAME


class Portfolio:
    def __init__(self, user_id):
        self.user_id = user_id

    def get_portfolio(self):
        with closing(sqlite3.connect(DB_NAME)) as connection:
            return connection.execute(
                "SELECT symbol, name, quantity, price FROM portfolio WHERE user_id = ?",
                (self.user_id,),
            ).fetchall()
