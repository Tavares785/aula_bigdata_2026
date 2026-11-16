# Pipeline MercadoFácil: S3 raw -> Glue (PySpark) -> silver/gold -> Athena.
#
# Duas restrições do AWS Academy Learner Lab moldam este arquivo inteiro:
#
# 1. O recurso `aws_s3_bucket` NÃO funciona. A SCP da organização nega
#    `s3:GetBucketObjectLockConfiguration`, e o provider chama essa API
#    em toda leitura do recurso — inclusive logo depois de criar. O
#    resultado é o pior tipo de falha: o bucket nasce, o apply morre com
#    `AccessDenied`, e o bucket fica criado FORA do state. Por isso ele
#    é criado pela CLI, via `terraform_data` + `local-exec`.
#
# 2. Não se cria role nem policy IAM. A `LabRole` já existe na conta e é
#    a única utilizável; o Glue Job e o Crawler a recebem por ARN.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Fixada: o enunciado pede 5.31.0, e provider novo muda o formato
      # do state sem avisar.
      version = "5.31.0"
    }
  }
}

provider "aws" {
  region = var.regiao
}

locals {
  bucket = "${var.prefixo_bucket}-${var.identificador_grupo}"

  # Caminhos da arquitetura medalhão. Declarados aqui, e não espalhados
  # pelos recursos, porque o Glue Job, o Crawler e os scripts precisam
  # concordar sobre eles — e divergir produz job que grava onde o
  # crawler não olha.
  raw        = "s3://${local.bucket}/raw/"
  silver     = "s3://${local.bucket}/silver/"
  gold       = "s3://${local.bucket}/gold/"
  quarentena = "s3://${local.bucket}/quarentena/"
  scripts    = "s3://${local.bucket}/scripts/"
}

# ── Bucket, pela CLI ───────────────────────────────────────────────────

resource "terraform_data" "bucket" {
  # Guarda o nome no state: o provisioner de destroy não enxerga
  # `local` nem `var`, só `self.input`.
  input = local.bucket

  provisioner "local-exec" {
    command = <<-CMD
      aws s3api create-bucket --bucket ${self.input} --region ${var.regiao}
      aws s3api put-public-access-block --bucket ${self.input} \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    CMD
  }

  # `--force` esvazia antes de remover: o S3 recusa apagar bucket com
  # objeto dentro, e a esta altura há Parquet gerado pelo job que o
  # Terraform não conhece.
  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input} --force || true"
  }
}

# ── Dados e script, enviados pelo próprio Terraform ────────────────────

# `aws_s3_object` é um recurso diferente de `aws_s3_bucket` e não chama a
# API bloqueada: ele usa PutObject, que a SCP permite.
resource "aws_s3_object" "dataset" {
  bucket = local.bucket
  key    = "raw/pedidos_mercadofacil.csv"
  source = "${path.module}/../../data/pedidos_mercadofacil.csv"
  etag   = filemd5("${path.module}/../../data/pedidos_mercadofacil.csv")

  depends_on = [terraform_data.bucket]
}

resource "aws_s3_object" "script_etl" {
  bucket = local.bucket
  key    = "scripts/etl_mercadofacil.py"
  source = "${path.module}/../job/etl_mercadofacil.py"
  # Sem o etag, mudar o script não reenvia o arquivo, e o job seguiria
  # rodando a versão velha — um erro que parece bug no código novo.
  etag = filemd5("${path.module}/../job/etl_mercadofacil.py")

  depends_on = [terraform_data.bucket]
}

# ── Catálogo, job e crawler ────────────────────────────────────────────

resource "aws_glue_catalog_database" "mercadofacil" {
  name        = var.nome_database
  description = "Camadas silver e gold do pipeline MercadoFacil"
}

resource "aws_glue_job" "etl" {
  name     = "${var.identificador_grupo}-mercadofacil-etl"
  role_arn = var.arn_lab_role

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    name           = "glueetl"
    python_version = "3"
    # `s3://` explicito, e nao escondido atras do local: quem le o bloco
    # ve de onde o script sai sem perseguir a definicao.
    script_location = "s3://${local.bucket}/scripts/etl_mercadofacil.py"
  }

  # Caminhos como argumento, não embutidos no script: o mesmo script
  # roda em outro bucket sem ser editado.
  default_arguments = {
    "--entrada_raw"      = local.raw
    "--saida_silver"     = local.silver
    "--saida_gold"       = local.gold
    "--saida_quarentena" = local.quarentena
    "--job-language"     = "python"
    "--enable-metrics"   = "true"
  }

  # Uma execução por vez: o Spark duplica a saída quando dois runs
  # gravam no mesmo prefixo.
  execution_property {
    max_concurrent_runs = 1
  }

  depends_on = [aws_s3_object.script_etl]
}

resource "aws_glue_crawler" "camadas" {
  name          = "${var.identificador_grupo}-mercadofacil-crawler"
  role          = var.arn_lab_role
  database_name = aws_glue_catalog_database.mercadofacil.name

  s3_target {
    path = local.silver
  }

  s3_target {
    path = local.gold
  }

  # A raw fica de fora de propósito: ela é CSV sujo, com coluna em
  # texto, e catalogá-la convidaria alguém a consultar o dado não
  # tratado no Athena achando que é o oficial.

  schema_change_policy {
    delete_behavior = "DELETE_FROM_DATABASE"
    update_behavior = "UPDATE_IN_DATABASE"
  }
}
