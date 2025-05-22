import re

def parse_invoice_text(text: str) -> dict:
    date_match = re.search(r'(\\d{2}[./-]\\d{2}[./-]\\d{4})', text)
    sum_match = re.search(r'Итого.*?(\\d+[.,]?\\d*)', text, re.IGNORECASE)
    supplier_match = re.search(r'Поставщик:?.*?([\\w\\s\"\\.,]+)', text)

    return {
        "date": date_match.group(1) if date_match else None,
        "total_sum": sum_match.group(1).replace(",", ".") if sum_match else None,
        "supplier": supplier_match.group(1).strip() if supplier_match else None
    }
