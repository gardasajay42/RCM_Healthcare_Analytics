# Technical Design Document

**Project:** Healthcare Revenue Cycle Management (RCM) Analytics Platform
**Author:** Ajay Gardas — BI & Data Engineering
**Date:** April 2026

---

## 1. Solution Overview

Build a daily automated analytics pipeline processing healthcare claims data and delivering a single executive dashboard to finance leadership using Medallion Architecture on Databricks Delta Lake.

---

## 2. Architecture

```
CSV Files → Unity Catalog Volume → Databricks (Bronze → Silver → Gold) → Power BI
```

| Layer | Purpose | Mode |
|-------|---------|------|
| Bronze | Raw ingestion — no cleaning, full history | Append only |
| Silver | Cleansed + CDC MERGE — latest state only | MERGE / Overwrite |
| Gold | Business aggregations joined with dimensions | Overwrite |

---

## 3. Why These Tools

| Tool | Reason |
|------|--------|
| Databricks | Native Delta Lake, PySpark, Unity Catalog, Serverless compute |
| Delta Lake | ACID transactions, time travel, MERGE INTO for CDC |
| Medallion Architecture | Clear layer separation, immutable Bronze, single source of truth in Silver |
| Power BI | Executive dashboards with slicers and conditional formatting |

---

## 4. CDC Implementation

Silver claims uses Delta MERGE for Change Data Capture.
A SHA-256 hash of key business columns detects changes without scanning the full table.

```
claim exists + hash changed → UPDATE row
claim exists + hash same    → skip (zero writes)
claim not in Silver yet     → INSERT new row
```

| Batch | Date | Result | Silver Rows |
|-------|------|--------|-------------|
| 1 | Apr 21 | INSERT 500,000 | 500,000 |
| 2 | Apr 22 | UPDATE 150,000 + INSERT 100,000 | 600,000 |
| 3 | Apr 23 | UPDATE 200,000 + INSERT 80,000 | 680,000 |

Bronze holds 1,030,000 rows (full history).
Silver holds 680,000 rows (latest state, no duplicates).

---

## 5. Spark Optimizations

| Optimization | Setting | Benefit |
|---|---|---|
| Shuffle partitions | Set to 50 (default 200) | Right-sized for single node — faster aggregations |
| Broadcast join | broadcast(dim_facility) | Eliminates shuffle for small dimension tables |
| DataFrame cache | enriched.cache() | Enriched dataset computed once, reused for 5 Gold tables |
| Partition pruning | partitionBy("trans_date") | Date-filtered queries skip irrelevant partitions |
| Adaptive Query Execution | adaptive.enabled = true | Dynamic partition coalescing at runtime |
| optimizeWrite | enabled = true | Prevents small file problem in Delta |
| Low shuffle MERGE | enableLowShuffle = true | Reduces data movement during CDC MERGE |

---

## 6. Data Quality and PII

Patient names SHA-256 hashed in Silver — following HIPAA de-identification standards.
Real names exist only in Bronze (restricted access).

Silver claims includes derived quality columns:

| Column | Description |
|--------|-------------|
| cpt_missing_flag | True if CPT code was null in source |
| ar_aging_bucket | 0-30 / 31-60 / 61-90 / 90+ Days |
| net_collection_rate | paid / billed |
| contractual_adj | billed - allowed |
| patient_responsibility | allowed - paid |

Corrupt rows at Bronze ingestion are captured in a quarantine table instead of failing the pipeline.

---

## 7. Delta Time Travel

Every Silver write creates a new Delta version — enabling point-in-time queries for audit and debugging.

```sql
SELECT COUNT(*) FROM rcm_silver.claims VERSION AS OF 0  -- 500,000 (after Batch 1)
SELECT COUNT(*) FROM rcm_silver.claims VERSION AS OF 1  -- 600,000 (after Batch 2)
SELECT COUNT(*) FROM rcm_silver.claims                  -- 680,000 (current)
```
