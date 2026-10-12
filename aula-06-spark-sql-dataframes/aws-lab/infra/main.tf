# =============================================================================
# main.tf — aws-lab (aula-06)
#
# Por que o bucket é criado via AWS CLI (local-exec) e não aws_s3_bucket?
#   O Learner Lab tem uma SCP que nega s3:GetBucketObjectLockConfiguration —
#   leitura que o recurso aws_s3_bucket sempre faz no create/refresh, resultando
#   em AccessDenied. O workaround é criar/destruir o bucket com AWS CLI dentro
#   do próprio terraform apply/destroy.
# =============================================================================

locals {
  glue_job_nome = "job-aula06-topn-clientes"

  # Caminhos relativos ao diretório infra/ (onde o terraform roda)
  job_file      = "${path.module}/../job/dataframe_job.py"
  pedidos_file  = "${path.module}/../data/pedidos.csv"
  clientes_file = "${path.module}/../data/clientes.csv"
}

# -----------------------------------------------------------------------------
# Bucket S3 — criado via AWS CLI para contornar a SCP do Learner Lab.
# terraform_data não gerencia estado de resource externo, mas o provisioner
# local-exec executa os comandos shell no apply e no destroy.
# -----------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  input = var.bucket_nome

  # CREATE: cria o bucket (privado) e bloqueia ACLs públicas.
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      aws s3api create-bucket `
        --bucket ${var.bucket_nome} `
        --region ${var.regiao}
      
      aws s3api put-public-access-block `
        --bucket ${var.bucket_nome} `
        --public-access-block-configuration `
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    EOT
  }

  # DESTROY: esvazia e remove o bucket.
  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      aws s3 rm s3://${self.input} --recursive || true
      aws s3api delete-bucket \
        --bucket ${self.input} \
        --region us-east-1 || true
    EOT
  }
}

# -----------------------------------------------------------------------------
# Upload do script PySpark para s3://BUCKET/scripts/
# -----------------------------------------------------------------------------
resource "terraform_data" "upload_script" {
  depends_on = [terraform_data.bucket]

  triggers_replace = [
    var.bucket_nome,
    filemd5(local.job_file),
  ]

  provisioner "local-exec" {
    command = "aws s3 cp ${local.job_file} s3://${var.bucket_nome}/scripts/dataframe_job.py"
  }
}

# -----------------------------------------------------------------------------
# Upload dos CSVs de entrada para s3://BUCKET/input/
# -----------------------------------------------------------------------------
resource "terraform_data" "upload_dados" {
  depends_on = [terraform_data.bucket]

  triggers_replace = [
    var.bucket_nome,
    filemd5(local.pedidos_file),
    filemd5(local.clientes_file),
  ]

  provisioner "local-exec" {
    command = <<-EOT
      aws s3 cp ${local.pedidos_file}  s3://${var.bucket_nome}/input/pedidos.csv
      aws s3 cp ${local.clientes_file} s3://${var.bucket_nome}/input/clientes.csv
    EOT
  }
}

# -----------------------------------------------------------------------------
# AWS Glue Job
# -----------------------------------------------------------------------------
resource "aws_glue_job" "topn" {
  depends_on = [terraform_data.upload_script]

  name     = local.glue_job_nome
  role_arn = var.labrole_arn

  # glueetl = job Spark gerenciado pelo Glue.
  # python_version 3 + glue_version 4.0 = Spark 3.3 / Python 3.10.
  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/dataframe_job.py"
  }

  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"

  # Argumentos padrão passados ao script PySpark.
  default_arguments = {
    "--PEDIDOS"          = "s3://${var.bucket_nome}/input/pedidos.csv"
    "--CLIENTES"         = "s3://${var.bucket_nome}/input/clientes.csv"
    "--OUTPUT"           = "s3://${var.bucket_nome}/output/top_clientes"
    "--TOP_N"            = "10"
    "--TempDir"          = "s3://${var.bucket_nome}/tmp/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-job-insights"              = "true"
    "--job-language"                     = "python"
  }

  # Retém os logs no CloudWatch por 1 dia (suficiente para o lab).
  execution_property {
    max_concurrent_runs = 1
  }

  tags = var.tags
}
