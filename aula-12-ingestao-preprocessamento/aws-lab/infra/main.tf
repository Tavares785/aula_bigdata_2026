locals {
  csv_local    = "${path.module}/../../data/pedidos_mercadofacil.csv"
  script_local = "${path.module}/../job/etl_mercadofacil.py"

  raw_uri        = "s3://${var.bucket_nome}/raw/pedidos_mercadofacil.csv"
  script_uri     = "s3://${var.bucket_nome}/scripts/etl_mercadofacil.py"
  silver_uri     = "s3://${var.bucket_nome}/silver"
  gold_uri       = "s3://${var.bucket_nome}/gold"
  quarentena_uri = "s3://${var.bucket_nome}/quarentena"
}

# O bucket e criado pela AWS CLI porque a SCP do Learner Lab nega uma leitura
# feita pelo recurso aws_s3_bucket.
resource "terraform_data" "bucket" {
  input = var.bucket_nome

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      if ! aws s3api head-bucket --bucket "${self.input}" 2>/dev/null; then
        aws s3api create-bucket --bucket "${self.input}" --region us-east-1
      fi
      aws s3api put-public-access-block --bucket "${self.input}" \
        --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    EOT
  }

  provisioner "local-exec" {
    when        = destroy
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      if aws s3api head-bucket --bucket "${self.output}" 2>/dev/null; then
        aws s3 rb "s3://${self.output}" --force
      fi
    EOT
  }
}

# Reenvia os arquivos sempre que o conteudo local mudar.
resource "terraform_data" "upload_csv" {
  triggers_replace = [filemd5(local.csv_local), terraform_data.bucket.id]

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "aws s3 cp '${local.csv_local}' '${local.raw_uri}' --only-show-errors"
  }
}

resource "terraform_data" "upload_script" {
  triggers_replace = [filemd5(local.script_local), terraform_data.bucket.id]

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = "aws s3 cp '${local.script_local}' '${local.script_uri}' --only-show-errors"
  }
}

resource "aws_glue_catalog_database" "mercadofacil" {
  name        = "${var.prefixo}_db"
  description = "Camadas silver, gold e quarentena do pipeline MercadoFacil."
}

resource "aws_glue_job" "etl" {
  name              = "${var.prefixo}-etl"
  role_arn          = var.labrole_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  max_retries       = 0
  timeout           = 20

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/etl_mercadofacil.py"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${var.bucket_nome}/tmp/"
    "--RAW_PATH"                         = local.raw_uri
    "--SILVER_PATH"                      = local.silver_uri
    "--GOLD_PATH"                        = local.gold_uri
    "--QUARANTINE_PATH"                  = local.quarentena_uri
    "--LGPD_SALT"                        = var.lgpd_salt
  }

  depends_on = [terraform_data.upload_csv, terraform_data.upload_script]
}

resource "aws_glue_crawler" "camadas" {
  name          = "${var.prefixo}-crawler"
  role          = var.labrole_arn
  database_name = aws_glue_catalog_database.mercadofacil.name

  s3_target {
    path = "${local.silver_uri}/itens_pedido/"
  }

  s3_target {
    path = "${local.quarentena_uri}/itens_rejeitados/"
  }

  s3_target {
    path = "${local.gold_uri}/atraso_estado_mes/"
  }

  s3_target {
    path = "${local.gold_uri}/atraso_vs_avaliacao/"
  }

  s3_target {
    path = "${local.gold_uri}/cancelamento_devolucao/"
  }

  s3_target {
    path = "${local.gold_uri}/vendas_sazonalidade/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  depends_on = [terraform_data.bucket]
}
