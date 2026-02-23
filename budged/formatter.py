"""Report formatting: ASCII tables and text output."""

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
            if isinstance(cell, str) and cell.replace(",", "").replace(".", "").replace("-", "").isdigit():
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


def format_aggregated(
    agg: dict,
    title: str,
    sort_by: str = SORT_BY_SUM,
    fmt: str = FMT_SIMPLE,
) -> str:
    """Format an aggregation dict with summary lines for Purchase and bonuses."""
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
        return format_ascii_table(headers, rows, title=f"{title} (sorted by {sort_by})")
    else:
        lines = [f"--- {title} (sorted by {sort_by}) ---"]
        for desc, category, total in display_items:
            lines.append(f"  ({desc}, {category}): {total:.2f} KZT")
        lines.append(f"  {'—' * 40}")
        lines.append(f"  Total purchases:        {purchase_total:.2f} KZT")
        lines.append(f"  Saved with bonuses:     {bonuses_total:.2f} KZT")
        lines.append(f"  Net purchases:          {purchase_total + bonuses_total:.2f} KZT")
        return "\n".join(lines)


def format_raw_report(
    parsed_data: list[dict],
    sort_by: str = SORT_BY_SUM,
    fmt: str = FMT_ASCII,
) -> str:
    """Format every parsed transaction with a summary footer."""
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
        return format_ascii_table(headers, rows, title=f"Raw Transactions (sorted by {sort_by})")
    else:
        lines = [f"--- Raw Transactions (sorted by {sort_by}) ---"]
        for date, desc, label, mcc, amount in display_rows:
            suffix = f"{label} [{mcc}]" if mcc else label or "—"
            lines.append(f"  {date}  {desc:<12}  {amount:>12.2f} KZT  {suffix}")
        lines.append(f"  {'—' * 50}")
        lines.append(f"  Total purchases:        {purchase_total:.2f} KZT")
        lines.append(f"  Saved with bonuses:     {bonuses_total:.2f} KZT")
        lines.append(f"  Net purchases:          {purchase_total - bonuses_total:.2f} KZT")
        lines.append(f"  Grand total:            {grand_total:.2f} KZT")
        return "\n".join(lines)
