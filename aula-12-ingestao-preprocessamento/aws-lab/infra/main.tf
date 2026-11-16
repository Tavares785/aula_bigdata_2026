terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

locals {
  s3_raw    = "s3://${var.bucket_name}/raw/"
  s3_silver = "s3://${var.bucket_name}/silver/pedidos/"
  s3_quar   = "s3://${var.bucket_name}/quarentena/pedidos/"
  s3_gold   = "s3://${var.bucket_name}/gold/"
  gold_tabelas = [
    "gold_atraso_por_estado_transportadora",
    "gold_nota_por_faixa_atraso",
    "gold_cancelamento_por_categoria_canal",
    "gold_vendas_mensal",
  ]
}

# Bucket privado criado via AWS CLI (o Learner Lab nega aws_s3_bucket).
# No destroy, esvazia e remove o bucket.
resource "terraform_data" "bucket" {
  input = var.bucket_name

  provisioner "local-exec" {
    command = <<-EOT
      aws s3api create-bucket --bucket ${var.bucket_name} --region us-east-1
      aws s3api put-public-access-block --bucket ${var.bucket_name} \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input} --force"
  }
}

# Camada raw: o CSV exatamente como chega.
resource "aws_s3_object" "raw_csv" {
  bucket     = var.bucket_name
  key        = "raw/pedidos_mercadofacil.csv"
  source     = "${path.module}/../../data/pedidos_mercadofacil.csv"
  etag       = filemd5("${path.module}/../../data/pedidos_mercadofacil.csv")
  depends_on = [terraform_data.bucket]
}

resource "aws_s3_object" "etl_script" {
  bucket     = var.bucket_name
  key        = "scripts/etl_medalhao.py"
  source     = "${path.module}/../job/etl_medalhao.py"
  etag       = filemd5("${path.module}/../job/etl_medalhao.py")
  depends_on = [terraform_data.bucket]
}

resource "aws_glue_catalog_database" "pipeline" {
  name = var.glue_database
}

resource "aws_glue_job" "etl" {
  name              = var.glue_job_name
  role_arn          = var.lab_role_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 15

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_name}/${aws_s3_object.etl_script.key}"
  }

  default_arguments = {
    "--job-language"    = "python"
    "--raw_path"        = local.s3_raw
    "--silver_path"     = local.s3_silver
    "--quarantine_path" = local.s3_quar
    "--gold_path"       = local.s3_gold
  }
}

# Catalogo: silver, quarentena e as tabelas gold (um s3_target por tabela).
resource "aws_glue_crawler" "pipeline" {
  name          = var.glue_crawler_name
  role          = var.lab_role_arn
  database_name = aws_glue_catalog_database.pipeline.name

  s3_target {
    path = local.s3_silver
  }

  s3_target {
    path = local.s3_quar
  }

  dynamic "s3_target" {
    for_each = local.gold_tabelas
    content {
      path = "${local.s3_gold}${s3_target.value}/"
    }
  }
}
