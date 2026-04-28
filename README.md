# RCM Healthcare Analytics

End-to-end Healthcare Revenue Cycle Management Analytics Platform built on **Azure Databricks**, **Delta Lake Medallion Architecture** and **Power BI** — processing 500,000 daily claims through Bronze, Silver and Gold layers with CDC using Delta MERGE.

---

## The Problem

A Virginia hospital network operating 50 facilities was losing significant revenue due to untracked claim denials, unpaid claims sitting beyond 90 days and no real-time visibility into revenue performance. Finance leadership relied on manual Excel reports taking 3 days to produce.

## The Solution

An automated daily data pipeline that ingests, cleanses and aggregates claims data — delivering a single executive dashboard that answers where the money is, why claims are being denied and which facilities and payers need attention.

---

## Architecture

    CSV Files (daily batch)
          ↓
    Unity Catalog Volume
          ↓
    ┌─────────────────────────────────────┐
    │            DATABRICKS               │
    │                                     │
    │  BRONZE  →  SILVER  →  GOLD        │
    │  Raw        Clean       Aggregated  │
    │  Append     CDC MERGE   Power BI    │
    └─────────────────────────────────────┘
          ↓
    Power BI Executive Dashboard

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Processing | Apache Spark (PySpark) |
| Table Format | Delta Lake |
| Platform | Databricks Serverless |
| Storage | Unity Catalog Volumes |
| CDC Pattern | Delta MERGE with SHA-256 hash |
| Visualisation | Microsoft Power BI |
| Languages | Python, Spark SQL |
| Version Control | Git / GitHub |

---

## Dataset

| Table | Layer | Rows | Description |
|-------|-------|------|-------------|
| claims (Batch 1) | Bronze / Silver | 500,000 | Initial daily load |
| claims (Batch 2) | Bronze / Silver | 250,000 | 150K updates + 100K new |
| claims (Batch 3) | Bronze / Silver | 280,000 | 200K updates + 80K new |
| dim_encounter | Bronze / Silver | 500,000 | Patient visits |
| dim_patient | Bronze / Silver | 200,000 | Patient demographics |
| dim_provider | Bronze / Silver | 5,000 | Doctors and clinical staff |
| dim_facility | Bronze / Silver | 50 | Hospital locations |
| dim_payer | Bronze / Silver | 50 | Insurance companies |
| **Total** | | **1,785,100** | |

Bronze holds 1,030,000 rows — full history of all batches.
Silver holds 680,000 rows — latest state of every claim, no duplicates.

---

## CDC — Change Data Capture

Silver layer implements CDC using Delta MERGE and SHA-256 hash comparison.

| Scenario | Action |
|----------|--------|
| New claim arrives | INSERT |
| Existing claim with changed values | UPDATE only that row |
| Existing claim with no changes | Skip — zero writes |

This ensures Silver always holds exactly one row per claim at its latest state — no duplicates, no full table scans.

---

## Spark Optimizations

| Optimization | Benefit |
|---|---|
| shuffle.partitions = 50 | Right-sized for single node — faster aggregations |
| broadcast(dim_facility) | Eliminates shuffle join for small dimension tables |
| enriched.cache() | Enriched dataset computed once, reused for 5 Gold tables |
| partitionBy("trans_date") | Partition pruning on date-filtered queries |
| adaptive.enabled = true | Dynamic partition coalescing at runtime |
| optimizeWrite = true | Prevents small file problem in Delta tables |
| enableLowShuffle MERGE | Reduces data movement during CDC MERGE |

---

## Dashboard — Power BI

Single executive dashboard with 6 interactive visuals and filters by date, facility, region, payer, claim status and provider specialty.

| Visual | Type | Answers |
|--------|------|---------|
| Net Collections, Collection Rate, Denial Rate, AR 90+ Days | KPI Cards | Are we hitting targets? |
| Daily Revenue Trend | Line Chart | Is revenue growing? |
| Collections by Payer | Horizontal Bar | Which payer brings most cash? |
| Denial Rate by Payer | Bar Chart | Who rejects claims most? |
| AR Aging by Payer | Stacked Bar | Where is money stuck? |
| Claims by Status | Donut Chart | Overall claims health |
| Facility and Payer Detail | Table | Which facility needs attention? |

---

## Project Structure

    RCM_Healthcare_Analytics/
    ├── 01_requirements/
    │   └── business_requirements.md
    ├── 02_solution_design/
    │   ├── technical_design.md
    │   └── data_model.md
    ├── 03_notebooks/
    │   ├── 01_bronze_dimensions.py
    │   ├── 02_silver_dimensions.py
    │   ├── 03_bronze_claims.py
    │   ├── 04_silver_cdc_claims.py
    │   └── 05_gold_aggregations.py
    ├── 04_sample_data/
    │   └── claims_sample.csv
    └── 05_screenshots/
        └── databricks_outputs/

---

## How to Run

**Step 1** — Upload CSV files to Databricks Unity Catalog Volume

    /Volumes/workspace/rcm/rcm_data/raw/claims/
    /Volumes/workspace/rcm/rcm_data/raw/dimensions/

**Step 2** — Run notebooks in order

    01_bronze_dimensions  → loads dimension tables to Bronze
    02_silver_dimensions  → cleans dimensions to Silver
    03_bronze_claims      → loads Batch 1 to Bronze (repeat for Batch 2, 3)
    04_silver_cdc_claims  → CDC MERGE into Silver (repeat for Batch 2, 3)
    05_gold_aggregations  → builds 5 Gold tables for Power BI

**Step 3** — Connect Power BI to Databricks SQL Warehouse and select rcm_gold tables

---

## Author

**Ajay Gardas** — BI and Data Engineering Developer
Tennessee, United States
[LinkedIn](https://www.linkedin.com/in/ajay-g-64a6b5184/)
