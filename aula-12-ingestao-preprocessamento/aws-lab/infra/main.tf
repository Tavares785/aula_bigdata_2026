locals {
  raw_prefix        = "raw"
  silver_prefix     = "silver"
  gold_prefix       = "gold"
  quarantine_prefix = "quarantine"
  script_key        = "scripts/etl_pedidos.py"
  raw_key           = "${local.raw_prefix}/pedidos_mercadofacil.csv"
}

# Bucket privado criado via AWS CLI: o Learner Lab nega chamadas que o
# recurso aws_s3_bucket faz (GetBucketObjectLockConfiguration).
resource "terraform_data" "bucket" {
  input = var.bucket_name

  provisioner "local-exec" {
    command = <<-EOT
      aws s3api create-bucket --bucket ${self.input} --region us-east-1
      aws s3api put-public-access-block --bucket ${self.input} \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input} --force"
  }
}

resource "aws_s3_object" "raw_csv" {
  bucket = var.bucket_name
  key    = local.raw_key
  source = "${path.module}/../../data/pedidos_mercadofacil.csv"
  etag   = filemd5("${path.module}/../../data/pedidos_mercadofacil.csv")

  depends_on = [terraform_data.bucket]
}

resource "aws_s3_object" "etl_script" {
  bucket = var.bucket_name
  key    = local.script_key
  source = "${path.module}/../job/etl_pedidos.py"
  etag   = filemd5("${path.module}/../job/etl_pedidos.py")

  depends_on = [terraform_data.bucket]
}

resource "aws_glue_catalog_database" "this" {
  name = var.database_name
}

resource "aws_glue_job" "etl" {
  name              = var.job_name
  role_arn          = var.lab_role_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_name}/${local.script_key}"
  }

  default_arguments = {
    "--raw_path"        = "s3://${var.bucket_name}/${local.raw_prefix}/"
    "--silver_path"     = "s3://${var.bucket_name}/${local.silver_prefix}/"
    "--gold_path"       = "s3://${var.bucket_name}/${local.gold_prefix}/"
    "--quarantine_path" = "s3://${var.bucket_name}/${local.quarantine_prefix}/"
    "--job-language"    = "python"
    "--enable-metrics"  = "true"
  }

  depends_on = [aws_s3_object.etl_script, aws_s3_object.raw_csv]
}

resource "aws_glue_crawler" "this" {
  name          = var.crawler_name
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.this.name

  s3_target {
    path = "s3://${var.bucket_name}/${local.silver_prefix}/"
  }

  s3_target {
    path = "s3://${var.bucket_name}/${local.gold_prefix}/"
  }

  s3_target {
    path = "s3://${var.bucket_name}/${local.quarantine_prefix}/"
  }
}
