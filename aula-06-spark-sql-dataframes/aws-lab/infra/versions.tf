# versions.tf - aws-lab (aula-06: Spark SQL / DataFrames no AWS Glue)
# Provider aws fixado em 5.31.0 (conforme README).

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}