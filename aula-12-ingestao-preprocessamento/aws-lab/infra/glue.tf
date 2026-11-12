# Glue Catalog Database
resource "aws_glue_catalog_database" "mercadofacil" {
  name        = "mercadofacil_db"
  description = "Database para dados do e-commerce MercadoFácil"
}

# Glue Job para ETL (raw -> silver -> gold)
resource "aws_glue_job" "etl_mercadofacil" {
  name         = "${var.project_name}-etl-job"
  role_arn     = var.lab_role_arn
  glue_version = var.glue_version
  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_name}/scripts/etl_mercadofacil.py"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${var.bucket_name}/logs/spark-logs/"
    "--TempDir"                          = "s3://${var.bucket_name}/temp/"
    # Argumentos customizados para o script
    "--INPUT_PATH"      = "s3://${var.bucket_name}/raw/"
    "--SILVER_PATH"     = "s3://${var.bucket_name}/silver/"
    "--GOLD_PATH"       = "s3://${var.bucket_name}/gold/"
    "--QUARANTINE_PATH" = "s3://${var.bucket_name}/quarantine/"
  }

  max_retries       = 0
  timeout           = 60
  number_of_workers = 2
  worker_type       = "G.1X"

  depends_on = [
    terraform_data.upload_glue_script,
    terraform_data.upload_raw_data
  ]

  tags = {
    Project     = var.project_name
    Environment = "dev"
  }
}

# Glue Crawler para catalogar dados silver e gold
resource "aws_glue_crawler" "mercadofacil_silver" {
  name          = "${var.project_name}-silver-crawler"
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.mercadofacil.name

  s3_target {
    path = "s3://${var.bucket_name}/silver/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  tags = {
    Project     = var.project_name
    Environment = "dev"
  }
}

# Glue Crawler para catalogar dados gold
resource "aws_glue_crawler" "mercadofacil_gold" {
  name          = "${var.project_name}-gold-crawler"
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.mercadofacil.name

  s3_target {
    path = "s3://${var.bucket_name}/gold/"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })

  tags = {
    Project     = var.project_name
    Environment = "dev"
  }
}
