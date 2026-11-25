# main.tf (aula-14) - PRONTO. Voce NAO precisa escrever Terraform hoje.
#
# O foco da aula e VISUALIZACAO. Esta stack entrega:
#   S3 (silver/pedidos/ com o CSV de 10 mil linhas + apoio/ com chuva e feriados)
#     -> Glue Data Catalog (tabelas pedidos, chuva_diaria, feriados)
#     -> Athena (workgroup proprio, resultados no mesmo bucket)
#     -> [opcional] EC2 com Apache Superset ja conectado ao Athena
#
# Regras do Learner Lab respeitadas:
#   - regiao us-east-1; nenhuma role/policy IAM criada (EC2 usa LabInstanceProfile)
#   - bucket criado via AWS CLI (terraform_data + local-exec), nao aws_s3_bucket,
#     porque a SCP do Learner Lab bloqueia a leitura de Object Lock que esse
#     recurso faz. Por isso o AWS CLI precisa estar instalado e autenticado.

provider "aws" {
  region = var.regiao
}

locals {
  csv_local = "${path.module}/../data/pedidos_mercadofacil_tratado.csv"
  csv_s3    = "s3://${var.bucket_nome}/silver/pedidos/"

  chuva_local    = "${path.module}/../data/chuva_diaria.csv"
  chuva_s3       = "s3://${var.bucket_nome}/apoio/chuva_diaria/"
  feriados_local = "${path.module}/../data/feriados.csv"
  feriados_s3    = "s3://${var.bucket_nome}/apoio/feriados/"
  superset       = var.criar_superset ? 1 : 0
}

# -----------------------------------------------------------------------------
# Bucket privado + upload do CSV
# -----------------------------------------------------------------------------
resource "terraform_data" "bucket" {
  input = {
    bucket = var.bucket_nome
    regiao = var.regiao
  }

  triggers_replace = [var.bucket_nome, var.regiao, filemd5(local.csv_local), filemd5(local.chuva_local), filemd5(local.feriados_local)]

  provisioner "local-exec" {
    command = <<-CMD
      set -e
      aws s3api create-bucket --bucket "${var.bucket_nome}" --region "${var.regiao}" >/dev/null 2>&1 || true
      aws s3api put-public-access-block --bucket "${var.bucket_nome}" \
        --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
      aws s3 cp "${local.csv_local}" "${local.csv_s3}pedidos_mercadofacil_tratado.csv"
      aws s3 cp "${local.chuva_local}" "${local.chuva_s3}chuva_diaria.csv"
      aws s3 cp "${local.feriados_local}" "${local.feriados_s3}feriados.csv"
    CMD
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket} --force || true"
  }
}

# -----------------------------------------------------------------------------
# Glue Data Catalog: banco + tabela externa sobre o CSV
# -----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "mercadofacil" {
  name        = var.glue_database
  description = "MercadoFacil - dados tratados para a Aula 14"
}

resource "aws_glue_catalog_table" "pedidos" {
  name          = "pedidos"
  database_name = aws_glue_catalog_database.mercadofacil.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                 = "TRUE"
    classification           = "csv"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = local.csv_s3
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters = {
        "field.delim"            = ","
        "serialization.format"   = ","
        "skip.header.line.count" = "1"
      }
    }

    dynamic "columns" {
      for_each = [
        ["pedido_id", "string"],
        ["item_id", "string"],
        ["data_pedido", "date"],
        ["cliente_id", "string"],
        ["cliente_segmento", "string"],
        ["estado", "string"],
        ["regiao", "string"],
        ["cidade", "string"],
        ["canal", "string"],
        ["categoria", "string"],
        ["sku", "string"],
        ["produto", "string"],
        ["marca", "string"],
        ["transportadora", "string"],
        ["centro_distribuicao", "string"],
        ["forma_pagamento", "string"],
        ["parcelas", "int"],
        ["quantidade", "int"],
        ["custo_unitario", "double"],
        ["preco_unitario", "double"],
        ["desconto_pct", "int"],
        ["valor_total", "double"],
        ["status_pedido", "string"],
        ["prazo_estimado_dias", "int"],
        ["prazo_real_dias", "int"],
        ["atraso_dias", "int"],
        ["data_entrega", "date"],
        ["nota_avaliacao", "int"],
      ]
      content {
        name = columns.value[0]
        type = columns.value[1]
      }
    }
  }

  depends_on = [terraform_data.bucket]
}

# Tabelas de apoio (APIs publicas): chuva diaria por cidade e feriados nacionais
resource "aws_glue_catalog_table" "chuva_diaria" {
  name          = "chuva_diaria"
  database_name = aws_glue_catalog_database.mercadofacil.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                 = "TRUE"
    classification           = "csv"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = local.chuva_s3
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters = {
        "field.delim"            = ","
        "serialization.format"   = ","
        "skip.header.line.count" = "1"
      }
    }

    columns {
      name = "cidade"
      type = "string"
    }
    columns {
      name = "dia"
      type = "date"
    }
    columns {
      name = "chuva_mm"
      type = "double"
    }
    columns {
      name = "chuva_3d_mm"
      type = "double"
    }
  }

  depends_on = [terraform_data.bucket]
}

resource "aws_glue_catalog_table" "feriados" {
  name          = "feriados"
  database_name = aws_glue_catalog_database.mercadofacil.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                 = "TRUE"
    classification           = "csv"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = local.feriados_s3
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters = {
        "field.delim"            = ","
        "serialization.format"   = ","
        "skip.header.line.count" = "1"
      }
    }

    columns {
      name = "dia"
      type = "date"
    }
    columns {
      name = "nome"
      type = "string"
    }
    columns {
      name = "tipo"
      type = "string"
    }
  }

  depends_on = [terraform_data.bucket]
}

# -----------------------------------------------------------------------------
# Athena: workgroup com resultados no bucket do grupo
# -----------------------------------------------------------------------------
resource "aws_athena_workgroup" "aula14" {
  name          = "wg-${var.bucket_nome}"
  force_destroy = true
  tags          = var.tags

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${var.bucket_nome}/athena-results/"
    }
  }

  depends_on = [terraform_data.bucket]
}

# -----------------------------------------------------------------------------
# Superset (opcional): EC2 + Security Group restrito ao seu IP
# -----------------------------------------------------------------------------
data "aws_vpc" "default" {
  default = true
}

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_security_group" "superset" {
  count       = local.superset
  name_prefix = "aula14-superset-"
  description = "Superset (8088) liberado so para o IP do aluno"
  vpc_id      = data.aws_vpc.default.id
  tags        = var.tags

  ingress {
    description = "Superset UI"
    from_port   = 8088
    to_port     = 8088
    protocol    = "tcp"
    cidr_blocks = [var.meu_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    precondition {
      condition     = var.meu_ip_cidr != "" && var.superset_senha != ""
      error_message = "Com criar_superset = true, preencha meu_ip_cidr e superset_senha no terraform.tfvars."
    }
  }
}

resource "aws_instance" "superset" {
  count                       = local.superset
  ami                         = data.aws_ssm_parameter.al2023.value
  instance_type               = var.instance_type
  iam_instance_profile        = var.instance_profile
  vpc_security_group_ids      = [aws_security_group.superset[0].id]
  associate_public_ip_address = true
  user_data_replace_on_change = true
  tags                        = merge(var.tags, { Name = "aula14-superset" })

  # Hop limit 2: o container Docker precisa alcancar o servico de metadados
  # para obter as credenciais da LabRole (usadas pelo Athena).
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/superset_user_data.sh.tftpl", {
    regiao       = var.regiao
    bucket       = var.bucket_nome
    workgroup    = aws_athena_workgroup.aula14.name
    database     = aws_glue_catalog_database.mercadofacil.name
    senha        = var.superset_senha
    secret_key   = sha256("${var.bucket_nome}-${var.superset_senha}")
    result_s3url = urlencode("s3://${var.bucket_nome}/athena-results/")
  })

  depends_on = [aws_athena_workgroup.aula14, aws_glue_catalog_table.pedidos, aws_glue_catalog_table.chuva_diaria, aws_glue_catalog_table.feriados]
}
