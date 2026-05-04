# Business Requirements Document

**Project Name:** Healthcare Revenue Cycle Management (RCM) Analytics Platform
**Requested by:** Chief Financial Officer (CFO)
**Business Unit:** Finance & Revenue Cycle
**Prepared by:** Ajay Gardas, BI & Data Engineering
**Date:** April 2026
**Status:** Approved

---

## 1. Background

Virginia Hospital Network operates 50 healthcare facilities
across 4 regions — Central VA, Northern VA, Coastal VA
and Western VA.

Every day the network processes thousands of patient claims
submitted to insurance companies (payers) such as Medicare,
Anthem BCBS, Aetna, UnitedHealth and others requesting
payment for medical services provided.

The current reporting process is entirely manual:
- Finance analysts export raw data from the billing system
- Data is compiled in Excel spreadsheets
- Reports are produced manually every week
- Process takes 3 days and is prone to errors
- Leadership has no real-time visibility into revenue health

---

## 2. Business Problem

The hospital network is experiencing three critical issues:

**Problem 1 — Revenue Leakage**
18% of claims submitted to insurance companies are being
denied. Each denied claim means delayed or lost revenue.
The finance team has no automated way to track which payers
are denying the most claims or why.

**Problem 2 — Unpaid Claims Going Unnoticed**
Claims sitting unpaid beyond 90 days have a very low
recovery rate. Without daily visibility into AR aging,
the collections team cannot prioritise which claims to
follow up on. Millions of dollars are at risk of being
written off.

**Problem 3 — No Single Source of Truth**
Different departments use different Excel files with
different numbers. Finance, operations and clinical
leadership often disagree on basic metrics like total
collections and denial rates. There is no single trusted
source of data.

---

## 3. Business Objective

Build an automated daily analytics platform that gives
finance and operations leadership a **single trusted
dashboard** showing the complete health of the revenue
cycle — updated every morning before the business day starts.

---

## 4. Stakeholders

| Stakeholder | Role | What They Need |
|-------------|------|----------------|
| CFO | Primary sponsor | High level KPIs, revenue trends |
| Revenue Cycle Director | Daily user | Denial rates, payer performance |
| AR Collections Team | Daily user | Which claims to chase today |
| Medical Director | Monthly user | Provider denial rates |
| IT / Data Engineering | Delivery team | Technical implementation |

---

## 5. Scope

### In Scope
- Daily automated ingestion of claims data (3 daily batches)
- Processing of patient, provider, facility and payer data
- Single executive dashboard with all key metrics
- Filters by date, facility, payer and claim type
- Drill through to provider performance detail
- Historical comparison across batches

### Out of Scope
- Real time streaming (daily batch is sufficient)
- Patient portal or clinical systems
- Billing system changes
- Predictive analytics (Phase 2)

---

## 6. Dashboard Requirement

### One Executive Dashboard — RCM Analytics

The CFO requested a **single page dashboard** giving complete
visibility into revenue cycle performance with a drill through
page for provider detail analysis.

---

### 6.1 Filters (Apply to All Visuals)

| Filter | Options |
|--------|---------|
| Date | All dates or specific batch date |
| Claim Type | All / Professional / Institutional |
| Facility Name | All or individual facility |
| Payer Name | All or individual payer |

**Requirement:** When any filter is changed all visuals
on the dashboard update instantly.

---

### 6.2 KPI Cards (Row 1)

Five KPI cards displayed across the top of the dashboard.

| # | KPI | Business Meaning |
|---|-----|-----------------|
| 1 | Total Claims | How many claims processed in selected period |
| 2 | Net Collections ($) | Total cash actually received from payers |
| 3 | Net Collection Rate (%) | % of billed amount successfully collected |
| 4 | Denial Rate (%) | % of claims rejected by payers |
| 5 | Avg Days Outstanding | Average days unpaid claims have been outstanding |

---

### 6.3 Net Collections by Payer — Horizontal Bar Chart

**Visual type:** Horizontal bar chart

| Axis | Value |
|------|-------|
| Y axis | Payer name |
| X axis | Cash collected ($) |

**Business question it answers:**
Which insurance company is our biggest revenue source?
Which payer contributes least to collections?

**Requirement:** Bars sorted highest to lowest by cash collected.

---

### 6.4 Total Claims by Claim Type — Donut Chart

**Visual type:** Donut chart

**Segments:**

| Segment | Description |
|---------|-------------|
| Professional | Doctor office visits, outpatient procedures |
| Institutional | Hospital stays, inpatient services |

**Business question it answers:**
What is the split between professional and institutional claims?
Which claim type drives most of our volume?

---

### 6.5 Performance by Facility and Payer — Detail Table

**Visual type:** Table with drill through

| Column | Description |
|--------|-------------|
| Facility Name | Hospital name |
| Payer Name | Insurance company |
| Total Claims | Number of claims |
| Gross Charges | Total billed ($) |
| Cash Collected | Cash received ($) |
| Net Collection Rate | % collected |
| Denial Rate | % denied |

**Requirements:**
- Sortable by any column
- Right click any row → Drill through → Provider Performance Detail
- Shows facility and payer combination performance

---

### 6.6 Denial Rate by Payer — Summary Table

**Visual type:** Table

| Column | Description |
|--------|-------------|
| Payer | Insurance company name |
| Denial Rate | % of claims denied by this payer |

**Business question it answers:**
Which insurance company is rejecting the most claims?
Are denial rates consistent or does one payer stand out?

---

### 6.7 Drill Through — Provider Performance Detail

**Page name:** Provider Details

Accessible by right clicking any row in the Performance
by Facility and Payer table and selecting Drill through.

| Column | Description |
|--------|-------------|
| Provider Name | Doctor full name |
| Specialty | Medical specialty |
| Contract Type | Employed / Contracted / Locum |
| Total Claims | Claims submitted |
| Collection Rate | % of billed amount collected |
| Denial Rate | % of claims denied |
| Denial Risk Flag | High Risk / Monitor / Normal |
| Productivity Tier | Top Quartile / Above Average / Below Average / Bottom Quartile |

**Business question it answers:**
For the selected facility and payer combination — which specific
doctors have high denial rates? Which providers need coaching
on billing practices?

**Back button** returns user to main dashboard.

---

## 7. Success Criteria

| Criteria | Measure |
|----------|---------|
| Dashboard reflects latest batch data | Refresh updates all visuals |
| All filters work correctly | Every visual updates on selection |
| Drill through works | Provider detail opens for any row |
| KPIs are accurate | Match Gold table aggregations |

---

## 8. Timeline

| Phase | Deliverable | Target |
|-------|-------------|--------|
| Phase 1 | Data pipeline (Bronze → Silver → Gold) | Week 1-2 |
| Phase 2 | Dashboard development | Week 3 |
| Phase 3 | UAT and sign-off | Week 4 |
| Phase 4 | Production deployment | Week 5 |

---

## 9. Assumptions

- Source data available as daily CSV exports from billing system
- Data volume approximately 500,000 claims per daily batch
- Databricks and Power BI licenses available
- Data refreshed by exporting Gold tables as CSV after each batch

---

## 10. Glossary

| Term | Definition |
|------|------------|
| Claim | A bill submitted to an insurance company for medical services |
| Payer | An insurance company (Medicare, Aetna, Anthem etc.) |
| Billed Amount | What the hospital charged for the service |
| Allowed Amount | What the payer agreed to pay per contract |
| Paid Amount | What the payer actually sent |
| Denial | When a payer refuses to pay a claim |
| AR Aging | How long claims have been unpaid |
| Collection Rate | Paid Amount / Billed Amount × 100 |
| CPT Code | Medical procedure code used for billing |
| ICD-10 | Medical diagnosis code |
| Drill Through | Navigate from summary to detail by right clicking a visual |
