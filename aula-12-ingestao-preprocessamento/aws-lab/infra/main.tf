# Bucket S3 do pipeline (raw/silver/gold), uploads dos dados e dos scripts,
# Glue Catalog Database, Glue Job (ETL PySpark) e Glue Crawler.
#
# O Learner Lab (SCP da AWS Academy) bloqueia:
#   - aws_s3_bucket (GetBucketObjectLockConfiguration)
#   - criacao de roles/policies IAM
# Por isso o bucket nasce via AWS CLI (local-exec) e tudo usa a LabRole.

# ---------------------------------------------------------------------------
# Bucket S3 criado via AWS CLI
# ---------------------------------------------------------------------------
resource "terraform_data" "s3_bucket" {
  # 'input' guarda o nome do bucket para o provisioner de destroy poder
  # referenciar via 'self' (referencia a var e proibida em destroy).
  input = var.bucket_name

  provisioner "local-exec" {
    command = "aws s3api create-bucket --bucket ${self.input} --region us-east-1"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rm s3://${self.input} --recursive && aws s3api delete-bucket --bucket ${self.input} --region us-east-1"
  }
}

# ---------------------------------------------------------------------------
# Upload do CSV bruto (raw/) e do script PySpark (scripts/) via AWS CLI
# ---------------------------------------------------------------------------
resource "terraform_data" "s3_raw_upload" {
  triggers_replace = [var.dataset_path, var.bucket_name]

  provisioner "local-exec" {
    command = "aws s3 cp ${var.dataset_path} s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
  }
}

resource "terraform_data" "s3_script_upload" {
  triggers_replace = [var.script_path, var.bucket_name]

  provisioner "local-exec" {
    command = "aws s3 cp ${var.script_path} s3://${var.bucket_name}/scripts/etl_mercadofacil.py"
  }
}

# ---------------------------------------------------------------------------
# Glue Catalog Database
# ---------------------------------------------------------------------------
resource "aws_glue_catalog_database" "mercadofacil" {
  name        = var.glue_database_name
  description = "Catalogo do pipeline MercadoFacil (silver/gold para o Athena)"
}

# ---------------------------------------------------------------------------
# Glue Job: ETL PySpark raw -> silver -> gold (Glue 4.0, LabRole)
# ---------------------------------------------------------------------------
resource "aws_glue_job" "etl_mercadofacil" {
  name         = var.glue_job_name
  role_arn     = var.lab_role_arn
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/scripts/etl_mercadofacil.py"
    python_version  = "3"
  }

  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30
  max_retries       = 0

  default_arguments = {
    "--s3_raw_path"    = "s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
    "--s3_silver_path" = "s3://${var.bucket_name}/silver/"
    "--s3_gold_path"   = "s3://${var.bucket_name}/gold/"
    "--database_name"  = var.glue_database_name
  }

  depends_on = [terraform_data.s3_script_upload]
}

# ---------------------------------------------------------------------------
# Glue Crawler: cataloga as tabelas Parquet das camadas silver e gold
# ---------------------------------------------------------------------------
resource "aws_glue_crawler" "mercadofacil" {
  name          = var.glue_crawler_name
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.mercadofacil.name

  s3_target {
    path = "s3://${var.bucket_name}/silver/"
  }

  s3_target {
    path = "s3://${var.bucket_name}/gold/"
  }
}
