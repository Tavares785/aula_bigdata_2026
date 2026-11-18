# ---------------------------------------------------------------------------
# Aula 12 - Pipeline MercadoFacil (raw -> silver -> gold)
# Infra provisionada com Terraform no AWS Academy Learner Lab
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 1. Bucket S3 via AWS CLI (SCP do Learner Lab bloqueia aws_s3_bucket)
# ---------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  triggers_replace = [var.bucket_nome, var.regiao]

  provisioner "local-exec" {
    command = <<-CMD
      set -e
      aws s3api create-bucket \
        --bucket "${var.bucket_nome}" \
        --region "${var.regiao}" 2>/dev/null || true
      aws s3api put-public-access-block \
        --bucket "${var.bucket_nome}" \
        --public-access-block-configuration \
          BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3 cp "${path.module}/../../data/pedidos_mercadofacil.csv" \
        "s3://${var.bucket_nome}/raw/pedidos_mercadofacil.csv"
      aws s3 cp "${path.module}/../job/etl_pipeline.py" \
        "s3://${var.bucket_nome}/scripts/etl_pipeline.py"
    CMD
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }

  input = {
    bucket = var.bucket_nome
    regiao = var.regiao
  }
}

# ---------------------------------------------------------------------------
# 2. Glue Catalog Database
# ---------------------------------------------------------------------------
resource "aws_glue_catalog_database" "mercadofacil" {
  name        = "db_mercadofacil"
  description = "Banco de dados do pipeline MercadoFacil - aula 12"

  depends_on = [terraform_data.bucket]
}

# ---------------------------------------------------------------------------
# 3. Glue Job (ETL raw -> silver -> gold)
# ---------------------------------------------------------------------------
resource "aws_glue_job" "etl" {
  name         = "job-mercadofacil-etl"
  role_arn     = var.labrole_arn
  glue_version = "4.0"
  worker_type  = "G.1X"

  number_of_workers = 2

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/etl_pipeline.py"
  }

  default_arguments = {
    "--INPUT"                            = "s3://${var.bucket_nome}/raw/pedidos_mercadofacil.csv"
    "--OUTPUT_SILVER"                    = "s3://${var.bucket_nome}/silver/"
    "--OUTPUT_GOLD"                      = "s3://${var.bucket_nome}/gold/"
    "--OUTPUT_QUARENTENA"                = "s3://${var.bucket_nome}/quarentena/"
    "--TempDir"                          = "s3://${var.bucket_nome}/tmp/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TOP_N"                            = tostring(var.top_n)
  }

  depends_on = [terraform_data.bucket]
}

# ---------------------------------------------------------------------------
# 4. Glue Crawler (cataloga silver e gold no Glue Catalog)
# ---------------------------------------------------------------------------
resource "aws_glue_crawler" "silver_gold" {
  name          = "crawler-mercadofacil"
  role          = var.labrole_arn
  database_name = aws_glue_catalog_database.mercadofacil.name

  s3_target {
    path = "s3://${var.bucket_nome}/silver/"
  }

  s3_target {
    path = "s3://${var.bucket_nome}/gold/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })
}
