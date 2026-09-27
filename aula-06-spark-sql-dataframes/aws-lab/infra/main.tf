# main.tf — aws-lab (aula-06: Spark SQL / DataFrames no AWS Glue)
# =============================================================================
# INFRA PRONTA DO LAB — você NÃO precisa alterar este arquivo.
#
# O que este arquivo provisiona:
#   - O bucket S3 do lab (PRIVADO) e o upload do script + 2 CSVs de entrada.
#     ATENÇÃO: o bucket NÃO é criado com aws_s3_bucket. No AWS Academy Learner
#     Lab há uma SCP que NEGA s3:GetBucketObjectLockConfiguration, e o recurso
#     aws_s3_bucket SEMPRE lê essa config (create/refresh) -> AccessDenied. Para
#     contornar, criamos o bucket via AWS CLI dentro do `terraform apply`
#     (terraform_data + local-exec). REQUER o AWS CLI instalado.
#   - Um AWS Glue Job (PySpark / glueetl) que roda o TOP-N de clientes por gasto.
#
# Por que Glue e não EMR Serverless?
#   Neste Learner Lab o EMR Serverless está BLOQUEADO (a LabRole não confia em
#   emr-serverless.amazonaws.com), mas o Glue FUNCIONA (confia em glue.amazonaws.com).
#
# Regras do Learner Lab:
#   - Região fixa us-east-1 (via var.regiao).
#   - NÃO criamos roles/policies IAM próprias: o Glue Job usa a LabRole por ARN.
#   - Bucket S3 PRIVADO (public access block com os 4 bloqueios = true).
#   - Rode `terraform destroy` ao final para não deixar recursos residuais.
# =============================================================================

provider "aws" {
  region = var.regiao
}

# -----------------------------------------------------------------------------
# Bucket S3 do lab (criado via AWS CLI, NÃO via aws_s3_bucket).
# Prefixos: scripts/, input/, output/, logs/, tmp/.
# - create: cria o bucket, aplica public-access-block (PRIVADO) e sobe o script
#   (dataframe_job.py) + os 2 CSVs de entrada (pedidos.csv e clientes.csv).
# - destroy: esvazia e remove o bucket no terraform destroy.
# -----------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  input = {
    bucket = var.bucket_nome
    regiao = var.regiao
  }

  triggers_replace = [var.bucket_nome, var.regiao]

  provisioner "local-exec" {
    command = <<-CMD
      set -e
      aws s3api create-bucket --bucket "${var.bucket_nome}" --region "${var.regiao}" 2>/dev/null || true
      aws s3api put-public-access-block --bucket "${var.bucket_nome}" \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3 cp "${path.module}/../job/dataframe_job.py"  "s3://${var.bucket_nome}/scripts/dataframe_job.py"
      aws s3 cp "${path.module}/../data/pedidos.csv"      "s3://${var.bucket_nome}/input/pedidos.csv"
      aws s3 cp "${path.module}/../data/clientes.csv"     "s3://${var.bucket_nome}/input/clientes.csv"
    CMD
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — o motor onde os DataFrames / Spark SQL vão rodar.
# LabRole por ARN (sem criar roles/policies próprias).
# Econômico: glue_version 4.0, worker G.1X, 2 workers.
#
# default_arguments:
#   --PEDIDOS   → caminho S3 do CSV de pedidos (order_id, customer_id, category, value)
#   --CLIENTES  → caminho S3 do CSV de clientes (customer_id, customer_name, customer_uf)
#   --OUTPUT    → prefixo S3 onde o resultado TOP-N será gravado (CSV com header)
#   --TOP_N     → número de clientes no TOP-N (padrão: 10)
# -----------------------------------------------------------------------------
resource "aws_glue_job" "topn_clientes" {
  name     = "job-aula06-topn-clientes"
  role_arn = var.labrole_arn
  tags     = var.tags

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
    "--PEDIDOS"  = "s3://${var.bucket_nome}/input/pedidos.csv"
    "--CLIENTES" = "s3://${var.bucket_nome}/input/clientes.csv"
    "--OUTPUT"   = "s3://${var.bucket_nome}/output/top_clientes"
    "--TOP_N"    = "10"
    # Logs contínuos do Spark/driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    # Diretório temporário exigido pelo Glue (fica dentro do mesmo bucket).
    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}
