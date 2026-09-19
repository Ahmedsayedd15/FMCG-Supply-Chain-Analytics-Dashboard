🏭 FMCG Supply Chain Analytics Dashboard

An end-to-end Business Intelligence project built to analyze the full supply chain of a simulated FMCG (Fast-Moving Consumer Goods) company — inspired by Nestlé — using Python, MySQL, Power Query, Power BI, and Deneb (Vega-Lite).

The dashboard provides executives with insights into sales, inventory, procurement, logistics, and promotions to support data-driven decision-making across the entire journey from supplier to shelf.

📌 Project Overview
This project simulates a real-world FMCG supply chain environment by generating a large-scale relational dataset using Python (Faker), storing and managing it in MySQL, cleaning and transforming it using Power Query, and building an interactive Power BI dashboard on top of a fully modeled relational schema.

The dashboard answers key business questions such as:

How is the company performing overall — sales, profit, and inventory?
Which products and channels actually drive profitable sales, not just volume?
How much inventory do we hold, and where is stock at risk of loss?
Are suppliers reliable, and where are procurement costs going?
Are deliveries on time, and what does logistics actually cost?
Are promotions driving real incremental sales, or just compressing margins?
How does company performance change over time?

🚀 Dashboard Pages

🏠 Landing Page
A custom-branded HTML/CSS landing page with company identity and navigation into every analytical module.

📊 Executive Overview
High-level KPIs — total sales, net profit, refunds, and current inventory — with a company-wide view of performance and returns.

🛒 Sales & Distribution
Sales trends, product performance, regional performance, and channel performance (Traditional Trade, Modern Trade, Wholesale, E-commerce).

📦 Inventory & Warehousing
Stock levels, inventory value, stock coverage, loss rate, warehouse health, and product-level overstock/expiry risk.

🚚 Procurement & Suppliers
Procurement spend, on-time delivery from suppliers, rejection rates, contract expiry timelines, and supplier payment terms.

🚛 Logistics & Delivery
Delivery status breakdown, on-time delivery performance, distributor performance, and delivery cost by vehicle type.

🏷️ Products & Promotions
Product and category performance, promotion impact on sales, and discount levels across active campaigns.

🛠️ Tech Stack
Python
Faker
MySQL
Power Query
Power BI
DAX
Deneb (Vega-Lite)
Data Modeling
HTML & CSS

📂 Project Workflow

Python (Faker) Data Generation

⬇️

MySQL Database (20 Tables)

⬇️

Power Query

⬇️

Data Cleaning & Transformation

⬇️

Data Modeling

⬇️

DAX Measures & KPIs

⬇️

Interactive Power BI Dashboard (with Deneb custom visuals)

📸 Dashboard Preview

Executive Overview
<img width="1220" height="509" alt="Executive Overview" src="https://github.com/user-attachments/assets/a9d02eed-564a-4882-832f-55c472a0bd7a" />

Sales & Distribution
<img width="1221" height="506" alt="Sales   Distribution" src="https://github.com/user-attachments/assets/e227f3e9-82e3-4ed2-a8df-ace6f73769b9" />

Inventory & Warehousing
<img width="1219" height="505" alt="Inventory   Warehousing" src="https://github.com/user-attachments/assets/be29ef69-7594-43a2-878f-a06bf8b710c6" />

Procurement & Suppliers
<img width="1222" height="506" alt="Procurement   Suppliers" src="https://github.com/user-attachments/assets/8f07a8b1-6749-49a6-8acc-65e4273783a8" />

Logistics & Delivery
<img width="1221" height="507" alt="Logistics   Delivery" src="https://github.com/user-attachments/assets/23b5b790-d0c6-4eb9-9bf5-d5124b3a84ae" />

Products & Promotions
<img width="1221" height="508" alt="Products   Promotions" src="https://github.com/user-attachments/assets/d6b0898b-ad88-47a3-a5f7-c70c53ab2e2b" />

🗄 Database
The project uses MySQL as the primary data source, with 20 interconnected tables.

The simulated FMCG supply chain environment includes:

Categories
Suppliers
Factories
Warehouses
Calendar
Distributors
Products
Stores
Vehicles
Employees
Purchase Orders
Purchase Order Details
Inventory Snapshots
Stock Movements
Batches
Promotions
Sales
Deliveries
Returns
Promotion Details

🧹 Data Preparation
The raw supply chain data was generated with intentional real-world inconsistencies, then reviewed and reconciled before analysis.

The data preparation process included:

Reconciling mismatched columns between source CSVs and the SQL schema (e.g. Distributor_ID not present in the sales table)
Standardizing renamed fields during load (Discount → Discount_Percentage, Net_Sales → Sales_Amount, Cost → Cost_Amount, Gross_Profit → Profit)
Handling ignored/unmapped columns during LOAD DATA (e.g. Warehouse_ID and Distance_KM in deliveries, Store_ID in returns)
Validating snapshot-based inventory logic to avoid double-counting stock across dates
Verifying relationships across 20 tables to prevent fan-out and filter context issues
Defining consistent denominators for rate-based metrics (loss rate, rejection rate, damage rate) instead of arbitrary calculations
Preparing the data for Power BI modeling

⭐ Key Business Insights
Analyzed sales and profit trends across four years, confirming a consistent ~32% profit margin.
Identified a 9.8% supplier rejection rate quietly impacting product quality before goods reach a warehouse.
Found 8.9 months of stock coverage — well above a healthy 1–3 month FMCG benchmark — pointing to significant frozen inventory value.
Evaluated delivery performance, finding a 92% on-time delivery rate against a meaningful total delivery cost by vehicle type.
Compared sales with and without active promotions to assess real incremental impact versus margin compression.
Built executive-level KPIs to support strategic decision-making across the full supply chain.

👨‍💻 Author
Ahmed Sayed

Data Analyst | Computer Engineering Student

LinkedIn: https://linkedin.com/in/ahmed-sayed-b03368283

Portfolio: https://ahmedsayedd15.github.io/my-portfolio

GitHub: https://github.com/Ahmedsayedd15

🏷️ Skills Demonstrated
Python Faker MySQL Power Query Power BI DAX Deneb (Vega-Lite) Data Modeling Data Cleaning Data Visualization Business Intelligence Supply Chain Analytics FMCG Analytics HTML/CSS
