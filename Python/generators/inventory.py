"""
generators/inventory.py
========================
Phase 3 — Inventory.
This is the core simulation engine of the whole dataset. For every
(Warehouse, Product) pair that is actually stocked, it runs a month-by-month
(s, Q) reorder-point simulation across the full 2022-2025 horizon:

    opening -> + received (from Phase 2 POs) + produced (reorder policy)
             + transferred_in + returned -> - damaged - expired
             -> stock_after_losses -> sold (capped by stock) -> closing

The `sold` quantity computed here is a hard cap — Phase 4 (Sales) distributes
exactly this quantity across individual store-level transaction lines, which
is what guarantees "sales never exceed available inventory" holds by
construction rather than by a post-hoc check.

Also produces:
- Batches (production events, used for FEFO / near-expiry flags)
- Stock_Movements for every inflow/outflow EXCEPT "Customer Sale"
  (those are appended in Phase 4, one per actual sales line, for full
  traceability from a stock movement back to the exact sale that caused it).
"""

import numpy as np
import pandas as pd

from config import (
    RNG, CATEGORIES, GOVERNORATES, STORE_TYPES, make_ids,
)
from utils.helpers import month_range, seasonal_multiplier_for_month

GLOBAL_DEMAND_SCALE = 260.0  # tuned so combo-month demand sits in realistic 10s-1000s range


def _category_lookup():
    return {c["Category_ID"]: c for c in CATEGORIES}


def _assign_stocking_warehouses(products_df, warehouses_df):
    """Each product is stocked in a subset of warehouses (not all 20)."""
    wh_ids = warehouses_df["Warehouse_ID"].values
    assignment = {}
    max_k = min(10, len(wh_ids))
    min_k = min(4, max_k)
    for pid in products_df["Product_ID"].values:
        k = int(RNG.integers(min_k, max_k + 1)) if max_k > min_k else max_k
        assignment[pid] = list(RNG.choice(wh_ids, size=k, replace=False))
    return assignment


def _warehouse_demand_weights(stores_df, distributors_df, warehouses_df):
    """Aggregate demand pull of every warehouse, from the stores it serves
    (via each store's distributor's Assigned_Warehouse_ID)."""
    dist_to_wh = distributors_df.set_index("Distributor_ID")["Assigned_Warehouse_ID"].to_dict()
    stores = stores_df.copy()
    stores["Warehouse_ID"] = stores["Distributor_ID"].map(dist_to_wh)
    stores["line_factor"] = stores["Store_Type"].map(lambda t: STORE_TYPES[t]["avg_lines_month"])
    stores["pull"] = stores["Monthly_Demand_Level"] * stores["line_factor"]
    agg = stores.groupby("Warehouse_ID")["pull"].sum()
    weights = agg.reindex(warehouses_df["Warehouse_ID"].values).fillna(agg.mean())
    weights = weights / weights.mean()
    return weights.to_dict(), stores  # stores now carries Warehouse_ID for Phase 4


def run_inventory_simulation(products_df, warehouses_df, stores_df, distributors_df, pod_df):
    months = month_range("2022-01-01", "2025-12-01")
    cat_lookup = _category_lookup()

    # Precompute category seasonal multiplier per month (shared across products in category)
    seasonal_cache = {}
    for cat in CATEGORIES:
        seasonal_cache[cat["Category_ID"]] = [
            seasonal_multiplier_for_month(m, cat) for m in months
        ]

    stocking_map = _assign_stocking_warehouses(products_df, warehouses_df)
    wh_weight_map, stores_with_wh = _warehouse_demand_weights(stores_df, distributors_df, warehouses_df)

    pop_weight_map = products_df.set_index("Product_ID")["Popularity_Weight"].to_dict()
    n_products = len(products_df)
    cat_of_product = products_df.set_index("Product_ID")["Category_ID"].to_dict()
    shelf_life_map = products_df.set_index("Product_ID")["Minimum_Shelf_Life_Days"].to_dict()
    storage_map = products_df.set_index("Product_ID")["Storage_Condition"].to_dict()

    # PO receipts indexed by (warehouse, product, year-month)
    pod_df = pod_df.dropna(subset=["Receipt_Month"])
    receipt_lookup = pod_df.groupby(["Warehouse_ID", "Product_ID", "Receipt_Month"])["Received_Quantity"].sum().to_dict()

    inv_rows = []
    movement_rows = []
    batch_rows = []
    sold_qty_lookup = {}  # (warehouse, product, month_str) -> qty sold, consumed by Phase 4
    mov_ctr = 1
    batch_ctr = 1

    for pid in products_df["Product_ID"].values:
        cat_id = cat_of_product[pid]
        shelf_life = shelf_life_map[pid]
        storage = storage_map[pid]
        pop_factor = pop_weight_map[pid] * n_products
        seasonal_series = seasonal_cache[cat_id]

        # category-based loss rates
        is_perishable = shelf_life <= 60
        damage_rate_base = 0.02 if storage == "Chilled" else (0.025 if storage == "Frozen" else 0.01)
        expiry_rate_base = 0.035 if is_perishable else (0.012 if shelf_life <= 180 else 0.003)
        return_rate = 0.015 if cat_lookup[cat_id]["Category_Name"] in ("Dairy Products", "Infant Nutrition") else 0.008

        for wh_id in stocking_map[pid]:
            wh_factor = wh_weight_map.get(wh_id, 1.0)
            combo_noise = float(RNG.lognormal(0, 0.30))
            baseline = GLOBAL_DEMAND_SCALE * pop_factor * wh_factor * combo_noise

            avg_demand = baseline * float(np.mean(seasonal_series))
            safety_stock = avg_demand * float(RNG.uniform(0.15, 0.35))
            reorder_point = safety_stock + avg_demand * float(RNG.uniform(0.5, 1.0))
            reorder_qty = avg_demand * float(RNG.uniform(0.9, 1.6))

            opening = reorder_point * float(RNG.uniform(1.0, 1.8))
            prev_sold = 0.0

            for m_idx, month in enumerate(months):
                month_str = month.strftime("%Y-%m")
                demand = baseline * seasonal_series[m_idx] * float(RNG.lognormal(0, 0.12))

                produced = 0.0
                if opening < reorder_point:
                    produced = reorder_qty * float(RNG.uniform(0.85, 1.15))
                elif RNG.random() < 0.05:
                    produced = reorder_qty * float(RNG.uniform(0.1, 0.3))

                received = float(receipt_lookup.get((wh_id, pid, month_str), 0.0))
                transferred_in = baseline * 0.01 if RNG.random() < 0.06 else 0.0
                transferred_out = baseline * 0.01 if RNG.random() < 0.06 else 0.0
                returned_qty = prev_sold * return_rate

                inflow = opening + received + produced + transferred_in + returned_qty
                damaged = inflow * damage_rate_base * float(RNG.uniform(0.5, 1.5))
                expired = inflow * expiry_rate_base * float(RNG.uniform(0.5, 1.5))
                losses = damaged + expired + transferred_out
                stock_after_losses = max(inflow - losses, 0.0)

                sold = min(demand, stock_after_losses)
                lost_sales = max(demand - stock_after_losses, 0.0)
                closing = stock_after_losses - sold

                inv_rows.append({
                    "Inventory_ID": f"INV{str(len(inv_rows)+1).zfill(7)}",
                    "Date": month.date(),
                    "Warehouse_ID": wh_id,
                    "Product_ID": pid,
                    "Opening_Stock": round(opening, 1),
                    "Received_Quantity": round(received, 1),
                    "Produced_Quantity": round(produced, 1),
                    "Sold_Quantity": round(sold, 1),
                    "Transferred_In": round(transferred_in, 1),
                    "Transferred_Out": round(transferred_out, 1),
                    "Returned_Quantity": round(returned_qty, 1),
                    "Damaged_Quantity": round(damaged, 1),
                    "Expired_Quantity": round(expired, 1),
                    "Closing_Stock": round(closing, 1),
                    "Safety_Stock": round(safety_stock, 1),
                    "Reorder_Point": round(reorder_point, 1),
                    "Reorder_Quantity": round(reorder_qty, 1),
                    "Lost_Sales_Quantity": round(lost_sales, 1),
                    "Stockout_Flag": lost_sales > 0.01,
                })

                sold_qty_lookup[(wh_id, pid, month_str)] = sold

                # ---- movements (everything except Customer Sale) ----
                if received > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Purchase Receipt",
                                           "Quantity": round(received, 1)}); mov_ctr += 1
                if produced > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Production Receipt",
                                           "Quantity": round(produced, 1)}); mov_ctr += 1
                    prod_date = month + pd.Timedelta(days=int(RNG.integers(0, 27)))
                    batch_rows.append({
                        "Batch_ID": f"BATCH{str(batch_ctr).zfill(8)}", "Product_ID": pid, "Warehouse_ID": wh_id,
                        "Production_Date": prod_date.date(), "Expiry_Date": (prod_date + pd.Timedelta(days=int(shelf_life))).date(),
                        "Quantity": round(produced, 1),
                    }); batch_ctr += 1
                if transferred_in > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Warehouse Transfer In",
                                           "Quantity": round(transferred_in, 1)}); mov_ctr += 1
                if transferred_out > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Warehouse Transfer Out",
                                           "Quantity": round(transferred_out, 1)}); mov_ctr += 1
                if returned_qty > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Customer Return",
                                           "Quantity": round(returned_qty, 1)}); mov_ctr += 1
                if damaged > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Damaged",
                                           "Quantity": round(damaged, 1)}); mov_ctr += 1
                if expired > 0.5:
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Expired",
                                           "Quantity": round(expired, 1)}); mov_ctr += 1
                if RNG.random() < 0.015:
                    adj = float(RNG.normal(0, baseline * 0.03))
                    movement_rows.append({"Movement_ID": f"MOV{str(mov_ctr).zfill(8)}", "Date": month.date(),
                                           "Warehouse_ID": wh_id, "Product_ID": pid, "Movement_Type": "Adjustment",
                                           "Quantity": round(adj, 1)}); mov_ctr += 1

                opening = closing
                prev_sold = sold

    inventory_df = pd.DataFrame(inv_rows)
    movements_df = pd.DataFrame(movement_rows)
    batches_df = pd.DataFrame(batch_rows)

    ref_date = pd.Timestamp("2025-12-31")
    batches_df["Days_To_Expiry"] = (pd.to_datetime(batches_df["Expiry_Date"]) - ref_date).dt.days
    batches_df["Expired_Flag"] = batches_df["Days_To_Expiry"] < 0
    batches_df["Near_Expiry_Flag"] = (batches_df["Days_To_Expiry"] >= 0) & (batches_df["Days_To_Expiry"] <= 30)

    return inventory_df, movements_df, batches_df, sold_qty_lookup, stores_with_wh
