import sqlite3

def setup_database():
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY,
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL
    );
    ''')
    conn.commit()
    conn.close()

def store_tokens(access_token, refresh_token):
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM tokens LIMIT 1")
    token_exists = cursor.fetchone()

    if token_exists:
        cursor.execute("UPDATE tokens SET access_token = ?, refresh_token = ? WHERE id = ?", (access_token, refresh_token, token_exists[0]))
    else:
        cursor.execute("INSERT INTO tokens (access_token, refresh_token) VALUES (?, ?)", (access_token, refresh_token))
    
    conn.commit()
    conn.close()

def fetch_tokens():
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute("SELECT access_token, refresh_token FROM tokens ORDER BY id DESC LIMIT 1")
    tokens = cursor.fetchone()
    conn.close()
    if tokens:
        return {'access_token': tokens[0], 'refresh_token': tokens[1]}
    else:
        return None
