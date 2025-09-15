import os
import requests
import psycopg2
from datetime import datetime
import logging
import sys

# Настройка логирования
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,   # подробный уровень
    format="%(asctime)s %(levelname)s: %(message)s"
)

API_LOGIN   = os.getenv("IIKO_API_LOGIN")
PGHOST      = os.getenv("PGHOST")
PGDATABASE  = os.getenv("PGDATABASE")
PGUSER      = os.getenv("PGUSER")
PGPASSWORD  = os.getenv("PGPASSWORD")
PGPORT      = os.getenv("PGPORT", 5432)


def mask_token(token: str) -> str:
    if not token:
        return "<empty>"
    return f"{token[:4]}...{token[-4:]}(len={len(token)})"


def get_access_token(api_login):
    url = "https://api-ru.iiko.services/api/1/access_token"
    headers = {"Content-Type": "application/json"}

    logging.debug(f"[API] URL={url}, headers={headers}, payload={{'apiLogin': '{api_login}'}}")

    try:
        response = requests.post(url, json={"apiLogin": api_login}, headers=headers, timeout=15)
        logging.debug(f"[API] Response status={response.status_code}, headers={dict(response.headers)}")
        response.raise_for_status()
        data = response.json()
        logging.debug(f"[API] Response JSON={data}")
    except Exception as e:
        logging.error(f"[API] Error during request: {e}", exc_info=True)
        raise

    token = data.get("token")
    if not token:
        logging.error(f"[API] No token in response JSON: {data}")
        raise RuntimeError("Token not found in response")

    logging.info(f"[API] Received token: {mask_token(token)}")
    return token


def save_token_to_db(token):
    logging.debug(f"[DB] Connecting to {PGUSER}@{PGHOST}:{PGPORT}/{PGDATABASE}")

    try:
        conn = psycopg2.connect(
            host=PGHOST,
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            port=PGPORT
        )
        cur = conn.cursor()
        logging.debug("[DB] Connection established, creating table if not exists...")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS iiko_access_tokens (
                id INT PRIMARY KEY DEFAULT 1,
                token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logging.debug("[DB] Table ensured.")

        cur.execute("""
            INSERT INTO iiko_access_tokens (id, token)
            VALUES (1, %s)
            ON CONFLICT (id) DO UPDATE
            SET token = EXCLUDED.token, created_at = CURRENT_TIMESTAMP;
        """, (token,))
        conn.commit()

        logging.info("[DB] Token saved/updated in database.")
    except Exception as e:
        logging.error(f"[DB] Error saving token: {e}", exc_info=True)
        raise
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    logging.info("=== Script started ===")
    logging.debug(f"[ENV] IIKO_API_LOGIN={API_LOGIN}, "
                  f"PGHOST={PGHOST}, PGDATABASE={PGDATABASE}, "
                  f"PGUSER={PGUSER}, PGPORT={PGPORT}")

    try:
        token = get_access_token(API_LOGIN)
        save_token_to_db(token)
        logging.info(f"✅ Token saved/updated at {datetime.now()}")
        print(f"✅ Token saved/updated at {datetime.now()}")
    except Exception as e:
        logging.error(f"❌ Script failed: {e}", exc_info=True)
        print(f"❌ Script failed: {e}", file=sys.stderr)
        sys.exit(1)
