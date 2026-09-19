# main.tf — aws-lab (aula-05: Spark/RDDs no AWS Glue)
# =============================================================================
# INFRA PRONTA DO LAB — você NÃO precisa alterar este arquivo.
#
# O que este arquivo provisiona:
#   - Um bucket S3 PRIVADO (guarda o script PySpark, os dados de entrada, a
#     saída do job e os logs). Um ÚNICO bucket com prefixos: scripts/, input/,
#     output/ e logs/.
#   - Um AWS Glue Job (PySpark / glueetl) que roda o word count com RDDs. O
#     Glue é o "Spark gerenciado": a AWS provisiona driver e executors sob
#     demanda quando o job é disparado, sem você ligar/desligar máquinas.
#
# Por que Glue e não EMR Serverless?
#   Neste Learner Lab o EMR Serverless está BLOQUEADO (a LabRole não confia em
#   emr-serverless.amazonaws.com), mas o Glue FUNCIONA (a LabRole confia em
#   glue.amazonaws.com). É o mesmo serviço usado na prova deste repositório.
#
# Regras do Learner Lab (leia antes de aplicar):
#   - Região fixa us-east-1 (via var.regiao).
#   - NÃO criamos roles/policies IAM próprias: o Glue Job usa a LabRole por ARN
#     (var.labrole_arn) como IAM role de execução.
#   - Bucket S3 PRIVADO (public access block com os 4 bloqueios = true).
#   - Rode `terraform destroy` ao final para não deixar recursos residuais.
# =============================================================================

# -----------------------------------------------------------------------------
# Provider AWS — PRONTO
# Região fixada em var.regiao (us-east-1) e tags de custo aplicadas
# automaticamente a todos os recursos via default_tags.
# -----------------------------------------------------------------------------
provider "aws" {
  region = var.regiao

  default_tags {
    tags = var.tags
  }
}

# -----------------------------------------------------------------------------
# Bucket S3 do lab — armazenamento distribuído/durável (o "HDFS da nuvem").
# ÚNICO bucket, organizado por prefixos:
#   - scripts/ : o rdd_job.py (script do Glue Job)
#   - input/   : sample_lines.txt (dado de entrada)
#   - output/  : resultado do wordcount (gravado pelo job)
#   - logs/    : logs do driver/executors do job
# -----------------------------------------------------------------------------
resource "terraform_data" "s3_bucket" {
  triggers_replace = [
    var.bucket_nome
  ]

  provisioner "local-exec" {
    command = "aws s3api head-bucket --bucket ${var.bucket_nome} 2>nul || aws s3api create-bucket --bucket ${var.bucket_nome} --region ${var.regiao}"
  }
}

# -----------------------------------------------------------------------------
# Bucket PRIVADO — bloqueia qualquer acesso público (os 4 bloqueios = true).
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = var.bucket_nome
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# Upload do script PySpark para o S3 (prefixo scripts/).
# O `terraform apply` já publica o script no bucket; é DAQUI que o Glue Job lê
# o código (script_location aponta para s3://.../scripts/rdd_job.py).
# O etag (filemd5) força o re-upload sempre que o script mudar.
# -----------------------------------------------------------------------------
resource "aws_s3_object" "script" {
  bucket = var.bucket_nome
  key    = "scripts/rdd_job.py"
  source = "${path.module}/../job/rdd_job.py"
  etag   = filemd5("${path.module}/../job/rdd_job.py")
}

# -----------------------------------------------------------------------------
# Upload do dado de exemplo para o S3 (prefixo input/).
# É o texto que o job vai ler (arg --INPUT). O etag força re-upload ao mudar.
# -----------------------------------------------------------------------------
resource "aws_s3_object" "input" {
  bucket = var.bucket_nome
  key    = "input/sample_lines.txt"
  source = "${path.module}/../data/sample_lines.txt"
  etag   = filemd5("${path.module}/../data/sample_lines.txt")
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — o motor onde os RDDs vão rodar.
# Não há cluster para ligar/desligar: driver e executors são provisionados
# sob demanda quando o job é disparado (aws glue start-job-run) e liberados no
# fim. NÃO cria IAM role: usa a LabRole por ARN (var.labrole_arn).
#
# Escolhas ECONÔMICAS para o orçamento do Learner Lab:
#   - glue_version 4.0    : runtime Spark atual e estável.
#   - worker_type G.1X    : o menor worker padrão (4 vCPU / 16 GB).
#   - number_of_workers 2 : mínimo para ter 1 driver + 1 executor, suficiente
#                           para o dataset pequeno deste lab.
# -----------------------------------------------------------------------------
resource "aws_glue_job" "wordcount" {
  name     = "job-aula05-wordcount"
  role_arn = var.labrole_arn

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  # command.name = "glueetl" indica um job PySpark (Spark ETL). O script é lido
  # do S3 (publicado pelo aws_s3_object.script acima).
  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${var.bucket_nome}/scripts/rdd_job.py"
  }

  # Argumentos passados ao script (getResolvedOptions os lê como --INPUT etc.).
  default_arguments = {
    "--INPUT"  = "s3://${var.bucket_nome}/input/sample_lines.txt"
    "--OUTPUT" = "s3://${var.bucket_nome}/output/wordcount"
    # Logs contínuos do Spark/driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    # Diretório temporário exigido pelo Glue (fica dentro do mesmo bucket).
    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }
}
