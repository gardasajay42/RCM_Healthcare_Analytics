
# Dataset

## Overview
This project processes 1.78 million rows across 8 files
representing 3 daily claim batches and 5 dimension tables.

## Full Dataset Download
All files available on Google Drive:

[Download Full Dataset](https://drive.google.com/drive/folders/1UMz0jpM4f1ii235xWE_2VsoMu2c2-RFi?usp=drive_link)

## File Details

| File | Layer | Rows | Size | Description |
|------|-------|------|------|-------------|
| claims_2026_04_21.csv | Raw | 500,000 | 86 MB | Batch 1 — initial load |
| claims_2026_04_22.csv | Raw | 250,000 | 43 MB | Batch 2 — 150K updates + 100K new |
| claims_2026_04_23.csv | Raw | 280,000 | 49 MB | Batch 3 — 200K updates + 80K new |
| encounters.csv | Dimension | 500,000 | 54 MB | Patient visits |
| patients.csv | Dimension | 200,000 | 17 MB | Patient demographics |
| providers.csv | Dimension | 5,000 | 0.5 MB | Doctors and staff |
| facilities.csv | Dimension | 50 | tiny | Hospital locations |
| payers.csv | Dimension | 50 | tiny | Insurance companies |

## Note
Files exceed GitHub 50MB limit.
Full dataset hosted on Google Drive.
