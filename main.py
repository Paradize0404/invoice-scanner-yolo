import os
import requests
import psycopg2
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

API_LOGIN   = os.getenv("IIKO_API_LOGIN")
PGHOST      = os.getenv("PGHOST")
PGDATABASE  = os.getenv("PGDATABASE")
PGUSER      = os.getenv("PGUSER")
PGPASSWORD  = os.getenv("PGPASSWORD")
PGPORT      = os.getenv("PGPORT", 5432)

def get_access_token(api_login):
    url = "https://api-ru.iiko.services/api/1/access_token"
    headers = {"Content-Type": "application/json"}
    logging.info(f"Requesting access token with api_login: {api_login}")
    response = requests.post(url, json={"apiLogin": api_login}, headers=headers)
    response.raise_for_status()
    token = response.json()["token"]
    logging.info(f"Received token: {token}")
    return token

def save_token_to_db(token):
    try:
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
        logging.info("Token saved/updated in database.")
    except Exception as e:
        logging.error(f"Error saving token to DB: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    logging.info("Script started.")
    logging.info(f"IIKO_API_LOGIN: {API_LOGIN}")
    token = get_access_token(API_LOGIN)
    save_token_to_db(token)
    logging.info(f"✅ Token saved/updated at {datetime.now()}")
    print(f"✅ Token saved/updated at {datetime.now()}")
