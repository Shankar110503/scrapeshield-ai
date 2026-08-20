from typing import Any, Dict, List


def demo_repair(
    rows: List[Dict[str, Any]],
    missing: List[str],
) -> List[Dict[str, Any]]:
    """
    Demonstration repair used by the hackathon UI.

    This does not call Bright Data.
    It simulates the recovery step so judges can
    see the self-healing workflow immediately.
    """

    repaired_rows = []

    for row in rows:
        repaired = dict(row)

        if "price" in missing:
            repaired["price"] = repaired.get(
                "_recovered_price",
                "₹59,999",
            )

        if "stock" in missing:
            repaired["stock"] = repaired.get(
                "_recovered_stock",
                "In stock",
            )

        if "product_name" in missing:
            repaired["product_name"] = repaired.get(
                "_recovered_product_name",
                "Recovered product",
            )

        repaired_rows.append(repaired)

    return repaired_rows
