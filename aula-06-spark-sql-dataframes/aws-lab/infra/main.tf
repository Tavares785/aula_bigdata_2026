provider "aws" {
  region = var.regiao
}

resource "terraform_data" "bucket" {
  input = {
    bucket = var.bucket_nome
    regiao = var.regiao
  }

  triggers_replace = [var.bucket_nome, var.regiao]

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command = join("; ", [
      "set -e",
      "aws s3api head-bucket --bucket \"${var.bucket_nome}\" 2>/dev/null || aws s3api create-bucket --bucket \"${var.bucket_nome}\" --region \"${var.regiao}\"",
      "aws s3api put-public-access-block --bucket \"${var.bucket_nome}\" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
      "aws s3 cp \"${path.module}/../job/dataframe_job.py\" \"s3://${var.bucket_nome}/scripts/dataframe_job.py\"",
      "aws s3 cp \"${path.module}/../data/pedidos.csv\" \"s3://${var.bucket_nome}/input/pedidos.csv\"",
      "aws s3 cp \"${path.module}/../data/clientes.csv\" \"s3://${var.bucket_nome}/input/clientes.csv\"",
    ])
  }

  provisioner "local-exec" {
    when        = destroy
    interpreter = ["bash", "-c"]
    command     = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

resource "aws_glue_job" "dataframes" {
  name     = "job-aula06-topn-clientes"
  role_arn = var.labrole_arn
  tags     = var.tags

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 20

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
    "--TOP_N"                            = "5"
    "--TempDir"                          = "s3://${var.bucket_nome}/tmp/"
    "--enable-continuous-cloudwatch-log" = "true"
  }
}