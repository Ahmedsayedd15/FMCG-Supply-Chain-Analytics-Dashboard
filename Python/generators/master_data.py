"""
generators/master_data.py
==========================
Phase 1 — Master Data.
Products, Categories, Suppliers, Factories, Warehouses, Distributors,
Retail Stores, Vehicles, Employees.

These tables have no dependency on transactional data, but transactional
generators (Phases 2-5) depend heavily on them, so referential correctness
here matters most.
"""

import numpy as np
import pandas as pd

from config import (
    RNG, N_PRODUCTS, N_SUPPLIERS, N_FACTORIES, N_WAREHOUSES, N_DISTRIBUTORS,
    N_STORES, N_VEHICLES, N_EMPLOYEES, CATEGORIES, BRANDS_BY_CATEGORY,
    PACKAGE_UNITS, STORAGE_CONDITIONS, GOV_LIST, GOVERNORATES, GOV_WEIGHTS,
    STORE_TYPES, STORE_TYPE_LIST, STORE_TYPE_WEIGHTS, CUSTOMER_SEGMENTS,
    WAREHOUSE_TYPES, VEHICLE_TYPES, FUEL_TYPES, SUPPLIER_TYPES,
    LOCAL_SUPPLIER_SHARE, EMPLOYEE_DEPARTMENTS, EMPLOYEE_ROLES, make_ids,
)
from utils.helpers import zipf_weights, random_dates_between
from utils.namegen import (
    local_supplier_name, imported_supplier_name, distributor_name,
    store_name, factory_name, person_name,
)


def gen_categories():
    return pd.DataFrame(CATEGORIES)[["Category_ID", "Category_Name"]]


def _pick_city(gov):
    return RNG.choice(GOVERNORATES[gov]["cities"])


def gen_products(categories_df, supplier_ids, factory_ids):
    n = N_PRODUCTS
    ids = make_ids("PRD", n)
    cat_ids = [c["Category_ID"] for c in CATEGORIES]
    # not perfectly uniform across categories -> some categories bigger (Snacks, Dairy)
    cat_weights = np.array([1.3, 1.4, 0.6, 0.8, 0.9, 1.2, 0.7, 1.0, 1.5, 0.7])
    cat_weights = cat_weights / cat_weights.sum()
    chosen_cats = RNG.choice(cat_ids, size=n, p=cat_weights)

    cat_lookup = {c["Category_ID"]: c for c in CATEGORIES}

    rows = []
    # Zipf-based popularity rank feeding downstream demand weighting
    popularity_rank = RNG.permutation(np.arange(1, n + 1))

    for i in range(n):
        pid = ids[i]
        cat_id = chosen_cats[i]
        cat_name = cat_lookup[cat_id]["Category_Name"]
        brand = RNG.choice(BRANDS_BY_CATEGORY[cat_id])
        unit = RNG.choice(PACKAGE_UNITS, p=[0.30, 0.25, 0.15, 0.10, 0.20])
        pack_size = int(RNG.choice([50, 100, 150, 200, 250, 330, 500, 750, 1000, 1500])) \
            if unit in ("g", "ml") else round(float(RNG.uniform(0.25, 5)), 2)

        storage = "Chilled" if cat_name == "Dairy Products" else (
            "Frozen" if cat_name == "Infant Nutrition" and RNG.random() < 0.05 else
            RNG.choice(STORAGE_CONDITIONS, p=[0.65, 0.20, 0.05, 0.10])
        )

        # shelf life varies strongly by category
        shelf_life_map = {
            "Dairy Products": (10, 45), "Bottled Water": (180, 730),
            "Infant Nutrition": (270, 720), "Coffee": (270, 720),
            "Cereals": (180, 540), "Chocolate & Confectionery": (120, 365),
            "Pet Care": (270, 730), "Culinary Products": (180, 540),
            "Snacks": (90, 270), "Nutrition Products": (180, 540),
        }
        lo, hi = shelf_life_map[cat_name]
        shelf_life = int(RNG.integers(lo, hi + 1))

        unit_cost = round(float(RNG.lognormal(mean=1.6, sigma=0.7)), 2)
        unit_cost = max(unit_cost, 2.5)
        margin_factor = RNG.uniform(1.15, 1.85)
        price = round(unit_cost * margin_factor, 2)

        launch_date = random_dates_between(RNG, "2015-01-01", "2023-06-01", 1)[0].date()
        status = RNG.choice(["Active", "Active", "Active", "Active", "Discontinued"], p=[0.75, 0.1, 0.06, 0.05, 0.04])

        rows.append({
            "Product_ID": pid,
            "SKU": f"SKU-{pid[3:]}-{cat_id}",
            "Product_Name": f"{brand} {cat_name.split()[0]} {pack_size}{unit}",
            "Category_ID": cat_id,
            "Category_Name": cat_name,
            "Subcategory": f"{cat_name} - {brand}",
            "Brand": brand,
            "Package_Size": pack_size,
            "Package_Unit": unit,
            "Units_Per_Case": int(RNG.choice([6, 12, 24, 48])),
            "Unit_Cost": unit_cost,
            "Standard_Selling_Price": price,
            "Minimum_Shelf_Life_Days": shelf_life,
            "Storage_Condition": storage,
            "Supplier_ID": RNG.choice(supplier_ids),
            "Factory_ID": RNG.choice(factory_ids),
            "Launch_Date": launch_date,
            "Product_Status": status,
            "Popularity_Rank": int(popularity_rank[i]),
        })

    df = pd.DataFrame(rows)
    # popularity weight for downstream sales generation (Zipf-like)
    weights = zipf_weights(n, s=1.05)
    order = df["Popularity_Rank"].values - 1
    df["Popularity_Weight"] = weights[order]
    return df


def gen_suppliers():
    n = N_SUPPLIERS
    ids = make_ids("SUP", n)
    n_local = int(n * LOCAL_SUPPLIER_SHARE)
    types = ["Local"] * n_local + ["Imported"] * (n - n_local)
    RNG.shuffle(types)

    rows = []
    local_ctr, import_ctr = 1, 1
    for i in range(n):
        sup_type = types[i]
        if sup_type == "Local":
            gov = RNG.choice(GOV_LIST, p=GOV_WEIGHTS)
            city = _pick_city(gov)
            country = "Egypt"
            name = local_supplier_name(local_ctr)
            local_ctr += 1
            lead_time = int(RNG.integers(3, 21))
        else:
            gov, city = "N/A", "N/A"
            country = RNG.choice(["China", "Germany", "Netherlands", "Turkey", "India", "Brazil", "Switzerland"])
            name = imported_supplier_name(import_ctr)
            import_ctr += 1
            lead_time = int(RNG.integers(20, 75))

        reliability = float(np.clip(RNG.normal(0.85, 0.10), 0.35, 0.99))
        quality = float(np.clip(RNG.normal(0.90, 0.08), 0.40, 0.99))
        start = random_dates_between(RNG, "2015-01-01", "2023-01-01", 1)[0]
        end = start + pd.Timedelta(days=int(RNG.integers(730, 2555)))

        rows.append({
            "Supplier_ID": ids[i],
            "Supplier_Name": name,
            "Supplier_Type": sup_type,
            "Country": country,
            "City": city,
            "Governorate": gov,
            "Payment_Terms": RNG.choice(["Net 30", "Net 45", "Net 60", "Net 90", "Advance Payment"]),
            "Lead_Time_Days": lead_time,
            "Reliability_Score": round(reliability, 2),
            "Quality_Score": round(quality, 2),
            "Minimum_Order_Quantity": int(RNG.choice([50, 100, 250, 500, 1000])),
            "Contract_Start_Date": start.date(),
            "Contract_End_Date": end.date(),
            "Supplier_Status": RNG.choice(["Active", "Active", "Active", "Under Review", "Suspended"], p=[0.85, 0.08, 0.04, 0.02, 0.01]),
        })
    return pd.DataFrame(rows)


def gen_factories():
    n = N_FACTORIES
    ids = make_ids("FAC", n)
    cats = [c["Category_Name"] for c in CATEGORIES]
    rows = []
    for i in range(n):
        gov = RNG.choice(GOV_LIST, p=GOV_WEIGHTS)
        city = _pick_city(gov)
        rows.append({
            "Factory_ID": ids[i],
            "Factory_Name": factory_name(i + 1, gov),
            "Governorate": gov,
            "City": city,
            "Production_Capacity": int(RNG.integers(50_000, 500_000)),
            "Product_Category": RNG.choice(cats),
            "Operating_Cost_Per_Unit": round(float(RNG.uniform(0.5, 4.0)), 2),
            "Factory_Status": RNG.choice(["Operational", "Operational", "Operational", "Maintenance"], p=[0.90, 0.05, 0.03, 0.02]),
        })
    return pd.DataFrame(rows)


def gen_warehouses():
    n = N_WAREHOUSES
    ids = make_ids("WH", n)
    rows = []
    for i in range(n):
        gov = RNG.choice(GOV_LIST, p=GOV_WEIGHTS)
        city = _pick_city(gov)
        wtype = RNG.choice(WAREHOUSE_TYPES, p=[0.20, 0.45, 0.15, 0.20])
        capacity = int(RNG.integers(80_000, 600_000))
        current = int(capacity * RNG.uniform(0.35, 0.85))
        rows.append({
            "Warehouse_ID": ids[i],
            "Warehouse_Name": f"{wtype} - {city}",
            "Governorate": gov,
            "City": city,
            "Warehouse_Type": wtype,
            "Storage_Capacity": capacity,
            "Current_Capacity": current,
            "Temperature_Controlled": wtype == "Cold Storage" or RNG.random() < 0.15,
            "Operating_Cost": int(RNG.integers(50_000, 300_000)),
            "Opening_Date": random_dates_between(RNG, "2010-01-01", "2021-01-01", 1)[0].date(),
            "Warehouse_Status": "Operational",
        })
    return pd.DataFrame(rows)


def gen_distributors(warehouse_ids):
    n = N_DISTRIBUTORS
    ids = make_ids("DIST", n)
    rows = []
    for i in range(n):
        gov = RNG.choice(GOV_LIST, p=GOV_WEIGHTS)
        city = _pick_city(gov)
        perf = float(np.clip(RNG.normal(0.75, 0.15), 0.20, 0.99))
        rows.append({
            "Distributor_ID": ids[i],
            "Distributor_Name": distributor_name(i + 1),
            "Governorate": gov,
            "City": city,
            "Assigned_Warehouse_ID": RNG.choice(warehouse_ids),
            "Coverage_Area": f"{gov} & surrounding areas",
            "Vehicle_Count": int(RNG.integers(2, 25)),
            "Credit_Limit": int(RNG.integers(50_000, 2_000_000)),
            "Payment_Terms": RNG.choice(["Net 15", "Net 30", "Net 45", "Cash on Delivery"]),
            "Performance_Score": round(perf, 2),
            "Distributor_Status": RNG.choice(["Active", "Active", "Active", "Underperforming"], p=[0.80, 0.10, 0.05, 0.05]),
        })
    return pd.DataFrame(rows)


def gen_stores(distributors_df):
    n = N_STORES
    ids = make_ids("STR", n)
    types = RNG.choice(STORE_TYPE_LIST, size=n, p=STORE_TYPE_WEIGHTS)

    dist_ids = distributors_df["Distributor_ID"].values
    dist_gov = distributors_df.set_index("Distributor_ID")["Governorate"].to_dict()

    rows = []
    for i in range(n):
        stype = types[i]
        dist_id = RNG.choice(dist_ids)
        gov = dist_gov[dist_id]
        city = _pick_city(gov)
        size_lo, size_hi = STORE_TYPES[stype]["size_range"]
        size = 0 if stype == "E-commerce" else int(RNG.integers(size_lo, size_hi + 1))

        demand_level = float(np.clip(RNG.normal(GOVERNORATES[gov]["demand_weight"], 0.2), 0.1, 1.5))

        rows.append({
            "Store_ID": ids[i],
            "Store_Name": store_name(i + 1, stype),
            "Store_Type": stype,
            "Governorate": gov,
            "City": city,
            "Distributor_ID": dist_id,
            "Customer_Segment": RNG.choice(CUSTOMER_SEGMENTS, p=[0.15, 0.50, 0.25, 0.10]),
            "Opening_Date": random_dates_between(RNG, "2012-01-01", "2024-06-01", 1)[0].date(),
            "Store_Size": size,
            "Monthly_Demand_Level": round(demand_level, 2),
            "Credit_Term": RNG.choice(["Cash", "Net 7", "Net 15", "Net 30"], p=[0.45, 0.20, 0.20, 0.15]),
            "Store_Status": RNG.choice(["Active", "Active", "Active", "Closed"], p=[0.90, 0.05, 0.03, 0.02]),
        })
    return pd.DataFrame(rows)


def gen_vehicles(warehouse_ids):
    n = N_VEHICLES
    ids = make_ids("VEH", n)
    rows = []
    for i in range(n):
        vtype = RNG.choice([v["type"] for v in VEHICLE_TYPES], p=[0.35, 0.35, 0.15, 0.15])
        cap_lo, cap_hi = next(v["capacity_range"] for v in VEHICLE_TYPES if v["type"] == vtype)
        rows.append({
            "Vehicle_ID": ids[i],
            "Vehicle_Type": vtype,
            "Capacity": int(RNG.integers(cap_lo, cap_hi + 1)),
            "Fuel_Type": RNG.choice(FUEL_TYPES, p=[0.75, 0.15, 0.10]),
            "Fuel_Efficiency": round(float(RNG.uniform(3.5, 12.0)), 1),
            "Assigned_Warehouse": RNG.choice(warehouse_ids),
            "Vehicle_Status": RNG.choice(["Active", "Active", "Active", "In Maintenance", "Retired"], p=[0.82, 0.08, 0.05, 0.03, 0.02]),
            "Purchase_Date": random_dates_between(RNG, "2014-01-01", "2024-01-01", 1)[0].date(),
            "Maintenance_Cost": int(RNG.integers(2_000, 40_000)),
        })
    return pd.DataFrame(rows)


def gen_employees(warehouse_ids, factory_ids, distributor_ids):
    n = N_EMPLOYEES
    ids = make_ids("EMP", n)
    rows = []
    for i in range(n):
        dept = RNG.choice(EMPLOYEE_DEPARTMENTS)
        role = RNG.choice(EMPLOYEE_ROLES[dept])
        if dept == "Warehouse Operations":
            loc_type, loc_id = "Warehouse", RNG.choice(warehouse_ids)
        elif dept == "Production":
            loc_type, loc_id = "Factory", RNG.choice(factory_ids)
        elif dept in ("Sales", "Logistics"):
            loc_type, loc_id = "Distributor", RNG.choice(distributor_ids)
        else:
            loc_type, loc_id = "Head Office", "HQ"

        gov = RNG.choice(GOV_LIST, p=GOV_WEIGHTS)
        rows.append({
            "Employee_ID": ids[i],
            "Employee_Name": person_name(),
            "Department": dept,
            "Role": role,
            "Assigned_Location_Type": loc_type,
            "Assigned_Location_ID": loc_id,
            "Governorate": gov,
            "Hire_Date": random_dates_between(RNG, "2015-01-01", "2025-06-01", 1)[0].date(),
            "Employment_Status": RNG.choice(["Active", "Active", "Active", "On Leave", "Terminated"], p=[0.88, 0.05, 0.03, 0.02, 0.02]),
        })
    return pd.DataFrame(rows)
