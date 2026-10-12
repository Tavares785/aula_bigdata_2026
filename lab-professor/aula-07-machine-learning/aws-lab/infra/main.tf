# main.tf — aws-lab (aula-07 • DEMO DO PROFESSOR — Previsão de direção de Ações)
# =============================================================================
# INFRA PRONTA DA DEMO — você NÃO precisa alterar este arquivo.
#
# Esta é a DEMO DO PROFESSOR: diferente do Trabalho Final do aluno (que faz
# classificação de CHURN), aqui o cenário é PREVISÃO DE DIREÇÃO DE AÇÕES —
# classificação binária de se a ação SOBE (1) ou CAI (0) no dia seguinte, a
# partir de features técnicas sintéticas. O pipeline MLlib + Glue é o mesmo;
# só muda o domínio, para dar repertório.
#
# O que este arquivo provisiona:
#   - O bucket S3 da demo (PRIVADO) e o upload do script PySpark + dataset de ações.
#     ATENÇÃO: o bucket NÃO é criado com aws_s3_bucket. No AWS Academy Learner
#     Lab há uma SCP que NEGA s3:GetBucketObjectLockConfiguration, e o recurso
#     aws_s3_bucket SEMPRE lê essa config (create/refresh) -> AccessDenied. Para
#     contornar, criamos o bucket via AWS CLI dentro do `terraform apply`
#     (terraform_data + local-exec). REQUER o AWS CLI instalado.
#   - Um AWS Glue Job (PySpark / glueetl) que treina DOIS modelos (Regressão
#     Logística e Random Forest), compara-os e grava as métricas e uma amostra
#     de previsões no S3.
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
# Bucket S3 da demo (criado via AWS CLI, NÃO via aws_s3_bucket).
# Prefixos: scripts/, input/, output/, tmp/.
# - create: cria o bucket, aplica public-access-block (PRIVADO) e sobe o script
#   PySpark (acoes_job.py) + o dataset de entrada (acoes.csv).
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
      aws s3 cp "${path.module}/../job/acoes_job.py" "s3://${var.bucket_nome}/scripts/acoes_job.py"
      aws s3 cp "${path.module}/../data/acoes.csv" "s3://${var.bucket_nome}/input/acoes.csv"
    CMD
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — o motor onde o pipeline de ML vai rodar. LabRole por ARN.
# Econômico: glue_version 4.0, worker G.1X, 2 workers.
# O --OUTPUT aponta para o prefixo output/ porque o job grava DOIS subprefixos:
# output/metrics e output/predictions (o job monta os caminhos a partir do --OUTPUT).
# -----------------------------------------------------------------------------
resource "aws_glue_job" "acoes" {
  name     = "job-aula07-demo-acoes"
  role_arn = var.labrole_arn
  tags     = var.tags

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  depends_on = [terraform_data.bucket]

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/acoes_job.py"
  }

  default_arguments = {
    "--INPUT"  = "s3://${var.bucket_nome}/input/acoes.csv"
    "--OUTPUT" = "s3://${var.bucket_nome}/output"
    # Logs contínuos do Spark/driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    # Diretório temporário exigido pelo Glue (fica dentro do mesmo bucket).
    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}
