variable "regiao" {
  description = "Regiao AWS do Learner Lab"
  type        = string
  default     = "us-east-1"
}

variable "labrole_arn" {
  description = "ARN da LabRole do Learner Lab"
  type        = string
}

variable "bucket_nome" {
  description = "Nome globalmente unico do bucket S3"
  type        = string
}

variable "top_n" {
  description = "Top N de resultados nas tabelas gold"
  type        = number
  default     = 10
}
