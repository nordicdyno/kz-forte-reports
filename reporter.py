import re
from collections import defaultdict
from pathlib import Path

import pdfplumber

# 1st dictionary: MCC Codes to Short Names
mcc2name = {
    "5411": "Grocery Stores, Supermarkets",
    "5814": "Fast Food Restaurants",
    "5812": "Eating Places, Restaurants",
    "5977": "Cosmetic Stores",
    "5943": "Stationery, Office Supplies",
    "5199": "Nondurable Goods",
    "4121": "Taxicabs and Limousines",
    "5995": "Pet Shops",
    "5691": "Men's and Women's Clothing Stores",
    "5200": "Home Supply Warehouse Stores",
    "5311": "Department Stores",
    "7941": "Athletic Fields, Commercial Sports",
    "5262": "Marketplaces",
    "5912": "Drug Stores and Pharmacies",
    "5541": "Service Stations (Gas)",
    "8099": "Medical Services",
    "5331": "Variety Stores",
    "4829": "Money Orders / Wire Transfer",
    "4215": "Courier Services",
    "1750": "Carpentry Contractors",
    "7832": "Motion Picture Theaters",
    "5641": "Children's and Infant's Wear Stores",
    "3068": "Airlines",
    "5499": "Miscellaneous Food Stores",
    "8071": "Dental and Medical Laboratories"
}

# 2nd dictionary: MCC Names grouped into broader categories
mccGroups = {
    "Food & Dining": [
        "Grocery Stores, Supermarkets", "Fast Food Restaurants", 
        "Eating Places, Restaurants", "Miscellaneous Food Stores"
    ],
    "Transport": [
        "Taxicabs and Limousines", "Airlines", "Service Stations (Gas)"
    ],
    "Shopping": [
        "Cosmetic Stores", "Stationery, Office Supplies", "Nondurable Goods", 
        "Men's and Women's Clothing Stores", "Department Stores", "Marketplaces", 
        "Variety Stores", "Children's and Infant's Wear Stores", "Home Supply Warehouse Stores"
    ],
    "Health & Beauty": [
        "Drug Stores and Pharmacies", "Medical Services", "Dental and Medical Laboratories"
    ],
    "Entertainment": [
        "Athletic Fields, Commercial Sports", "Motion Picture Theaters"
    ],
    "Services": [
        "Courier Services", "Carpentry Contractors", "Money Orders / Wire Transfer"
    ],
    "Pets": [
        "Pet Shops"
    ]
}

# Invert mccGroups for O(1) lookups during aggregation
name_to_group = {}
for group, names in mccGroups.items():
    for name in names:
        name_to_group[name] = group

def parse_sum(sum_str):
    """Converts a string like '-30000.00 KZT' to a float -30000.0"""
    clean_str = re.sub(r'[^\d\.-]', '', sum_str)
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def parse_details(details_str):
    """Parses the Details string into a structured dictionary map."""
    details_map = {
        "raw": details_str.strip(),
        "merchant": None,
        "bank": None,
        "mcc": None,
        "payment_method": None,
        "receiver_account": None
    }
    
    # Check for MCC
    mcc_match = re.search(r'MCC:\s*(\d{4})|МСС:\s*(\d{4})', details_str, re.IGNORECASE)
    if mcc_match:
        details_map["mcc"] = mcc_match.group(1) or mcc_match.group(2)
        
    # Check for Apple Pay
    if "APPLE PAY" in details_str.upper():
        details_map["payment_method"] = "APPLE PAY"
        
    # Check for Bank
    if "JSC Halyk Bank" in details_str or "Halyk Bank" in details_str:
        details_map["bank"] = "Halyk Bank"
    elif "Kaspi Bank" in details_str:
        details_map["bank"] = "Kaspi Bank"
    elif "Freedom Bank" in details_str:
        details_map["bank"] = "Freedom Bank"
    elif "Jusan Bank" in details_str:
        details_map["bank"] = "Jusan Bank"
    elif "Bereke Bank" in details_str:
        details_map["bank"] = "Bereke Bank"
    elif "BCC" in details_str:
        details_map["bank"] = "BCC"
    
    # Check for receiver account (Transfers)
    receiver_match = re.search(r'Receiver:\s*([\d\*]+)', details_str)
    if receiver_match:
        details_map["receiver_account"] = receiver_match.group(1)
        
    # Attempt to extract merchant name (usually everything before the first comma)
    parts = details_str.split(',')
    if len(parts) > 1 and not receiver_match:
        details_map["merchant"] = parts[0].strip()
        
    return details_map

def parse_row(date, sum_str, description, details_str):
    """Parses a single row into a structured dictionary."""
    return {
        "Date": date.strip(),
        "Sum": parse_sum(sum_str),
        "Description": description.strip(),
        "Details": parse_details(details_str)
    }

def group_by_description_and_mcc(data):
    """
    Summarizes records' Sum by (Description, MCC_Short_Name).
    Returns a dictionary with keys as tuples: (Description, MCC_Name).

    "Purchase with bonuses" is folded into "Purchase" (offsets spend),
    and a separate "Saved with bonuses" row tracks the bonus totals.
    """
    aggregated = defaultdict(float)
    
    for row in data:
        desc = row["Description"]
        mcc_code = row["Details"]["mcc"]
        
        mcc_name = mcc2name.get(mcc_code, "Unknown/No MCC") if mcc_code else "No MCC"
        
        if desc == "Purchase with bonuses":
            aggregated[("Purchase", mcc_name)] += row["Sum"]
            aggregated[("Saved with bonuses", mcc_name)] += row["Sum"]
        else:
            aggregated[(desc, mcc_name)] += row["Sum"]
        
    return dict(aggregated)

def group_by_description_and_mcc_group(data):
    """
    Summarizes records' Sum by (Description, MCC_Group).
    Reuses group_by_description_and_mcc.
    """
    # 1. Get the base aggregation by exact MCC name
    base_aggregation = group_by_description_and_mcc(data)
    
    # 2. Roll up the MCC names into their respective groups
    group_aggregated = defaultdict(float)
    
    for (desc, mcc_name), total_sum in base_aggregation.items():
        if mcc_name == "No MCC":
            group_name = "Transfers/Other"
        else:
            group_name = name_to_group.get(mcc_name, "Other Uncategorized")
            
        key = (desc, group_name)
        group_aggregated[key] += total_sum
        
    return dict(group_aggregated)

DATE_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
SUM_PATTERN = re.compile(r"^-?[\d,.]+\s+KZT$")


def _is_data_row(row: list) -> bool:
    """Return True if a table row contains actual transaction data."""
    if not row or len(row) < 4:
        return False
    date, sum_str, desc, _ = row[0], row[1], row[2], row[3]
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

    Returns a list of (date, sum, description, details) tuples — the same
    shape as the ``raw_data`` list used by the rest of this module.
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


SORT_BY_SUM = "sum"
SORT_BY_NAME = "name"
SORT_BY_DATE = "date"

FMT_SIMPLE = "simple"
FMT_ASCII = "ascii"

REPORT_RAW = "raw"
REPORT_MCC = "mcc"
REPORT_GROUP = "group"


def _sort_key(item, sort_by=SORT_BY_SUM):
    (desc, category), total = item
    if sort_by == SORT_BY_NAME:
        return (desc, category)
    return (total,)


# ---------------------------------------------------------------------------
# Generic ASCII table renderer
# ---------------------------------------------------------------------------

def _stringify(value) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if value is None:
        return ""
    return str(value)


def format_ascii_table(headers: list[str], rows: list[list], title: str | None = None) -> str:
    """Render *headers* and *rows* as a box-drawing ASCII table."""
    str_rows = [[_stringify(c) for c in row] for row in rows]
    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def sep(left, mid, right, fill="─"):
        return left + mid.join(fill * (w + 2) for w in col_widths) + right

    def data_line(cells):
        parts = []
        for i, cell in enumerate(cells):
            if isinstance(cell, str) and (cell.replace(",", "").replace(".", "").replace("-", "").isdigit()):
                parts.append(cell.rjust(col_widths[i]))
            else:
                parts.append(cell.ljust(col_widths[i]))
        return "│ " + " │ ".join(parts) + " │"

    lines: list[str] = []
    if title:
        lines.append(title)
    lines.append(sep("┌", "┬", "┐"))
    lines.append(data_line(headers))
    lines.append(sep("├", "┼", "┤"))
    for row in str_rows:
        lines.append(data_line(row))
    lines.append(sep("└", "┴", "┘"))
    return "\n".join(lines)


def print_table(data, title: str | None = None):
    """
    Pretty-print any of the common data shapes used in this module.

    Supported shapes:
    - ``list[dict]``  – e.g. *parsed_data* (each dict becomes a row)
    - ``list[tuple]`` – e.g. raw tuples from *parse_pdf*
    - ``dict[tuple, float]`` – e.g. *mcc_agg* / *group_agg*
    """
    if isinstance(data, dict):
        sample_key = next(iter(data))
        if isinstance(sample_key, tuple):
            n = len(sample_key)
            headers = [f"Key{i+1}" for i in range(n)] + ["Value"]
            rows = [list(k) + [v] for k, v in data.items()]
        else:
            headers = ["Key", "Value"]
            rows = [[k, v] for k, v in data.items()]
    elif isinstance(data, list) and data:
        sample = data[0]
        if isinstance(sample, dict):
            headers = list(sample.keys())
            rows = []
            for item in data:
                row = []
                for h in headers:
                    val = item.get(h)
                    if isinstance(val, dict):
                        val = val.get("raw") or str(val)
                    row.append(val)
                rows.append(row)
        elif isinstance(sample, (tuple, list)):
            headers = [f"Col{i+1}" for i in range(len(sample))]
            rows = [list(t) for t in data]
        else:
            headers = ["Value"]
            rows = [[v] for v in data]
    else:
        headers = ["Value"]
        rows = [[str(data)]]

    print(format_ascii_table(headers, rows, title=title))


# ---------------------------------------------------------------------------
# Aggregation printer (with format switch)
# ---------------------------------------------------------------------------

def print_aggregated(
    agg: dict,
    title: str,
    sort_by: str = SORT_BY_SUM,
    fmt: str = FMT_SIMPLE,
):
    """Print an aggregation dict with summary lines for Purchase and bonuses."""
    sorted_items = sorted(agg.items(), key=lambda it: _sort_key(it, sort_by))

    purchase_total = 0.0
    bonuses_total = 0.0
    display_items: list[tuple] = []

    for (desc, category), total in sorted_items:
        if desc == "Saved with bonuses":
            bonuses_total += total
            continue
        if desc == "Purchase":
            purchase_total += total
        display_items.append((desc, category, total))

    if fmt == FMT_ASCII:
        headers = ["Description", "Category", "Sum (KZT)"]
        rows = [list(r) for r in display_items]
        rows.append(["", "", ""])
        rows.append(["Total purchases", "", purchase_total])
        rows.append(["Saved with bonuses", "", bonuses_total])
        rows.append(["Net purchases", "", purchase_total + bonuses_total])
        print(format_ascii_table(headers, rows, title=f"{title} (sorted by {sort_by})"))
        print()
    else:
        print(f"--- {title} (sorted by {sort_by}) ---")
        for desc, category, total in display_items:
            print(f"  ({desc}, {category}): {total:.2f} KZT")
        print(f"  {'—' * 40}")
        print(f"  Total purchases:        {purchase_total:.2f} KZT")
        print(f"  Saved with bonuses:     {bonuses_total:.2f} KZT")
        print(f"  Net purchases:          {purchase_total + bonuses_total:.2f} KZT")
        print()


def print_raw_report(
    parsed_data: list[dict],
    sort_by: str = SORT_BY_SUM,
    fmt: str = FMT_ASCII,
):
    """Print every parsed transaction with a summary footer."""
    if sort_by == SORT_BY_DATE:
        sorted_data = sorted(parsed_data, key=lambda r: r["Date"].split(".")[::-1])
    elif sort_by == SORT_BY_SUM:
        sorted_data = sorted(parsed_data, key=lambda r: r["Sum"])
    elif sort_by == SORT_BY_NAME:
        sorted_data = sorted(parsed_data, key=lambda r: (r["Description"], r["Details"]["raw"]))
    else:
        sorted_data = parsed_data

    purchase_total = 0.0
    bonuses_total = 0.0
    grand_total = 0.0
    display_rows: list[tuple] = []

    for row in sorted_data:
        desc = row["Description"]
        amount = row["Sum"]
        grand_total += amount
        if desc == "Purchase with bonuses":
            bonuses_total += amount
            purchase_total += amount
            desc = "Purchase"
        elif desc == "Purchase":
            purchase_total += amount

        mcc = row["Details"]["mcc"] or ""
        receiver = row["Details"]["receiver_account"]
        if receiver:
            label = f"card *{receiver[-4:]}"
        else:
            label = row["Details"]["merchant"] or ""
        display_rows.append((row["Date"], desc, label, mcc, amount))

    if fmt == FMT_ASCII:
        headers = ["Date", "Type", "Description", "MCC", "Sum (KZT)"]
        rows = [list(r) for r in display_rows]
        rows.append(["", "", "", "", ""])
        rows.append(["", "Total purchases", "", "", purchase_total])
        rows.append(["", "Saved with bonuses", "", "", bonuses_total])
        rows.append(["", "Net purchases", "", "", purchase_total - bonuses_total])
        rows.append(["", "Grand total", "", "", grand_total])
        print(format_ascii_table(headers, rows, title=f"Raw Transactions (sorted by {sort_by})"))
        print()
    else:
        print(f"--- Raw Transactions (sorted by {sort_by}) ---")
        for date, desc, label, mcc, amount in display_rows:
            suffix = f"{label} [{mcc}]" if mcc else label or "—"
            print(f"  {date}  {desc:<12}  {amount:>12.2f} KZT  {suffix}")
        print(f"  {'—' * 50}")
        print(f"  Total purchases:        {purchase_total:.2f} KZT")
        print(f"  Saved with bonuses:     {bonuses_total:.2f} KZT")
        print(f"  Net purchases:          {purchase_total - bonuses_total:.2f} KZT")
        print(f"  Grand total:            {grand_total:.2f} KZT")
        print()


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Parse ForteBank PDF statements")
    parser.add_argument(
        "--sort", choices=[SORT_BY_SUM, SORT_BY_NAME, SORT_BY_DATE],
        default=SORT_BY_SUM,
        help="Sort order: sum, name, or date (default: sum). "
             "date is only supported for raw report; mcc/group ignore it and fall back to sum.",
    )
    parser.add_argument(
        "--format", choices=[FMT_SIMPLE, FMT_ASCII], default=FMT_ASCII,
        dest="fmt", help="Output format: simple or ascii table (default: ascii)",
    )
    parser.add_argument(
        "--report", choices=[REPORT_RAW, REPORT_MCC, REPORT_GROUP],
        default=REPORT_GROUP,
        help="Report type: raw transactions, mcc breakdown, or group breakdown (default: group)",
    )
    parser.add_argument(
        "--statements-dir", default="./statements",
        help="Directory containing PDF statements (default: ./statements)",
    )
    args = parser.parse_args()

    pdf_dir = Path(args.statements_dir)
    pdfs = list(pdf_dir.glob("*.pdf"))

    if not pdfs:
        print("No PDF files found in resources/", file=sys.stderr)
        sys.exit(1)

    for pdf_file in pdfs:
        print(f"=== {pdf_file.name} ===")
        raw_data = parse_pdf(pdf_file)
        print(f"Parsed {len(raw_data)} transactions\n")

        parsed_data = [parse_row(d, s, desc, det) for d, s, desc, det in raw_data]

        if args.report == REPORT_RAW:
            print_raw_report(parsed_data, args.sort, args.fmt)
        elif args.report == REPORT_MCC:
            agg_sort = args.sort if args.sort != SORT_BY_DATE else SORT_BY_SUM
            mcc_agg = group_by_description_and_mcc(parsed_data)
            print_aggregated(mcc_agg, "Grouped by Description and MCC Name", agg_sort, args.fmt)
        else:
            agg_sort = args.sort if args.sort != SORT_BY_DATE else SORT_BY_SUM
            group_agg = group_by_description_and_mcc_group(parsed_data)
            print_aggregated(group_agg, "Grouped by Description and MCC Group", agg_sort, args.fmt)
