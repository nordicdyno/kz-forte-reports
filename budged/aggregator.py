"""Spending aggregation by MCC code and category group."""

from collections import defaultdict

from budged.categories import mcc2name, name_to_group


def group_by_description_and_mcc(data: list[dict]) -> dict[tuple[str, str], float]:
    """
    Summarize transaction amounts by (Description, MCC_Short_Name).

    "Purchase with bonuses" is folded into "Purchase" (offsets spend),
    and a separate "Saved with bonuses" row tracks the bonus totals.
    """
    aggregated: dict[tuple[str, str], float] = defaultdict(float)

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


def group_by_description_and_mcc_group(data: list[dict]) -> dict[tuple[str, str], float]:
    """
    Summarize transaction amounts by (Description, MCC_Group).

    Rolls up MCC names into their broader category groups.
    """
    base = group_by_description_and_mcc(data)
    group_aggregated: dict[tuple[str, str], float] = defaultdict(float)

    for (desc, mcc_name), total_sum in base.items():
        if mcc_name == "No MCC":
            group_name = "Transfers/Other"
        else:
            group_name = name_to_group.get(mcc_name, "Other Uncategorized")
        group_aggregated[(desc, group_name)] += total_sum

    return dict(group_aggregated)


def compute_purchase_totals(data: list[dict]) -> dict[str, float]:
    """Compute summary totals from parsed transactions.

    Returns dict with keys: purchase_total, bonuses_total, net_purchases,
    grand_total, income_total.
    """
    purchase_total = 0.0
    bonuses_total = 0.0
    grand_total = 0.0
    income_total = 0.0

    for row in data:
        desc = row["Description"]
        amount = row["Sum"]
        grand_total += amount

        if amount > 0:
            income_total += amount

        if desc == "Purchase with bonuses":
            bonuses_total += amount
            purchase_total += amount
        elif desc == "Purchase":
            purchase_total += amount

    return {
        "purchase_total": purchase_total,
        "bonuses_total": bonuses_total,
        "net_purchases": purchase_total - bonuses_total,
        "grand_total": grand_total,
        "income_total": income_total,
    }
