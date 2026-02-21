"""Generate ForteBank-style card-statement PDFs for testing."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "tests" / "resources" / "test.pdf"

SAMPLE_TRANSACTIONS: list[tuple[str, str, str, str]] = [
    ("31.01.2026", "-30000.00 KZT", "Transfer", "Receiver: 440043******8791"),
    ("30.01.2026", "-5490.00 KZT", "Purchase",
     "MAGNUM CASH&CARRY, JSC Halyk Bank, MCC: 5411, APPLE PAY"),
    ("30.01.2026", "-3200.00 KZT", "Purchase", "WOLT, MCC: 5814"),
    ("29.01.2026", "-1500.00 KZT", "Purchase with bonuses", "Glovo KZ, MCC: 5812"),
    ("29.01.2026", "-12000.00 KZT", "Transfer", "Receiver: 524821******1234"),
    ("28.01.2026", "-2100.00 KZT", "Purchase", "MARWIN, MCC: 5977"),
    ("28.01.2026", "-890.00 KZT", "Purchase",
     "Kaspi Magazin, Kaspi Bank, MCC: 5943"),
    ("27.01.2026", "-4500.00 KZT", "Purchase", "Arbuz.kz, MCC: 5411"),
    ("27.01.2026", "-15000.00 KZT", "Purchase", "Technodom, MCC: 5311"),
    ("26.01.2026", "-7800.00 KZT", "Purchase", "Yandex Go, MCC: 4121"),
    ("26.01.2026", "-3500.00 KZT", "Purchase", "PetCity, MCC: 5995"),
    ("25.01.2026", "112950.86 KZT", "Account replenishment", "Salary"),
    ("25.01.2026", "-2200.00 KZT", "Purchase", "Europharma, MCC: 5912"),
    ("24.01.2026", "-8900.00 KZT", "Purchase", "ZARA, MCC: 5691"),
    ("24.01.2026", "-6500.00 KZT", "Purchase", "Shell, MCC: 5541"),
    ("23.01.2026", "-1200.00 KZT", "Purchase with bonuses",
     "Burger King, MCC: 5814"),
    ("23.01.2026", "-4300.00 KZT", "Purchase", "Dostyk Plaza, MCC: 5311"),
    ("22.01.2026", "-950.00 KZT", "Purchase", "Chocolife, MCC: 7941"),
    ("22.01.2026", "-3800.00 KZT", "Purchase", "Wildberries, MCC: 5262"),
    ("21.01.2026", "-5000.00 KZT", "Transfer", "Receiver: 400012******5678"),
]


def generate_forte_pdf(
    transactions: list[tuple[str, str, str, str]] = SAMPLE_TRANSACTIONS,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> Path:
    """Generate a ForteBank-style card statement PDF.

    Parameters
    ----------
    transactions:
        List of ``(date, sum, description, details)`` tuples.
    output_path:
        Where to write the PDF file.

    Returns
    -------
    Path to the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    cell_style = styles["Normal"].clone("cell")
    cell_style.fontSize = 8
    cell_style.leading = 10

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    elements: list = []

    heading = styles["Heading2"]
    elements.append(
        Paragraph(
            "Card account statement for period 01.01.2026 - 31.01.2026",
            heading,
        )
    )
    elements.append(Spacer(1, 5 * mm))

    header = ["Date", "Sum", "Description", "Details"]
    table_data: list[list] = [header]

    for date, sum_str, desc, details in transactions:
        table_data.append([
            date,
            sum_str,
            desc,
            Paragraph(escape(details), cell_style),
        ])

    page_width = A4[0] - 30 * mm
    col_widths = [22 * mm, 30 * mm, 38 * mm, page_width - 90 * mm]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F2F2F2")]),
    ]))

    elements.append(table)
    doc.build(elements)
    return output_path


if __name__ == "__main__":
    path = generate_forte_pdf()
    print(f"Generated: {path}")
