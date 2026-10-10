# Evidências — Lab Aula 07 (Machine Learning com Spark MLlib na AWS)

## 1. Identificação

- **Nome:** Gabriel Reis Cunha
- **RA:** 6325149
- **Branch:** aula-07-6325149
- **Data:** 2026-10-10

---

## 2. Identidade AWS ativa

**Comando:**
```bash
aws sts get-caller-identity
```

Saída (conta mascarada):
```text
arn:aws:sts::<conta>:assumed-role/voclabs/user5367756=Gabriel_Reis_Cunha
```

Confirmado: não é usuário root; é a role padrão do AWS Academy Learner Lab
(`assumed-role/voclabs/...`). Antes do apply, a conta estava vazia (0 buckets,
0 jobs Glue).

---

## 3. `terraform apply` concluído

**Onde:** `cd aws-lab/infra && terraform apply`

```text
terraform_data.bucket: Creation complete after 7s [id=6c53872b-5497-c7a9-f019-c26b7d2923c1]
aws_glue_job.ml_churn: Creation complete after 1s [id=job-aula07-ml-churn]
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

bucket_nome = "lab-aula07-glue-6325149"
glue_job_nome = "job-aula07-ml-churn"
```

---

## 4. Job com estado SUCCEEDED (Glue)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

```text
RUN_ID = jr_51cb9cad433719c38dd731e6858b81f680f14f902f189a7a9714099ac63bceb8
Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)...
estado: RUNNING   (16 verificações)
estado: SUCCEEDED
Job concluido com SUCESSO.
```

Tempo de execução reportado pelo Glue: 258 s (2 workers G.1X, Glue 4.0).

---

## 5. Resultado (métricas + amostra de previsões)

Obtido baixando o prefixo `output/` do bucket (`aws s3 cp --recursive`, o mesmo
que o `ver_resultado.sh` faz) logo antes do `terraform destroy`.

```text
$ aws s3 ls s3://lab-aula07-glue-6325149/output/ --recursive
2026-10-10 10:18:46         44 output/metrics/part-00000-1318de43-2476-457a-9452-fcecba8f44ef-c000.csv
2026-10-10 10:18:47        404 output/predictions/part-00000-8c442429-8eb0-4328-bf99-562cc17889d5-c000.csv
```

Métricas:
```text
metrica,valor
accuracy,1.0
areaUnderROC,1.0
```

Amostra de previsões (18 linhas do conjunto de teste):
```text
meses_ativo,gasto_mensal,chamados_suporte,atraso_pagamento,label,prediction
2,41.0,8,1,1,1.0
3,30.0,5,1,1,1.0
3,35.0,6,1,1,1.0
3,39.0,6,0,1,1.0
5,60.0,4,1,1,1.0
5,62.0,5,1,1,1.0
6,70.0,5,1,1,1.0
29,105.0,2,0,0,0.0
32,125.0,2,0,0,0.0
35,140.0,0,0,0,0.0
36,120.0,0,0,0,0.0
41,175.0,1,0,0,0.0
42,180.0,0,0,0,0.0
44,190.0,0,0,0,0.0
46,195.0,0,0,0,0.0
48,210.0,1,0,0,0.0
50,230.0,0,0,0,0.0
60,300.0,1,0,0,0.0
```

---

## 6. Interpretação (2–3 frases)

> O pipeline montou o vetor de features com `VectorAssembler`, dividiu os dados
> 70/30 (`seed=42`), treinou uma Regressão Logística e avaliou no teste: acurácia
> 1.0 e AUC 1.0, com as 18 previsões iguais ao rótulo. Esse resultado perfeito
> deve ser lido com cautela: o dataset tem só 40 linhas e é praticamente separável
> (clientes que cancelam têm poucos meses de contrato, muitos chamados e atrasos),
> então o teste é pequeno e fácil, e isso não garante o mesmo desempenho com dados
> reais maiores. O Glue distribuiu o treino entre driver e executors sem eu
> gerenciar cluster.

---

## 7. Logs do driver (opcional / bônus)

Não coletado.

---

## 8. Limpeza (`terraform destroy`)

**Onde:** `cd aws-lab/infra && terraform destroy`

```text
aws_glue_job.ml_churn: Destruction complete after 1s
terraform_data.bucket (local-exec): remove_bucket: lab-aula07-glue-6325149
terraform_data.bucket: Destruction complete after 3s
Destroy complete! Resources: 2 destroyed.
```

Verificação posterior (nada restou):
```text
aws s3api head-bucket --bucket lab-aula07-glue-6325149
  -> An error occurred (404) when calling the HeadBucket operation: Not Found
aws glue get-job --job-name job-aula07-ml-churn
  -> An error occurred (EntityNotFoundException) when calling the GetJob operation: Job not found.
buckets: 0  jobs: 0
```

---

## Checklist de conferência

- [x] 1. Identificação preenchida (Nome, RA, Branch, Data)
- [x] 2. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 3. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 4. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`/`RUN_ID`)
- [x] 5. Resultado: métricas (`accuracy`, `areaUnderROC`) + amostra de previsões
- [x] 6. Interpretação das métricas (2–3 frases)
- [ ] 7. Logs do driver no CloudWatch (opcional / bônus)
- [x] 8. Limpeza com `terraform destroy` ("Destroy complete!")
