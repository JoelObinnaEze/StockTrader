import sqlite3
from portfolio import Portfolio
from transaction import Transaction
from stock import Stock


class User:
    def __init__(self, id, username, password, balance=10000):
        self.id = id
        self.username = username
        self.password = password
        self.balance = balance
        self.portfolio = Portfolio(self.id)
        self.transaction_history = Transaction(self.id)


    @classmethod
    def register(cls, username, password):
        try:
            with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password, balance) VALUES (?, ?, ?)',
                               (username.lower(), password, 10000))  # Start with a $10,000 balance
                conn.commit()

                # Get the newly created user
                cursor.execute('SELECT id, username, password, balance FROM users WHERE username = ?', (username,))
                user_data = cursor.fetchone()

                if user_data:
                    return cls(*user_data)
        except sqlite3.IntegrityError:
            return False
    
    @classmethod
    def login(cls, username, password):
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()

            # Convert both username in database and input to lowercase
            cursor.execute('SELECT id, username, password, balance FROM users WHERE LOWER(username) = LOWER(?) AND password = ?',
                        (username.lower(), password))
            user_data = cursor.fetchone()

            if user_data:
                return cls(*user_data)
            else:
                return False

    def buy_stock(self, stock, quantity):
        total_price = stock.price * quantity
        if self.balance >= total_price:
            self.balance -= total_price
            self.portfolio.add_stock(stock.symbol, stock.name, quantity, stock.price)
            self.transaction_history.add_transaction(stock.name, quantity, stock.price, 'BUY')
            with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (self.balance, self.id))
                conn.commit()
            return True
        return False

    def sell_stock(self, stock, quantity):
        
        total_price = stock.price * quantity
        self.balance += total_price
        self.portfolio.sell_stock(stock.symbol, quantity)
        self.transaction_history.add_transaction(stock.name, quantity, stock.price, 'SELL')
        with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (self.balance, self.id))
                conn.commit()
        return True
    
    def get_user_balances(user_id):
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id))
            user_balance = cursor.fetchone()
            
            return user_balance[0] if user_balance else 0
