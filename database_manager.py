import psycopg2
import os

DATABASE_URL = os.environ['DATABASE_URL']

def setup_database():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        id SERIAL PRIMARY KEY,
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL
    );
    ''')
    conn.commit()
    conn.close()

def store_tokens(access_token, refresh_token):
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM tokens LIMIT 1")
        token_exists = cursor.fetchone()

        if token_exists:
            cursor.execute("UPDATE tokens SET access_token = %s, refresh_token = %s WHERE id = %s", (access_token, refresh_token, token_exists[0]))
        else:
            cursor.execute("INSERT INTO tokens (access_token, refresh_token) VALUES (%s, %s)", (access_token, refresh_token))
        
        conn.commit()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")

def fetch_tokens():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute("SELECT access_token, refresh_token FROM tokens ORDER BY id DESC LIMIT 1")
    tokens = cursor.fetchone()
    conn.close()
    if tokens:
        return {'access_token': tokens[0], 'refresh_token': tokens[1]}
    else:
        return None
