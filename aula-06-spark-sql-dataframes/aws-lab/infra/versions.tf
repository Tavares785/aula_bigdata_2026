# versions.tf — aws-lab (aula-06: Spark SQL/DataFrames no AWS Glue)
# PRONTO — não precisa alterar.
#
# Fixa a versão mínima do Terraform e do provider AWS usados no lab.
# O provider AWS é configurado em main.tf (região via var.regiao).
# Sem backend remoto: o state fica LOCAL (arquivo terraform.tfstate na pasta).
#
# IMPORTANTE (AWS Academy Learner Lab): o provider aws está FIXADO em 5.31.0.
# Versões mais novas (ex.: 5.100.x) fazem, no refresh do aws_s3_bucket, uma
# chamada s3:GetBucketObjectLockConfiguration que a SCP da organização do
# Academy NEGA (AccessDenied). A 5.31.0 não faz esse GET, evitando o erro.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}
