# versions.tf — aws-lab (aula-07 • DEMO DO PROFESSOR — Previsão de Ações)
# PRONTO — não precisa alterar.
#
# IMPORTANTE (AWS Academy Learner Lab): o provider aws é FIXADO em 5.31.0
# (note o "=" implícito, NÃO ">="). Versões mais novas reintroduzem, no refresh
# de S3, a leitura da configuração de Object Lock
# (ex.: GetBucketObjectLockConfiguration) que a SCP da organização do Learner Lab
# NEGA, causando AccessDenied. O pin em 5.31.0 evita essa regressão de ambiente.
# Além disso, o bucket é criado via AWS CLI (ver main.tf), não com aws_s3_bucket.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}
