variable "regiao" {
  type        = string
  default     = "us-east-1"
  description = "Regiao do Learner Lab. O lab so opera em us-east-1."
}

variable "identificador_grupo" {
  type        = string
  description = <<-TXT
    Identificador do grupo, usado no nome do bucket e dos recursos.
    Nome de bucket S3 e GLOBAL: sem isso, dois grupos colidem e o
    segundo apply falha com BucketAlreadyExists.
  TXT
}

variable "prefixo_bucket" {
  type        = string
  default     = "mercadofacil-lab"
  description = "Prefixo do bucket; o identificador do grupo e concatenado."
}

variable "arn_lab_role" {
  type        = string
  description = <<-TXT
    ARN da LabRole, que muda a cada conta do lab. Obtenha com:
    aws iam get-role --role-name LabRole --query Role.Arn --output text

    E variavel, e nao constante, porque o numero da conta faz parte do
    ARN e e diferente para cada aluno.
  TXT
}

variable "nome_database" {
  type        = string
  default     = "mercadofacil"
  description = "Nome do banco no Glue Data Catalog."
}
