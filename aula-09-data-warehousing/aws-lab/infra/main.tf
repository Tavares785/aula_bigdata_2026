# main.tf — aws-lab (aula-09: Data Warehousing com Spark SQL no AWS Glue)
# =============================================================================
# Mesmo padrão do aws-lab da aula-07:
#   - Bucket S3 PRIVADO criado via AWS CLI (terraform_data + local-exec), porque
#     a SCP do Learner Lab nega s3:GetBucketObjectLockConfiguration e o recurso
#     aws_s3_bucket sempre lê essa config -> AccessDenied. REQUER o AWS CLI.
#   - Upload do job (warehouse_job.py), do módulo com as queries do TF
#     (src/warehouse_queries.py, via --extra-py-files) e do dataset de vendas.
#   - Um AWS Glue Job (glueetl) que monta a camada "lake" em Parquet
#     particionado por região e roda as 3 queries SQL do warehouse.
#
# Regras do Learner Lab:
#   - Região fixa us-east-1 (via var.regiao).
#   - NÃO criamos roles/policies IAM próprias: o Glue Job usa a LabRole por ARN.
#   - Rode `terraform destroy` ao final para não deixar recursos residuais.
# =============================================================================

provider "aws" {
  region = var.regiao
}

# -----------------------------------------------------------------------------
# Bucket S3 do lab (criado via AWS CLI, NÃO via aws_s3_bucket).
# Prefixos: scripts/, input/, output/, tmp/.
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
      aws s3 cp "${path.module}/../job/warehouse_job.py" "s3://${var.bucket_nome}/scripts/warehouse_job.py"
      aws s3 cp "${path.module}/../../src/warehouse_queries.py" "s3://${var.bucket_nome}/scripts/warehouse_queries.py"
      aws s3 cp "${path.module}/../../data/sample_sales.csv" "s3://${var.bucket_nome}/input/sample_sales.csv"
    CMD
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — LabRole por ARN. Econômico: Glue 4.0, 2x G.1X.
# --extra-py-files deixa o `import warehouse_queries` disponível no driver.
# -----------------------------------------------------------------------------
resource "aws_glue_job" "warehouse" {
  name     = "job-aula09-warehouse"
  role_arn = var.labrole_arn
  tags     = var.tags

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  depends_on = [terraform_data.bucket]

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/warehouse_job.py"
  }

  default_arguments = {
    "--INPUT"           = "s3://${var.bucket_nome}/input/sample_sales.csv"
    "--OUTPUT"          = "s3://${var.bucket_nome}/output"
    "--TOP_N"           = "2"
    "--THRESHOLD"       = "5000"
    "--extra-py-files"  = "s3://${var.bucket_nome}/scripts/warehouse_queries.py"
    # Logs contínuos do driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${var.bucket_nome}/tmp/"
  }
}
