terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Bucket S3 via AWS CLI (sem aws_s3_bucket)
# ---------------------------------------------------------------------------
resource "terraform_data" "s3_bucket" {
  triggers_replace = [var.bucket_name]

  provisioner "local-exec" {
    command = "aws s3api create-bucket --bucket ${var.bucket_name} --region ${var.aws_region}"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rm s3://${self.triggers_replace[0]} --recursive && aws s3api delete-bucket --bucket ${self.triggers_replace[0]} --region us-east-1"
  }
}

# ---------------------------------------------------------------------------
# Upload do CSV para raw/
# ---------------------------------------------------------------------------
resource "terraform_data" "upload_csv" {
  depends_on       = [terraform_data.s3_bucket]
  triggers_replace = [var.bucket_name, var.raw_csv_local_path]

  provisioner "local-exec" {
    command = "aws s3 cp ${var.raw_csv_local_path} s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
  }
}

# ---------------------------------------------------------------------------
# Upload do script ETL para scripts/
# ---------------------------------------------------------------------------
resource "terraform_data" "upload_etl" {
  depends_on       = [terraform_data.s3_bucket]
  triggers_replace = [var.bucket_name, var.etl_script_local_path]

  provisioner "local-exec" {
    command = "aws s3 cp ${var.etl_script_local_path} s3://${var.bucket_name}/scripts/etl.py"
  }
}

# ---------------------------------------------------------------------------
# Glue Catalog Database
# ---------------------------------------------------------------------------
resource "aws_glue_catalog_database" "mercadofacil" {
  name = var.glue_database_name
}

# ---------------------------------------------------------------------------
# Glue Job
# ---------------------------------------------------------------------------
resource "aws_glue_job" "etl" {
  depends_on        = [terraform_data.upload_etl]
  name              = var.glue_job_name
  role_arn          = var.lab_role_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/scripts/etl.py"
    python_version  = "3"
  }

  default_arguments = {
    "--RAW_PATH"                         = "s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
    "--SILVER_PATH"                      = "s3://${var.bucket_name}/silver/"
    "--GOLD_PATH"                        = "s3://${var.bucket_name}/gold/"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-continuous-cloudwatch-log" = "true"
  }
}

# ---------------------------------------------------------------------------
# Glue Crawler
# ---------------------------------------------------------------------------
resource "aws_glue_crawler" "mercadofacil" {
  depends_on    = [aws_glue_catalog_database.mercadofacil]
  name          = var.glue_crawler_name
  role          = var.lab_role_arn
  database_name = var.glue_database_name

  s3_target {
    path = "s3://${var.bucket_name}/gold/"
  }

  s3_target {
    path = "s3://${var.bucket_name}/silver/pedidos/"
  }
}
