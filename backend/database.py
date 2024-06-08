import sqlite3

def get_db_connection():
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            subscription TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tenant_profiles (
            user_id INTEGER PRIMARY KEY,
            gender TEXT,
            age INTEGER,
            nationality TEXT,
            race TEXT,
            occupation TEXT,
            work_pass TEXT,
            moving_in_date TEXT,
            length_of_stay TEXT,
            budget TEXT,
            embedding BLOB,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    c.close()
    conn.close()
