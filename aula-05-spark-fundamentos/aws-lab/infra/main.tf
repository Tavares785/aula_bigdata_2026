# main.tf — aws-lab (aula-05: Spark/RDDs no AWS Glue)
# =============================================================================
# INFRA PRONTA DO LAB — você NÃO precisa alterar este arquivo.
#
# O que este arquivo provisiona:
#   - O bucket S3 do lab (PRIVADO) e o upload do script + dado de entrada.
#     ATENÇÃO: o bucket NÃO é criado com aws_s3_bucket. No AWS Academy Learner
#     Lab há uma SCP que NEGA s3:GetBucketObjectLockConfiguration, e o recurso
#     aws_s3_bucket SEMPRE lê essa config (create/refresh) -> AccessDenied. Para
#     contornar, criamos o bucket via AWS CLI dentro do `terraform apply`
#     (terraform_data + local-exec). REQUER o AWS CLI instalado.
#   - Um AWS Glue Job (PySpark / glueetl) que roda o word count com RDDs.
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
# Bucket S3 do lab — armazenamento distribuído/durável (o "HDFS da nuvem").
# ÚNICO bucket, organizado por prefixos:
#   - scripts/ : o rdd_job.py (script do Glue Job)
#   - input/   : sample_lines.txt (dado de entrada)
#   - output/  : resultado do wordcount (gravado pelo job)
#   - logs/    : logs do driver/executors do job
#
# ⚠️ Por que null_resource + local-exec (e não o recurso nativo
# aws_s3_bucket)?
#   O recurso nativo "aws_s3_bucket" do provider, logo após criar (ou destruir
#   e recriar) o bucket, SEMPRE chama a API GetBucketObjectLockConfiguration
#   pra popular um atributo do state — mesmo sem usar Object Lock e mesmo
#   definindo object_lock_enabled = false explicitamente. No AWS Academy
#   Learner Lab essa chamada é NEGADA por uma SCP da organização (Object Lock
#   cria travas de retenção que nem um admin consegue desfazer, perigoso numa
#   conta compartilhada de ensino), o que quebrava o `terraform apply` com
#   AccessDenied mesmo o bucket sendo criado com sucesso.
#   Solução: criar o bucket via AWS CLI (que não faz essa leitura extra) num
#   provisioner local-exec dentro de um null_resource. O Terraform passa a
#   tratar a criação/destruição do bucket como um comando externo, em vez de
#   um recurso com schema próprio.
# -----------------------------------------------------------------------------
resource "null_resource" "bucket" {
  # Guarda o nome do bucket no state deste null_resource. É usado no
  # provisioner de destroy (abaixo), que só pode referenciar `self`.
  triggers = {
    bucket_nome = var.bucket_nome
  }

  provisioner "local-exec" {
    command = "aws s3api create-bucket --bucket ${var.bucket_nome} --region ${var.regiao}"
  }

  # Provisioner de DESTROY: roda quando o recurso é destruído (terraform
  # destroy do Passo 7), apagando o bucket e tudo dentro dele (--force).
  # Só pode usar `self` — por isso lemos o nome de self.triggers, não de
  # var.bucket_nome diretamente.
  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.triggers.bucket_nome} --force"
  }
}

# -----------------------------------------------------------------------------
# Bucket PRIVADO — bloqueia qualquer acesso público (os 4 bloqueios = true).
# depends_on é necessário porque agora não há mais um atributo de recurso
# (tipo aws_s3_bucket.lab.id) pra criar a dependência implícita — usamos a
# string var.bucket_nome direto, então precisamos declarar a ordem à mão.
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = var.bucket_nome
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  depends_on = [null_resource.bucket]
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

  depends_on = [null_resource.bucket]
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

  depends_on = [null_resource.bucket]
}

# -----------------------------------------------------------------------------
# AWS Glue Job (glueetl) — o motor onde os RDDs vão rodar. LabRole por ARN.
# Econômico: glue_version 4.0, worker G.1X, 2 workers.
# -----------------------------------------------------------------------------
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
    # Logs contínuos do Spark/driver no CloudWatch (grupo /aws-glue/jobs/output).
    "--enable-continuous-cloudwatch-log" = "true"
    # Diretório temporário exigido pelo Glue (fica dentro do mesmo bucket).
    "--TempDir" = "s3://${var.bucket_nome}/tmp/"
  }

  # Sem atributo de recurso pra criar dependência implícita (usamos a string
  # var.bucket_nome), então declaramos que o bucket precisa existir antes.
  depends_on = [null_resource.bucket]
}
