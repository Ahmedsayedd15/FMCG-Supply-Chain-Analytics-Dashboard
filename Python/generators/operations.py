"""
generators/operations.py
=========================
Phase 5 — Operations.
Promotions (generated FIRST since Sales needs to know active discounts),
Deliveries (consolidated distributor-level shipments), Returns (sampled
from actual Sales lines, skewed toward return-prone categories/channels).
"""

import numpy as np
import pandas as pd

from config import (
    RNG, N_PROMOTIONS, PROMOTION_TYPES, RETURN_REASONS, GOVERNORATES,
    TARGET_DELIVERIES, TARGET_RETURNS, START_DATE, END_DATE, RAMADAN_RANGES, make_ids,
)
from utils.helpers import random_dates_between


def gen_promotions(products_df):
    n = N_PROMOTIONS
    promo_ids = make_ids("PROMO", n)
    rows = []
    detail_rows = []
    detail_ctr = 1

    all_products = products_df["Product_ID"].values
    ramadan_promo_share = 0.30

    for i in range(n):
        is_ramadan_promo = RNG.random() < ramadan_promo_share
        ptype = "Ramadan Promotion" if is_ramadan_promo else RNG.choice(
            [t for t in PROMOTION_TYPES if t != "Ramadan Promotion"])
        if is_ramadan_promo:
            r = RAMADAN_RANGES[int(RNG.integers(0, len(RAMADAN_RANGES)))]
            start = pd.Timestamp(r[0])
            end = pd.Timestamp(r[1])
        else:
            start = random_dates_between(RNG, START_DATE, "2025-11-01", 1)[0]
            end = start + pd.Timedelta(days=int(RNG.integers(7, 45)))

        discount = round(float(RNG.uniform(0.05, 0.35)), 2)
        n_products = int(RNG.integers(1, 8))
        promo_products = RNG.choice(all_products, size=n_products, replace=False)

        rows.append({
            "Promotion_ID": promo_ids[i],
            "Promotion_Name": f"{ptype} - {start.strftime('%b %Y')}",
            "Promotion_Type": ptype,
            "Start_Date": start.date(),
            "End_Date": end.date(),
            "Discount_Percentage": discount,
        })
        for pid in promo_products:
            detail_rows.append({
                "Promotion_Detail_ID": f"PROMD{str(detail_ctr).zfill(6)}",
                "Promotion_ID": promo_ids[i],
                "Product_ID": pid,
                "Discount_Percentage": discount,
            })
            detail_ctr += 1

    return pd.DataFrame(rows), pd.DataFrame(detail_rows)


def _distance_km(gov_a, gov_b):
    if gov_a == gov_b:
        return float(RNG.uniform(8, 45))
    region_a = GOVERNORATES[gov_a]["region"]
    region_b = GOVERNORATES[gov_b]["region"]
    if region_a == region_b:
        return float(RNG.uniform(45, 160))
    return float(RNG.uniform(160, 700))


def gen_deliveries(sales_df, distributors_df, warehouses_df, vehicles_df):
    wh_gov = warehouses_df.set_index("Warehouse_ID")["Governorate"].to_dict()
    dist_gov = distributors_df.set_index("Distributor_ID")["Governorate"].to_dict()
    dist_wh = distributors_df.set_index("Distributor_ID")["Assigned_Warehouse_ID"].to_dict()
    vehicles_by_wh = {wh: g["Vehicle_ID"].values for wh, g in vehicles_df.groupby("Assigned_Warehouse")}
    all_vehicles = vehicles_df["Vehicle_ID"].values

    sales_by_dist_month = sales_df.copy()
    sales_by_dist_month["Order_Month"] = pd.to_datetime(sales_by_dist_month["Order_Date"]).dt.strftime("%Y-%m")
    rep_sale_lookup = sales_by_dist_month.groupby(["Distributor_ID", "Order_Month"])["Sales_ID"].apply(list).to_dict()

    months = pd.date_range(START_DATE, END_DATE, freq="MS")
    rows = []
    delivery_ctr = 1
    target_avg = int(np.mean(TARGET_DELIVERIES))
    per_dist_month_mean = target_avg / (len(distributors_df) * len(months))

    for dist_id in distributors_df["Distributor_ID"].values:
        wh_id = dist_wh[dist_id]
        wh_g = wh_gov.get(wh_id)
        d_g = dist_gov.get(dist_id)
        base_distance = _distance_km(wh_g, d_g)
        vfleet = vehicles_by_wh.get(wh_id, all_vehicles)
        if len(vfleet) == 0:
            vfleet = all_vehicles

        for month in months:
            n_ship = RNG.poisson(max(per_dist_month_mean, 0.5))
            month_str = month.strftime("%Y-%m")
            candidate_sales = rep_sale_lookup.get((dist_id, month_str), [None])

            for _ in range(n_ship):
                distance = base_distance * float(RNG.uniform(0.85, 1.15))
                dispatch = month + pd.Timedelta(days=int(RNG.integers(0, month.days_in_month)))
                transit_days = max(1, int(np.ceil(distance / 300)))
                expected = dispatch + pd.Timedelta(days=transit_days)

                is_delayed = RNG.random() < 0.14
                delay_days = int(RNG.integers(1, 6)) if is_delayed else 0
                actual = expected + pd.Timedelta(days=delay_days)

                status = RNG.choice(
                    ["Delivered", "Delivered", "Delayed", "Cancelled"],
                    p=[0.80, 0.12, 0.06, 0.02]
                )
                vehicle_id = RNG.choice(vfleet)
                cost_per_km = float(RNG.uniform(3.5, 9.0))
                transport_cost = round(distance * cost_per_km + RNG.uniform(50, 300), 2)

                rows.append({
                    "Delivery_ID": f"DLV{str(delivery_ctr).zfill(8)}",
                    "Order_ID": RNG.choice(candidate_sales) if candidate_sales else None,
                    "Warehouse_ID": wh_id,
                    "Distributor_ID": dist_id,
                    "Vehicle_ID": vehicle_id,
                    "Dispatch_Date": dispatch.date(),
                    "Expected_Delivery_Date": expected.date(),
                    "Actual_Delivery_Date": actual.date() if status != "Cancelled" else None,
                    "Delivery_Status": status,
                    "Distance_KM": round(distance, 1),
                    "Transportation_Cost": transport_cost,
                    "Delay_Days": delay_days if status != "Cancelled" else 0,
                })
                delivery_ctr += 1

    return pd.DataFrame(rows)


def gen_returns(sales_df, products_df):
    n_target = int(np.mean(TARGET_RETURNS))
    cat_of_product = products_df.set_index("Product_ID")["Category_Name"].to_dict()

    sales_df = sales_df.copy()
    sales_df["Category_Name"] = sales_df["Product_ID"].map(cat_of_product)
    return_prone = {"Dairy Products", "Chocolate & Confectionery", "Snacks", "Infant Nutrition"}
    weight = sales_df["Category_Name"].map(lambda c: 2.2 if c in return_prone else 1.0).values
    weight = weight * (sales_df["Sales_Channel"] == "E-commerce").map({True: 1.8, False: 1.0}).values
    weight = weight / weight.sum()

    idx = RNG.choice(sales_df.index.values, size=min(n_target, len(sales_df)), replace=False, p=weight)
    sampled = sales_df.loc[idx]

    rows = []
    for i, (_, s) in enumerate(sampled.iterrows()):
        cat = s["Category_Name"]
        reason_weights = [0.30, 0.20, 0.15, 0.15, 0.15, 0.05] if cat in return_prone else \
                          [0.20, 0.10, 0.25, 0.25, 0.10, 0.10]
        reason = RNG.choice(RETURN_REASONS, p=reason_weights)
        returned_qty = int(max(1, round(s["Quantity"] * RNG.uniform(0.2, 1.0))))
        refund = round(returned_qty * s["Unit_Price"] * (1 - s["Discount"]), 2)
        return_date = pd.Timestamp(s["Order_Date"]) + pd.Timedelta(days=int(RNG.integers(1, 21)))

        rows.append({
            "Return_ID": f"RET{str(i+1).zfill(7)}",
            "Sales_ID": s["Sales_ID"],
            "Store_ID": s["Store_ID"],
            "Product_ID": s["Product_ID"],
            "Return_Date": return_date.date(),
            "Returned_Quantity": returned_qty,
            "Return_Reason": reason,
            "Refund_Amount": refund,
        })

    return pd.DataFrame(rows)
