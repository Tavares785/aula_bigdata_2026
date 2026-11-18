variable "bucket_nome" {
  description = "Nome globalmente unico do bucket S3 do pipeline."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.bucket_nome))
    error_message = "Use de 3 a 63 caracteres: letras minusculas, numeros e hifens."
  }
}

variable "labrole_arn" {
  description = "ARN da LabRole do Learner Lab, usada pelo Glue Job e pelo Crawler."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/LabRole$", var.labrole_arn))
    error_message = "Informe o ARN completo da LabRole."
  }
}

variable "lgpd_salt" {
  description = "Salt da pseudonimizacao do cliente. Gere com: openssl rand -hex 32."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.lgpd_salt) >= 32
    error_message = "O salt precisa de pelo menos 32 caracteres."
  }
}

variable "prefixo" {
  description = "Prefixo dos recursos Glue."
  type        = string
  default     = "mercadofacil"
}
