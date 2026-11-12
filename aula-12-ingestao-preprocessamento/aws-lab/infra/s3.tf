# =============================================================================
# S3 Bucket e Uploads
# =============================================================================
# Nota: O Learner Lab bloqueia o recurso aws_s3_bucket devido a restrições
# de SCP (GetBucketObjectLockConfiguration). Usamos AWS CLI via local-exec.
# =============================================================================

# Criar bucket S3 via AWS CLI
resource "terraform_data" "s3_bucket" {
  input = {
    bucket_name = var.bucket_name
  }

  provisioner "local-exec" {
    command = "aws s3api create-bucket --bucket ${var.bucket_name} --region us-east-1"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "aws s3 rb s3://${self.input.bucket_name} --force"
  }
}

# Upload do CSV raw para S3
resource "terraform_data" "upload_raw_data" {
  depends_on = [terraform_data.s3_bucket]

  triggers_replace = {
    csv_hash = filemd5("${path.module}/../../data/pedidos_mercadofacil.csv")
  }

  provisioner "local-exec" {
    command = "aws s3 cp ${path.module}/../../data/pedidos_mercadofacil.csv s3://${var.bucket_name}/raw/pedidos_mercadofacil.csv"
  }
}

# Upload do script PySpark para S3
resource "terraform_data" "upload_glue_script" {
  depends_on = [terraform_data.s3_bucket]

  triggers_replace = {
    script_hash = filemd5("${path.module}/../job/etl_mercadofacil.py")
  }

  provisioner "local-exec" {
    command = "aws s3 cp ${path.module}/../job/etl_mercadofacil.py s3://${var.bucket_name}/scripts/etl_mercadofacil.py"
  }
}
