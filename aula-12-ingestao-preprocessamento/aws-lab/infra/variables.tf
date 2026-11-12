variable "aws_region" {
  description = "Regiao da AWS. O Learner Lab so permite us-east-1."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = var.aws_region == "us-east-1"
    error_message = "O AWS Academy Learner Lab so permite a regiao us-east-1."
  }
}

variable "lab_role_arn" {
  description = "ARN da LabRole (aws iam get-role --role-name LabRole --query Role.Arn --output text)."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:role/LabRole$", var.lab_role_arn))
    error_message = "Informe o ARN completo da LabRole (arn:aws:iam::<conta>:role/LabRole)."
  }
}

variable "bucket_name" {
  description = "Nome do bucket S3 do pipeline. E global: inclua o identificador do grupo (ex.: mercadofacil-grupo-6325226)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Nome de bucket invalido: use 3-63 caracteres minusculos, numeros, ponto ou hifen."
  }
}

variable "project_name" {
  description = "Prefixo dos recursos Glue (job, crawler, database)."
  type        = string
  default     = "mercadofacil"
}

variable "glue_worker_type" {
  description = "Tipo de worker do Glue Job."
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Quantidade de workers do Glue Job (minimo 2). O dataset e pequeno: 2 basta."
  type        = number
  default     = 2
}
