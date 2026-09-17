# versions.tf — aws-lab (aula-05: Spark/RDDs no AWS Glue)
# PRONTO — não precisa alterar.
#
# Fixa a versão mínima do Terraform e do provider AWS usados no lab.
# O provider AWS é configurado em main.tf (região via var.regiao).
# Sem backend remoto: o state fica LOCAL (arquivo terraform.tfstate na pasta).

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}
