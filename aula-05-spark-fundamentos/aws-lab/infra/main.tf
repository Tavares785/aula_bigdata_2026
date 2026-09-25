provider "aws" {
  region = var.regiao
}

resource "terraform_data" "bucket" {
  input = {
    bucket = var.bucket_nome
    regiao = var.regiao
  }

  triggers_replace = [
    var.bucket_nome,
    var.regiao
  ]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<-POWERSHELL
      $ErrorActionPreference = "Stop"

      aws s3api create-bucket `
        --bucket "${var.bucket_nome}" `
        --region "${var.regiao}"

      aws s3api put-public-access-block `
        --bucket "${var.bucket_nome}" `
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

      aws s3 cp `
        "${path.module}/../job/rdd_job.py" `
        "s3://${var.bucket_nome}/scripts/rdd_job.py"

      aws s3 cp `
        "${path.module}/../data/sample_lines.txt" `
        "s3://${var.bucket_nome}/input/sample_lines.txt"
    POWERSHELL
  }

  provisioner "local-exec" {
    when = destroy

    interpreter = ["PowerShell", "-Command"]

    command = <<-POWERSHELL
      $ErrorActionPreference = "SilentlyContinue"

      aws s3 rb `
        "s3://${self.input.bucket}" `
        --force
    POWERSHELL
  }
}

resource "aws_glue_job" "wordcount" {
  name     = "job-aula05-wordcount"
  role_arn = var.labrole_arn
  tags     = var.tags

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  depends_on = [terraform_data.bucket]

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/rdd_job.py"
  }

  default_arguments = {
    "--INPUT"  = "s3://${var.bucket_nome}/input/sample_lines.txt"
    "--OUTPUT" = "s3://${var.bucket_nome}/output/wordcount"

    "--enable-continuous-cloudwatch-log" = "true"

    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}
