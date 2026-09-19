"""
generate_data.py
=================
Main orchestrator. Runs every phase in order and writes all CSVs + README.

    python generate_data.py

Phases:
  1. Master Data      -> categories, products, suppliers, factories,
                          warehouses, distributors, stores, vehicles, employees
  2. Procurement      -> purchase_orders, purchase_order_details
  3. Inventory        -> inventory_snapshots, stock_movements (non-sale),
                          batches  (the core month-by-month simulation)
  4. Sales            -> sales, + stock_movements (Customer Sale rows)
  5. Operations       -> promotions, promotion_details, deliveries, returns
  6. Validation       -> prints report, raises on critical failures
  7. Write CSVs + README
"""

import os
import time
import pandas as pd

from config import GOV_LIST
from generators import master_data as md
from generators import procurement as proc
from generators import inventory as inv
from generators import sales as sl
from generators import operations as ops
from validators.validate import validate_all

OUTPUT_DIR = "/home/claude/data_generation/output"


def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(">> PHASE 1: Master Data")
    categories = md.gen_categories()
    suppliers = md.gen_suppliers()
    factories = md.gen_factories()
    warehouses = md.gen_warehouses()
    distributors = md.gen_distributors(warehouses["Warehouse_ID"].values)
    products = md.gen_products(categories, suppliers["Supplier_ID"].values, factories["Factory_ID"].values)
    stores = md.gen_stores(distributors)
    vehicles = md.gen_vehicles(warehouses["Warehouse_ID"].values)
    employees = md.gen_employees(warehouses["Warehouse_ID"].values, factories["Factory_ID"].values, distributors["Distributor_ID"].values)
    print(f"   products={len(products)} suppliers={len(suppliers)} factories={len(factories)} "
          f"warehouses={len(warehouses)} distributors={len(distributors)} stores={len(stores)} "
          f"vehicles={len(vehicles)} employees={len(employees)}  ({time.time()-t0:.1f}s)")

    print(">> PHASE 2: Procurement")
    purchase_orders, purchase_order_details = proc.gen_purchase_orders(products, suppliers, warehouses)
    print(f"   purchase_orders={len(purchase_orders)} purchase_order_details={len(purchase_order_details)}  ({time.time()-t0:.1f}s)")

    print(">> PHASE 5a: Promotions (generated before Sales — Sales needs active discounts)")
    promotions, promotion_details = ops.gen_promotions(products)
    print(f"   promotions={len(promotions)} promotion_details={len(promotion_details)}  ({time.time()-t0:.1f}s)")

    print(">> PHASE 3: Inventory simulation (this is the slow part — please wait)")
    inventory_snapshots, stock_movements_base, batches, sold_qty_lookup, stores_with_wh = inv.run_inventory_simulation(
        products, warehouses, stores, distributors, purchase_order_details
    )
    print(f"   inventory_snapshots={len(inventory_snapshots)} stock_movements(pre-sales)={len(stock_movements_base)} "
          f"batches={len(batches)}  ({time.time()-t0:.1f}s)")

    print(">> PHASE 4: Sales")
    sales, sale_movements = sl.gen_sales(sold_qty_lookup, stores_with_wh, products, promotions, promotion_details)
    stock_movements = pd.concat([stock_movements_base, sale_movements], ignore_index=True)
    print(f"   sales={len(sales)} total_stock_movements={len(stock_movements)}  ({time.time()-t0:.1f}s)")

    print(">> PHASE 5b: Deliveries & Returns")
    deliveries = ops.gen_deliveries(sales, distributors, warehouses, vehicles)
    returns = ops.gen_returns(sales, products)
    print(f"   deliveries={len(deliveries)} returns={len(returns)}  ({time.time()-t0:.1f}s)")

    calendar = pd.DataFrame({"Date": pd.date_range("2022-01-01", "2025-12-31", freq="D")})
    calendar["Year"] = calendar["Date"].dt.year
    calendar["Month"] = calendar["Date"].dt.month
    calendar["Day"] = calendar["Date"].dt.day
    calendar["Month_Name"] = calendar["Date"].dt.strftime("%B")
    calendar["Quarter"] = calendar["Date"].dt.quarter
    calendar["Day_Of_Week"] = calendar["Date"].dt.strftime("%A")
    calendar["Is_Weekend"] = calendar["Date"].dt.dayofweek.isin([4, 5])  # Fri/Sat weekend in Egypt

    tables = {
        "categories": categories, "products": products, "suppliers": suppliers,
        "factories": factories, "warehouses": warehouses, "distributors": distributors,
        "stores": stores.drop(columns=["Warehouse_ID", "line_factor", "pull"], errors="ignore"),
        "vehicles": vehicles, "employees": employees,
        "purchase_orders": purchase_orders, "purchase_order_details": purchase_order_details,
        "inventory_snapshots": inventory_snapshots, "stock_movements": stock_movements,
        "batches": batches, "sales": sales, "deliveries": deliveries, "returns": returns,
        "promotions": promotions, "promotion_details": promotion_details, "calendar": calendar,
    }

    print(">> PHASE 6: Validation")
    validate_all(tables)

    print(">> Writing CSVs")
    for name, df in tables.items():
        path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"   {name}.csv  ({len(df)} rows, {os.path.getsize(path)/1e6:.1f} MB)")

    print(f"\nDONE in {time.time()-t0:.1f}s. Output at {OUTPUT_DIR}")
    return tables


if __name__ == "__main__":
    main()
