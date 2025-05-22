import psycopg2
import os

def save_invoice_to_db(data: dict):
    print("[DEBUG] Соединение с PostgreSQL установлено")
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432")
    )
    cur = conn.cursor()
    print("[DEBUG] Соединение с PostgreSQL установлено")



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


def init_db_schema():
    print("[INIT] Проверка и обновление структуры таблицы invoices_ocr_data")
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432")
    )
    cur = conn.cursor()

    # 1. Создание таблицы, если её нет
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

    # 2. Получение текущих колонок
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices_ocr_data'")
    existing_cols = {row[0] for row in cur.fetchall()}

    # 3. Ожидаемые поля
    expected_cols = {
        "id", "filename", "raw_text", "parsed_date", "supplier", "total_sum", "source_path"
    }

    # 4. Добавление недостающих колонок
    for col in expected_cols - existing_cols:
        if col == "id":
            continue  # ID уже создан
        print(f"[MIGRATION] Добавляется колонка: {col}")
        cur.execute(f"ALTER TABLE invoices_ocr_data ADD COLUMN {col} TEXT")

    # 5. Удаление лишних колонок (если нужно)
    for col in existing_cols - expected_cols:
        if col == "id":
            continue  # Не трогаем id
        print(f"[MIGRATION] Удаляется лишняя колонка: {col}")
        cur.execute(f"ALTER TABLE invoices_ocr_data DROP COLUMN {col}")

    conn.commit()
    cur.close()
    conn.close()