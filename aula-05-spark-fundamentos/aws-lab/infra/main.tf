# main.tf — aws-lab (aula-05: Spark/RDDs no AWS Glue)

provider "aws" {
  region = var.regiao

  default_tags {
    tags = var.tags
  }
}

# -----------------------------------------------------------------------------
# Bucket PRIVADO
# O bucket já existe na AWS e é informado por var.bucket_nome.
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = var.bucket_nome
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# Upload do script PySpark
# -----------------------------------------------------------------------------
resource "aws_s3_object" "script" {
  bucket = var.bucket_nome
  key    = "scripts/rdd_job.py"
  source = "${path.module}/../job/rdd_job.py"
  etag   = filemd5("${path.module}/../job/rdd_job.py")
}

# -----------------------------------------------------------------------------
# Upload do dado de exemplo
# -----------------------------------------------------------------------------
resource "aws_s3_object" "input" {
  bucket = var.bucket_nome
  key    = "input/sample_lines.txt"
  source = "${path.module}/../data/sample_lines.txt"
  etag   = filemd5("${path.module}/../data/sample_lines.txt")
}

# -----------------------------------------------------------------------------
# AWS Glue Job
# -----------------------------------------------------------------------------
resource "aws_glue_job" "wordcount" {
  name     = "job-aula05-wordcount"
  role_arn = var.labrole_arn

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/rdd_job.py"
  }

  default_arguments = {
    "--INPUT"  = "s3://${var.bucket_nome}/input/sample_lines.txt"
    "--OUTPUT" = "s3://${var.bucket_nome}/output/wordcount"

    "--enable-continuous-cloudwatch-log" = "true"

    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}