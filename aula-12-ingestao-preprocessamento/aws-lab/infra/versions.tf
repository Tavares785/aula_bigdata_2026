# Aula 12 - Ingestao e Pre-processamento (MercadoFacil)
# Pipeline: S3 raw -> Glue Job (PySpark) -> S3 silver/gold -> Glue Catalog -> Athena
# Restricoes do Learner Lab:
#   - provider aws fixado em 5.31.0, regiao us-east-1
#   - bucket criado via AWS CLI (terraform_data + local-exec), NAO via aws_s3_bucket
#   - nenhuma role/policy IAM criada: usa a LabRole da AWS Academy

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
