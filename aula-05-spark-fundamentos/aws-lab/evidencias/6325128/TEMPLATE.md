# Evidências — Lab Aula 05 (Spark RDDs na AWS)

> Copie este arquivo para `evidencias/<SEU_RA>/EVIDENCIAS.md` e preencha.
> Salve os prints na mesma pasta e referencie-os no texto.

## Identificação

- **Nome:** Felipe Damasceno
- **RA:** 6325128
- **Branch:** main
- **Data:** 16/09/2026

---

## 1. Identidade AWS ativa

Saída de `aws sts get-caller-identity` (confirma que as credenciais do Learner
Lab estão ativas). Cole a saída no bloco de código abaixo (pode mascarar o
`Account`/`UserId`).

**Comando:**
```bash
aws sts get-caller-identity
```

Cole aqui a saída:
```text
 aws sts get-caller-identity
{
    "UserId": "AROA3UCY7UQHY7AARRFZU:user5369375=Felipe_Damasceno",
    "Account": "799050540047",
    "Arn": "arn:aws:sts::799050540047:assumed-role/voclabs/user5369375=Felipe_Damasceno"
}
```

Print (opcional):
```
![identidade AWS](01-identity.png)
```

---

## 2. `terraform apply` concluído

Print ou trecho final do `terraform apply` mostrando **"Apply complete!"** e os
outputs (`bucket_nome`, `glue_job_nome`, `labrole_arn`). **NÃO** mostre credenciais.

**Onde:** `cd aws-lab/infra && terraform apply`

Cole aqui a saída:
```text
terraform apply

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_glue_job.wordcount will be created
  + resource "aws_glue_job" "wordcount" {
      + arn               = (known after apply)
      + default_arguments = {
          + "--INPUT"                            = "s3://lab-aula05-glue-6325128/input/sample_lines.txt"
          + "--OUTPUT"                           = "s3://lab-aula05-glue-6325128/output/wordcount"
          + "--TempDir"                          = "s3://lab-aula05-glue-6325128/tmp/"
          + "--enable-continuous-cloudwatch-log" = "true"
        }
      + glue_version      = "4.0"
      + id                = (known after apply)
      + job_mode          = (known after apply)
      + max_capacity      = (known after apply)
      + name              = "job-aula05-wordcount"
      + number_of_workers = 2
      + region            = "us-east-1"
      + role_arn          = "arn:aws:iam::799050540047:role/LabRole"
      + tags_all          = {
          + "Ambiente"   = "LearnerLab"
          + "Disciplina" = "Big Data"
          + "Projeto"    = "lab-aula-05-spark"
        }
      + timeout           = (known after apply)
      + worker_type       = "G.1X"

      + command {
          + name            = "glueetl"
          + python_version  = "3"
          + runtime         = (known after apply)
          + script_location = "s3://lab-aula05-glue-6325128/scripts/rdd_job.py"
        }

      + execution_property (known after apply)

      + notification_property (known after apply)
    }

  # aws_s3_bucket_public_access_block.lab will be created
  + resource "aws_s3_bucket_public_access_block" "lab" {
      + block_public_acls       = true
      + block_public_policy     = true
      + bucket                  = "lab-aula05-glue-6325128"
      + id                      = (known after apply)
      + ignore_public_acls      = true
      + region                  = "us-east-1"
      + restrict_public_buckets = true
    }

  # aws_s3_object.input will be created
  + resource "aws_s3_object" "input" {
      + acl                    = (known after apply)
      + arn                    = (known after apply)
      + bucket                 = "lab-aula05-glue-6325128"
      + bucket_key_enabled     = (known after apply)
      + checksum_crc32         = (known after apply)
      + checksum_crc32c        = (known after apply)
      + checksum_crc64nvme     = (known after apply)
      + checksum_sha1          = (known after apply)
      + checksum_sha256        = (known after apply)
      + content_type           = (known after apply)
      + etag                   = "28b73acfb27d9a9c54b5ddfd58e33181"
      + force_destroy          = false
      + id                     = (known after apply)
      + key                    = "input/sample_lines.txt"
      + kms_key_id             = (known after apply)
      + region                 = "us-east-1"
      + server_side_encryption = (known after apply)
      + source                 = "./../data/sample_lines.txt"
      + storage_class          = (known after apply)
      + tags_all               = {
          + "Ambiente"   = "LearnerLab"
          + "Disciplina" = "Big Data"
          + "Projeto"    = "lab-aula-05-spark"
        }
      + version_id             = (known after apply)
    }

  # aws_s3_object.script will be created
  + resource "aws_s3_object" "script" {
      + acl                    = (known after apply)
      + arn                    = (known after apply)
      + bucket                 = "lab-aula05-glue-6325128"
      + bucket_key_enabled     = (known after apply)
      + checksum_crc32         = (known after apply)
      + checksum_crc32c        = (known after apply)
      + checksum_crc64nvme     = (known after apply)
      + checksum_sha1          = (known after apply)
      + checksum_sha256        = (known after apply)
      + content_type           = (known after apply)
      + etag                   = "d931e7cc370ae56b78256fdf93a98221"
      + force_destroy          = false
      + id                     = (known after apply)
      + key                    = "scripts/rdd_job.py"
      + kms_key_id             = (known after apply)
      + region                 = "us-east-1"
      + server_side_encryption = (known after apply)
      + source                 = "./../job/rdd_job.py"
      + storage_class          = (known after apply)
      + tags_all               = {
          + "Ambiente"   = "LearnerLab"
          + "Disciplina" = "Big Data"
          + "Projeto"    = "lab-aula-05-spark"
        }
      + version_id             = (known after apply)
    }

  # terraform_data.lab_bucket will be created
  + resource "terraform_data" "lab_bucket" {
      + id     = (known after apply)
      + input  = "lab-aula05-glue-6325128"
      + output = (known after apply)
    }

Plan: 5 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

terraform_data.lab_bucket: Creating...
terraform_data.lab_bucket: Provisioning with 'local-exec'...
terraform_data.lab_bucket (local-exec): Executing: ["/bin/sh" "-c" "set -eu\nif ! aws s3api head-bucket --bucket \"$BUCKET\" >/dev/null 2>&1; then\n  if [ \"$REGION\" = \"us-east-1\" ]; then\n    aws s3api create-bucket --bucket \"$BUCKET\" --region \"$REGION\"\n  else\n    aws s3api create-bucket --bucket \"$BUCKET\" --region \"$REGION\" \\\n      --create-bucket-configuration LocationConstraint=\"$REGION\"\n  fi\nfi\n"]
terraform_data.lab_bucket: Creation complete after 1s [id=e25b6240-67cc-502d-6884-c5c764307a4d]
aws_s3_bucket_public_access_block.lab: Creating...
aws_s3_object.script: Creating...
aws_s3_object.input: Creating...
aws_s3_object.input: Creation complete after 1s [id=lab-aula05-glue-6325128/input/sample_lines.txt]
aws_s3_object.script: Creation complete after 1s [id=lab-aula05-glue-6325128/scripts/rdd_job.py]
aws_s3_bucket_public_access_block.lab: Creation complete after 1s [id=lab-aula05-glue-6325128]
aws_glue_job.wordcount: Creating...
aws_glue_job.wordcount: Creation complete after 1s [id=job-aula05-wordcount]

Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:

bucket_nome = "lab-aula05-glue-6325128"
glue_job_nome = "job-aula05-wordcount"
labrole_arn = "arn:aws:iam::799050540047:role/LabRole"
```

Print:
```
01-apply.png
```

---

## 3. Job com estado SUCCEEDED (Glue)

Print/saída final do `./run_job.sh` mostrando `estado: SUCCEEDED` e o `RUN_ID`.
(Alternativa: print do console **AWS Glue → Jobs → seu job → aba Runs** com status
**Succeeded**.)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

Cole aqui a saída:
```text
felip@SHASHUMGA:~/ADS/BigData/aula_bigdata_2026/aula-05-spark-fundamentos/aws-lab/scripts$ ./run_job.sh
BUCKET   = lab-aula05-glue-6325128
GLUE_JOB = job-aula05-wordcount
ROLE_ARN = arn:aws:iam::799050540047:role/LabRole
$ aws s3 cp /home/felip/ADS/BigData/aula_bigdata_2026/aula-05-spark-fundamentos/aws-lab/scripts/../job/rdd_job.py s3://lab-aula05-glue-6325128/scripts/rdd_job.py
upload: ../job/rdd_job.py to s3://lab-aula05-glue-6325128/scripts/rdd_job.py
$ aws s3 cp /home/felip/ADS/BigData/aula_bigdata_2026/aula-05-spark-fundamentos/aws-lab/scripts/../data/sample_lines.txt s3://lab-aula05-glue-6325128/input/sample_lines.txt
upload: ../data/sample_lines.txt to s3://lab-aula05-glue-6325128/input/sample_lines.txt
$ aws s3 rm s3://lab-aula05-glue-6325128/output/wordcount --recursive
$ aws glue start-job-run --job-name job-aula05-wordcount ...
RUN_ID = jr_320dc057ae7d9d6709317302ce5d8cc80852bf5117e501682ad0a01114c1e426
Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)...
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: SUCCEEDED
Job concluido com SUCESSO.
Veja o resultado com: ./ver_resultado.sh
```

Print:
```
02-job-success.png
```

---

## 4. Resultado do word count

Saída do `./ver_resultado.sh` (lista do output + conteúdo `palavra,contagem`).
Cole no bloco de código abaixo.

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

Cole aqui a saída:
```text
felip@SHASHUMGA:~/ADS/BigData/aula_bigdata_2026/aula-05-spark-fundamentos/aws-lab/scripts$ ./ver_resultado.sh
BUCKET = lab-aula05-glue-6325128
$ aws s3 ls s3://lab-aula05-glue-6325128/output/wordcount/
2026-09-17 00:42:37        311 part-00000
2026-09-17 00:42:37        377 part-00001
2026-09-17 00:42:37        377 part-00002
2026-09-17 00:42:37        394 part-00003
=== Conteudo do word count (palavra,contagem) ===
$ aws s3 cp --recursive s3://lab-aula05-glue-6325128/output/wordcount/ /tmp/tmp.QF90hpqNMr
download: s3://lab-aula05-glue-6325128/output/wordcount/part-00003 to ../../../../../../../../tmp/tmp.QF90hpqNMr/part-00003
download: s3://lab-aula05-glue-6325128/output/wordcount/part-00002 to ../../../../../../../../tmp/tmp.QF90hpqNMr/part-00002
download: s3://lab-aula05-glue-6325128/output/wordcount/part-00000 to ../../../../../../../../tmp/tmp.QF90hpqNMr/part-00000
download: s3://lab-aula05-glue-6325128/output/wordcount/part-00001 to ../../../../../../../../tmp/tmp.QF90hpqNMr/part-00001
o,60
a,22
e,19
pedido,19
cliente,18
entrega,17
do,16
produto,16
estoque,14
pagamento,11
com,9
de,8
um,7
para,6
cada,5
dia,5
mais,5
que,5
ao,4
foi,4
grande,4
novo,4
pediu,4
da,3
muitos,3
na,3
pedidos,3
pelo,3
voltou,3
antes,2
apos,2
cartao,2
chegou,2
em,2
expressa,2
fez,2
ficou,2
fila,2
fim,2
interior,2
loja,2
no,2
pix,2
prazo,2
reembolso,2
saiu,2
abastece,1
abriu,1
aceitou,1
acompanhou,1
agiliza,1
agrada,1
analise,1
antigo,1
aplicativo,1
aprova,1
aprovou,1
area,1
as,1
assim,1
atencao,1
avaliou,1
aviso,1
avisou,1
buscou,1
caiu,1
caminho,1
central,1
cidade,1
codigo,1
combinado,1
comeca,1
compra,1
conferir,1
confirma,1
confirmou,1
contou,1
cuidado,1
custa,1
datas,1
dentro,1
dessa,1
devolvido,1
diferentes,1
dividida,1
dois,1
duas,1
durante,1
elogiou,1
embalado,1
emitida,1
entende,1
entra,1
entregador,1
entregues,1
equipe,1
escolheu,1
esta,1
estava,1
exigente,1
exigiu,1
favorito,1
fechou,1
feito,1
feliz,1
fiscal,1
gestor,1
hora,1
leva,1
liberou,1
liga,1
limite,1
lojas,1
maior,1
manha,1
mas,1
mostrou,1
nota,1
online,1
outro,1
pagou,1
parado,1
parcelado,1
partes,1
pela,1
por,1
poucas,1
prepara,1
produtos,1
quando,1
quase,1
rapida,1
rapido,1
rastreio,1
recebe,1
receber,1
recusado,1
reduziu,1
relatorio,1
repos,1
reposicao,1
reserva,1
retornou,1
revisou,1
rota,1
sai,1
satisfeito,1
segue,1
separa,1
separacao,1
sistema,1
sucesso,1
tarde,1
tem,1
tempo,1
tentou,1
teve,1
time,1
troca,1
unidades,1
usaram,1
vai,1
varias,1
vendido,1
vez,1
vezes,1
via,1
```

Print (opcional):
```
03-resultado.png
```

---

## 5. Top palavras / interpretação

Cole o **TOP 5** do word count e escreva **2–3 frases** interpretando o resultado
(ex.: por que "pedido/cliente/entrega" dominam, o que isso diz sobre o texto de
e-commerce). Relacione com os conceitos de **RDD / driver / executors** da aula.

Top 5:
```text
o,60
a,22
e,19
pedido,19
cliente,18
```

Interpretação:

> Isso indica que o texto descreve principalmente ações e entidades relacionadas ao processo de compra, enquanto o driver coordena as transformações dos RDDs e os executors distribuem a contagem e a gravação dos resultados no S3.

---

## 6. Logs do driver (opcional / bônus)

Print dos logs do **driver** no **CloudWatch** (grupo `/aws-glue/jobs/output`)
mostrando o `print(...)` do `rdd_job.py`.

**Onde:** AWS Glue → Jobs → seu job → aba **Runs** → selecione o run → **Output logs**
(abre o CloudWatch no grupo `/aws-glue/jobs/output`).

Print:
```
![logs do driver](05-driver-log.png)
```

---

## 7. Limpeza (`terraform destroy`)

Print/trecho do `terraform destroy` com **"Destroy complete!"** confirmando que os
recursos foram removidos (guardrail de custo).

**Onde:** `cd aws-lab/infra && terraform destroy`

Cole aqui a saída:
```text
felip@SHASHUMGA:~/ADS/BigData/aula_bigdata_2026/aula-05-spark-fundamentos/aws-lab/infra$ terraform destroy
terraform_data.lab_bucket: Refreshing state... [id=e25b6240-67cc-502d-6884-c5c764307a4d]
aws_s3_bucket_public_access_block.lab: Refreshing state... [id=lab-aula05-glue-6325128]
aws_s3_object.script: Refreshing state... [id=lab-aula05-glue-6325128/scripts/rdd_job.py]
aws_s3_object.input: Refreshing state... [id=lab-aula05-glue-6325128/input/sample_lines.txt]
aws_glue_job.wordcount: Refreshing state... [id=job-aula05-wordcount]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_glue_job.wordcount will be destroyed
  - resource "aws_glue_job" "wordcount" {
      - arn                       = "arn:aws:glue:us-east-1:799050540047:job/job-aula05-wordcount" -> null
      - connections               = [] -> null
      - default_arguments         = {
          - "--INPUT"                            = "s3://lab-aula05-glue-6325128/input/sample_lines.txt"
          - "--OUTPUT"                           = "s3://lab-aula05-glue-6325128/output/wordcount"
          - "--TempDir"                          = "s3://lab-aula05-glue-6325128/tmp/"
          - "--enable-continuous-cloudwatch-log" = "true"
        } -> null
      - glue_version              = "4.0" -> null
      - id                        = "job-aula05-wordcount" -> null
      - job_mode                  = "SCRIPT" -> null
      - job_run_queuing_enabled   = false -> null
      - max_capacity              = 2 -> null
      - max_retries               = 0 -> null
      - name                      = "job-aula05-wordcount" -> null
      - non_overridable_arguments = {} -> null
      - number_of_workers         = 2 -> null
      - region                    = "us-east-1" -> null
      - role_arn                  = "arn:aws:iam::799050540047:role/LabRole" -> null
      - tags                      = {} -> null
      - tags_all                  = {
          - "Ambiente"   = "LearnerLab"
          - "Disciplina" = "Big Data"
          - "Projeto"    = "lab-aula-05-spark"
        } -> null
      - timeout                   = 2880 -> null
      - worker_type               = "G.1X" -> null
        # (4 unchanged attributes hidden)

      - command {
          - name            = "glueetl" -> null
          - python_version  = "3" -> null
          - script_location = "s3://lab-aula05-glue-6325128/scripts/rdd_job.py" -> null
            # (1 unchanged attribute hidden)
        }

      - execution_property {
          - max_concurrent_runs = 1 -> null
        }
    }

  # aws_s3_bucket_public_access_block.lab will be destroyed
  - resource "aws_s3_bucket_public_access_block" "lab" {
      - block_public_acls       = true -> null
      - block_public_policy     = true -> null
      - bucket                  = "lab-aula05-glue-6325128" -> null
      - id                      = "lab-aula05-glue-6325128" -> null
      - ignore_public_acls      = true -> null
      - region                  = "us-east-1" -> null
      - restrict_public_buckets = true -> null
    }

  # aws_s3_object.input will be destroyed
  - resource "aws_s3_object" "input" {
      - arn                           = "arn:aws:s3:::lab-aula05-glue-6325128/input/sample_lines.txt" -> null
      - bucket                        = "lab-aula05-glue-6325128" -> null
      - bucket_key_enabled            = false -> null
      - content_type                  = "text/plain" -> null
      - etag                          = "28b73acfb27d9a9c54b5ddfd58e33181" -> null
      - force_destroy                 = false -> null
      - id                            = "lab-aula05-glue-6325128/input/sample_lines.txt" -> null
      - key                           = "input/sample_lines.txt" -> null
      - metadata                      = {} -> null
      - region                        = "us-east-1" -> null
      - server_side_encryption        = "AES256" -> null
      - source                        = "./../data/sample_lines.txt" -> null
      - storage_class                 = "STANDARD" -> null
      - tags                          = {} -> null
      - tags_all                      = {} -> null
        # (14 unchanged attributes hidden)
    }

  # aws_s3_object.script will be destroyed
  - resource "aws_s3_object" "script" {
      - arn                           = "arn:aws:s3:::lab-aula05-glue-6325128/scripts/rdd_job.py" -> null
      - bucket                        = "lab-aula05-glue-6325128" -> null
      - bucket_key_enabled            = false -> null
      - content_type                  = "text/x-python" -> null
      - etag                          = "80d05f34c40df230fc81db9caccded66" -> null
      - force_destroy                 = false -> null
      - id                            = "lab-aula05-glue-6325128/scripts/rdd_job.py" -> null
      - key                           = "scripts/rdd_job.py" -> null
      - metadata                      = {} -> null
      - region                        = "us-east-1" -> null
      - server_side_encryption        = "AES256" -> null
      - source                        = "./../job/rdd_job.py" -> null
      - storage_class                 = "STANDARD" -> null
      - tags                          = {} -> null
      - tags_all                      = {} -> null
        # (14 unchanged attributes hidden)
    }

  # terraform_data.lab_bucket will be destroyed
  - resource "terraform_data" "lab_bucket" {
      - id     = "e25b6240-67cc-502d-6884-c5c764307a4d" -> null
      - input  = "lab-aula05-glue-6325128" -> null
      - output = "lab-aula05-glue-6325128" -> null
    }

Plan: 0 to add, 0 to change, 5 to destroy.

Changes to Outputs:
  - bucket_nome   = "lab-aula05-glue-6325128" -> null
  - glue_job_nome = "job-aula05-wordcount" -> null
  - labrole_arn   = "arn:aws:iam::799050540047:role/LabRole" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

aws_s3_bucket_public_access_block.lab: Destroying... [id=lab-aula05-glue-6325128]
aws_glue_job.wordcount: Destroying... [id=job-aula05-wordcount]
aws_glue_job.wordcount: Destruction complete after 1s
aws_s3_object.input: Destroying... [id=lab-aula05-glue-6325128/input/sample_lines.txt]
aws_s3_object.script: Destroying... [id=lab-aula05-glue-6325128/scripts/rdd_job.py]
aws_s3_bucket_public_access_block.lab: Destruction complete after 1s
aws_s3_object.input: Destruction complete after 0s
aws_s3_object.script: Destruction complete after 0s
terraform_data.lab_bucket: Destroying... [id=e25b6240-67cc-502d-6884-c5c764307a4d]
terraform_data.lab_bucket: Provisioning with 'local-exec'...
terraform_data.lab_bucket (local-exec): Executing: ["/bin/sh" "-c" "set -eu\naws s3 rm \"s3://$BUCKET\" --recursive\naws s3api delete-bucket --bucket \"$BUCKET\"\n"]
terraform_data.lab_bucket (local-exec): delete: s3://lab-aula05-glue-6325128/output/wordcount/part-00003
terraform_data.lab_bucket (local-exec): delete: s3://lab-aula05-glue-6325128/output/wordcount/part-00000
terraform_data.lab_bucket (local-exec): delete: s3://lab-aula05-glue-6325128/output/wordcount/part-00002
terraform_data.lab_bucket (local-exec): delete: s3://lab-aula05-glue-6325128/output/wordcount/part-00001
terraform_data.lab_bucket: Destruction complete after 4s

Destroy complete! Resources: 5 destroyed.
```

Print:
```
04-destroy.png
```

---

## Checklist de conferência

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (Glue) (+ `RUN_ID`)
- [x] 4. Resultado do word count (`./ver_resultado.sh`)
- [x] 5. Top palavras + interpretação (2–3 frases)
- [ ] 6. Logs do driver (opcional / bônus)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")
