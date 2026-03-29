import sqlite3
import config

def get_db():
    try:
        from flask import current_app
        db_path = current_app.config.get('DATABASE_PATH', config.DATABASE_PATH)
    except RuntimeError:
        db_path = config.DATABASE_PATH
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # return rows as dicts
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # folders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # bookmarks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            folder_id   INTEGER NOT NULL,
            recipe_id   INTEGER NOT NULL,
            rating      INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)   REFERENCES users(id),
            FOREIGN KEY (folder_id) REFERENCES folders(id),
            UNIQUE(folder_id, recipe_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized!")

if __name__ == "__main__":
    init_db()