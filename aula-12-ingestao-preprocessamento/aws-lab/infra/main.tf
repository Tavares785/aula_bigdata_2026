locals {
  dataset_file = "${path.module}/../../data/pedidos_mercadofacil.csv"
  etl_file     = "${path.module}/../job/etl_mercadofacil.py"

  # Nome do database no Glue Catalog: so letras minusculas, numeros e "_".
  database_name = replace("${var.project_name}_db", "-", "_")

  # Camadas da arquitetura medalhao dentro do mesmo bucket.
  raw_prefix        = "raw/pedidos/"
  silver_prefix     = "silver/"
  gold_prefix       = "gold/"
  quarantine_prefix = "quarentena/"

  # Tabelas geradas pelo ETL (uma pasta por tabela = uma tabela no Catalog).
  silver_tables = ["pedidos_itens"]
  gold_tables = [
    "entregas_estado_mes",
    "atraso_transportadora_cd",
    "atraso_vs_nota",
    "cancelamento_devolucao",
    "vendas_mensais_categoria",
  ]
}

# -----------------------------------------------------------------------------
# Bucket S3 privado criado via AWS CLI.
# O recurso aws_s3_bucket nao funciona no Learner Lab (a SCP nega
# GetBucketObjectLockConfiguration), por isso o bucket nasce e morre aqui.
# -----------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  input = var.bucket_name

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      if aws s3api head-bucket --bucket "${self.input}" 2>/dev/null; then
        echo "Bucket ${self.input} ja existe; reutilizando."
      else
        aws s3api create-bucket --bucket "${self.input}" --region ${var.aws_region}
        aws s3api wait bucket-exists --bucket "${self.input}"
      fi
      aws s3api put-public-access-block --bucket "${self.input}" \
        --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3api put-bucket-encryption --bucket "${self.input}" \
        --server-side-encryption-configuration \
        '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
    EOT
  }

  # No destroy, esvazia o bucket (todas as camadas) e o remove.
  provisioner "local-exec" {
    when        = destroy
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      if aws s3api head-bucket --bucket "${self.output}" 2>/dev/null; then
        aws s3 rm "s3://${self.output}" --recursive
        aws s3api delete-bucket --bucket "${self.output}"
      else
        echo "Bucket ${self.output} nao existe; nada a remover."
      fi
    EOT
  }
}

# -----------------------------------------------------------------------------
# Uploads feitos pelo proprio Terraform: dataset bruto (raw) e script do ETL.
# -----------------------------------------------------------------------------
resource "aws_s3_object" "raw_csv" {
  bucket = terraform_data.bucket.output
  key    = "${local.raw_prefix}pedidos_mercadofacil.csv"
  source = local.dataset_file
  etag   = filemd5(local.dataset_file)

  content_type = "text/csv"
}

resource "aws_s3_object" "etl_script" {
  bucket = terraform_data.bucket.output
  key    = "scripts/etl_mercadofacil.py"
  source = local.etl_file
  etag   = filemd5(local.etl_file)

  content_type = "text/x-python"
}

# -----------------------------------------------------------------------------
# Glue Data Catalog + Glue Job (PySpark) + Crawler.
# Nenhuma role/policy IAM e criada: tudo usa a LabRole por ARN.
# -----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "this" {
  name        = local.database_name
  description = "MercadoFacil - camadas silver, gold e quarentena (Aula 12)"
}

resource "aws_glue_job" "etl" {
  name              = "${var.project_name}-etl-raw-silver-gold"
  description       = "ETL medalhao: raw (CSV) -> silver + quarentena + gold (Parquet)"
  role_arn          = var.lab_role_arn
  glue_version      = "4.0"
  worker_type       = var.glue_worker_type
  number_of_workers = var.glue_number_of_workers
  timeout           = 20
  max_retries       = 0

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${terraform_data.bucket.output}/${aws_s3_object.etl_script.key}"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
    "--TempDir"                          = "s3://${terraform_data.bucket.output}/tmp/"
    "--RAW_PATH"                         = "s3://${terraform_data.bucket.output}/${aws_s3_object.raw_csv.key}"
    "--SILVER_PATH"                      = "s3://${terraform_data.bucket.output}/${local.silver_prefix}"
    "--GOLD_PATH"                        = "s3://${terraform_data.bucket.output}/${local.gold_prefix}"
    "--QUARANTINE_PATH"                  = "s3://${terraform_data.bucket.output}/${local.quarantine_prefix}"
  }
}

resource "aws_glue_crawler" "curated" {
  name          = "${var.project_name}-crawler-silver-gold"
  description   = "Cataloga silver, gold e quarentena para consulta no Athena"
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.this.name

  # Um s3_target por tabela: cada pasta vira uma tabela no Catalog.
  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.silver_prefix}pedidos_itens/"
  }

  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.quarantine_prefix}"
  }

  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.gold_prefix}entregas_estado_mes/"
  }

  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.gold_prefix}atraso_transportadora_cd/"
  }

  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.gold_prefix}atraso_vs_nota/"
  }

  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.gold_prefix}cancelamento_devolucao/"
  }

  s3_target {
    path = "s3://${terraform_data.bucket.output}/${local.gold_prefix}vendas_mensais_categoria/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DELETE_FROM_DATABASE"
  }
}
