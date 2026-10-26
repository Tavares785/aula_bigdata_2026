# variables.tf — aws-lab (aula-09: Data Warehousing com Spark SQL no AWS Glue)
# Preencha os valores em terraform.tfvars.

variable "regiao" {
  description = "Região AWS obrigatória do lab (Learner Lab)."
  type        = string
  default     = "us-east-1"
}

variable "labrole_arn" {
  description = "ARN da role LabRole do Learner Lab, usada como IAM role do Glue Job."
  type        = string
}

variable "bucket_nome" {
  description = "Nome global único do bucket S3 do lab (script, dados de entrada, lake e resultados)."
  type        = string
}

variable "tags" {
  description = "Tags de custo padronizadas aplicadas a todos os recursos."
  type        = map(string)
  default = {
    Projeto    = "lab-aula-09-dw"
    Disciplina = "Big Data"
    Ambiente   = "LearnerLab"
  }
}
