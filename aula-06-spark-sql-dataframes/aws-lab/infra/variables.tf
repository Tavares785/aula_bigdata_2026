variable "regiao" {
  description = "Região AWS onde os recursos serão criados (Learner Lab: us-east-1)."
  type        = string
  default     = "us-east-1"
}

variable "labrole_arn" {
  description = "ARN da LabRole pré-provisionada no Learner Lab. Obtenha com: aws iam get-role --role-name LabRole --query Role.Arn --output text"
  type        = string
}

variable "bucket_nome" {
  description = "Nome globalmente único do bucket S3 do lab (ex.: lab-aula06-glue-SEURA)."
  type        = string
}

variable "tags" {
  description = "Tags de custo aplicadas a todos os recursos."
  type        = map(string)
  default = {
    Projeto    = "lab-aula-06-spark-sql"
    Disciplina = "Big Data"
    Ambiente   = "LearnerLab"
  }
}
