import sqlite3


DB_NAME = 'data.db'

class Portfolio:
    def __init__(self, user_id):
        self.user_id = user_id
        self.holdings = self.load_holdings()

    def load_holdings(self):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute("SELECT symbol, quantity FROM portfolio WHERE user_id = ?", (self.user_id,))
        holdings = cursor.fetchall()

        conn.close()
        return holdings

    def calculate_value(self):
        return sum(
            stock_data['stock'].price * stock_data['quantity']
            for stock_data in self.holdings.values()
        )
    
    
    def get_portfolio(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        cursor.execute('SELECT symbol, name, quantity, price FROM portfolio WHERE user_id = ?', (self.user_id,))
        stocks = cursor.fetchall()

        connection.close()
        return stocks

    def add_stock(self, symbol, name, quantity, price):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        # Check if the stock already exists in the portfolio
        cursor.execute('SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?', (self.user_id, symbol))
        existing = cursor.fetchone()

        if existing:
            new_quantity = existing[0] + quantity
            cursor.execute('UPDATE portfolio SET quantity = ? WHERE user_id = ? AND symbol = ?', 
                           (new_quantity, self.user_id, symbol))
        else:
            cursor.execute('INSERT INTO portfolio (user_id, symbol, name, quantity, price) VALUES (?, ?, ?, ?, ?)', 
                           (self.user_id, symbol, name, quantity, price))

        connection.commit()
        connection.close()

    def sell_stock(self, symbol, quantity):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        cursor.execute('SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?', (self.user_id, symbol))
        existing = cursor.fetchone()

        if existing and existing[0] >= quantity:
            new_quantity = existing[0] - quantity
            if new_quantity > 0:
                cursor.execute('UPDATE portfolio SET quantity = ? WHERE user_id = ? AND symbol = ?', 
                               (new_quantity, self.user_id, symbol))
            else:
                cursor.execute('DELETE FROM portfolio WHERE user_id = ? AND symbol = ?', 
                               (self.user_id, symbol))

            connection.commit()
            connection.close()
            return True
        else:
            connection.close()
            return False
