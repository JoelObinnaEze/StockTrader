import sqlite3

DB_NAME = 'data.db'

def create_tables():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Create users table (if not already created)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL NOT NULL
        )
    ''')

    # Create portfolio table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''                 
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock TEXT,
            quantity INTEGER,
            price REAL,
            type TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_tables()
