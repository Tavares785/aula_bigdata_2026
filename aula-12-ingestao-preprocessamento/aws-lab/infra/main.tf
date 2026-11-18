# =============================================================================
# Aula 12 — Pipeline MercadoFácil
# Infra: S3 (via AWS CLI) → Glue Job (PySpark) → Glue Crawler → Athena
# ATENÇÃO: não use aws_s3_bucket nem crie roles/policies IAM no Learner Lab.
# =============================================================================

locals {
  data_csv_local   = "${path.module}/../../data/pedidos_mercadofacil.csv"
  etl_script_local = "${path.module}/../job/etl_mercadofacil.py"
  s3_raw_prefix    = "s3://${var.bucket_name}/raw/"
  s3_silver_prefix = "s3://${var.bucket_name}/silver/"
  s3_gold_prefix   = "s3://${var.bucket_name}/gold/"
  s3_scripts_key   = "scripts/etl_mercadofacil.py"
  s3_script_uri    = "s3://${var.bucket_name}/${local.s3_scripts_key}"
}

# -----------------------------------------------------------------------------
# Bucket S3 criado via AWS CLI (SCP do Learner Lab impede aws_s3_bucket)
# -----------------------------------------------------------------------------
resource "terraform_data" "s3_bucket" {
  triggers_replace = [var.bucket_name]

  provisioner "local-exec" {
    command = <<-EOT
      aws s3api create-bucket \
        --bucket ${var.bucket_name} \
        --region us-east-1
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      aws s3 rm s3://${self.triggers_replace[0]} --recursive || true
      aws s3api delete-bucket \
        --bucket ${self.triggers_replace[0]} \
        --region us-east-1 || true
    EOT
  }
}

# -----------------------------------------------------------------------------
# Upload do CSV para a camada raw/
# -----------------------------------------------------------------------------
resource "terraform_data" "upload_csv" {
  depends_on = [terraform_data.s3_bucket]

  triggers_replace = [var.bucket_name]

  provisioner "local-exec" {
    command = "aws s3 cp ${local.data_csv_local} s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
  }
}

# -----------------------------------------------------------------------------
# Upload do script do ETL para scripts/
# -----------------------------------------------------------------------------
resource "terraform_data" "upload_etl_script" {
  depends_on = [terraform_data.s3_bucket]

  triggers_replace = [var.bucket_name]

  provisioner "local-exec" {
    command = "aws s3 cp ${local.etl_script_local} ${local.s3_script_uri}"
  }
}

# -----------------------------------------------------------------------------
# Glue Catalog Database
# -----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "mercadofacil" {
  name        = var.glue_db_name
  description = "Banco de dados do pipeline MercadoFácil (silver e gold)"
}

# -----------------------------------------------------------------------------
# Glue Job — ETL PySpark (raw → silver → gold)
# -----------------------------------------------------------------------------
resource "aws_glue_job" "etl_mercadofacil" {
  depends_on = [terraform_data.upload_etl_script]

  name     = var.glue_job_name
  role_arn = var.lab_role_arn

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 60

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/${local.s3_scripts_key}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
    "--TempDir"                          = "s3://${var.bucket_name}/tmp/"
    "--INPUT_PATH"                       = "${local.s3_raw_prefix}pedidos_mercadofacil.csv"
    "--SILVER_PATH"                      = local.s3_silver_prefix
    "--GOLD_PATH"                        = local.s3_gold_prefix
  }
}

# -----------------------------------------------------------------------------
# Glue Crawler — cataloga silver e gold para o Athena
# -----------------------------------------------------------------------------
resource "aws_glue_crawler" "mercadofacil" {
  depends_on = [aws_glue_catalog_database.mercadofacil]

  name          = var.glue_crawler_name
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.mercadofacil.name
  description   = "Crawler que cataloga as camadas silver e gold do pipeline MercadoFácil"

  s3_target {
    path = local.s3_silver_prefix
  }

  s3_target {
    path = local.s3_gold_prefix
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })
}
