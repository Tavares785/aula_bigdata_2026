# versions.tf — aws-lab (aula-06: Spark SQL e DataFrames no AWS Glue)
#
# ESCRITO PELO ALUNO: este arquivo nao veio no repositorio do professor.
# Ver a nota em main.tf.
#
# IMPORTANTE (AWS Academy Learner Lab): o provider aws e FIXADO em 5.31.0
# (note o "=" implicito, NAO ">="). Versoes mais novas reintroduzem, no refresh
# de S3, a leitura da configuracao de Object Lock
# (ex.: GetBucketObjectLockConfiguration) que a SCP da organizacao do Learner
# Lab NEGA, causando AccessDenied. O pin em 5.31.0 evita essa regressao.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}
