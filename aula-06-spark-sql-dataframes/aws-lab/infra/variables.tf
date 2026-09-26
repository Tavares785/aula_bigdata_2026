variable "regiao" {
  description = "Regiao AWS obrigatoria do Learner Lab."
  type        = string
  default     = "us-east-1"
}

variable "labrole_arn" {
  description = "ARN da LabRole pre-provisionada do Learner Lab."
  type        = string
}

variable "bucket_nome" {
  description = "Nome globalmente unico do bucket S3 do laboratorio."
  type        = string
}

variable "tags" {
  description = "Tags aplicadas aos recursos AWS do laboratorio."
  type        = map(string)
  default = {
    Projeto    = "lab-aula-06-spark-sql"
    Disciplina = "Big Data"
    Ambiente   = "LearnerLab"
  }
}