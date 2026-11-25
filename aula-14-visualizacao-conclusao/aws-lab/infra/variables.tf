# variables.tf (aula-14) - PRONTO. Preencha os valores em terraform.tfvars.

variable "regiao" {
  description = "Regiao AWS obrigatoria do Learner Lab."
  type        = string
  default     = "us-east-1"
}

variable "bucket_nome" {
  description = "Nome GLOBALMENTE unico do bucket S3 (ex.: aula14-grupo3-rm12345)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,61}[a-z0-9]$", var.bucket_nome))
    error_message = "Use 3-63 caracteres: letras minusculas, numeros e hifen."
  }
}

variable "glue_database" {
  description = "Nome do banco no Glue Data Catalog (aparece no Athena)."
  type        = string
  default     = "mercadofacil_aula14"
}

variable "criar_superset" {
  description = "Se true, sobe uma EC2 com Apache Superset ja ligado ao Athena."
  type        = bool
  default     = true
}

variable "meu_ip_cidr" {
  description = "Seu IP publico em CIDR (ex.: 200.10.20.30/32). So ele acessa o Superset. Descubra com: curl -s https://checkip.amazonaws.com"
  type        = string
  default     = ""

  validation {
    condition     = var.meu_ip_cidr == "" || can(cidrhost(var.meu_ip_cidr, 0))
    error_message = "meu_ip_cidr deve ser um CIDR valido, ex.: 200.10.20.30/32."
  }
}

variable "superset_senha" {
  description = "Senha do usuario admin do Superset (8+ caracteres: letras, numeros e _ - . @ # % + =)."
  type        = string
  sensitive   = true
  default     = ""

  validation {
    condition     = var.superset_senha == "" || can(regex("^[A-Za-z0-9_@#%+=.-]{8,}$", var.superset_senha))
    error_message = "Senha invalida: use 8+ caracteres entre letras, numeros e _ - . @ # % + =."
  }
}

variable "instance_profile" {
  description = "Instance profile pre-criado do Learner Lab (nao crie IAM proprio)."
  type        = string
  default     = "LabInstanceProfile"
}

variable "instance_type" {
  description = "Tipo da EC2 do Superset (precisa de ~4 GB de RAM)."
  type        = string
  default     = "t3.medium"
}

variable "tags" {
  description = "Tags aplicadas aos recursos."
  type        = map(string)
  default = {
    Projeto    = "aula-14-visualizacao"
    Disciplina = "Big Data"
    Ambiente   = "LearnerLab"
  }
}
