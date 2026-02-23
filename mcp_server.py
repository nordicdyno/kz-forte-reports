"""MCP server exposing ForteBank invoice parsing and spending analytics."""

import json
import sys
from pathlib import Path

# Prevent stray stdout (e.g. newlines from libs or exception handlers) from
# corrupting the JSON-RPC stdio stream; MCP client expects one JSON object per line.
_real_stdout = sys.stdout

class _StdoutFilter:
    """Forward stdout but drop whitespace-only writes that would break JSON-RPC."""
    __slots__ = ("_real",)

    def __init__(self, real):
        self._real = real

    @property
    def buffer(self):
        return self._real.buffer

    def write(self, s: str):
        if s and s.strip() == "":
            return
        self._real.write(s)

    def flush(self):
        self._real.flush()

    def __getattr__(self, name):
        return getattr(self._real, name)

sys.stdout = _StdoutFilter(_real_stdout)

from mcp.server.fastmcp import FastMCP

from budged import (
    parse_pdf,
    parse_transactions,
    group_by_description_and_mcc,
    group_by_description_and_mcc_group,
    compute_purchase_totals,
    format_raw_report,
    format_aggregated,
    mcc2name,
    mcc_groups,
    SORT_BY_SUM,
    SORT_BY_NAME,
    SORT_BY_DATE,
    FMT_ASCII,
    FMT_SIMPLE,
)

mcp = FastMCP(
    "Budged – ForteBank Statement Analyzer",
    instructions=(
        "This server parses ForteBank (Kazakhstan) PDF card statements "
        "and provides spending analytics. Use list_statements to discover "
        "available PDF files, parse_invoice to extract transactions, "
        "spending_summary to get categorized breakdowns, and "
        "parse_statement_raw to get plain-text/markdown output suitable "
        "for uploading or pasting into local chatbot apps."
    ),
)

DEFAULT_DIR = "./statements"


@mcp.tool()
def list_statements(directory: str = DEFAULT_DIR) -> str:
    """List available PDF statement files in a directory.

    Args:
        directory: Path to the folder containing PDF statements.
                   Defaults to ./statements.
    """
    pdf_dir = Path(directory).expanduser().resolve()
    if not pdf_dir.is_dir():
        return json.dumps({"error": f"Directory not found: {pdf_dir}"})

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    return json.dumps({
        "directory": str(pdf_dir),
        "files": [{"name": p.name, "path": str(p)} for p in pdfs],
        "count": len(pdfs),
    }, indent=2)


@mcp.tool()
def parse_invoice(pdf_path: str) -> str:
    """Parse a ForteBank PDF statement and return structured transaction data.

    Each transaction includes date, amount (KZT), description, merchant,
    MCC code, bank, and payment method where available.

    Args:
        pdf_path: Absolute or relative path to the PDF file.
    """
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {path}"})

    raw = parse_pdf(path)
    parsed = parse_transactions(raw)

    transactions = []
    for row in parsed:
        transactions.append({
            "date": row["Date"],
            "amount_kzt": row["Sum"],
            "description": row["Description"],
            "merchant": row["Details"]["merchant"],
            "mcc_code": row["Details"]["mcc"],
            "mcc_name": mcc2name.get(row["Details"]["mcc"], None) if row["Details"]["mcc"] else None,
            "bank": row["Details"]["bank"],
            "payment_method": row["Details"]["payment_method"],
            "receiver_account": row["Details"]["receiver_account"],
            "raw_details": row["Details"]["raw"],
        })

    totals = compute_purchase_totals(parsed)

    return json.dumps({
        "file": path.name,
        "transaction_count": len(transactions),
        "transactions": transactions,
        "totals": totals,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def spending_summary(
    pdf_path: str,
    group_by: str = "group",
    sort_by: str = "sum",
    output_format: str = "json",
) -> str:
    """Get a categorized spending summary from a ForteBank PDF statement.

    Args:
        pdf_path: Path to the PDF statement file.
        group_by: How to group spending — "group" for broad categories
                  (Food & Dining, Transport, etc.) or "mcc" for individual
                  MCC merchant codes. Default: "group".
        sort_by: Sort order — "sum" (default) or "name".
        output_format: "json" for structured data, "ascii" for a
                       formatted table, "simple" for plain text. Default: "json".
    """
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {path}"})

    raw = parse_pdf(path)
    parsed = parse_transactions(raw)

    if group_by == "mcc":
        agg = group_by_description_and_mcc(parsed)
        title = "Grouped by Description and MCC Name"
    else:
        agg = group_by_description_and_mcc_group(parsed)
        title = "Grouped by Description and MCC Group"

    if sort_by not in (SORT_BY_SUM, SORT_BY_NAME):
        sort_by = SORT_BY_SUM

    if output_format in (FMT_ASCII, FMT_SIMPLE):
        return format_aggregated(agg, title, sort_by, output_format)

    categories: dict[str, float] = {}
    for (desc, category), total in agg.items():
        if desc == "Saved with bonuses":
            continue
        categories.setdefault(category, 0.0)
        categories[category] += total

    totals = compute_purchase_totals(parsed)

    return json.dumps({
        "file": path.name,
        "group_by": group_by,
        "categories": dict(sorted(categories.items(), key=lambda x: x[1])),
        "totals": totals,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def raw_transactions_report(
    pdf_path: str,
    sort_by: str = "sum",
    output_format: str = "ascii",
) -> str:
    """Get a formatted list of all transactions from a ForteBank PDF statement.

    Args:
        pdf_path: Path to the PDF statement file.
        sort_by: Sort order — "sum" (default), "name", or "date".
        output_format: "ascii" for box-drawing table (default),
                       "simple" for plain text.
    """
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {path}"})

    raw = parse_pdf(path)
    parsed = parse_transactions(raw)

    if sort_by not in (SORT_BY_SUM, SORT_BY_NAME, SORT_BY_DATE):
        sort_by = SORT_BY_SUM
    fmt = output_format if output_format in (FMT_ASCII, FMT_SIMPLE) else FMT_ASCII

    return format_raw_report(parsed, sort_by, fmt)


@mcp.tool()
def get_categories() -> str:
    """Return the MCC code mappings and spending category groups used for classification."""
    return json.dumps({
        "mcc_codes": mcc2name,
        "category_groups": mcc_groups,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def parse_statement_raw(pdf_path: str) -> str:
    """Parse a ForteBank PDF statement and return raw transactions as plain text.

    Output is formatted for pasting or uploading into local chatbot apps
    (e.g. Ollama, Open WebUI, LM Studio): one block of markdown-style text
    with a simple table of date, amount, description, and details. No JSON —
    so you can save it as .txt/.md and upload in the chat interface, or
    paste directly into the conversation.

    Args:
        pdf_path: Absolute or relative path to the ForteBank PDF file.
    """
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found: {path}"

    raw = parse_pdf(path)
    if not raw:
        return f"# ForteBank statement: {path.name}\n\nNo transactions found in PDF."

    lines = [
        f"# ForteBank statement: {path.name}",
        f"Transactions: {len(raw)}",
        "",
        "| Date | Sum | Description | Details |",
        "|------|-----|--------------|----------|",
    ]
    for date, sum_str, description, details in raw:
        # Escape pipe chars in cells so the table doesn't break
        description_safe = (description or "").replace("|", "\\|").replace("\n", " ")
        details_safe = (details or "").replace("|", "\\|").replace("\n", " ").strip()
        if len(details_safe) > 80:
            details_safe = details_safe[:77] + "..."
        lines.append(f"| {date} | {sum_str} | {description_safe} | {details_safe} |")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
