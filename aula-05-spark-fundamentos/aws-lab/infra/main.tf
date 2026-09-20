# main.tf - aws-lab (aula-05: Spark/RDDs no AWS Glue)
# Bucket criado via AWS CLI (aws s3 mb) - gerenciado como data source
# para evitar erro de GetObjectLockConfiguration no Learner Lab.

provider "aws" {
  region = var.regiao

  default_tags {
    tags = var.tags
  }
}

# Referencia o bucket S3 ja existente (criado via aws s3 mb)
# Usamos data source para evitar o erro GetObjectLockConfiguration do Learner Lab
data "aws_s3_bucket" "lab" {
  bucket = var.bucket_nome
}

# Bucket PRIVADO - bloqueia acesso publico
resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = data.aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload do script PySpark para o S3 (prefixo scripts/)
resource "aws_s3_object" "script" {
  bucket = data.aws_s3_bucket.lab.id
  key    = "scripts/rdd_job.py"
  source = "${path.module}/../job/rdd_job.py"
  etag   = filemd5("${path.module}/../job/rdd_job.py")
}

# Upload do dado de exemplo para o S3 (prefixo input/)
resource "aws_s3_object" "input" {
  bucket = data.aws_s3_bucket.lab.id
  key    = "input/sample_lines.txt"
  source = "${path.module}/../data/sample_lines.txt"
  etag   = filemd5("${path.module}/../data/sample_lines.txt")
}

# AWS Glue Job (glueetl) - motor onde os RDDs vao rodar
resource "aws_glue_job" "wordcount" {
  name     = "job-aula05-wordcount"
  role_arn = var.labrole_arn

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${data.aws_s3_bucket.lab.bucket}/scripts/rdd_job.py"
  }

  default_arguments = {
    "--INPUT"  = "s3://${data.aws_s3_bucket.lab.bucket}/input/sample_lines.txt"
    "--OUTPUT" = "s3://${data.aws_s3_bucket.lab.bucket}/output/wordcount"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir" = "s3://${data.aws_s3_bucket.lab.bucket}/tmp/"
  }
}