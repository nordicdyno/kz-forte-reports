"""CLI entry point for parsing ForteBank PDF statements."""

from pathlib import Path

from budged import (
    SORT_BY_SUM,
    SORT_BY_NAME,
    SORT_BY_DATE,
    FMT_SIMPLE,
    FMT_ASCII,
    REPORT_RAW,
    REPORT_MCC,
    REPORT_GROUP,
    parse_pdf,
    parse_transactions,
    group_by_description_and_mcc,
    group_by_description_and_mcc_group,
    format_aggregated,
    format_raw_report,
)

# Re-export for backward compatibility (used in tests)
from budged.parser import DATE_PATTERN, SUM_PATTERN, _clean_details, _is_data_row
from budged.formatter import format_ascii_table


def print_table(data, title: str | None = None):
    """
    Pretty-print any of the common data shapes used in this module.

    Supported shapes:
    - ``list[dict]``  – parsed_data (each dict becomes a row)
    - ``list[tuple]`` – raw tuples from parse_pdf
    - ``dict[tuple, float]`` – mcc_agg / group_agg
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


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Parse ForteBank PDF statements")
    parser.add_argument(
        "--sort",
        choices=[SORT_BY_SUM, SORT_BY_NAME, SORT_BY_DATE],
        default=SORT_BY_SUM,
        help="Sort order: sum, name, or date (default: sum). "
        "date is only supported for raw report; mcc/group ignore it and fall back to sum.",
    )
    parser.add_argument(
        "--format",
        choices=[FMT_SIMPLE, FMT_ASCII],
        default=FMT_ASCII,
        dest="fmt",
        help="Output format: simple or ascii table (default: ascii)",
    )
    parser.add_argument(
        "--report",
        choices=[REPORT_RAW, REPORT_MCC, REPORT_GROUP],
        default=REPORT_GROUP,
        help="Report type: raw transactions, mcc breakdown, or group breakdown (default: group)",
    )
    parser.add_argument(
        "--statements-dir",
        default="./statements",
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

        parsed_data = parse_transactions(raw_data)

        if args.report == REPORT_RAW:
            print(format_raw_report(parsed_data, args.sort, args.fmt))
            print()
        elif args.report == REPORT_MCC:
            agg_sort = args.sort if args.sort != SORT_BY_DATE else SORT_BY_SUM
            mcc_agg = group_by_description_and_mcc(parsed_data)
            print(format_aggregated(mcc_agg, "Grouped by Description and MCC Name", agg_sort, args.fmt))
            print()
        else:
            agg_sort = args.sort if args.sort != SORT_BY_DATE else SORT_BY_SUM
            group_agg = group_by_description_and_mcc_group(parsed_data)
            print(format_aggregated(group_agg, "Grouped by Description and MCC Group", agg_sort, args.fmt))
            print()
