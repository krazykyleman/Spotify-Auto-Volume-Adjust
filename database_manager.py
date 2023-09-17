import psycopg2
import os

from psycopg2 import pool


DATABASE_URL = os.environ['DATABASE_URL']

# Create a connection pool
db_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)

def get_conn():
    return db_pool.getconn()

def release_conn(conn):
    db_pool.putconn(conn)

def setup_database():
    conn = get_conn()

    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        id SERIAL PRIMARY KEY,
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL
    );
    ''')
    conn.close()
    release_conn(conn)

def store_tokens(access_token, refresh_token):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tokens (access_token, refresh_token) VALUES (%s, %s)
            ON CONFLICT (id) DO UPDATE SET access_token = %s, refresh_token = %s
        """, (access_token, refresh_token, access_token, refresh_token))
        
        conn.commit()
        release_conn(conn)
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
