import sqlite3
from contextlib import closing

from database import DB_NAME


class Transaction:
    def __init__(self, user_id):
        self.user_id = user_id

    def get_transactions(self):
        with closing(sqlite3.connect(DB_NAME)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT stock, quantity, price, type, timestamp "
                "FROM transactions WHERE user_id = ? "
                "ORDER BY timestamp DESC LIMIT 500",
                (self.user_id,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "stock": row[0],
                    "quantity": row[1],
                    "price": row[2],
                    "type": row[3],
                    "timestamp": row[4],
                }
                for row in rows
            ]

