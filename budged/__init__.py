"""budged – ForteBank statement parsing and spending analytics."""

from budged.categories import mcc2name, mcc_groups, name_to_group
from budged.parser import (
    DATE_PATTERN,
    SUM_PATTERN,
    parse_details,
    parse_pdf,
    parse_row,
    parse_sum,
    parse_transactions,
)
from budged.aggregator import (
    group_by_description_and_mcc,
    group_by_description_and_mcc_group,
    compute_purchase_totals,
)
from budged.formatter import (
    SORT_BY_SUM,
    SORT_BY_NAME,
    SORT_BY_DATE,
    FMT_SIMPLE,
    FMT_ASCII,
    REPORT_RAW,
    REPORT_MCC,
    REPORT_GROUP,
    format_ascii_table,
    format_aggregated,
    format_raw_report,
)

__all__ = [
    "mcc2name",
    "mcc_groups",
    "name_to_group",
    "DATE_PATTERN",
    "SUM_PATTERN",
    "parse_details",
    "parse_pdf",
    "parse_row",
    "parse_sum",
    "parse_transactions",
    "group_by_description_and_mcc",
    "group_by_description_and_mcc_group",
    "compute_purchase_totals",
    "SORT_BY_SUM",
    "SORT_BY_NAME",
    "SORT_BY_DATE",
    "FMT_SIMPLE",
    "FMT_ASCII",
    "REPORT_RAW",
    "REPORT_MCC",
    "REPORT_GROUP",
    "format_ascii_table",
    "format_aggregated",
    "format_raw_report",
]
