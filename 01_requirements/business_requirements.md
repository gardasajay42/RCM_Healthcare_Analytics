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
| CFO | Primary sponsor | High level KPIs, revenue trends, YoY growth |
| Revenue Cycle Director | Daily user | Denial rates, AR aging, payer performance |
| AR Collections Team | Daily user | Which claims to chase today |
| Medical Director | Monthly user | Provider denial rates, coaching data |
| IT / Data Engineering | Delivery team | Technical implementation |

---

## 5. Scope

### In Scope
- Daily automated ingestion of claims data
- Processing of patient, provider, facility and payer data
- Single executive dashboard with all key metrics
- Filters by date, facility, region, payer and claim status
- Historical comparison (batch over batch)

### Out of Scope
- Real time streaming (daily batch is sufficient)
- Patient portal or clinical systems
- Billing system changes
- Predictive analytics (Phase 2)

---

## 6. Dashboard Requirement

### One Executive Dashboard — RCM Analytics

The CFO has requested a **single page dashboard** that 
gives complete visibility into revenue cycle performance.
The dashboard must update automatically every morning 
with the previous day's data.

---

### 6.1 Filters (Apply to All Visuals)

The following filters must be available and must control
every visual on the dashboard simultaneously:

| Filter | Options |
|--------|---------|
| Date Range | Any date range selection |
| Facility | All or individual facility |
| Region | Central VA / Northern VA / Coastal VA / Western VA |
| Payer | All or individual payer |
| Claim Status | All / Paid / Denied / Pending / Partial |
| Provider Specialty | All or individual specialty |

**Requirement:** When any filter is changed, ALL visuals
on the dashboard must update instantly — no page refresh.

---

### 6.2 KPI Cards (Row 1)

Five KPI cards displayed across the top of the dashboard.
Each card shows current value and change vs previous period.

| # | KPI | Business Meaning |
|---|-----|-----------------|
| 1 | Total Claims | How many claims processed in selected period |
| 2 | Net Collections ($) | Total cash actually received from payers |
| 3 | Net Collection Rate (%) | % of billed amount successfully collected |
| 4 | Denial Rate (%) | % of claims rejected by payers |
| 5 | Open AR 90+ Days ($) | Money unpaid for more than 90 days — at risk |

**Requirement:** Each KPI must show an up/down arrow 
and % change vs previous period so leadership can see 
at a glance whether each metric is improving or worsening.

---

### 6.3 Revenue Trend — Line Chart

**Visual type:** Line chart  
**Title:** Daily cash collections trend

| Axis | Value |
|------|-------|
| X axis | Date |
| Y axis | Cash collected ($) |

**Business question it answers:**  
Is our revenue growing day over day? Which days had 
unusually high or low collections?

**Requirement:** Must show individual data points so 
users can hover and see exact value for each date.

---

### 6.4 Collections by Payer — Horizontal Bar Chart

**Visual type:** Horizontal bar chart  
**Title:** Cash collected by payer

| Axis | Value |
|------|-------|
| Y axis | Payer name |
| X axis | Cash collected ($) |

**Business question it answers:**  
Which insurance company is our biggest revenue source? 
Which payer contributes least?

**Requirement:** Bars must be sorted highest to lowest.
Government payers (Medicare, Medicaid) displayed in 
different colour to commercial payers.

---

### 6.5 Denial Rate by Payer — Bar Chart

**Visual type:** Vertical bar chart  
**Title:** Denial rate by payer (%)

| Axis | Value |
|------|-------|
| X axis | Payer name |
| Y axis | Denial rate % |

**Business question it answers:**  
Which insurance company is rejecting the most claims? 
Are any payers above our acceptable threshold?

**Requirement:** Must include a reference line at 18% 
(network average). Bars above the line displayed in red. 
Bars below displayed in green.

---

### 6.6 AR Aging Breakdown — Stacked Bar Chart

**Visual type:** Stacked bar chart  
**Title:** Accounts receivable aging by payer

| Axis | Value |
|------|-------|
| X axis | Payer name |
| Y axis | Outstanding AR ($) |
| Stack | Aging bucket |

**Color coding:**

| Bucket | Color | Meaning |
|--------|-------|---------|
| 0-30 Days | Green | Healthy — recently submitted |
| 31-60 Days | Amber | Watch — approaching risk |
| 61-90 Days | Orange | Concern — follow up needed |
| 90+ Days | Red | Critical — at risk of write-off |

**Business question it answers:**  
For each payer, how much money is in each aging bucket? 
Which payer has the most money in the dangerous 90+ zone?

---

### 6.7 Claims by Status — Donut Chart

**Visual type:** Donut chart  
**Title:** Claim status distribution

**Segments:**

| Segment | Color |
|---------|-------|
| Paid | Green |
| Partial | Blue |
| Pending | Amber |
| Denied | Red |

**Business question it answers:**  
What percentage of our claims are in each status? 
Is our Denied segment growing or shrinking over time?

**Requirement:** Centre of donut must show total claim count.

---

### 6.8 Summary Detail Table

**Visual type:** Table  
**Title:** Performance by facility and payer

| Column | Description |
|--------|-------------|
| Facility | Hospital name |
| Payer | Insurance company |
| Total Claims | Number of claims |
| Gross Charges | Total billed ($) |
| Net Collected | Cash received ($) |
| Collection Rate | % collected |
| Denial Rate | % denied |
| AR 90+ Days | Outstanding over 90 days ($) |

**Requirements:**  
- Sortable by any column  
- Clicking any row filters all charts above  
- Conditional formatting — red if denial rate > 20%  
- Shows top 10 rows by default  

---

## 7. Success Criteria

The project is considered successful when:

| Criteria | Measure |
|----------|---------|
| Dashboard available every morning | Before 8AM daily |
| Data is accurate | Matches source billing system |
| All filters work correctly | Every visual updates on filter change |
| Leadership adopts it | CFO uses dashboard in weekly review meeting |
| Replaces Excel reports | Manual Excel process discontinued |

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

- Source data is available as daily CSV exports from billing system
- Data volume is approximately 500,000 claims per daily batch
- Historical data available from January 2025 onwards
- Databricks and Power BI licenses are available
- Azure Data Factory available for pipeline orchestration

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
| Write-off | A claim given up on — revenue permanently lost |
| CPT Code | Medical procedure code used for billing |
| ICD-10 | Medical diagnosis code |
