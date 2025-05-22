import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from io import StringIO


HEADERS = ["filename", "raw_text", "parsed_date", "supplier", "total_sum", "source_path"]

def authorize_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_creds = os.environ["GSPREAD_CREDENTIALS_JSON"]
    parsed = json.loads(json_creds)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(parsed, scope)
    return gspread.authorize(creds)

def get_or_create_sheet():
    client = authorize_gsheet()
    try:
        sheet = client.open("Invoices OCR").sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create("Invoices OCR").sheet1
        sheet.append_row(HEADERS)
    return sheet

def write_invoice_to_gsheet(data: dict):
    sheet = get_or_create_sheet()
    sheet.append_row([
        data['filename'],
        data['raw_text'],
        data.get('parsed_date'),
        data.get('supplier'),
        data.get('total_sum'),
        data['source_path']
    ])
