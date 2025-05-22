import psycopg2
import os

def save_invoice_to_db(data: dict):
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432")
    )
    cur = conn.cursor()

    # ✅ Создание таблицы, если её ещё нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices_ocr_data (
            id SERIAL PRIMARY KEY,
            filename TEXT UNIQUE,
            raw_text TEXT,
            parsed_date TEXT,
            supplier TEXT,
            total_sum TEXT,
            source_path TEXT
        )
    """)

    # 📥 Вставка данных
    cur.execute("""
        INSERT INTO invoices_ocr_data (filename, raw_text, parsed_date, supplier, total_sum, source_path)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (filename) DO NOTHING
    """, (
        data['filename'],
        data['raw_text'],
        data.get('parsed_date'),
        data.get('supplier'),
        data.get('total_sum'),
        data['source_path']
    ))

    conn.commit()
    cur.close()
    conn.close()
