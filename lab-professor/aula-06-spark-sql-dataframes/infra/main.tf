# ★ GABARITO DO PROFESSOR ★ — infra idêntica à do aluno (já vem pronta). NÃO distribuir.
# main.tf — aws-lab (aula-06: Spark SQL/DataFrames no AWS Glue)
# =============================================================================
# INFRA PRONTA DO LAB — você NÃO precisa alterar este arquivo.
#
# O que este arquivo provisiona:
#   - O bucket S3 do lab (PRIVADO) e o upload do script + 2 CSVs de entrada.
#     ATENÇÃO: o bucket NÃO é criado com o recurso aws_s3_bucket. No AWS Academy
#     Learner Lab há uma SCP (Service Control Policy) que NEGA
#     s3:GetBucketObjectLockConfiguration, e o recurso aws_s3_bucket SEMPRE lê
#     essa configuração (na criação e no refresh) -> AccessDenied. Para contornar,
#     criamos o bucket via AWS CLI (aws s3 mb) dentro do próprio terraform apply,
#     usando um terraform_data + provisioner local-exec. Assim o bucket entra no
#     fluxo do Terraform (apply cria, destroy remove) SEM disparar o GET proibido.
#   - Um AWS Glue Job (PySpark / glueetl) que faz join + agregação com a API de
#     DataFrames/Spark SQL e grava o TOP-N de clientes por gasto. O Glue é o
#     "Spark gerenciado": a AWS provisiona driver e executors sob demanda quando
#     o job é disparado, sem você ligar/desligar máquinas.
#
# Por que Glue e não EMR Serverless?
#   Neste Learner Lab o EMR Serverless está BLOQUEADO (a LabRole não confia em
#   emr-serverless.amazonaws.com), mas o Glue FUNCIONA (a LabRole confia em
#   glue.amazonaws.com). É o mesmo serviço usado na prova deste repositório.
#
# Regras do Learner Lab (leia antes de aplicar):
#   - Região fixa us-east-1 (via var.regiao).
#   - NÃO criamos roles/policies IAM próprias: o Glue Job usa a LabRole por ARN.
#   - Bucket S3 PRIVADO (public access block com os 4 bloqueios = true).
#   - Rode `terraform destroy` ao final para não deixar recursos residuais.
#   - REQUER o AWS CLI instalado (o bucket é criado via CLI pelo local-exec).
# =============================================================================

# -----------------------------------------------------------------------------
# Provider AWS — PRONTO. Região fixada em var.regiao (us-east-1).
# -----------------------------------------------------------------------------
provider "aws" {
  region = var.regiao
}

# -----------------------------------------------------------------------------
# Bucket S3 do lab (criado via AWS CLI, NÃO via aws_s3_bucket) — ver cabeçalho.
# ÚNICO bucket, organizado por prefixos: scripts/, input/, output/, logs/, tmp/.
#
# - triggers_replace: recria se o nome do bucket mudar.
# - provisioner "local-exec" (create): cria o bucket (idempotente com "|| true"),
#   aplica o public-access-block (bucket PRIVADO, 4 bloqueios) e sobe o script e
#   os 2 CSVs de entrada para o S3.
# - provisioner "local-exec" (destroy): esvazia e remove o bucket no
#   `terraform destroy` (guardrail de custo do Learner Lab).
# -----------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  input = {
    bucket = var.bucket_nome
    regiao = var.regiao
    # Diretório do módulo, para localizar os arquivos a subir no create.
    dir = path.module
  }

  triggers_replace = [var.bucket_nome, var.regiao]

  # CREATE: cria o bucket, deixa privado e sobe script + dados.
  provisioner "local-exec" {
    command = <<-CMD
      set -e
      aws s3api create-bucket --bucket "${var.bucket_nome}" --region "${var.regiao}" 2>/dev/null || true
      aws s3api put-public-access-block --bucket "${var.bucket_nome}" \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3 cp "${path.module}/../job/dataframe_job.py" "s3://${var.bucket_nome}/scripts/dataframe_job.py"
      aws s3 cp "${path.module}/../data/pedidos.csv"     "s3://${var.bucket_nome}/input/pedidos.csv"
      aws s3 cp "${path.module}/../data/clientes.csv"    "s3://${var.bucket_nome}/input/clientes.csv"
    CMD
  }

  # DESTROY: esvazia e remove o bucket (roda no terraform destroy).
  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — o motor onde os DataFrames/Spark SQL vão rodar.
# Não há cluster para ligar/desligar: driver e executors são provisionados
# sob demanda quando o job é disparado (aws glue start-job-run) e liberados no
# fim. NÃO cria IAM role: usa a LabRole por ARN (var.labrole_arn).
#
# depends_on: garante que o bucket e o script já existam antes de criar o Job.
#
# Escolhas ECONÔMICAS para o orçamento do Learner Lab:
#   - glue_version 4.0    : runtime Spark atual e estável.
#   - worker_type G.1X    : o menor worker padrão (4 vCPU / 16 GB).
#   - number_of_workers 2 : mínimo para ter 1 driver + 1 executor.
# -----------------------------------------------------------------------------
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

  # Argumentos passados ao script (getResolvedOptions os lê como --PEDIDOS etc.).
  default_arguments = {
    "--PEDIDOS"  = "s3://${var.bucket_nome}/input/pedidos.csv"
    "--CLIENTES" = "s3://${var.bucket_nome}/input/clientes.csv"
    "--OUTPUT"   = "s3://${var.bucket_nome}/output/top_clientes"
    "--TOP_N"    = "5"
    # Logs contínuos do Spark/driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    # Diretório temporário exigido pelo Glue (fica dentro do mesmo bucket).
    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}
