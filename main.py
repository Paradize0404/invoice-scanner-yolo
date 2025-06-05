import os
import requests
import psycopg2
from datetime import datetime

API_LOGIN   = os.getenv("IIKO_API_LOGIN")
PGHOST      = os.getenv("PGHOST")
PGDATABASE  = os.getenv("PGDATABASE")
PGUSER      = os.getenv("PGUSER")
PGPASSWORD  = os.getenv("PGPASSWORD")
PGPORT      = os.getenv("PGPORT", 5432)

def get_access_token(api_login):
    url = "https://api-ru.iiko.services/api/1/access_token"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json={"apiLogin": api_login}, headers=headers)
    response.raise_for_status()
    return response.json()["token"]

def save_token_to_db(token):
    conn = psycopg2.connect(
        host=PGHOST,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        port=PGPORT
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iiko_access_tokens (
            id INT PRIMARY KEY DEFAULT 1,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        INSERT INTO iiko_access_tokens (id, token)
        VALUES (1, %s)
        ON CONFLICT (id) DO UPDATE
        SET token = EXCLUDED.token, created_at = CURRENT_TIMESTAMP;
    """, (token,))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    token = get_access_token(API_LOGIN)
    save_token_to_db(token)
    print(f"✅ Token saved/updated at {datetime.now()}")
