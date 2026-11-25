# versions.tf (aula-14) - PRONTO, nao precisa alterar.
#
# O provider aws e FIXADO em 5.31.0: versoes mais novas leem a configuracao de
# Object Lock do S3, que a SCP do Learner Lab nega (AccessDenied).

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}
