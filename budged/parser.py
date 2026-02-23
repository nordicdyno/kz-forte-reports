"""PDF parsing and transaction extraction for ForteBank statements."""

import re
from pathlib import Path

import pdfplumber

DATE_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
SUM_PATTERN = re.compile(r"^-?[\d,.]+\s+KZT$")


def parse_sum(sum_str: str) -> float:
    """Convert a string like '-30000.00 KZT' to a float."""
    clean_str = re.sub(r"[^\d\.\-]", "", sum_str)
    try:
        return float(clean_str)
    except ValueError:
        return 0.0


def parse_details(details_str: str) -> dict:
    """Parse the Details string into a structured dictionary."""
    details_map = {
        "raw": details_str.strip(),
        "merchant": None,
        "bank": None,
        "mcc": None,
        "payment_method": None,
        "receiver_account": None,
    }

    mcc_match = re.search(r"MCC:\s*(\d{4})|МСС:\s*(\d{4})", details_str, re.IGNORECASE)
    if mcc_match:
        details_map["mcc"] = mcc_match.group(1) or mcc_match.group(2)

    if "APPLE PAY" in details_str.upper():
        details_map["payment_method"] = "APPLE PAY"

    bank_keywords = {
        "Halyk Bank": ["JSC Halyk Bank", "Halyk Bank"],
        "Kaspi Bank": ["Kaspi Bank"],
        "Freedom Bank": ["Freedom Bank"],
        "Jusan Bank": ["Jusan Bank"],
        "Bereke Bank": ["Bereke Bank"],
        "BCC": ["BCC"],
    }
    for bank_name, keywords in bank_keywords.items():
        if any(kw in details_str for kw in keywords):
            details_map["bank"] = bank_name
            break

    receiver_match = re.search(r"Receiver:\s*([\d\*]+)", details_str)
    if receiver_match:
        details_map["receiver_account"] = receiver_match.group(1)

    parts = details_str.split(",")
    if len(parts) > 1 and not receiver_match:
        details_map["merchant"] = parts[0].strip()

    return details_map


def parse_row(date: str, sum_str: str, description: str, details_str: str) -> dict:
    """Parse a single raw row into a structured transaction dictionary."""
    return {
        "Date": date.strip(),
        "Sum": parse_sum(sum_str),
        "Description": description.strip(),
        "Details": parse_details(details_str),
    }


def parse_transactions(raw_data: list[tuple[str, str, str, str]]) -> list[dict]:
    """Convert raw PDF tuples into structured transaction dicts."""
    return [parse_row(d, s, desc, det) for d, s, desc, det in raw_data]


def _is_data_row(row: list) -> bool:
    """Return True if a table row contains actual transaction data."""
    if not row or len(row) < 4:
        return False
    date, sum_str = row[0], row[1]
    if not date or not sum_str:
        return False
    return bool(DATE_PATTERN.match(date.strip()) and SUM_PATTERN.match(sum_str.strip()))


def _clean_details(details: str | None) -> str:
    """Remove PDF line-wrapping artifacts from the Details field."""
    if not details:
        return ""
    cleaned = re.sub(r"(?<![,.])\n", " ", details)
    cleaned = re.sub(r"([,.])\n", r"\1 ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def parse_pdf(pdf_path: str | Path) -> list[tuple[str, str, str, str]]:
    """
    Parse a ForteBank card statement PDF into a list of transaction tuples.

    Returns a list of (date, sum, description, details) tuples.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    rows: list[tuple[str, str, str, str]] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not _is_data_row(row):
                        continue
                    date = row[0].strip()
                    sum_str = row[1].strip()
                    description = row[2].strip()
                    details = _clean_details(row[3])
                    rows.append((date, sum_str, description, details))

    return rows
