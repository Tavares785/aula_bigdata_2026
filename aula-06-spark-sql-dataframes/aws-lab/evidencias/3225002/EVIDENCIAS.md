# Evidências — Lab Aula 06 (Spark SQL / DataFrames na AWS)

> Copie este arquivo para `evidencias/<SEU_RA>/EVIDENCIAS.md` e preencha.
> Salve os prints na mesma pasta e referencie-os no texto.

## Identificação

- **Nome:** José Henrique Teixeira Luiz
- **RA:** 3225002
- **Branch:** `aula-06-aws-3225002`
- **Data:** 22/10/2026

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
```json
{
    "UserId": "AROA4T4UPYVEA5VPVPD5L:user5367843=Jos___Henrique_Teixeira_Luiz",
    "Account": "<CONTA>",
    "Arn": "arn:aws:sts::<CONTA>:assumed-role/voclabs/user5367843=Jos___Henrique_Teixeira_Luiz"
}
```

> `Account`/`UserId` mascarados conforme o aviso de segurança desta página.

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
terraform_data.bucket (local-exec): upload: ../job/dataframe_job.py to s3://lab-aula06-glue-3225002/scripts/dataframe_job.py
terraform_data.bucket (local-exec): upload: ../data/pedidos.csv  to s3://lab-aula06-glue-3225002/input/pedidos.csv
terraform_data.bucket (local-exec): upload: ../data/clientes.csv to s3://lab-aula06-glue-3225002/input/clientes.csv
terraform_data.bucket: Creation complete after 5s
aws_glue_job.spark_sql: Creating...
aws_glue_job.spark_sql: Creation complete after 1s [id=job-aula06-topn-clientes]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

bucket_nome   = "lab-aula06-glue-3225002"
glue_job_nome = "job-aula06-topn-clientes"
labrole_arn   = "arn:aws:iam::<CONTA>:role/LabRole"
```

> ⚠️ **A infra desta pasta foi escrita por mim.** O repositório publicou
> `infra/` contendo apenas o `terraform.tfvars.example`; faltavam `main.tf`,
> `variables.tf`, `versions.tf` e `outputs.tf`. Escrevi os quatro espelhando a
> aula-07, adaptados aos dois CSVs de entrada e aos argumentos que o
> `dataframe_job.py` lê. Detalhes no cabeçalho do `main.tf`.

Print:
```
![terraform apply](02-apply.png)
```

---

## 3. Job com estado SUCCEEDED (Glue)

Print/saída final do `./run_job.sh` mostrando `estado: SUCCEEDED` e o `RUN_ID`
(`JobRunId`). (Alternativa: print do console **AWS Glue → Jobs → seu job → aba
Runs** com status **Succeeded**.)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

Cole aqui a saída:
```text
BUCKET   = lab-aula06-glue-3225002
GLUE_JOB = job-aula06-topn-clientes
$ aws glue start-job-run --job-name job-aula06-topn-clientes ...
RUN_ID = jr_99fbef8b5acb82f465b8d8edf61fb8d787c149c5793ca89ad35f456a52f4554a
Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)...
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: SUCCEEDED
Job concluido com SUCESSO.
```

Print:
```
![job success](03-job-success.png)
```

---

## 4. Resultado do TOP-N de clientes

Saída do `./ver_resultado.sh` (lista do output + conteúdo
`customer_id,customer_name,total_spend`). Cole no bloco de código abaixo.

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

Cole aqui a saída:
```text
$ aws s3 ls s3://lab-aula06-glue-3225002/output/top_clientes/
2026-10-22 09:13:22        189 part-00000-13644ced-800f-478a-93fc-5a1dbd3ba38e-c000.csv

customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

Print (opcional):
```
![resultado top-n](04-resultado.png)
```

---

## 5. Interpretação do TOP-N

Cole o **TOP-N** de clientes por gasto e escreva **2–3 frases** interpretando o
resultado. Relacione com os conceitos de **join**, **groupBy + agregação** e
**DataFrames**, e com o papel de **driver / executors** no Spark gerenciado.

Top-N:
```text
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

Interpretação:

> O ranking é bastante concentrado: Isabela Nunes (R$ 12.928,10) e Diego
> Ferreira (R$ 9.862,40) sozinhos respondem por mais gasto que os outros três
> somados, e a distância entre o 2º e o 3º colocado é de quase três vezes —
> sinal de uma cauda longa típica de base de clientes, em que poucos compradores
> concentram a maior parte da receita. O resultado vem do `join` entre pedidos e
> clientes pela `customer_id` seguido de `groupBy(customer_id, customer_name)`;
> agrupar pelos dois campos de uma vez evita um segundo join só para recuperar o
> nome depois da agregação. Vale registrar que os totais aparecem como
> `12928.099999999999` por serem `double`: em um cenário real de faturamento o
> tipo correto seria `decimal`, que não acumula erro de ponto flutuante.

---

## 6. Logs do driver (opcional / bônus)

Print dos logs do **driver** no **CloudWatch** (grupo `/aws-glue/jobs/output`)
mostrando o `print(...)` do `dataframe_job.py`.

**Onde:** AWS Glue → Jobs → seu job → aba **Runs** → selecione o run → **Output logs**
(abre o CloudWatch no grupo `/aws-glue/jobs/output`).

Saída do grupo `/aws-glue/jobs/output`, stream do run
`jr_99fbef8b5acb82f465b8d8edf61fb8d787c149c5793ca89ad35f456a52f4554a` (obtida com `aws logs get-log-events`):

```text
=== Top clientes por gasto (customer_id,customer_name,total_spend) ===
+-----------+--------------+------------------+
|customer_id|customer_name |total_spend       |
+-----------+--------------+------------------+
|C009       |Isabela Nunes |12928.099999999999|
|C004       |Diego Ferreira|9862.4            |
|C001       |Ana Souza     |3612.0900000000006|
|C007       |Gabriela Lima |2739.0            |
|C002       |Bruno Almeida |2721.4            |
+-----------+--------------+------------------+
Resultado gravado em: s3://lab-aula06-glue-3225002/output/top_clientes
```

São os `print(...)` do `dataframe_job.py` executados no **driver** do Glue.

---

## 7. Limpeza (`terraform destroy`)

Print/trecho do `terraform destroy` com **"Destroy complete!"** confirmando que os
recursos foram removidos (guardrail de custo).

**Onde:** `cd aws-lab/infra && terraform destroy`

Cole aqui a saída:
```text
terraform_data.bucket (local-exec): delete: s3://lab-aula06-glue-3225002/scripts/dataframe_job.py
terraform_data.bucket (local-exec): remove_bucket: lab-aula06-glue-3225002
terraform_data.bucket: Destruction complete after 2s

Destroy complete! Resources: 2 destroyed.
```

Conferência de que não sobrou recurso:
```text
$ aws s3 ls | grep lab-aula06
(nenhum bucket restante)
$ aws glue list-jobs --query 'JobNames' --output text | grep aula06
(nenhum Glue Job restante)
```

Print:
```
![terraform destroy](06-destroy.png)
```

---

## Checklist de conferência

- [x] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [x] 4. Resultado do TOP-N de clientes (`./ver_resultado.sh`)
- [x] 5. Interpretação do TOP-N (2–3 frases)
- [x] 6. Logs do driver (opcional / bônus)
- [x] 7. Limpeza com `terraform destroy` ("Destroy complete!")
