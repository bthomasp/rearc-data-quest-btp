variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name" {
  type        = string
  description = "Existing S3 bucket with /bls/ data"
}

variable "contact_email" {
  type        = string
  description = "Email to put in BLS/Census User-Agent/From"
}

variable "json_key" {
  type    = string
  default = "bls/api/us_population_csv/us_population_2013_2018.csv"
}

variable "pr_prefix" {
  type    = string
  default = "bls/pr/"
}
