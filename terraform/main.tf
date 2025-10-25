terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -----------------------
# SQS queue + policy so S3 can send notifications
# -----------------------
resource "aws_sqs_queue" "reports_queue" {
  name                       = "rearc-quest-reports"
  visibility_timeout_seconds = 180
}

data "aws_iam_policy_document" "s3_to_sqs" {
  statement {
    sid    = "AllowS3ToSend"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.reports_queue.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = ["arn:aws:s3:::${var.bucket_name}"]
    }
  }
}

resource "aws_sqs_queue_policy" "reports_queue" {
  queue_url = aws_sqs_queue.reports_queue.id
  policy    = data.aws_iam_policy_document.s3_to_sqs.json
}

# -----------------------
# S3 -> SQS notification (fires when the population CSV is written)
# -----------------------
resource "aws_s3_bucket_notification" "notify_json" {
  bucket = var.bucket_name

  queue {
    queue_arn     = aws_sqs_queue.reports_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".csv"
    filter_prefix = "bls/api/"
  }
}

# -----------------------
# IAM for Lambda #1 (ingest: Parts 1 & 2)
# -----------------------
data "aws_iam_policy_document" "ingest_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ingest_role" {
  name               = "rearc-quest-ingest-role"
  assume_role_policy = data.aws_iam_policy_document.ingest_assume.json
}

data "aws_iam_policy_document" "ingest_policy" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["*"]
  }

  statement {
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject",
      "s3:HeadObject"
    ]
    resources = [
      "arn:aws:s3:::${var.bucket_name}",
      "arn:aws:s3:::${var.bucket_name}/*"
    ]
  }
}

resource "aws_iam_policy" "ingest_policy" {
  name   = "rearc-quest-ingest-policy"
  policy = data.aws_iam_policy_document.ingest_policy.json
}

resource "aws_iam_role_policy_attachment" "ingest_attach" {
  role       = aws_iam_role.ingest_role.name
  policy_arn = aws_iam_policy.ingest_policy.arn
}

# -----------------------
# IAM for Lambda #2 (reports: Part 3 logs)
# -----------------------
resource "aws_iam_role" "reports_role" {
  name               = "rearc-quest-reports-role"
  assume_role_policy = data.aws_iam_policy_document.ingest_assume.json
}

data "aws_iam_policy_document" "reports_policy" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["*"]
  }

  statement {
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      "arn:aws:s3:::${var.bucket_name}",
      "arn:aws:s3:::${var.bucket_name}/*"
    ]
  }

  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.reports_queue.arn]
  }
}

resource "aws_iam_policy" "reports_policy" {
  name   = "rearc-quest-reports-policy"
  policy = data.aws_iam_policy_document.reports_policy.json
}

resource "aws_iam_role_policy_attachment" "reports_attach" {
  role       = aws_iam_role.reports_role.name
  policy_arn = aws_iam_policy.reports_policy.arn
}

# -----------------------
# Lambda #1 (ingest) — pulls BLS + writes population CSV (Parts 1 & 2)
# -----------------------
data "archive_file" "ingest_zip" {
  type        = "zip"

  source {
    content  = file("${path.module}/lambda/ingest_lambda.py")
    filename = "ingest_lambda.py"
  }

  output_path = "${path.module}/lambda/ingest_lambda.zip"
}

resource "aws_lambda_function" "ingest" {
  function_name = "rearc-quest-ingest"
  role          = aws_iam_role.ingest_role.arn
  handler       = "ingest_lambda.handler"
  runtime       = "python3.11"
  timeout       = 180
  filename      = data.archive_file.ingest_zip.output_path

  environment {
    variables = {
      BUCKET        = var.bucket_name
      PR_PREFIX     = var.pr_prefix
      JSON_CSV_KEY  = var.json_key
      CONTACT_EMAIL = var.contact_email
    }
  }
}

# Daily schedule
resource "aws_cloudwatch_event_rule" "daily" {
  name                = "rearc-quest-daily"
  schedule_expression = "cron(15 9 * * ? *)" # 09:15 UTC daily
}

resource "aws_cloudwatch_event_target" "daily_target" {
  rule      = aws_cloudwatch_event_rule.daily.name
  target_id = "ingest"
  arn       = aws_lambda_function.ingest.arn
}

resource "aws_lambda_permission" "allow_events" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn
}

# -----------------------
# Lambda #2 (reports) — triggered by SQS, logs Part 3 results
# -----------------------
data "archive_file" "reports_zip" {
  type        = "zip"

  source {
    content  = file("${path.module}/lambda/reports_lambda.py")
    filename = "reports_lambda.py"
  }

  output_path = "${path.module}/lambda/reports_lambda.zip"
}

resource "aws_lambda_function" "reports" {
  function_name = "rearc-quest-reports"
  role          = aws_iam_role.reports_role.arn
  handler       = "reports_lambda.handler"
  runtime       = "python3.11"
  timeout       = 120
  filename      = data.archive_file.reports_zip.output_path

  environment {
    variables = {
      BUCKET       = var.bucket_name
      PR_PREFIX    = var.pr_prefix
      POP_CSV_KEY  = var.json_key
    }
  }
}

resource "aws_lambda_event_source_mapping" "reports_sqs" {
  event_source_arn = aws_sqs_queue.reports_queue.arn
  function_name    = aws_lambda_function.reports.arn
  batch_size       = 1
  enabled          = true
}
