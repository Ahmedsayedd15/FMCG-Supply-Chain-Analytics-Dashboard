"""
config.py
=========
Single source of truth for the Nestlé Egypt FMCG synthetic dataset.
Every generator MUST import reference data (geography, categories, seed,
ID ranges) from here so tables stay consistent across phases.
"""

import numpy as np

# ---------------------------------------------------------------------------
# REPRODUCIBILITY
# ---------------------------------------------------------------------------
SEED = 42
RNG = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# TIME PERIOD
# ---------------------------------------------------------------------------
START_DATE = "2022-01-01"
END_DATE = "2025-12-31"

# Ramadan approximate date ranges (Gregorian) 2022-2025 — used for seasonality
RAMADAN_RANGES = [
    ("2022-04-02", "2022-05-01"),
    ("2023-03-23", "2023-04-20"),
    ("2024-03-11", "2024-04-08"),
    ("2025-03-01", "2025-03-29"),
]
EID_AL_FITR = ["2022-05-02", "2023-04-21", "2024-04-10", "2025-03-30"]
EID_AL_ADHA = ["2022-07-09", "2023-06-28", "2024-06-16", "2025-06-06"]
BACK_TO_SCHOOL = [(m, y) for y in range(2022, 2026) for m in [9]]

# ---------------------------------------------------------------------------
# DATASET SIZE TARGETS (Portfolio-scale, same logic as enterprise version)
# ---------------------------------------------------------------------------
N_PRODUCTS = 280
N_SUPPLIERS = 130
N_FACTORIES = 20
N_WAREHOUSES = 20
N_DISTRIBUTORS = 130
N_STORES = 3000
N_VEHICLES = 200
N_EMPLOYEES = 320
N_PROMOTIONS = 130

TARGET_SALES_LINES = (200_000, 300_000)
TARGET_STOCK_MOVEMENTS = (400_000, 600_000)
TARGET_DELIVERIES = (35_000, 50_000)
TARGET_RETURNS = (3_000, 5_000)
TARGET_PURCHASE_ORDERS = 8_000

# ---------------------------------------------------------------------------
# GEOGRAPHY — Governorates, Regions, Cities
# ---------------------------------------------------------------------------
GOVERNORATES = {
    "Cairo":          {"region": "Greater Cairo",        "demand_weight": 1.00, "cities": ["Nasr City", "Maadi", "Heliopolis", "Downtown Cairo", "New Cairo"]},
    "Giza":           {"region": "Greater Cairo",        "demand_weight": 0.85, "cities": ["Dokki", "Haram", "6th of October", "Sheikh Zayed", "Faisal"]},
    "Qalyubia":       {"region": "Greater Cairo",        "demand_weight": 0.55, "cities": ["Banha", "Shubra El Kheima", "Qaha"]},
    "Alexandria":     {"region": "Alexandria & North Coast", "demand_weight": 0.80, "cities": ["Miami", "Smouha", "Montaza", "Sidi Gaber"]},
    "Matrouh":        {"region": "Alexandria & North Coast", "demand_weight": 0.30, "cities": ["Marsa Matrouh", "El Alamein"]},
    "Dakahlia":       {"region": "Delta",                "demand_weight": 0.50, "cities": ["Mansoura", "Talkha", "Mit Ghamr"]},
    "Gharbia":        {"region": "Delta",                "demand_weight": 0.48, "cities": ["Tanta", "El Mahalla El Kubra", "Zifta"]},
    "Sharqia":        {"region": "Delta",                "demand_weight": 0.47, "cities": ["Zagazig", "10th of Ramadan", "Belbeis"]},
    "Monufia":        {"region": "Delta",                "demand_weight": 0.42, "cities": ["Shibin El Kom", "Sadat City"]},
    "Beheira":        {"region": "Delta",                "demand_weight": 0.40, "cities": ["Damanhur", "Kafr El Dawwar"]},
    "Kafr El Sheikh": {"region": "Delta",                "demand_weight": 0.35, "cities": ["Kafr El Sheikh City", "Desouk"]},
    "Damietta":       {"region": "Delta",                "demand_weight": 0.33, "cities": ["Damietta City", "Ras El Bar"]},
    "Port Said":      {"region": "Canal",                "demand_weight": 0.38, "cities": ["Port Said City"]},
    "Ismailia":       {"region": "Canal",                "demand_weight": 0.37, "cities": ["Ismailia City", "Fayed"]},
    "Suez":           {"region": "Canal",                "demand_weight": 0.36, "cities": ["Suez City"]},
    "Fayoum":         {"region": "Upper Egypt",          "demand_weight": 0.30, "cities": ["Fayoum City", "Sinnuris"]},
    "Beni Suef":      {"region": "Upper Egypt",          "demand_weight": 0.28, "cities": ["Beni Suef City", "Nasser"]},
    "Minya":          {"region": "Upper Egypt",          "demand_weight": 0.30, "cities": ["Minya City", "Mallawi"]},
    "Assiut":         {"region": "Upper Egypt",          "demand_weight": 0.32, "cities": ["Assiut City", "Dairut"]},
    "Sohag":          {"region": "Upper Egypt",          "demand_weight": 0.29, "cities": ["Sohag City", "Akhmim"]},
    "Qena":           {"region": "Upper Egypt",          "demand_weight": 0.27, "cities": ["Qena City", "Nag Hammadi"]},
    "Luxor":          {"region": "Upper Egypt",          "demand_weight": 0.30, "cities": ["Luxor City"]},
    "Aswan":          {"region": "Upper Egypt",          "demand_weight": 0.26, "cities": ["Aswan City"]},
    "Red Sea":        {"region": "Red Sea",               "demand_weight": 0.34, "cities": ["Hurghada", "Safaga"]},
    "New Valley":     {"region": "Upper Egypt",          "demand_weight": 0.15, "cities": ["Kharga"]},
}
GOV_LIST = list(GOVERNORATES.keys())
GOV_WEIGHTS = np.array([GOVERNORATES[g]["demand_weight"] for g in GOV_LIST])
GOV_WEIGHTS = GOV_WEIGHTS / GOV_WEIGHTS.sum()

# ---------------------------------------------------------------------------
# PRODUCT CATEGORIES  (category_id, name, seasonality profile)
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"Category_ID": "CAT01", "Category_Name": "Coffee",                    "ramadan_mult": 1.35, "summer_mult": 0.90, "eid_mult": 1.10},
    {"Category_ID": "CAT02", "Category_Name": "Dairy Products",            "ramadan_mult": 1.20, "summer_mult": 1.05, "eid_mult": 1.15},
    {"Category_ID": "CAT03", "Category_Name": "Infant Nutrition",          "ramadan_mult": 1.00, "summer_mult": 1.00, "eid_mult": 1.00},
    {"Category_ID": "CAT04", "Category_Name": "Bottled Water",             "ramadan_mult": 1.25, "summer_mult": 1.60, "eid_mult": 1.05},
    {"Category_ID": "CAT05", "Category_Name": "Cereals",                   "ramadan_mult": 0.85, "summer_mult": 0.95, "eid_mult": 1.00},
    {"Category_ID": "CAT06", "Category_Name": "Chocolate & Confectionery", "ramadan_mult": 1.10, "summer_mult": 0.80, "eid_mult": 1.75},
    {"Category_ID": "CAT07", "Category_Name": "Pet Care",                  "ramadan_mult": 1.00, "summer_mult": 1.00, "eid_mult": 0.95},
    {"Category_ID": "CAT08", "Category_Name": "Culinary Products",         "ramadan_mult": 1.55, "summer_mult": 0.95, "eid_mult": 1.20},
    {"Category_ID": "CAT09", "Category_Name": "Snacks",                    "ramadan_mult": 0.90, "summer_mult": 1.15, "eid_mult": 1.30},
    {"Category_ID": "CAT10", "Category_Name": "Nutrition Products",        "ramadan_mult": 1.05, "summer_mult": 1.05, "eid_mult": 1.00},
]

BRANDS_BY_CATEGORY = {
    "CAT01": ["Golden Roast", "Café Select", "MorningCup"],
    "CAT02": ["DairyPure", "FarmFresh", "CremeRoyale"],
    "CAT03": ["BabyGrow", "NutriStart"],
    "CAT04": ["AquaSpring", "PureFlow"],
    "CAT05": ["CrunchStart", "GrainMorn"],
    "CAT06": ["ChocoDelight", "CocoaKing", "SweetNile"],
    "CAT07": ["PetCare Plus", "FurFriend"],
    "CAT08": ["ChefsChoice", "SavoryMix", "QuickCook"],
    "CAT09": ["CrispBite", "SnackTime"],
    "CAT10": ["VitaBoost", "PowerNutri"],
}

PACKAGE_UNITS = ["g", "ml", "kg", "l", "pcs"]
STORAGE_CONDITIONS = ["Ambient", "Chilled", "Frozen", "Dry Storage"]

# ---------------------------------------------------------------------------
# STORE TYPES  (weights + avg monthly sales-lines factor used in Phase 4)
# ---------------------------------------------------------------------------
STORE_TYPES = {
    "Grocery":          {"weight": 0.50, "avg_lines_month": 1.5, "size_range": (20, 80)},
    "Convenience Store":{"weight": 0.25, "avg_lines_month": 1.0, "size_range": (15, 50)},
    "Pharmacy":         {"weight": 0.10, "avg_lines_month": 0.8, "size_range": (15, 60)},
    "Supermarket":      {"weight": 0.08, "avg_lines_month": 4.0, "size_range": (150, 600)},
    "Wholesale":        {"weight": 0.04, "avg_lines_month": 2.5, "size_range": (300, 1200)},
    "Hypermarket":      {"weight": 0.02, "avg_lines_month": 6.0, "size_range": (1500, 6000)},
    "E-commerce":       {"weight": 0.01, "avg_lines_month": 3.0, "size_range": (0, 0)},
}
STORE_TYPE_LIST = list(STORE_TYPES.keys())
STORE_TYPE_WEIGHTS = np.array([STORE_TYPES[s]["weight"] for s in STORE_TYPE_LIST])

CUSTOMER_SEGMENTS = ["Premium", "Mainstream", "Value", "Institutional"]
PAYMENT_METHODS = ["Cash", "Credit Card", "Mobile Wallet", "Bank Transfer", "Credit Term"]
SALES_CHANNELS = ["Traditional Trade", "Modern Trade", "E-commerce", "Wholesale"]

WAREHOUSE_TYPES = ["Central Distribution Center", "Regional Distribution Center", "Cold Storage", "Finished Goods Warehouse"]
VEHICLE_TYPES = [
    {"type": "Small Van",      "capacity_range": (500, 1500)},
    {"type": "Medium Truck",   "capacity_range": (1500, 5000)},
    {"type": "Large Truck",    "capacity_range": (5000, 15000)},
    {"type": "Refrigerated Truck", "capacity_range": (2000, 8000)},
]
FUEL_TYPES = ["Diesel", "Gasoline", "CNG"]

SUPPLIER_TYPES = ["Local", "Imported"]
LOCAL_SUPPLIER_SHARE = 0.80

RETURN_REASONS = ["Damaged Product", "Expired Product", "Wrong Product", "Customer Complaint", "Quality Issue", "Delivery Error"]
PROMOTION_TYPES = ["Percentage Discount", "Buy One Get One", "Bundle", "Seasonal Promotion", "Ramadan Promotion", "Clearance"]

EMPLOYEE_DEPARTMENTS = ["Sales", "Warehouse Operations", "Procurement", "Logistics", "Quality Control", "Finance", "HR", "Production"]
EMPLOYEE_ROLES = {
    "Sales": ["Sales Representative", "Key Account Manager", "Sales Supervisor"],
    "Warehouse Operations": ["Warehouse Operator", "Inventory Controller", "Warehouse Supervisor"],
    "Procurement": ["Procurement Officer", "Buyer", "Procurement Manager"],
    "Logistics": ["Dispatcher", "Fleet Coordinator", "Logistics Manager"],
    "Quality Control": ["QC Inspector", "QA Manager"],
    "Finance": ["Accountant", "Finance Analyst"],
    "HR": ["HR Officer", "Recruiter"],
    "Production": ["Production Operator", "Line Supervisor", "Plant Manager"],
}

# ---------------------------------------------------------------------------
# ID PREFIXES  (single source, avoids collisions across phases)
# ---------------------------------------------------------------------------
ID_PREFIX = {
    "product": "PRD", "supplier": "SUP", "factory": "FAC", "warehouse": "WH",
    "distributor": "DIST", "store": "STR", "vehicle": "VEH", "employee": "EMP",
    "po": "PO", "pod": "POD", "batch": "BATCH", "movement": "MOV",
    "inv_snap": "INV", "sale": "SAL", "delivery": "DLV", "return": "RET",
    "promo": "PROMO", "promo_detail": "PROMD", "category": "CAT",
}


def make_ids(prefix, n, width=6):
    return [f"{prefix}{str(i).zfill(width)}" for i in range(1, n + 1)]
