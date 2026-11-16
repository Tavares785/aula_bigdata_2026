terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}
provider "aws" {
  region = "us-east-1"
}
variable "bucket_name" {
  type = string
}
variable "lab_role_arn" {
  type = string
}
variable "resource_prefix" {
  type = string
}
resource "terraform_data" "bucket" {
  input = var.bucket_name
  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = { BUCKET = self.input }
    command     = <<-EOT
      set -euo pipefail
      aws s3api create-bucket --bucket "$BUCKET" --region us-east-1
      aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
    EOT
  }
  provisioner "local-exec" {
    when        = destroy
    interpreter = ["/bin/bash", "-c"]
    environment = { BUCKET = self.input }
    command     = "aws s3 rb \"s3://$BUCKET\" --force --region us-east-1"
  }
}
resource "terraform_data" "upload" {
  depends_on = [terraform_data.bucket]
  triggers_replace = [
    filesha256("${path.module}/../../data/pedidos_mercadofacil.csv"),
    filesha256("${path.module}/../job/etl.py")
  ]
  provisioner "local-exec" {
    environment = { BUCKET = var.bucket_name }
    command     = <<-EOT
      set -e
      aws s3 cp '${path.module}/../../data/pedidos_mercadofacil.csv' "s3://$BUCKET/raw/pedidos_mercadofacil.csv"
      aws s3 cp '${path.module}/../job/etl.py' "s3://$BUCKET/scripts/etl.py"
    EOT
  }
}
resource "aws_glue_catalog_database" "catalog" {
  name = replace(var.resource_prefix, "-", "_")
}
resource "aws_glue_job" "etl" {
  depends_on        = [terraform_data.upload]
  name              = "${var.resource_prefix}-etl"
  role_arn          = var.lab_role_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 25
  max_retries       = 0
  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/scripts/etl.py"
    python_version  = "3"
  }
  default_arguments = {
    "--RAW_PATH"            = "s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
    "--SILVER_PATH"         = "s3://${var.bucket_name}/silver/items"
    "--GOLD_PATH"           = "s3://${var.bucket_name}/gold"
    "--QUARANTINE_PATH"     = "s3://${var.bucket_name}/quarantine/items"
    "--TempDir"             = "s3://${var.bucket_name}/temp/"
    "--job-bookmark-option" = "job-bookmark-disable"
  }
}
resource "aws_glue_crawler" "gold" {
  depends_on    = [terraform_data.bucket]
  name          = "${var.resource_prefix}-crawler"
  database_name = aws_glue_catalog_database.catalog.name
  role          = var.lab_role_arn
  s3_target {
    path = "s3://${var.bucket_name}/gold/atrasos_estado"
  }
  s3_target {
    path = "s3://${var.bucket_name}/gold/vendas_categoria"
  }
}
output "bucket" {
  value = var.bucket_name
}
output "job" {
  value = aws_glue_job.etl.name
}
output "crawler" {
  value = aws_glue_crawler.gold.name
}
output "database" {
  value = aws_glue_catalog_database.catalog.name
}
