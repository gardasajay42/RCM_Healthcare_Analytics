# Data Model

**Project:** Healthcare Revenue Cycle Management (RCM) Analytics Platform
**Author:** Ajay Gardas — BI & Data Engineering
**Date:** April 2026

---

## 1. Overview

This project uses a Star Schema — one central fact table surrounded by dimension tables. Claims is the fact table. All other tables describe the claim.

    dim_patient ──┐
    dim_provider ─┤
    dim_facility ─┼──► fact_claims (Silver) ──► Gold Tables ──► Power BI
    dim_payer ────┤
    dim_encounter─┘

---

## 2. Fact Table — claims

Every row is one insurance claim submitted by the hospital to a payer requesting payment for medical services.

| Column | Type | Description |
|--------|------|-------------|
| claim_id | String | Unique claim identifier |
| encounter_id | String | Links to dim_encounter |
| patient_id | String | Links to dim_patient |
| provider_id | String | Links to dim_provider |
| facility_id | String | Links to dim_facility |
| payer_name | String | Insurance company name |
| cpt_code | String | Medical procedure code |
| icd10_primary | String | Primary diagnosis code |
| claim_type | String | Professional or Institutional |
| service_date | Date | When service was provided |
| billed_amount | Double | What hospital charged |
| allowed_amount | Double | What payer agreed to pay |
| paid_amount | Double | What payer actually sent |
| claim_status | String | Paid / Denied / Pending / Partial |
| denial_reason | String | Why claim was denied |
| is_denied | Integer | 1 = denied, 0 = not denied |
| last_modified_date | Date | When claim was last updated |
| trans_date | Date | Which batch this row belongs to |

**Silver derived columns:**

| Column | Description |
|--------|-------------|
| contractual_adj | billed - allowed (written off per contract) |
| patient_responsibility | allowed - paid (patient owes this) |
| net_collection_rate | paid / billed (collection efficiency) |
| ar_aging_bucket | 0-30 / 31-60 / 61-90 / 90+ Days |
| cpt_missing_flag | True if CPT was null in source |

**Data volumes:**

| Batch | Date | Rows |
|-------|------|------|
| Batch 1 | Apr 21, 2026 | 500,000 |
| Batch 2 | Apr 22, 2026 | 250,000 |
| Batch 3 | Apr 23, 2026 | 280,000 |
| Bronze total | All batches appended | 1,030,000 |
| Silver total | Latest state only | 680,000 |

---

## 3. Dimension Tables

### dim_facility
Hospitals and clinics where patients receive care.

| Column | Type | Description |
|--------|------|-------------|
| facility_id | String | Unique facility identifier |
| facility_name | String | Hospital name |
| facility_type | String | Acute Care / Outpatient / Specialty |
| city | String | City location |
| state | String | State (VA) |
| region | String | Central / Northern / Coastal / Western VA |
| bed_count | Integer | Number of beds |
| is_active | Boolean | Whether facility is currently active |

Rows: 50

---

### dim_payer
Insurance companies that pay for patient care.

| Column | Type | Description |
|--------|------|-------------|
| payer_id | String | Unique payer identifier |
| payer_name | String | Insurance company name |
| plan_type | String | HMO / PPO / EPO / HDHP |
| contract_start | Date | Contract effective date |
| contract_end | Date | Contract expiry date |
| reimbursement_rate | Double | Contracted payment rate |
| is_government | Boolean | True for Medicare, Medicaid, Tricare |

Rows: 50

---

### dim_provider
Doctors and clinical staff who treat patients.

| Column | Type | Description |
|--------|------|-------------|
| provider_id | String | Unique provider identifier |
| npi | String | National Provider Identifier (10 digits) |
| first_name | String | First name |
| last_name | String | Last name |
| full_name | String | Full name with title |
| specialty | String | Cardiology / Surgery / Oncology etc. |
| facility_id | String | Primary facility |
| contract_type | String | Employed / Contracted / Locum |
| hire_date | Date | Date joined the network |
| is_active | Boolean | Currently active |

Rows: 5,000

---

### dim_patient
Patient demographics — who received care.

| Column | Type | Description |
|--------|------|-------------|
| patient_id | String | Unique patient identifier |
| first_name_hashed | String | SHA-256 hashed — HIPAA compliance |
| last_name_hashed | String | SHA-256 hashed — HIPAA compliance |
| dob | Date | Date of birth |
| gender | String | Male / Female / Unknown |
| zip_code | String | Postal code |
| state | String | State of residence |
| insurance_plan | String | HMO / PPO / HDHP etc. |
| payer_name | String | Primary insurance company |
| facility_id | String | Primary facility |
| age_group | String | 0-17 / 18-34 / 35-49 / 50-64 / 65+ |

Rows: 200,000

---

### dim_encounter
Every patient visit — inpatient, outpatient, emergency.

| Column | Type | Description |
|--------|------|-------------|
| encounter_id | String | Unique visit identifier |
| patient_id | String | Links to dim_patient |
| provider_id | String | Links to dim_provider |
| facility_id | String | Links to dim_facility |
| admit_date | Date | When patient was admitted |
| discharge_date | Date | When patient was discharged |
| los_days | Integer | Length of stay in days |
| visit_type | String | Inpatient / Outpatient / Emergency / Observation |
| drg_code | String | Diagnosis Related Group code |
| primary_icd10 | String | Primary diagnosis code |
| discharge_disposition | String | Where patient went after discharge |
| total_charges | Double | Total charges for the visit |

Rows: 500,000

---

## 4. Gold Tables

Built by joining Silver claims with all dimension tables. Power BI reads directly from these.

| Gold Table | Joins Used | Powers |
|---|---|---|
| gold_daily_snapshot | claims + dim_facility | Revenue trend, KPI cards |
| gold_ar_aging | claims + dim_facility | AR aging stacked bar |
| gold_denial_analytics | claims + dim_facility + dim_provider | Denial rate charts |
| gold_revenue_summary | claims + dim_facility + dim_payer | Collections by payer |
| gold_provider_scorecard | claims + dim_facility + dim_provider | Provider scorecard |

---

## 5. Star Schema

    dim_patient (200K)
          |
    dim_provider (5K) ──► fact_claims (680K) ◄── dim_encounter (500K)
          |                    Silver
    dim_facility (50) ──────────────────────── dim_payer (50)
