"""
validators/validate.py
=======================
Phase 6 — Data Quality Validation.
Runs after generation and prints a report. Raises AssertionError (failing
loudly) on CRITICAL violations only; WARNING-level issues (expected, small
amounts of realistic imperfection) are reported but do not stop the run.
"""

import pandas as pd
import numpy as np


class ValidationReport:
    def __init__(self):
        self.checks = []

    def check(self, name, passed, detail="", critical=True):
        self.checks.append((name, passed, detail, critical))

    def print_report(self):
        print("\n" + "=" * 70)
        print("DATA QUALITY VALIDATION REPORT")
        print("=" * 70)
        n_pass = sum(1 for c in self.checks if c[1])
        n_fail = len(self.checks) - n_pass
        for name, passed, detail, critical in self.checks:
            status = "PASS" if passed else ("FAIL[CRITICAL]" if critical else "WARN")
            print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
        print("-" * 70)
        print(f"Total checks: {len(self.checks)} | Passed: {n_pass} | Failed: {n_fail}")
        print("=" * 70)

        critical_failures = [c for c in self.checks if not c[1] and c[3]]
        if critical_failures:
            names = ", ".join(c[0] for c in critical_failures)
            raise AssertionError(f"CRITICAL data quality violations found: {names}")


def validate_all(tables: dict):
    r = ValidationReport()

    products = tables["products"]
    suppliers = tables["suppliers"]
    warehouses = tables["warehouses"]
    distributors = tables["distributors"]
    stores = tables["stores"]
    pos = tables["purchase_orders"]
    pod = tables["purchase_order_details"]
    inventory = tables["inventory_snapshots"]
    movements = tables["stock_movements"]
    sales = tables["sales"]
    deliveries = tables["deliveries"]
    returns = tables["returns"]
    batches = tables["batches"]

    # --- Duplicate primary keys ---
    for name, df, pk in [
        ("products", products, "Product_ID"), ("suppliers", suppliers, "Supplier_ID"),
        ("warehouses", warehouses, "Warehouse_ID"), ("distributors", distributors, "Distributor_ID"),
        ("stores", stores, "Store_ID"), ("purchase_orders", pos, "PO_ID"),
        ("sales", sales, "Sales_ID"), ("deliveries", deliveries, "Delivery_ID"),
        ("returns", returns, "Return_ID"), ("inventory_snapshots", inventory, "Inventory_ID"),
    ]:
        dup = df[pk].duplicated().sum()
        r.check(f"No duplicate PKs in {name}", dup == 0, f"{dup} duplicates found")

    # --- Orphan foreign keys ---
    r.check("Sales.Product_ID all exist in Products",
            sales["Product_ID"].isin(products["Product_ID"]).all())
    r.check("Sales.Store_ID all exist in Stores",
            sales["Store_ID"].isin(stores["Store_ID"]).all())
    r.check("Purchase_Order_Details.PO_ID all exist in Purchase_Orders",
            pod["PO_ID"].isin(pos["PO_ID"]).all())
    r.check("Stores.Distributor_ID all exist in Distributors",
            stores["Distributor_ID"].isin(distributors["Distributor_ID"]).all())
    r.check("Returns.Sales_ID all exist in Sales",
            returns["Sales_ID"].isin(sales["Sales_ID"]).all())

    # --- Negative quantities ---
    r.check("No negative Sales.Quantity", (sales["Quantity"] >= 0).all())
    r.check("No negative Inventory Closing_Stock", (inventory["Closing_Stock"] >= -0.01).all())
    r.check("No negative Returned_Quantity", (returns["Returned_Quantity"] >= 0).all())

    # --- Received <= Ordered (PO details) ---
    over_received = (pod["Received_Quantity"] > pod["Ordered_Quantity"]).sum()
    r.check("Received_Quantity <= Ordered_Quantity", over_received == 0, f"{over_received} violations")

    # --- Inventory equation consistency (spot check, tolerance for rounding) ---
    calc_closing = (
        inventory["Opening_Stock"] + inventory["Received_Quantity"] + inventory["Produced_Quantity"]
        + inventory["Transferred_In"] + inventory["Returned_Quantity"]
        - inventory["Sold_Quantity"] - inventory["Transferred_Out"]
        - inventory["Damaged_Quantity"] - inventory["Expired_Quantity"]
    )
    diff = (calc_closing - inventory["Closing_Stock"]).abs()
    bad_rows = (diff > 1.0).sum()
    r.check("Inventory equation holds (Closing = Opening+In-Out)", bad_rows == 0,
            f"{bad_rows}/{len(inventory)} rows off by >1 unit (rounding)")

    # --- Sales never exceed what inventory sim made available (by construction) ---
    sales_tmp = sales[["Warehouse_ID", "Product_ID", "Order_Date", "Quantity"]].copy()
    sales_tmp["Month"] = pd.to_datetime(sales_tmp["Order_Date"]).dt.strftime("%Y-%m")
    sales_by_key = (sales_tmp.groupby(["Warehouse_ID", "Product_ID", "Month"], as_index=False)["Quantity"]
                    .sum().rename(columns={"Quantity": "sales_qty"}))

    inv_tmp = inventory[["Warehouse_ID", "Product_ID", "Date", "Sold_Quantity"]].copy()
    inv_tmp["Month"] = pd.to_datetime(inv_tmp["Date"]).dt.strftime("%Y-%m")
    inv_by_key = inv_tmp[["Warehouse_ID", "Product_ID", "Month", "Sold_Quantity"]].rename(
        columns={"Sold_Quantity": "inv_sold_qty"})

    merged = sales_by_key.merge(inv_by_key, on=["Warehouse_ID", "Product_ID", "Month"], how="left")
    mismatch = (merged["sales_qty"] > merged["inv_sold_qty"] + 1.0).sum()
    r.check("Sales quantity never exceeds simulated available stock", mismatch == 0,
            f"{mismatch}/{len(merged)} warehouse-product-month combos exceeded by >1 unit (rounding)", critical=False)

    # --- Date logic ---
    bad_po_dates = (pd.to_datetime(pos["Actual_Delivery_Date"], errors="coerce") < pd.to_datetime(pos["PO_Date"])).sum()
    r.check("PO Actual_Delivery_Date >= PO_Date", bad_po_dates == 0, f"{bad_po_dates} violations")

    bad_delivery = (
        pd.to_datetime(deliveries["Actual_Delivery_Date"], errors="coerce")
        < pd.to_datetime(deliveries["Dispatch_Date"])
    ).sum()
    r.check("Delivery Actual_Delivery_Date >= Dispatch_Date", bad_delivery == 0, f"{bad_delivery} violations")

    bad_expiry = (pd.to_datetime(batches["Expiry_Date"]) < pd.to_datetime(batches["Production_Date"])).sum()
    r.check("Batch Expiry_Date >= Production_Date", bad_expiry == 0, f"{bad_expiry} violations")

    bad_return_dates = (pd.to_datetime(returns["Return_Date"]) < pd.to_datetime(
        sales.set_index("Sales_ID").loc[returns["Sales_ID"], "Order_Date"].values)).sum()
    r.check("Return_Date >= corresponding Sale's Order_Date", bad_return_dates == 0, f"{bad_return_dates} violations")

    # --- Warehouse capacity sanity (soft check — simplified single-product-line capacity model) ---
    monthly_wh_total = inventory.groupby(["Warehouse_ID", "Date"])["Closing_Stock"].sum().reset_index()
    cap_lookup = warehouses.set_index("Warehouse_ID")["Storage_Capacity"].to_dict()
    monthly_wh_total["Capacity"] = monthly_wh_total["Warehouse_ID"].map(cap_lookup)
    over_capacity = (monthly_wh_total["Closing_Stock"] > monthly_wh_total["Capacity"]).sum()
    r.check("Warehouse aggregate stock stays within Storage_Capacity", over_capacity == 0,
            f"{over_capacity}/{len(monthly_wh_total)} warehouse-months over capacity (abstract unit simplification — see README)",
            critical=False)

    # --- Stock movements reference valid warehouses/products ---
    r.check("Stock_Movements.Warehouse_ID all valid", movements["Warehouse_ID"].isin(warehouses["Warehouse_ID"]).all())
    r.check("Stock_Movements.Product_ID all valid", movements["Product_ID"].isin(products["Product_ID"]).all())

    r.print_report()
    return r
