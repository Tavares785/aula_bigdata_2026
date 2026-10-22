# main.tf — aws-lab (aula-06: Spark SQL e DataFrames no AWS Glue)
# =============================================================================
# ⚠️ ESCRITO PELO ALUNO — este arquivo NAO veio no repositorio do professor.
#
# A pasta infra/ desta aula foi publicada contendo apenas o
# terraform.tfvars.example; faltavam main.tf, variables.tf, versions.tf e
# outputs.tf (a aula-07 tem os cinco). Sem eles o `terraform apply` descrito
# no README nao tem o que aplicar.
#
# Reescrevi a infra espelhando a da aula-07, que funciona, adaptada ao que
# esta aula precisa:
#   - DOIS CSVs de entrada (pedidos.csv e clientes.csv), nao um
#   - os argumentos que o dataframe_job.py le: --PEDIDOS, --CLIENTES,
#     --OUTPUT e --TOP_N
#   - os outputs que o scripts/run_job.sh consome por `terraform output -raw`:
#     bucket_nome, glue_job_nome e labrole_arn
#
# O que este arquivo provisiona:
#   - O bucket S3 do lab (PRIVADO) e o upload do job + os dois CSVs.
#     ATENCAO: o bucket NAO e criado com aws_s3_bucket. No AWS Academy Learner
#     Lab ha uma SCP que NEGA s3:GetBucketObjectLockConfiguration, e o recurso
#     aws_s3_bucket SEMPRE le essa config (create/refresh) -> AccessDenied.
#     Por isso criamos o bucket via AWS CLI dentro do `terraform apply`
#     (terraform_data + local-exec). REQUER o AWS CLI instalado.
#   - Um AWS Glue Job (PySpark / glueetl) que calcula a receita por categoria
#     e o top-N de clientes por gasto, gravando o resultado no S3.
#
# Por que Glue e nao EMR Serverless?
#   Neste Learner Lab o EMR Serverless esta BLOQUEADO (a LabRole nao confia em
#   emr-serverless.amazonaws.com); o Glue funciona (confia em glue.amazonaws.com).
#
# Regras do Learner Lab:
#   - Regiao fixa us-east-1 (via var.regiao).
#   - NAO criamos roles/policies IAM proprias: o Glue Job usa a LabRole por ARN.
#   - Bucket S3 PRIVADO (public access block com os 4 bloqueios = true).
#   - Rode `terraform destroy` ao final para nao deixar recursos residuais.
# =============================================================================

provider "aws" {
  region = var.regiao
}

# -----------------------------------------------------------------------------
# Bucket S3 do lab (criado via AWS CLI, NAO via aws_s3_bucket).
# Prefixos: scripts/, input/, output/, tmp/.
# - create: cria o bucket, aplica public-access-block (PRIVADO) e sobe o job
#   (dataframe_job.py) + os dois CSVs de entrada.
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
      aws s3 cp "${path.module}/../job/dataframe_job.py" "s3://${var.bucket_nome}/scripts/dataframe_job.py"
      aws s3 cp "${path.module}/../data/pedidos.csv"  "s3://${var.bucket_nome}/input/pedidos.csv"
      aws s3 cp "${path.module}/../data/clientes.csv" "s3://${var.bucket_nome}/input/clientes.csv"
    CMD
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — onde as consultas de DataFrame vao rodar.
# LabRole por ARN. Economico: glue_version 4.0, worker G.1X, 2 workers.
# Os quatro argumentos abaixo sao exatamente os que o dataframe_job.py pede em
# getResolvedOptions(sys.argv, ["JOB_NAME","PEDIDOS","CLIENTES","OUTPUT","TOP_N"]).
# -----------------------------------------------------------------------------
resource "aws_glue_job" "spark_sql" {
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
    "--OUTPUT"   = "s3://${var.bucket_nome}/output"
    "--TOP_N"    = tostring(var.top_n)
    # Logs continuos do Spark/driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    # Diretorio temporario exigido pelo Glue (dentro do mesmo bucket).
    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}
