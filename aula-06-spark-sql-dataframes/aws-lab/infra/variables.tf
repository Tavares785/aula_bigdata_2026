# variables.tf - aws-lab (aula-06)

variable "regiao" {
  description = "Regiao AWS obrigatoria do lab (Learner Lab)."
  type        = string
  default     = "us-east-1"
}

variable "labrole_arn" {
  description = "ARN da LabRole do Learner Lab, usada como IAM role do Glue Job."
  type        = string
}

variable "bucket_nome" {
  description = "Nome global unico do bucket S3 do lab (script, 2 CSVs, output e logs)."
  type        = string
}

variable "top_n" {
  description = "Quantos clientes retornar no TOP-N."
  type        = number
  default     = 5
}

variable "tags" {
  description = "Tags de custo padronizadas."
  type        = map(string)
  default = {
    Projeto    = "lab-aula-06-spark-sql"
    Disciplina = "Big Data"
    Ambiente   = "LearnerLab"
  }
}