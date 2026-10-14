# versions.tf — aws-lab (aula-05: Spark/RDDs no AWS Glue)
# PRONTO — não precisa alterar.
#
# IMPORTANTE (AWS Academy Learner Lab): provider aws FIXADO em 5.31.0. Versões
# mais novas fazem, no refresh de S3, chamadas (ex.: GetBucketObjectLockConfiguration)
# que a SCP da organização do Academy NEGA. Além disso, o bucket é criado via
# AWS CLI (ver main.tf), e não com o recurso aws_s3_bucket.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}
