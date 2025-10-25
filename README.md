# 📊 Rearc Data Quest — Barry Petersen

A concise, end-to-end data pipeline for the Rearc Quest using **AWS (S3, Lambda, SQS)**, **Databricks**, and **Terraform**.  
Includes ingestion (BLS “pr” files), an API population snapshot, analytics, and IaC.

---

## 🗂 Repository Structure

```text
rearc_quest_submission/
├── notebooks/
│   ├── bls_landing.ipynb              # Parts 1 & 2 – ingest BLS + population API → S3
│   └── analytics_part3.ipynb          # Part 3 – analytics & joins (mean/stddev, best year, join)
│
├── terraform/
│   ├── main.tf                        # Infrastructure (Lambdas, SQS, wiring)
│   ├── variables.tf
│   ├── terraform.tfvars               # Region/bucket/contact overrides
│   └── lambda/
│       ├── ingest_lambda.py           # Part 1 & 2 ingestion Lambda (idempotent)
│       └── reports_lambda.py          # Emits Part 3 summaries on new JSON arrival
│
├── outputs/
│   ├── mean_stddev_2013_2018.csv
│   ├── best_year_per_series.csv
│   └── prs30006032_q01_with_population.csv
│
├── s3_links.txt                       # Handy S3 URIs / console links
└── README.md
```

---

## ⚙️ Quickstart (Terraform)

```bash
cd terraform
terraform init
terraform apply -auto-approve
```

**`terraform.tfvars`**
```hcl
aws_region    = "us-east-1"
bucket_name   = "databricks-workspace-stack-e3d32-bucket"
contact_email = "bthomasp@gmail.com"
```

### What gets deployed
- 1× **Lambda** for ingestion (BLS “pr” & population JSON/CSV → S3).
- 1× **SQS** queue that triggers the **reports** Lambda when new JSON lands.
- 1× **Lambda** for reporting (logs Part 3 results to CloudWatch).

> The S3 bucket already exists; Terraform wires the eventing/compute.

---

## ✅ Validation Checklist

- **S3 layout**
  - `s3://databricks-workspace-stack-e3d32-bucket/bls/pr/`
  - `s3://databricks-workspace-stack-e3d32-bucket/bls/api/`
  - `s3://databricks-workspace-stack-e3d32-bucket/bls/api/us_population_csv/`

- **CloudWatch Logs**
  - Look for `rearc-quest-reports` entries showing:
    - 3a) population mean/stddev (2013–2018)
    - 3b) best year per series
    - 3c) PRS30006032 Q01 + population join

- **Databricks Notebooks**
  - `notebooks/bls_landing.ipynb` (Parts 1 & 2)
  - `notebooks/analytics_part3.ipynb` (Part 3)
  - Outputs also saved here in `outputs/*.csv`.

---

## 📈 Notes

- External requests include a **User-Agent with contact info** (BLS data access policy).
- Ingestion is **idempotent** (safe to re-run; existing S3 keys are skipped).
- Population API and BLS scans are **throttled** politely.

---

## 🔗 Helpful S3 Links

- `s3://databricks-workspace-stack-e3d32-bucket/bls/pr/`  
- `s3://databricks-workspace-stack-e3d32-bucket/bls/api/`  
- `s3://databricks-workspace-stack-e3d32-bucket/bls/api/us_population_csv/`

> Console view example:  
> https://us-east-1.console.aws.amazon.com/s3/buckets/databricks-workspace-stack-e3d32-bucket?region=us-east-1&prefix=bls/&showversions=false

---

## 📨 Author

**Barry Petersen**  
📧 bthomasp@gmail.com  
GitHub: https://github.com/bthomasp
