# Notebooks — Technical Overview

**Project:** Healthcare RCM Analytics Platform
**Author:** Ajay Gardas — BI & Data Engineering

---

## Pipeline Overview

```
CSV Files → Bronze (raw) → Silver (clean + CDC) → Gold (aggregated) → Power BI
```

Each notebook owns one step. Parameters drive execution — only
BATCH_DATE and BATCH_ID change per run. All other logic is fixed.

---

## 01_bronze_dimensions — Load Reference Data

Loads 5 dimension CSV files into Bronze Delta tables. Runs once.
Dimensions are static — facilities, payers, providers, patients
and encounters do not change daily.

**Key design decisions:**
- Schema enforced explicitly — prevents Spark from mistyping date and numeric columns during inference
- PERMISSIVE read mode — corrupt rows captured in _corrupt_record column instead of failing the pipeline
- Dates kept as strings — type casting deferred to Silver to preserve raw source values in Bronze for audit
- Two audit columns added — _ingestion_ts records when loaded, _batch_date records which batch

**Output:** 5 permanent Delta tables in rcm_bronze database

---

## 02_silver_dimensions — Clean Reference Data

Reads Bronze dimension tables, applies data quality fixes and
writes clean Silver dimension tables. Runs once after Bronze dimensions.

**Transformations applied:**

| Table | What was fixed |
|-------|---------------|
| dim_facility | Trimmed spaces, city to title case, state to uppercase, integer to boolean |
| dim_payer | Contract dates cast from string to DateType — enables date arithmetic |
| dim_provider | Names to title case, hire_date cast to DateType |
| dim_patient | Names SHA-256 hashed (HIPAA), gender standardised, DOB cast to DateType |
| dim_encounter | Admit and discharge dates cast to DateType — enables LOS validation |

**Why PII hashing matters:**
Patient names are SHA-256 hashed before Silver storage. The hash satisfies
HIPAA Safe Harbor de-identification — it cannot be reversed, yet identical
names always produce identical hashes preserving patient matching ability
across systems without exposing real names. Real names exist only in Bronze.

**Output:** 5 permanent Delta tables in rcm_silver database

---

## 03_bronze_claims — Daily Batch Ingestion

Appends one daily claims CSV batch to Bronze. Runs 3 times — once per batch.
Only BATCH_DATE and BATCH_ID change between runs.

**Key design decisions:**
- APPEND mode only — Bronze is immutable. Overwriting is prohibited.
  Bronze is the reprocessing source if Silver has bugs and the evidence
  trail if a regulatory audit requires original submitted values.
- _record_hash — SHA-256 fingerprint of 5 key columns (claim_id,
  billed_amount, paid_amount, claim_status, last_modified_date).
  Drives CDC detection in Silver — changed values = changed hash = UPDATE.
  Unchanged values = same hash = SKIP with zero write cost.

**Bronze totals after each batch:**

| Batch | Date | Added | Total |
|-------|------|-------|-------|
| 1 | Apr 21 | 500,000 | 500,000 |
| 2 | Apr 22 | 250,000 | 750,000 |
| 3 | Apr 23 | 280,000 | 1,030,000 |

**Output:** Rows appended to rcm_bronze.claims

---

## 04_silver_cdc_claims — CDC MERGE

The most critical notebook. Reads current batch from Bronze, cleanses it
and merges into Silver using Delta MERGE with hash-based Change Data Capture.

**Cleansing applied before MERGE:**
- Negative billed amounts corrected using ABS()
- Null CPT codes replaced with UNKNOWN and flagged
- All date columns cast from string to DateType
- Three financial KPIs derived — contractual_adj, patient_responsibility, net_collection_rate
- AR aging bucket assigned — 0-30 / 31-60 / 61-90 / 90+ Days

**How the MERGE works:**

```
For every incoming row from Bronze:

  Claim exists in Silver + hash CHANGED  →  UPDATE that row only
  Claim exists in Silver + hash SAME     →  SKIP  (zero writes)
  Claim not in Silver yet                →  INSERT new row
```

The hash comparison is the efficiency engine — in a typical batch,
60-70% of rows are unchanged. Those rows consume zero write I/O.
Only genuinely changed claims incur the cost of an UPDATE.

**CDC results across 3 batches:**

| Batch | Before | After | Inserted | Updated |
|-------|--------|-------|----------|---------|
| 1 | 0 | 500,000 | 500,000 | 0 |
| 2 | 500,000 | 600,000 | 100,000 | ~150,000 |
| 3 | 600,000 | 680,000 | 80,000 | ~200,000 |

Silver always holds exactly one row per claim at its latest state.
Bronze holds the complete version history of every row ever received.

**Delta time travel — proof of CDC:**

| Query | Result |
|-------|--------|
| VERSION AS OF 0 | 500,000 rows (after Batch 1) |
| VERSION AS OF 1 | 600,000 rows (after Batch 2) |
| Current | 680,000 rows (after Batch 3) |

**Output:** rcm_silver.claims — 680,000 unique claims, no duplicates

---

## 05_gold_aggregations — Business Aggregations

Joins Silver claims with all dimension tables and builds 5 Gold
tables for Power BI. Runs after every Silver CDC cycle.

**How joins work:**
Dimension tables are small (50 to 5,000 rows). Broadcast joins send
the entire dimension to every partition — eliminating shuffle. All 5
Gold tables are built from one enriched dataset constructed once and reused.

**Gold tables produced:**

| Table | Business Purpose | Key Metric |
|-------|-----------------|------------|
| gold_daily_snapshot | Day-over-day revenue trend | Cash collected + DoD variance |
| gold_ar_aging | Where is money stuck | Outstanding AR by aging bucket |
| gold_denial_analytics | Why claims are denied | Denial rate + rolling 3-batch avg |
| gold_revenue_summary | Revenue by payer and facility | Net collection rate + running total |
| gold_provider_scorecard | Provider denial performance | PERCENT_RANK within specialty |

**Window functions used:**

```sql
-- Day over day variance
LAG(cash_collected) OVER (PARTITION BY facility_name, payer_name ORDER BY trans_date)

-- Rolling 3-batch denial rate
AVG(denial_rate) OVER (PARTITION BY payer_name ORDER BY trans_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- Cumulative running total
SUM(cash_collected) OVER (PARTITION BY payer_name ORDER BY trans_date ROWS UNBOUNDED PRECEDING)

-- Provider percentile within specialty
PERCENT_RANK() OVER (PARTITION BY specialty ORDER BY total_paid)
```

**Final Gold row counts:**

| Table | Rows |
|-------|------|
| gold_daily_snapshot | 1,350 |
| gold_ar_aging | 450 |
| gold_denial_analytics | 9,450 |
| gold_revenue_summary | 2,700 |
| gold_provider_scorecard | 233,643 |

**Output:** 5 Delta tables in rcm_gold — consumed by Power BI via CSV export
