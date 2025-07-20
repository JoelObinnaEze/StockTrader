import sqlite3
from datetime import datetime

DB_NAME = 'data.db'

class Transaction:
    def __init__(self, user_id):
        self.user_id = user_id

    def add_transaction(self, stock, quantity, price, transaction_type):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, stock, quantity, price, type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.user_id, stock, quantity, price, transaction_type, timestamp))
            conn.commit()

    def get_transactions(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT stock, quantity, price, type, timestamp
                FROM transactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (self.user_id,))
            rows = cursor.fetchall()
            return [
                {
                    'stock': row[0],
                    'quantity': row[1],
                    'price': row[2],
                    'type': row[3],
                    'timestamp': row[4]
                }
                for row in rows
            ]

