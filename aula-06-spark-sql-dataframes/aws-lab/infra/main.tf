# main.tf - aws-lab (aula-06: Spark SQL / DataFrames no AWS Glue)
# =============================================================================
# INFRA DO LAB
#
# O bucket S3 e criado via AWS CLI (local-exec), nao via resource aws_s3_bucket,
# porque a SCP do Learner Lab nega s3:GetBucketObjectLockConfiguration - leitura
# que o recurso aws_s3_bucket sempre faz, resultando em AccessDenied.
# O mesmo apply sobe o script e os 2 CSVs; o destroy remove o bucket.
# =============================================================================

provider "aws" {
  region = var.regiao

  default_tags {
    tags = var.tags
  }
}

# ---------------------------------------------------------------------------
# Bucket S3 + uploads via AWS CLI (local-exec).
# create: cria o bucket (privado), bloqueia acesso publico e sobe script + CSVs.
# destroy: esvazia e remove o bucket (triggers guardam bucket/regiao/paths).
# ---------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  triggers_replace = {
    bucket   = var.bucket_nome
    regiao   = var.regiao
    script   = filemd5("${path.module}/../job/dataframe_job.py")
    pedidos  = filemd5("${path.module}/../data/pedidos.csv")
    clientes = filemd5("${path.module}/../data/clientes.csv")
  }

  # Criar bucket + bloquear acesso publico + subir artefatos.
  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -e
      aws s3api create-bucket --bucket "${var.bucket_nome}" --region "${var.regiao}"
      aws s3api put-public-access-block \
        --bucket "${var.bucket_nome}" \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3 cp "${path.module}/../job/dataframe_job.py" "s3://${var.bucket_nome}/scripts/dataframe_job.py"
      aws s3 cp "${path.module}/../data/pedidos.csv" "s3://${var.bucket_nome}/input/pedidos.csv"
      aws s3 cp "${path.module}/../data/clientes.csv" "s3://${var.bucket_nome}/input/clientes.csv"
    EOT
  }

  # Esvaziar e remover o bucket no destroy.
  provisioner "local-exec" {
    when        = destroy
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      aws s3 rm "s3://${self.triggers_replace.bucket}" --recursive || true
      aws s3api delete-bucket --bucket "${self.triggers_replace.bucket}" --region "${self.triggers_replace.regiao}" || true
    EOT
  }
}

# ---------------------------------------------------------------------------
# AWS Glue Job (glueetl) - motor onde os DataFrames vao rodar.
# Nao cria IAM role: usa a LabRole por ARN (var.labrole_arn).
# ---------------------------------------------------------------------------
resource "aws_glue_job" "topn" {
  name     = "job-aula06-topn-clientes"
  role_arn = var.labrole_arn

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  depends_on = [terraform_data.bucket]

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/dataframe_job.py"
  }

  default_arguments = {
    "--PEDIDOS"                          = "s3://${var.bucket_nome}/input/pedidos.csv"
    "--CLIENTES"                         = "s3://${var.bucket_nome}/input/clientes.csv"
    "--OUTPUT"                           = "s3://${var.bucket_nome}/output/top_clientes"
    "--TOP_N"                            = tostring(var.top_n)
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${var.bucket_nome}/tmp/"
  }
}