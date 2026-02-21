from pathlib import Path

import pytest

from tools.forte_generator import SAMPLE_TRANSACTIONS
from reporter import (
    DATE_PATTERN,
    SUM_PATTERN,
    _clean_details,
    _is_data_row,
    parse_pdf,
)

TEST_PDF = Path(__file__).resolve().parent / "resources" / "test.pdf"


# ---------------------------------------------------------------------------
# _clean_details
# ---------------------------------------------------------------------------

class TestCleanDetails:
    def test_removes_mid_word_line_breaks(self):
        assert _clean_details("Halyk Bank of Ka\nzakhstan") == "Halyk Bank of Ka zakhstan"

    def test_preserves_break_after_comma(self):
        assert _clean_details("MCC: 5814,\nAPPLE PAY") == "MCC: 5814, APPLE PAY"

    def test_collapses_multiple_spaces(self):
        assert _clean_details("too  many   spaces") == "too many spaces"

    def test_none_returns_empty_string(self):
        assert _clean_details(None) == ""

    def test_empty_string(self):
        assert _clean_details("") == ""

    def test_no_changes_needed(self):
        text = "Receiver: 440043******8791"
        assert _clean_details(text) == text


# ---------------------------------------------------------------------------
# _is_data_row
# ---------------------------------------------------------------------------

class TestIsDataRow:
    def test_valid_row(self):
        row = ["31.01.2026", "-30000.00 KZT", "Transfer", "Receiver: 440043******8791"]
        assert _is_data_row(row) is True

    def test_positive_sum(self):
        row = ["30.01.2026", "112950.86 KZT", "Account replenishment", "details"]
        assert _is_data_row(row) is True

    def test_header_row(self):
        row = ["Date", "Sum", "Description", "Details"]
        assert _is_data_row(row) is False

    def test_empty_row(self):
        row = ["", None, None, None]
        assert _is_data_row(row) is False

    def test_none_row(self):
        assert _is_data_row(None) is False

    def test_short_row(self):
        assert _is_data_row(["31.01.2026"]) is False

    def test_metadata_row(self):
        row = ["Card account statement ...", None, None, None]
        assert _is_data_row(row) is False


# ---------------------------------------------------------------------------
# parse_pdf – integration tests against the generated statement
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def transactions():
    return parse_pdf(TEST_PDF)


class TestParsePdf:
    def test_returns_list(self, transactions):
        assert isinstance(transactions, list)

    def test_non_empty(self, transactions):
        assert len(transactions) > 0

    def test_tuple_shape(self, transactions):
        for txn in transactions:
            assert isinstance(txn, tuple)
            assert len(txn) == 4

    def test_date_format(self, transactions):
        for date, *_ in transactions:
            assert DATE_PATTERN.match(date), f"Bad date: {date}"

    def test_sum_format(self, transactions):
        for _, sum_str, *_ in transactions:
            assert SUM_PATTERN.match(sum_str), f"Bad sum: {sum_str}"

    def test_description_not_empty(self, transactions):
        for *_, desc, _ in transactions:
            assert desc, "Description must not be empty"

    def test_no_newlines_in_details(self, transactions):
        for *_, details in transactions:
            assert "\n" not in details, f"Newline in details: {details!r}"

    def test_known_first_transaction(self, transactions):
        first = transactions[0]
        assert first[0] == "31.01.2026"
        assert first[1] == "-30000.00 KZT"
        assert first[2] == "Transfer"
        assert "Receiver:" in first[3]

    def test_has_purchases_and_transfers(self, transactions):
        descriptions = {t[2] for t in transactions}
        assert "Purchase" in descriptions
        assert "Transfer" in descriptions

    def test_details_contain_mcc(self, transactions):
        mcc_count = sum(1 for *_, d in transactions if "MCC:" in d)
        assert mcc_count > 10, "Expected many transactions with MCC codes"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_pdf("/nonexistent/file.pdf")

    def test_total_transaction_count(self, transactions):
        assert len(transactions) == len(SAMPLE_TRANSACTIONS)

    def test_roundtrip_all_transactions(self, transactions):
        """Every generated transaction must survive the parse round-trip."""
        for parsed, original in zip(transactions, SAMPLE_TRANSACTIONS):
            assert parsed[0] == original[0], f"Date mismatch: {parsed[0]}"
            assert parsed[1] == original[1], f"Sum mismatch: {parsed[1]}"
            assert parsed[2] == original[2], f"Description mismatch: {parsed[2]}"
            assert original[3] in parsed[3] or parsed[3] in original[3], (
                f"Details mismatch:\n  parsed:   {parsed[3]!r}\n  original: {original[3]!r}"
            )
