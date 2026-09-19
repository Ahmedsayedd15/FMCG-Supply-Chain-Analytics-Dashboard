"""
generators/procurement.py
==========================
Phase 2 — Procurement.
Purchase_Orders + Purchase_Order_Details.

Suppliers deliver PRODUCTS to WAREHOUSES (the common simplification used in
this kind of analytics case study — Product already carries its Factory_ID
for provenance). Supplier reliability/quality scores directly drive late
delivery, partial delivery and rejected-quantity rates, which is what makes
this data useful for the "which suppliers cause delays" business question.

Output of this phase feeds Phase 3 (Inventory) as one of the monthly supply
sources (the "Received_Quantity" component).
"""

import numpy as np
import pandas as pd

from config import RNG, TARGET_PURCHASE_ORDERS, START_DATE, END_DATE, make_ids
from utils.helpers import random_dates_between


def gen_purchase_orders(products_df, suppliers_df, warehouses_df):
    n_po = TARGET_PURCHASE_ORDERS
    po_ids = make_ids("PO", n_po)

    supplier_ids = suppliers_df["Supplier_ID"].values
    supplier_lookup = suppliers_df.set_index("Supplier_ID")

    warehouse_ids = warehouses_df["Warehouse_ID"].values

    po_dates = random_dates_between(RNG, START_DATE, END_DATE, n_po)
    chosen_suppliers = RNG.choice(supplier_ids, size=n_po)
    chosen_warehouses = RNG.choice(warehouse_ids, size=n_po)

    po_rows = []
    pod_rows = []
    pod_ctr = 1

    # cache product-by-supplier for realism: prefer products actually linked to that supplier
    prod_by_supplier = products_df.groupby("Supplier_ID")["Product_ID"].apply(list).to_dict()
    all_products = products_df["Product_ID"].values
    unit_costs = products_df.set_index("Product_ID")["Unit_Cost"].to_dict()

    for i in range(n_po):
        sup_id = chosen_suppliers[i]
        wh_id = chosen_warehouses[i]
        sup = supplier_lookup.loc[sup_id]
        lead_time = int(sup["Lead_Time_Days"])
        reliability = float(sup["Reliability_Score"])
        quality = float(sup["Quality_Score"])

        po_date = po_dates[i]
        expected_delivery = po_date + pd.Timedelta(days=lead_time)

        # delay probability inversely tied to reliability
        is_late = RNG.random() > reliability
        delay_days = int(RNG.integers(1, 15)) if is_late else 0
        actual_delivery = expected_delivery + pd.Timedelta(days=delay_days)

        po_status = RNG.choice(
            ["Completed", "Completed", "Partially Delivered", "Cancelled"],
            p=[0.80, 0.12, 0.06, 0.02]
        )
        payment_status = RNG.choice(["Paid", "Paid", "Pending", "Overdue"], p=[0.70, 0.15, 0.10, 0.05])

        candidate_products = prod_by_supplier.get(sup_id, [])
        if len(candidate_products) == 0:
            candidate_products = list(RNG.choice(all_products, size=5, replace=False))
        n_lines = int(RNG.integers(1, min(8, max(2, len(candidate_products) + 1))))
        line_products = RNG.choice(candidate_products, size=min(n_lines, len(candidate_products)), replace=False) \
            if len(candidate_products) >= n_lines else RNG.choice(all_products, size=n_lines, replace=False)

        total_po_value = 0.0
        for prod_id in line_products:
            ordered_qty = int(RNG.integers(200, 5000))
            # quality issues -> rejected quantity; reliability issues -> partial receipt
            reject_rate = np.clip(RNG.normal(1 - quality, 0.03), 0, 0.25)
            if po_status == "Cancelled":
                received_qty = 0
                rejected_qty = 0
            elif po_status == "Partially Delivered":
                received_qty = int(ordered_qty * RNG.uniform(0.4, 0.85))
                rejected_qty = int(received_qty * reject_rate)
            else:
                received_qty = int(ordered_qty * RNG.uniform(0.95, 1.0))
                rejected_qty = int(received_qty * reject_rate)

            unit_cost = unit_costs.get(prod_id, round(float(RNG.uniform(3, 20)), 2))
            line_total = round(received_qty * unit_cost, 2)
            total_po_value += line_total

            pod_rows.append({
                "PO_Detail_ID": f"POD{str(pod_ctr).zfill(7)}",
                "PO_ID": po_ids[i],
                "Product_ID": prod_id,
                "Ordered_Quantity": ordered_qty,
                "Received_Quantity": received_qty,
                "Rejected_Quantity": rejected_qty,
                "Unit_Cost": unit_cost,
                "Line_Total": line_total,
                "Warehouse_ID": wh_id,
                "Receipt_Month": actual_delivery.to_period("M").strftime("%Y-%m") if po_status != "Cancelled" else None,
            })
            pod_ctr += 1

        po_rows.append({
            "PO_ID": po_ids[i],
            "Supplier_ID": sup_id,
            "Warehouse_ID": wh_id,
            "PO_Date": po_date.date(),
            "Expected_Delivery_Date": expected_delivery.date(),
            "Actual_Delivery_Date": actual_delivery.date() if po_status != "Cancelled" else None,
            "PO_Status": po_status,
            "Payment_Status": payment_status if po_status != "Cancelled" else "N/A",
            "Total_PO_Value": round(total_po_value, 2),
            "Delay_Days": delay_days if po_status != "Cancelled" else 0,
        })

    return pd.DataFrame(po_rows), pd.DataFrame(pod_rows)
