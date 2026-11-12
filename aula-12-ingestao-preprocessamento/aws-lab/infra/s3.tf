# Bucket S3 criado via AWS CLI (requisito do projeto)
resource "terraform_data" "s3_bucket" {
  # Criação do bucket via AWS CLI
  provisioner "local-exec" {
    command = "aws s3 mb s3://${var.bucket_name} --region us-east-1"
  }

  # Destruição: esvaziar e remover o bucket
  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket_name} --force"
  }

  input = {
    bucket_name = var.bucket_name
  }
}

# Upload do CSV raw para o S3
resource "terraform_data" "upload_raw_data" {
  depends_on = [terraform_data.s3_bucket]

  provisioner "local-exec" {
    command = "aws s3 cp ../../data/pedidos_mercadofacil.csv s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
  }

  triggers_replace = {
    bucket_name = var.bucket_name
    # Força recriação se o arquivo CSV mudar
    file_hash = filemd5("../../data/pedidos_mercadofacil.csv")
  }
}

# Upload do script PySpark para o S3
resource "terraform_data" "upload_glue_script" {
  depends_on = [terraform_data.s3_bucket]

  provisioner "local-exec" {
    command = "aws s3 cp ../job/etl_mercadofacil.py s3://${var.bucket_name}/scripts/etl_mercadofacil.py"
  }

  triggers_replace = {
    bucket_name = var.bucket_name
    # Força recriação se o script mudar
    file_hash = filemd5("../job/etl_mercadofacil.py")
  }
}
