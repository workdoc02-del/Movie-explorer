from database import get_connection

def init():
    conn = get_connection()
    cursor = conn.cursor()
    tables = [
        "CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY, media_id TEXT UNIQUE, title TEXT, poster TEXT, media_type TEXT)",
        "CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY, media_id TEXT UNIQUE, title TEXT, poster TEXT, media_type TEXT)",
        "CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, media_id TEXT, rating INTEGER, review TEXT)",
        "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, media_id TEXT, title TEXT, poster TEXT, media_type TEXT, watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS collections (id INTEGER PRIMARY KEY AUTOINCREMENT, collection_name TEXT, media_id TEXT, title TEXT, poster TEXT, media_type TEXT)"
    ]
    for table in tables:
        cursor.execute(table)
    conn.commit()
    conn.close()
    print("✅ All Week 1-4 Tables Initialized.")

if __name__ == "__main__":
    init()