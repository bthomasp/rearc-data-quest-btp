\# 📊 Rearc Data Quest — Barry Petersen



A concise, end-to-end data pipeline for the Rearc Quest using \*\*AWS (S3, Lambda, SQS)\*\*, \*\*Databricks\*\*, and \*\*Terraform\*\*.  

Includes ingestion (BLS “pr” files), an API population snapshot, analytics, and IaC.



---



\## 🗂 Repository Structure



```text

rearc\_quest\_submission/

├── notebooks/

│   ├── bls\_landing.ipynb              # Parts 1 \& 2 – ingest BLS + population API → S3

│   └── analytics\_part3.ipynb          # Part 3 – analytics \& joins (mean/stddev, best year, join)

│

├── terraform/

│   ├── main.tf                        # Infrastructure (Lambdas, SQS, wiring)

│   ├── variables.tf

│   ├── terraform.tfvars               # Region/bucket/contact overrides

│   └── lambda/

│       ├── ingest\_lambda.py           # Part 1 \& 2 ingestion Lambda (idempotent)

│       └── reports\_lambda.py          # Emits Part 3 summaries on new JSON arrival

│

├── outputs/

│   ├── mean\_stddev\_2013\_2018.csv

│   ├── best\_year\_per\_series.csv

│   └── prs30006032\_q01\_with\_population.csv

│

├── s3\_links.txt                       # Handy S3 URIs / console links

└── README.md



⚙️ Quickstart
cd terraform
terraform init
terraform apply -auto-approve



Config (terraform.tfvars):

aws\_region   = "us-east-1"
bucket\_name  = "databricks-workspace-stack-e3d32-bucket"
contact\_email= "bthomasp@gmail.com"



Validation:

S3 contains /bls/pr/ and /bls/api/us\_population\_\*.{json,csv}

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

s3://databricks-workspace-stack-e3d32-bucket/bls/api/us\_population\_csv/

📨 Author

Barry Petersen
📧 bthomasp@gmail.com

🔗 GitHub – bthomasp

