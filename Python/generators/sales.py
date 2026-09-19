"""
generators/sales.py
====================
Phase 4 — Sales.
Takes the `sold_qty_lookup` produced by Phase 3's inventory simulation
(keyed by Warehouse, Product, Month) and materializes it into individual
store-level Sales lines. This is what guarantees, by construction, that
total sales quantity per warehouse-product-month never exceeds what the
inventory simulation actually made available.

Each generated Sales line also gets a mirrored "Customer Sale" Stock_Movement
row (Phase 3 deliberately left these out), so every unit sold is traceable
to both a transaction and a stock movement.
"""

import numpy as np
import pandas as pd

from config import RNG, PAYMENT_METHODS, make_ids

CHANNEL_BY_STORE_TYPE = {
    "Hypermarket": "Modern Trade", "Supermarket": "Modern Trade",
    "Grocery": "Traditional Trade", "Convenience Store": "Traditional Trade",
    "Pharmacy": "Traditional Trade", "Wholesale": "Wholesale", "E-commerce": "E-commerce",
}


def _active_promo_lookup(promotions_df, promotion_details_df):
    """(Product_ID, 'YYYY-MM') -> discount fraction, for months a promo is live."""
    lookup = {}
    if promotions_df.empty:
        return lookup
    merged = promotion_details_df.merge(
        promotions_df[["Promotion_ID", "Start_Date", "End_Date"]], on="Promotion_ID"
    )
    for _, row in merged.iterrows():
        months = pd.period_range(row["Start_Date"], row["End_Date"], freq="M")
        for m in months:
            lookup[(row["Product_ID"], str(m))] = row["Discount_Percentage"]
    return lookup


def gen_sales(sold_qty_lookup, stores_with_wh, products_df, promotions_df, promotion_details_df):
    promo_lookup = _active_promo_lookup(promotions_df, promotion_details_df)

    price_map = products_df.set_index("Product_ID")["Standard_Selling_Price"].to_dict()
    cost_map = products_df.set_index("Product_ID")["Unit_Cost"].to_dict()

    stores_by_wh = {wh: g for wh, g in stores_with_wh.groupby("Warehouse_ID")}

    sales_rows = []
    movement_rows = []
    sale_ctr = 1
    mov_ctr = 1

    for (wh_id, pid, month_str), qty in sold_qty_lookup.items():
        if qty < 1:
            continue
        stores_g = stores_by_wh.get(wh_id)
        if stores_g is None or len(stores_g) == 0:
            continue

        n_lines = int(RNG.integers(1, 6))
        n_lines = min(n_lines, len(stores_g))
        w = stores_g["pull"].values.astype(float)
        w = w / w.sum() if w.sum() > 0 else np.ones(len(stores_g)) / len(stores_g)
        chosen_idx = RNG.choice(len(stores_g), size=n_lines, replace=False, p=w)
        chosen_stores = stores_g.iloc[chosen_idx]

        split_w = RNG.dirichlet(np.ones(n_lines))
        line_qtys = np.maximum(np.round(qty * split_w), 1).astype(int)
        diff = int(round(qty)) - line_qtys.sum()
        if len(line_qtys) > 0:
            line_qtys[0] = max(1, line_qtys[0] + diff)

        month_start = pd.Timestamp(month_str + "-01")
        days_in_month = month_start.days_in_month

        for j, (_, store) in enumerate(chosen_stores.iterrows()):
            line_qty = int(line_qtys[j])
            if line_qty <= 0:
                continue
            unit_price = price_map.get(pid, 10.0)
            discount = promo_lookup.get((pid, month_str), 0.0)
            if discount == 0.0 and RNG.random() < 0.03:
                discount = round(float(RNG.uniform(0.05, 0.15)), 2)  # occasional ad-hoc discount

            net_sales = round(line_qty * unit_price * (1 - discount), 2)
            unit_cost = cost_map.get(pid, unit_price * 0.6)
            cost = round(line_qty * unit_cost, 2)
            gross_profit = round(net_sales - cost, 2)

            order_date = month_start + pd.Timedelta(days=int(RNG.integers(0, days_in_month)))
            store_type = store["Store_Type"]
            channel = CHANNEL_BY_STORE_TYPE.get(store_type, "Traditional Trade")
            payment = "Mobile Wallet" if channel == "E-commerce" and RNG.random() < 0.6 else \
                RNG.choice(PAYMENT_METHODS, p=[0.45, 0.20, 0.15, 0.10, 0.10])

            sales_id = f"SAL{str(sale_ctr).zfill(8)}"
            sales_rows.append({
                "Sales_ID": sales_id,
                "Order_Date": order_date.date(),
                "Store_ID": store["Store_ID"],
                "Distributor_ID": store["Distributor_ID"],
                "Warehouse_ID": wh_id,
                "Product_ID": pid,
                "Quantity": line_qty,
                "Unit_Price": unit_price,
                "Discount": discount,
                "Net_Sales": net_sales,
                "Cost": cost,
                "Gross_Profit": gross_profit,
                "Payment_Method": payment,
                "Sales_Channel": channel,
            })
            sale_ctr += 1

            movement_rows.append({
                "Movement_ID": f"MOV{str(mov_ctr).zfill(8)}S", "Date": order_date.date(),
                "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Customer Sale",
                "Quantity": line_qty, "Reference_Sales_ID": sales_id,
            })
            mov_ctr += 1

    return pd.DataFrame(sales_rows), pd.DataFrame(movement_rows)
