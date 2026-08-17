def demo_repair(rows, missing):
    out = []
    for row in rows:
        r = dict(row)
        if "price" in missing: r["price"] = r.get("_recovered_price", "₹59,999")
        if "stock" in missing: r["stock"] = r.get("_recovered_stock", "In stock")
        if "product_name" in missing: r["product_name"] = r.get("_recovered_product_name", "Recovered product")
        out.append(r)
    return out
