📊 Rearc Data Quest — Barry Petersen

Full data pipeline implementation
Built using AWS, Databricks, Terraform, Lambda, SQS, and Python.

🚀 Structure
rearc_quest_submission/
├── notebooks/
│   ├── bls_landing.ipynb        # Parts 1 & 2 – Data ingestion + API integration
│   └── analytics_part3.ipynb     # Part 3 – Analytics & joins
│
├── terraform/
│   ├── main.tf                   # Infrastructure deployment
│   ├── variables.tf
│   ├── terraform.tfvars
│   └── lambda/
│       ├── ingest_lambda.py
│       └── reports_lambda.py
│
├── outputs/
│   ├── mean_stddev_2013_2018.csv
│   ├── best_year_per_series.csv
│   └── prs30006032_q01_with_population.csv
│
├── s3_links.txt
└── README.md

⚙️ Quickstart
cd terraform
terraform init
terraform apply -auto-approve


Config (terraform.tfvars):

aws_region   = "us-east-1"
bucket_name  = "databricks-workspace-stack-e3d32-bucket"
contact_email= "bthomasp@gmail.com"


Validation:

S3 contains /bls/pr/ and /bls/api/us_population_*.{json,csv}

CloudWatch Logs for rearc-quest-reports show 3a/3b/3c summaries

Lambda and SQS event triggers verified in AWS Console

📈 Notes

External API calls include user-agent contact info per BLS policy

Ingestion is idempotent (safe to re-run)

Terraform deploys:

1x S3 bucket (existing)

1x Lambda for ingestion

1x SQS queue with trigger to reporting Lambda

🧩 S3 Links

s3://databricks-workspace-stack-e3d32-bucket/bls/pr/

s3://databricks-workspace-stack-e3d32-bucket/bls/api/

s3://databricks-workspace-stack-e3d32-bucket/bls/api/us_population_csv/

📨 Author

Barry Petersen
📧 bthomasp@gmail.com

🔗 GitHub – bthomasp