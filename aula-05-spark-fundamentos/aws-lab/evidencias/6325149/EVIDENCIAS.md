# Evidências — Lab Aula 05 (Spark RDDs na AWS)

## Identificação

- **Nome:** Gabriel Reis Cunha
- **RA:** 6325149
- **Branch:** aula-05-6325149
- **Data:** 2026-09-16

---

## 1. Identidade AWS ativa

**Comando:**
```bash
aws sts get-caller-identity
```

Saída:
```text
{
    "UserId": "AROAV74TBXJLSVU7TDHCA:user5367756=Gabriel_Reis_Cunha",
    "Account": "412088384087",
    "Arn": "arn:aws:sts::412088384087:assumed-role/voclabs/user5367756=Gabriel_Reis_Cunha"
}
```

Confirmado: não é usuário root, é a role padrão do AWS Academy Learner Lab
(`assumed-role/voclabs/...`).

---

## 2. `terraform apply` concluído

**Onde:** `cd aws-lab/infra && terraform apply`

> Observação técnica: a primeira chamada de `apply` cria o bucket S3 com sucesso,
> mas o Terraform reporta erro ao *ler de volta* a configuração de object-lock do
> bucket recém-criado — uma SCP desta conta do Learner Lab nega
> `s3:GetBucketObjectLockConfiguration` (não afeta a criação em si). Resolvido com
> `terraform untaint aws_s3_bucket.lab` e reaplicando o restante com
> `-refresh=false` (evita a mesma leitura bloqueada).

Saída final (segunda chamada, recursos restantes):
```text
aws_s3_bucket_public_access_block.lab: Creating...
aws_s3_object.script: Creating...
aws_s3_object.input: Creating...
aws_glue_job.wordcount: Creating...
aws_s3_object.script: Creation complete after 2s [id=scripts/rdd_job.py]
aws_s3_object.input: Creation complete after 2s [id=input/sample_lines.txt]
aws_s3_bucket_public_access_block.lab: Creation complete after 2s [id=lab-aula05-glue-6325149]
aws_glue_job.wordcount: Creation complete after 2s [id=job-aula05-wordcount]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

bucket_nome = "lab-aula05-glue-6325149"
glue_job_nome = "job-aula05-wordcount"
labrole_arn = "arn:aws:iam::412088384087:role/LabRole"
```

`terraform state list` confirmou os 5 recursos ativos: `aws_glue_job.wordcount`,
`aws_s3_bucket.lab`, `aws_s3_bucket_public_access_block.lab`,
`aws_s3_object.input`, `aws_s3_object.script`.

---

## 3. Job com estado SUCCEEDED (Glue)

> Observação técnica: a primeira execução (`./run_job.sh`) terminou em `FAILED`
> com `ClassNotFoundException: Class org.apache.hadoop.mapred.DirectOutputCommitter
> not found` no `saveAsTextFile` — o runtime do Glue 4.0 configura por padrão um
> output committer que não existe nas libs Hadoop empacotadas com o Glue. Corrigido
> em `job/rdd_job.py` forçando o committer padrão do Hadoop antes de gravar:
> ```python
> sc._jsc.hadoopConfiguration().set(
>     "mapred.output.committer.class",
>     "org.apache.hadoop.mapred.FileOutputCommitter",
> )
> ```
> Depois da correção, o job rodou com sucesso (ver saída abaixo).

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

Saída (execução com sucesso):
```text
BUCKET   = lab-aula05-glue-6325149
GLUE_JOB = job-aula05-wordcount
ROLE_ARN = arn:aws:iam::412088384087:role/LabRole
$ aws glue start-job-run --job-name job-aula05-wordcount ...
RUN_ID = jr_21ac6912c30351130083e663ae7f003aea9c9cd27af0b82302ea1962245d45ca
Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)...
estado: RUNNING
(...)
estado: SUCCEEDED
Job concluido com SUCESSO.
```

---

## 4. Resultado do word count

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

```text
BUCKET = lab-aula05-glue-6325149
$ aws s3 ls s3://lab-aula05-glue-6325149/output/wordcount/
2026-09-16 22:12:32        311 part-00000
2026-09-16 22:12:32        377 part-00001
2026-09-16 22:12:32        377 part-00002
2026-09-16 22:12:32        394 part-00003
=== Conteudo do word count (palavra,contagem) ===
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
...
(175 linhas no total — bate exatamente com a validação local em PySpark)
```

---

## 5. Top palavras / interpretação

Top 5:
```text
o,60
a,22
e,19
pedido,19
cliente,18
```

Interpretação:

> O texto é uma narrativa de e-commerce (fluxo de pedido → pagamento → estoque →
> entrega), então é esperado que artigos/conjunções ("o", "a", "e") dominem por
> frequência gramatical. Entre as palavras de conteúdo, "pedido" e "cliente"
> lideram, refletindo que o relato gira em torno do ciclo de vida do pedido do
> cliente. Isso é coerente com o **driver** coordenando a leitura de todas as
> linhas do S3 (`spark.read.text(args["INPUT"])`) e os **executors** processando
> as partições dos RDDs em paralelo via `flatMap`/`map`/`reduceByKey` — a mesma
> API vista na aula, agora rodando de verdade num Glue Job gerenciado pela AWS.

---

## 6. Logs do driver

**Onde:** CloudWatch, grupo `/aws-glue/jobs/output`, stream
`jr_21ac6912c30351130083e663ae7f003aea9c9cd27af0b82302ea1962245d45ca`
(`aws logs get-log-events --log-group-name /aws-glue/jobs/output --log-stream-name <RUN_ID>`).

```text
=== Word count (palavra,contagem) ===
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
...
```

Confirma que o `print(...)` do driver (`rdd_job.py`) aparece no log do Glue,
igual à saída de `ver_resultado.sh`.

---

## 7. Limpeza (`terraform destroy`) — CONCLUÍDA

**Onde:** `cd aws-lab/infra && terraform destroy -refresh=false -auto-approve`

> Usei `-refresh=false` pelo mesmo motivo da seção 2 (a SCP bloqueia a leitura de
> object-lock do bucket, o que travaria o destroy). O bucket também foi esvaziado
> manualmente antes (`aws s3 rm --recursive`), pois `force_destroy = false`.

```text
aws_s3_object.input: Destroying... [id=input/sample_lines.txt]
aws_s3_bucket_public_access_block.lab: Destroying... [id=lab-aula05-glue-6325149]
aws_glue_job.wordcount: Destroying... [id=job-aula05-wordcount]
aws_s3_object.script: Destroying... [id=scripts/rdd_job.py]
aws_s3_object.input: Destruction complete after 4s
aws_s3_object.script: Destruction complete after 5s
aws_glue_job.wordcount: Destruction complete after 5s
aws_s3_bucket_public_access_block.lab: Destruction complete after 5s
aws_s3_bucket.lab: Destroying... [id=lab-aula05-glue-6325149]
aws_s3_bucket.lab: Destruction complete after 1s

Destroy complete! Resources: 5 destroyed.
```

Confirmação adicional (recursos realmente não existem mais):
```text
$ aws s3api head-bucket --bucket lab-aula05-glue-6325149
An error occurred (404) when calling the HeadBucket operation: Not Found

$ aws glue get-job --job-name job-aula05-wordcount
An error occurred (EntityNotFoundException) when calling the GetJob operation: Job not found.
```

`terraform state list` retornou vazio — nenhum recurso rastreado, nenhum residual
na conta.

---

## Checklist de conferência

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (Glue) (+ `RUN_ID`)
- [x] 4. Resultado do word count (`./ver_resultado.sh`)
- [x] 5. Top palavras + interpretação
- [x] 6. Logs do driver (bônus)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!" + confirmação 404/EntityNotFoundException)

## Notas adicionais sobre esta entrega

Dois bugs de ambiente encontrados e corrigidos ao longo do processo (detalhes nas
seções 2 e 3 acima), nenhum relacionado à lógica de RDD implementada:

1. Leitura de object-lock do S3 bloqueada por SCP da conta (contornado com
   `untaint` + `-refresh=false`, não afeta o resultado final).
2. `DirectOutputCommitter` ausente no runtime do Glue 4.0 (corrigido forçando
   `FileOutputCommitter` no `main()` de `job/rdd_job.py`, antes do
   `saveAsTextFile`).
