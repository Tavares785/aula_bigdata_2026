# Evidências — Lab Aula 07 (Machine Learning com Spark MLlib na AWS)

> Copie este arquivo para `evidencias/<SEU_RA>/EVIDENCIAS.md` e preencha.
> Salve os prints na mesma pasta e referencie-os no texto.

## 1. Identificação

- **Nome:**
- **RA:**
- **Branch:** aula-07-aws-SEURA
- **Data:**

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
```text
(cole a saída aqui)
```

Print (opcional):
```
![identidade AWS](01-identity.png)
```

---

## 3. `terraform apply` concluído

Print ou trecho final do `terraform apply` mostrando **"Apply complete!"** e os
outputs (`bucket_nome`, `glue_job_nome`, `labrole_arn`). **NÃO** mostre credenciais.

**Onde:** `cd aws-lab/infra && terraform apply`

Cole aqui a saída:
```text
(cole a saída aqui)
```

Print:
```
![terraform apply](02-apply.png)
```

---

## 4. Job com estado SUCCEEDED (Glue)

Print/saída final do `./run_job.sh` mostrando `estado: SUCCEEDED` e o
`JobRunId`/`RUN_ID`. (Alternativa: print do console **AWS Glue → Jobs → seu job
→ aba Runs** com status **Succeeded**.)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

Cole aqui a saída:
```text
(cole a saída aqui — inclua o JobRunId/RUN_ID)
```

Print:
```
![job success](03-job-success.png)
```

---

## 5. Resultado (métricas + amostra de previsões)

Saída do `./ver_resultado.sh`, mostrando as **métricas** (`accuracy`,
`areaUnderROC`) e a **amostra de previsões** (`features,label,prediction`).
Cole nos blocos de código abaixo.

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

Métricas:
```text
(cole aqui — ex.: accuracy,0.8333 / areaUnderROC,0.9000)
```

Amostra de previsões (features, label, prediction):
```text
(cole aqui a amostra features,label,prediction)
```

Print (opcional):
```
![resultado ML](04-resultado.png)
```

---

## 6. Interpretação (2–3 frases)

Escreva **2–3 frases** interpretando as métricas e o que elas dizem sobre o
**churn**. Relacione com os conceitos da aula: as **features**
(`meses_ativo`, `gasto_mensal`, `chamados_suporte`, `atraso_pagamento`), a
divisão **treino/teste** (70/30) e o **classificador** (LogisticRegression).

Interpretação:

> (escreva aqui 2–3 frases)

---

## 7. Logs do driver (opcional / bônus)

Print dos logs do **driver** no **CloudWatch** (grupo `/aws-glue/jobs/output`)
mostrando os `print(...)` do `ml_job.py` (ex.: a seção `=== Metricas (churn) ===`).

**Onde:** AWS Glue → Jobs → seu job → aba **Runs** → selecione o run → **Output logs**
(abre o CloudWatch no grupo `/aws-glue/jobs/output`).

Print:
```
![logs do driver](05-driver-log.png)
```

---

## 8. Limpeza (`terraform destroy`)

Print/trecho do `terraform destroy` com **"Destroy complete!"** confirmando que os
recursos foram removidos (guardrail de custo).

**Onde:** `cd aws-lab/infra && terraform destroy`

Cole aqui a saída:
```text
(cole a saída aqui)
```

Print:
```
![terraform destroy](06-destroy.png)
```

---

## Checklist de conferência

- [ ] 1. Identificação preenchida (Nome, RA, Branch, Data)
- [ ] 2. Identidade AWS ativa (`aws sts get-caller-identity`)
- [ ] 3. `terraform apply` concluído ("Apply complete!" + outputs)
- [ ] 4. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`/`RUN_ID`)
- [ ] 5. Resultado: métricas (`accuracy`, `areaUnderROC`) + amostra de previsões
- [ ] 6. Interpretação das métricas (2–3 frases)
- [ ] 7. Logs do driver no CloudWatch (opcional / bônus)
- [ ] 8. Limpeza com `terraform destroy` ("Destroy complete!")

---

## ⚠️ Aviso de segurança

**NUNCA** inclua credenciais ou segredos nos prints ou nas saídas coladas. Se
aparecerem a **Access Key**, o **Secret Access Key** ou o **Session Token**
(bem como `Account`/`UserId`), **mascare** esses valores antes de salvar a
imagem ou de colar o texto nas evidências.
