import os
import time
import schedule
import boto3
from tempfile import NamedTemporaryFile
from ocr import get_text_from_yandex
from parser import parse_invoice_text
from db import save_invoice_to_db
from gsheet import write_invoice_to_gsheet

BUCKET_NAME = os.environ["YANDEX_BUCKET_NAME"]
PREFIX = os.environ.get("YANDEX_INVOICE_PREFIX", "invoices/")
FOLDER_ID = os.environ["YANDEX_FOLDER_ID"]
IAM_TOKEN = os.environ["YANDEX_IAM_TOKEN"]

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=os.environ["YANDEX_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["YANDEX_SECRET_ACCESS_KEY"]
)

def already_processed(filename):
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432")
    )
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM invoices_ocr_data WHERE filename = %s", (filename,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def process_new_files():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
    if 'Contents' not in response:
        print("[INFO] Нет новых файлов в", PREFIX)
        return

    for obj in response['Contents']:
        key = obj['Key']
        if not key.endswith(('.jpg', '.jpeg', '.png')):
            continue

        filename = os.path.basename(key)
        if already_processed(filename):
            continue

        print(f"[🟡] Обработка нового файла: {filename}")
        tmp_file = NamedTemporaryFile(delete=False)
        s3.download_file(BUCKET_NAME, key, tmp_file.name)

        try:
            text = get_text_from_yandex(tmp_file.name, IAM_TOKEN, FOLDER_ID)
            parsed = parse_invoice_text(text)

            data = {
                "filename": filename,
                "raw_text": text,
                "parsed_date": parsed.get("date"),
                "supplier": parsed.get("supplier"),
                "total_sum": parsed.get("total_sum"),
                "source_path": key
            }

            save_invoice_to_db(data)
            write_invoice_to_gsheet(data)
            print(f"[✅] Успешно обработан: {filename}")

        except Exception as e:
            print(f"[⛔] Ошибка при обработке {filename}: {e}")
        finally:
            tmp_file.close()
            os.remove(tmp_file.name)

interval = int(os.environ.get("SCAN_INTERVAL_SECONDS", 600))
schedule.every(interval).seconds.do(process_new_files)

print(f"[🚀] Запущен сканер. Интервал: {interval} секунд")
process_new_files()  # первичная проверка при запуске

while True:
    schedule.run_pending()
    time.sleep(1)
