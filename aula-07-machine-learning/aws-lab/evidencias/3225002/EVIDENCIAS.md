# Evidências — Lab Aula 07 (Machine Learning com Spark MLlib na AWS)


## 1. Identificação

- **Nome:** José Henrique Teixeira Luiz
- **RA:** 3225002
- **Branch:** `aula-07-aws-3225002`
- **Data:** 14/10/2026

---

## 2. Identidade AWS ativa

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

---

## 3. `terraform apply` concluído

Print ou trecho final do `terraform apply` mostrando **"Apply complete!"** e os
outputs (`bucket_nome`, `glue_job_nome`, `labrole_arn`). **NÃO** mostre credenciais.

**Onde:** `cd aws-lab/infra && terraform apply`

Cole aqui a saída:
```text
terraform_data.bucket (local-exec): {
terraform_data.bucket (local-exec):     "Location": "/lab-aula07-glue-3225002",
terraform_data.bucket (local-exec):     "BucketArn": "arn:aws:s3:::lab-aula07-glue-3225002"
terraform_data.bucket (local-exec): }
terraform_data.bucket (local-exec): upload: ../job/ml_job.py to s3://lab-aula07-glue-3225002/scripts/ml_job.py
terraform_data.bucket (local-exec): upload: ../data/churn.csv to s3://lab-aula07-glue-3225002/input/churn.csv
terraform_data.bucket: Creation complete after 4s
aws_glue_job.ml_churn: Creating...
aws_glue_job.ml_churn: Creation complete after 1s [id=job-aula07-ml-churn]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

bucket_nome   = "lab-aula07-glue-3225002"
glue_job_nome = "job-aula07-ml-churn"
labrole_arn   = "arn:aws:iam::<CONTA>:role/LabRole"
```

> O bucket é criado via **AWS CLI** dentro do `apply` (`terraform_data` +
> `local-exec`), e não com `aws_s3_bucket`, por causa da SCP do Learner Lab que
> nega `s3:GetBucketObjectLockConfiguration`.

---

## 4. Job com estado SUCCEEDED (Glue)

Print/saída final do `./run_job.sh` mostrando `estado: SUCCEEDED` e o
`JobRunId`/`RUN_ID`. (Alternativa: print do console **AWS Glue → Jobs → seu job
→ aba Runs** com status **Succeeded**.)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

Cole aqui a saída:
```text
BUCKET   = lab-aula07-glue-3225002
GLUE_JOB = job-aula07-ml-churn
$ aws s3 cp ../job/ml_job.py s3://lab-aula07-glue-3225002/scripts/ml_job.py
$ aws s3 cp ../data/churn.csv s3://lab-aula07-glue-3225002/input/churn.csv
$ aws s3 rm s3://lab-aula07-glue-3225002/output --recursive
$ aws glue start-job-run --job-name job-aula07-ml-churn ...
RUN_ID = jr_95dc16e38427c077a262d7ff529c241b3b2b13fd5ceaca5f68009acbe7d0eaf2
Aguardando o job terminar (estados: STARTING -> RUNNING -> SUCCEEDED/FAILED)...
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: RUNNING
estado: SUCCEEDED
Job concluido com SUCESSO.
```

---

## 5. Resultado (métricas + amostra de previsões)

Saída do `./ver_resultado.sh`, mostrando as **métricas** (`accuracy`,
`areaUnderROC`) e a **amostra de previsões** (`features,label,prediction`).
Cole nos blocos de código abaixo.

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

Métricas:
```text
metrica,valor
accuracy,1.0
areaUnderROC,1.0
```

Amostra de previsões (features, label, prediction):
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

As 18 linhas do conjunto de teste foram classificadas corretamente
(`label` == `prediction` em todas), o que é coerente com `accuracy = 1.0`.

---

## 6. Interpretação (2–3 frases)

Escreva **2–3 frases** interpretando as métricas e o que elas dizem sobre o
**churn**. Relacione com os conceitos da aula: as **features**
(`meses_ativo`, `gasto_mensal`, `chamados_suporte`, `atraso_pagamento`), a
divisão **treino/teste** (70/30) e o **classificador** (LogisticRegression).

Interpretação:

> O modelo acertou todas as 18 linhas do conjunto de teste (`accuracy = 1.0` e
> `areaUnderROC = 1.0`), separando perfeitamente quem cancela de quem permanece.
> Olhando a amostra de previsões, as quatro features se movem em bloco: quem dá
> churn tem poucos `meses_ativo` (2 a 6), `gasto_mensal` baixo, muitos
> `chamados_suporte` (4 a 8) e quase sempre `atraso_pagamento = 1`, enquanto quem
> permanece tem o perfil oposto — 29 meses ou mais, gasto alto e praticamente
> nenhum chamado ou atraso. Como as classes são linearmente separáveis nesse
> recorte, a `LogisticRegression` encontra uma fronteira que acerta tudo; vale
> registrar que o dataset tem apenas 40 linhas e a divisão 70/30 deixou 18 no
> teste, então uma acurácia de 100% aqui indica um problema fácil e um conjunto
> pequeno, não um desempenho que se possa prometer em dados reais.

---

## 7. Logs do driver (opcional / bônus)

Print dos logs do **driver** no **CloudWatch** (grupo `/aws-glue/jobs/output`)
mostrando os `print(...)` do `ml_job.py` (ex.: a seção `=== Metricas (churn) ===`).

**Onde:** AWS Glue → Jobs → seu job → aba **Runs** → selecione o run → **Output logs**
(abre o CloudWatch no grupo `/aws-glue/jobs/output`).

Saída do grupo `/aws-glue/jobs/output`, stream do run
`jr_95dc16e38427c077a262d7ff529c241b3b2b13fd5ceaca5f68009acbe7d0eaf2`
(obtida com `aws logs get-log-events`):

```text
=== Metricas (churn) ===
accuracy,1.0000
areaUnderROC,1.0000
Resultado gravado em: s3://lab-aula07-glue-3225002/output/metrics e s3://lab-aula07-glue-3225002/output/predictions
```

São os `print(...)` do `ml_job.py` executados no **driver** do Glue.

---

## 8. Limpeza (`terraform destroy`)

Print/trecho do `terraform destroy` com **"Destroy complete!"** confirmando que os
recursos foram removidos (guardrail de custo).

**Onde:** `cd aws-lab/infra && terraform destroy`

Cole aqui a saída:
```text
terraform_data.bucket (local-exec): delete: s3://lab-aula07-glue-3225002/scripts/ml_job.py
terraform_data.bucket (local-exec): delete: s3://lab-aula07-glue-3225002/input/churn.csv
terraform_data.bucket (local-exec): delete: s3://lab-aula07-glue-3225002/output/metrics/part-00000-...csv
terraform_data.bucket (local-exec): delete: s3://lab-aula07-glue-3225002/output/predictions/part-00000-...csv
terraform_data.bucket (local-exec): remove_bucket: lab-aula07-glue-3225002
terraform_data.bucket: Destruction complete after 2s

Destroy complete! Resources: 2 destroyed.
```

Conferência de que não sobrou recurso:
```text
$ aws s3 ls | grep lab-aula07
(nenhum bucket restante)
$ aws glue list-jobs --query 'JobNames' --output text | grep aula07
(nenhum Glue Job restante)
```

---

## Checklist de conferência

- [x] 1. Identificação preenchida (Nome, RA, Branch, Data)
- [x] 2. Identidade AWS ativa (`aws sts get-caller-identity`)
- [x] 3. `terraform apply` concluído ("Apply complete!" + outputs)
- [x] 4. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`/`RUN_ID`)
- [x] 5. Resultado: métricas (`accuracy`, `areaUnderROC`) + amostra de previsões
- [x] 6. Interpretação das métricas (2–3 frases)
- [x] 7. Logs do driver no CloudWatch (opcional / bônus)
- [x] 8. Limpeza com `terraform destroy` ("Destroy complete!")

---

## ⚠️ Aviso de segurança

**NUNCA** inclua credenciais ou segredos nos prints ou nas saídas coladas. Se
aparecerem a **Access Key**, o **Secret Access Key** ou o **Session Token**
(bem como `Account`/`UserId`), **mascare** esses valores antes de salvar a
imagem ou de colar o texto nas evidências.
