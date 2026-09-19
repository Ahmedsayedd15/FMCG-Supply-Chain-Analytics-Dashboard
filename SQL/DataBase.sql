-- =====================================================================
-- FMCG Supply Chain — full schema (20 tables)
-- Created in dependency order so every FOREIGN KEY resolves on first run.
-- Run top to bottom in one go.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS fmcg_supply_chain;
USE fmcg_supply_chain;

SET FOREIGN_KEY_CHECKS = 0;  -- safe to re-run DROP TABLEs in any order

DROP TABLE IF EXISTS promotion_details;
DROP TABLE IF EXISTS returns;
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS batches;
DROP TABLE IF EXISTS stock_movements;
DROP TABLE IF EXISTS inventory_snapshots;
DROP TABLE IF EXISTS purchase_order_details;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS promotions;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS stores;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS distributors;
DROP TABLE IF EXISTS warehouses;
DROP TABLE IF EXISTS factories;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS calendar;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- MASTER DATA — no dependencies
-- =====================================================================

CREATE TABLE categories (
    Category_ID    VARCHAR(20) PRIMARY KEY,
    Category_Name  VARCHAR(100) NOT NULL
);

CREATE TABLE suppliers (
    Supplier_ID             VARCHAR(20) PRIMARY KEY,
    Supplier_Name           VARCHAR(150) NOT NULL,
    Supplier_Type           VARCHAR(50),
    Country                 VARCHAR(50),
    City                    VARCHAR(50),
    Governorate             VARCHAR(50),
    Payment_Terms           VARCHAR(50),
    Lead_Time_Days          INT,
    Reliability_Score       DECIMAL(4,2),
    Quality_Score           DECIMAL(4,2),
    Minimum_Order_Quantity  INT,
    Contract_Start_Date     DATE,
    Contract_End_Date       DATE,
    Supplier_Status         VARCHAR(20)
);

CREATE TABLE factories (
    Factory_ID               VARCHAR(20) PRIMARY KEY,
    Factory_Name             VARCHAR(150) NOT NULL,
    Governorate               VARCHAR(50),
    City                     VARCHAR(50),
    Production_Capacity      INT,
    Product_Category         VARCHAR(100),
    Operating_Cost_Per_Unit  DECIMAL(10,2),
    Factory_Status           VARCHAR(20)
);

CREATE TABLE warehouses (
    Warehouse_ID            VARCHAR(20) PRIMARY KEY,
    Warehouse_Name          VARCHAR(150) NOT NULL,
    Governorate              VARCHAR(50),
    City                    VARCHAR(50),
    Warehouse_Type          VARCHAR(50),
    Storage_Capacity        INT,
    Current_Capacity        INT,
    Temperature_Controlled  BOOLEAN,
    Operating_Cost          INT,
    Opening_Date            DATE,
    Warehouse_Status        VARCHAR(20)
);

CREATE TABLE calendar (
    `Date`        DATE PRIMARY KEY,
    Year          INT,
    Month         INT,
    Day           INT,
    Month_Name    VARCHAR(20),
    Quarter       INT,
    Day_Of_Week   VARCHAR(20),
    Is_Weekend    BOOLEAN
);

-- =====================================================================
-- MASTER DATA — depends on the above
-- =====================================================================

CREATE TABLE distributors (
    Distributor_ID          VARCHAR(20) PRIMARY KEY,
    Distributor_Name        VARCHAR(150) NOT NULL,
    Governorate               VARCHAR(50),
    City                     VARCHAR(50),
    Assigned_Warehouse_ID   VARCHAR(20),
    Coverage_Area            VARCHAR(150),
    Vehicle_Count            INT,
    Credit_Limit             INT,
    Payment_Terms            VARCHAR(50),
    Performance_Score        DECIMAL(4,2),
    Distributor_Status       VARCHAR(20),
    FOREIGN KEY (Assigned_Warehouse_ID) REFERENCES warehouses(Warehouse_ID)
);

CREATE TABLE products (
    Product_ID               VARCHAR(20) PRIMARY KEY,
    SKU                      VARCHAR(50) UNIQUE NOT NULL,
    Product_Name             VARCHAR(150) NOT NULL,
    Category_ID              VARCHAR(20),
    Category_Name            VARCHAR(100),
    Subcategory               VARCHAR(100),
    Brand                    VARCHAR(100),
    Package_Size              DECIMAL(10,2),
    Package_Unit               VARCHAR(20),
    Units_Per_Case            INT,
    Unit_Cost                 DECIMAL(10,2),
    Standard_Selling_Price    DECIMAL(10,2),
    Minimum_Shelf_Life_Days   INT,
    Storage_Condition          VARCHAR(50),
    Supplier_ID                VARCHAR(20),
    Factory_ID                 VARCHAR(20),
    Launch_Date                DATE,
    Product_Status              VARCHAR(20),
    Popularity_Rank              INT,
    Popularity_Weight             DECIMAL(6,4),
    FOREIGN KEY (Category_ID) REFERENCES categories(Category_ID),
    FOREIGN KEY (Supplier_ID) REFERENCES suppliers(Supplier_ID),
    FOREIGN KEY (Factory_ID) REFERENCES factories(Factory_ID)
);

CREATE TABLE stores (
    Store_ID               VARCHAR(20) PRIMARY KEY,
    Store_Name              VARCHAR(150) NOT NULL,
    Store_Type              VARCHAR(50),
    Governorate               VARCHAR(50),
    City                     VARCHAR(50),
    Distributor_ID           VARCHAR(20),
    Customer_Segment          VARCHAR(50),
    Opening_Date              DATE,
    Store_Size                INT,
    Monthly_Demand_Level       DECIMAL(10,2),
    Credit_Term                 VARCHAR(50),
    Store_Status                VARCHAR(20),
    FOREIGN KEY (Distributor_ID) REFERENCES distributors(Distributor_ID)
);

CREATE TABLE vehicles (
    Vehicle_ID           VARCHAR(20) PRIMARY KEY,
    Vehicle_Type          VARCHAR(50),
    Capacity               INT,
    Fuel_Type               VARCHAR(30),
    Fuel_Efficiency          DECIMAL(6,2),
    Assigned_Warehouse        VARCHAR(20),
    Vehicle_Status             VARCHAR(20),
    Purchase_Date               DATE,
    Maintenance_Cost             INT,
    FOREIGN KEY (Assigned_Warehouse) REFERENCES warehouses(Warehouse_ID)
);

-- Employees can be assigned to different location types (warehouse, factory,
-- store, distributor...), so Assigned_Location_ID is kept as a plain
-- reference column (no single FK target) with Assigned_Location_Type
-- telling you which table it points into.
CREATE TABLE employees (
    Employee_ID               VARCHAR(20) PRIMARY KEY,
    Employee_Name              VARCHAR(150) NOT NULL,
    Department                  VARCHAR(50),
    Role                         VARCHAR(50),
    Assigned_Location_Type        VARCHAR(30),
    Assigned_Location_ID           VARCHAR(20),
    Governorate                     VARCHAR(50),
    Hire_Date                        DATE,
    Employment_Status                 VARCHAR(20)
);

-- =====================================================================
-- PROCUREMENT
-- =====================================================================

CREATE TABLE purchase_orders (
    PO_ID                    VARCHAR(20) PRIMARY KEY,
    Supplier_ID               VARCHAR(20),
    Warehouse_ID                VARCHAR(20),
    PO_Date                      DATE,
    Expected_Delivery_Date        DATE,
    Actual_Delivery_Date           DATE,
    PO_Status                       VARCHAR(20),
    Payment_Status                   VARCHAR(20),
    Total_PO_Value                    DECIMAL(12,2),
    Delay_Days                         INT,
    FOREIGN KEY (Supplier_ID) REFERENCES suppliers(Supplier_ID),
    FOREIGN KEY (Warehouse_ID) REFERENCES warehouses(Warehouse_ID)
);

CREATE TABLE purchase_order_details (
    PO_Detail_ID         VARCHAR(20) PRIMARY KEY,
    PO_ID                  VARCHAR(20),
    Product_ID               VARCHAR(20),
    Ordered_Quantity          INT,
    Received_Quantity          INT,
    Rejected_Quantity           INT,
    Unit_Cost                    DECIMAL(10,2),
    Line_Total                    DECIMAL(12,2),
    Warehouse_ID                   VARCHAR(20),
    Receipt_Month                    VARCHAR(20),
    FOREIGN KEY (PO_ID) REFERENCES purchase_orders(PO_ID),
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID),
    FOREIGN KEY (Warehouse_ID) REFERENCES warehouses(Warehouse_ID)
);

-- =====================================================================
-- INVENTORY
-- =====================================================================

CREATE TABLE inventory_snapshots (
    Inventory_ID          VARCHAR(20) PRIMARY KEY,
    `Date`                  DATE,
    Warehouse_ID              VARCHAR(20),
    Product_ID                 VARCHAR(20),
    Opening_Stock                DECIMAL(12,2),
    Received_Quantity              DECIMAL(12,2),
    Produced_Quantity                DECIMAL(12,2),
    Sold_Quantity                      DECIMAL(12,2),
    Transferred_In                       DECIMAL(12,2),
    Transferred_Out                        DECIMAL(12,2),
    Returned_Quantity                        DECIMAL(12,2),
    Damaged_Quantity                           DECIMAL(12,2),
    Expired_Quantity                             DECIMAL(12,2),
    Closing_Stock                                  DECIMAL(12,2),
    Safety_Stock                                     DECIMAL(12,2),
    Reorder_Point                                      DECIMAL(12,2),
    Reorder_Quantity                                     DECIMAL(12,2),
    Lost_Sales_Quantity                                    DECIMAL(12,2),
    Stockout_Flag                                            BOOLEAN,
    FOREIGN KEY (Warehouse_ID) REFERENCES warehouses(Warehouse_ID),
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID),
    FOREIGN KEY (`Date`) REFERENCES calendar(`Date`)
);

CREATE TABLE stock_movements (
    Movement_ID       VARCHAR(20) PRIMARY KEY,
    `Date`              DATE,
    Warehouse_ID          VARCHAR(20),
    Product_ID              VARCHAR(20),
    Movement_Type             VARCHAR(30),
    Quantity                    DECIMAL(12,2),
    FOREIGN KEY (Warehouse_ID) REFERENCES warehouses(Warehouse_ID),
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID),
    FOREIGN KEY (`Date`) REFERENCES calendar(`Date`)
);

CREATE TABLE batches (
    Batch_ID            VARCHAR(20) PRIMARY KEY,
    Product_ID             VARCHAR(20),
    Warehouse_ID              VARCHAR(20),
    Production_Date             DATE,
    Expiry_Date                    DATE,
    Quantity                          DECIMAL(12,2),
    Days_To_Expiry                       INT,
    Expired_Flag                            BOOLEAN,
    Near_Expiry_Flag                           BOOLEAN,
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID),
    FOREIGN KEY (Warehouse_ID) REFERENCES warehouses(Warehouse_ID)
);

-- =====================================================================
-- SALES & OPERATIONS
-- =====================================================================

CREATE TABLE promotions (
    Promotion_ID           VARCHAR(20) PRIMARY KEY,
    Promotion_Name           VARCHAR(150) NOT NULL,
    Promotion_Type             VARCHAR(50),
    Start_Date                    DATE,
    End_Date                        DATE,
    Discount_Percentage                DECIMAL(5,2),
    Budget                                DECIMAL(12,2),
    Promotion_Status                        VARCHAR(20)
);

CREATE TABLE sales (
    Sales_ID              VARCHAR(20) PRIMARY KEY,
    Order_Date               DATE,
    Store_ID                    VARCHAR(20),
    Product_ID                     VARCHAR(20),
    Warehouse_ID                      VARCHAR(20),
    Quantity                             INT,
    Unit_Price                              DECIMAL(10,2),
    Discount_Percentage                        DECIMAL(5,2),
    Discount_Amount                               DECIMAL(10,2),
    Sales_Amount                                     DECIMAL(12,2),
    Cost_Amount                                         DECIMAL(12,2),
    Profit                                                 DECIMAL(12,2),
    Promotion_ID                                              VARCHAR(20),
    Customer_Segment                                             VARCHAR(50),
    Payment_Method                                                  VARCHAR(30),
    Sales_Channel                                                      VARCHAR(30),
    FOREIGN KEY (Store_ID) REFERENCES stores(Store_ID),
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID),
    FOREIGN KEY (Warehouse_ID) REFERENCES warehouses(Warehouse_ID),
    FOREIGN KEY (Promotion_ID) REFERENCES promotions(Promotion_ID),
    FOREIGN KEY (Order_Date) REFERENCES calendar(`Date`)
);

CREATE TABLE deliveries (
    Delivery_ID             VARCHAR(20) PRIMARY KEY,
    Sales_ID                   VARCHAR(20),
    Distributor_ID                VARCHAR(20),
    Vehicle_ID                       VARCHAR(20),
    Dispatch_Date                       DATE,
    Expected_Delivery_Date                 DATE,
    Actual_Delivery_Date                      DATE,
    Delivery_Status                              VARCHAR(20),
    Delivery_Days                                   INT,
    Delivery_Cost                                      DECIMAL(10,2),
    FOREIGN KEY (Sales_ID) REFERENCES sales(Sales_ID),
    FOREIGN KEY (Distributor_ID) REFERENCES distributors(Distributor_ID),
    FOREIGN KEY (Vehicle_ID) REFERENCES vehicles(Vehicle_ID)
);

CREATE TABLE returns (
    Return_ID           VARCHAR(20) PRIMARY KEY,
    Sales_ID               VARCHAR(20),
    Product_ID                 VARCHAR(20),
    Return_Date                   DATE,
    Returned_Quantity                INT,
    Return_Reason                       VARCHAR(100),
    Refund_Amount                          DECIMAL(10,2),
    Return_Status                             VARCHAR(20),
    FOREIGN KEY (Sales_ID) REFERENCES sales(Sales_ID),
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID)
);

CREATE TABLE promotion_details (
    Promotion_Detail_ID       VARCHAR(20) PRIMARY KEY,
    Promotion_ID                 VARCHAR(20),
    Product_ID                       VARCHAR(20),
    Original_Price                      DECIMAL(10,2),
    Discounted_Price                       DECIMAL(10,2),
    FOREIGN KEY (Promotion_ID) REFERENCES promotions(Promotion_ID),
    FOREIGN KEY (Product_ID) REFERENCES products(Product_ID)
);

-- =====================================================================
-- LOAD DATA — adjust paths, keep IGNORE 1 ROWS for CSV headers.
-- Order matches the CREATE TABLE order above (respects FK dependencies).
-- =====================================================================

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/categories.csv' INTO TABLE categories
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/suppliers.csv' INTO TABLE suppliers
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/factories.csv' INTO TABLE factories
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/warehouses.csv' INTO TABLE warehouses
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/calendar.csv' INTO TABLE calendar
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/distributors.csv' INTO TABLE distributors
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/products.csv' INTO TABLE products
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/stores.csv' INTO TABLE stores
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/vehicles.csv' INTO TABLE vehicles
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/employees.csv' INTO TABLE employees
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/purchase_orders.csv' INTO TABLE purchase_orders
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/purchase_order_details.csv' INTO TABLE purchase_order_details
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/inventory_snapshots.csv' INTO TABLE inventory_snapshots
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/stock_movements.csv' INTO TABLE stock_movements
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/batches.csv' INTO TABLE batches
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/promotions.csv' INTO TABLE promotions
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- =========================
-- SALES
-- =========================

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/sales.csv'
INTO TABLE sales
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
Sales_ID,
Order_Date,
Store_ID,
@Distributor_ID,
Warehouse_ID,
Product_ID,
Quantity,
Unit_Price,
@Discount,
@Net_Sales,
@Cost,
@Gross_Profit,
Payment_Method,
Sales_Channel
)
SET
Discount_Percentage = @Discount,
Sales_Amount = @Net_Sales,
Cost_Amount = @Cost,
Profit = @Gross_Profit;



-- =========================
-- DELIVERIES
-- =========================

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/deliveries.csv'
INTO TABLE deliveries
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
Delivery_ID,
Sales_ID,
@Warehouse_ID,
Distributor_ID,
Vehicle_ID,
Dispatch_Date,
Expected_Delivery_Date,
Actual_Delivery_Date,
Delivery_Status,
@Distance_KM,
@Transportation_Cost,
@Delay_Days
)
SET
Delivery_Days = @Delay_Days,
Delivery_Cost = @Transportation_Cost;



-- =========================
-- RETURNS
-- =========================

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/returns.csv'
INTO TABLE returns
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
Return_ID,
Sales_ID,
@Store_ID,
Product_ID,
Return_Date,
Returned_Quantity,
Return_Reason,
Refund_Amount
);
-- =========================
-- PROMOTION DETAILS
-- =========================

LOAD DATA LOCAL INFILE 'F:/Project/Nestle/Data/data/promotion_details.csv'
INTO TABLE promotion_details
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- =====================================================================
-- Sanity checks — run after all LOAD DATA statements
-- =====================================================================
SELECT 'categories' AS tbl, COUNT(*) FROM categories
UNION ALL SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL SELECT 'factories', COUNT(*) FROM factories
UNION ALL SELECT 'warehouses', COUNT(*) FROM warehouses
UNION ALL SELECT 'calendar', COUNT(*) FROM calendar
UNION ALL SELECT 'distributors', COUNT(*) FROM distributors
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'stores', COUNT(*) FROM stores
UNION ALL SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL SELECT 'employees', COUNT(*) FROM employees
UNION ALL SELECT 'purchase_orders', COUNT(*) FROM purchase_orders
UNION ALL SELECT 'purchase_order_details', COUNT(*) FROM purchase_order_details
UNION ALL SELECT 'inventory_snapshots', COUNT(*) FROM inventory_snapshots
UNION ALL SELECT 'stock_movements', COUNT(*) FROM stock_movements
UNION ALL SELECT 'batches', COUNT(*) FROM batches
UNION ALL SELECT 'promotions', COUNT(*) FROM promotions
UNION ALL SELECT 'sales', COUNT(*) FROM sales
UNION ALL SELECT 'deliveries', COUNT(*) FROM deliveries
UNION ALL SELECT 'returns', COUNT(*) FROM returns
UNION ALL SELECT 'promotion_details', COUNT(*) FROM promotion_details;