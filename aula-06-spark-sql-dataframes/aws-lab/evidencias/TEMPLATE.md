# Evidências — Lab Aula 06 (Spark SQL / DataFrames na AWS)

> Copie este arquivo para `evidencias/<SEU_RA>/EVIDENCIAS.md` e preencha.
> Salve os prints na mesma pasta e referencie-os no texto.

## Identificação

- **Nome:**
- **RA:**
- **Branch:** aula-06-aws-SEURA
- **Data:**

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
(cole a saída aqui)
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
(cole a saída aqui)
```

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
(cole a saída aqui)
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
(cole a saída aqui)
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
(cole o top-n aqui — customer_id,customer_name,total_spend)
```

Interpretação:

> (escreva aqui 2–3 frases)

---

## 6. Logs do driver (opcional / bônus)

Print dos logs do **driver** no **CloudWatch** (grupo `/aws-glue/jobs/output`)
mostrando o `print(...)` do `dataframe_job.py`.

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
(cole a saída aqui)
```

Print:
```
![terraform destroy](06-destroy.png)
```

---

## Checklist de conferência

- [ ] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [ ] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [ ] 3. Job com estado `SUCCEEDED` (Glue) (+ `JobRunId`)
- [ ] 4. Resultado do TOP-N de clientes (`./ver_resultado.sh`)
- [ ] 5. Interpretação do TOP-N (2–3 frases)
- [ ] 6. Logs do driver (opcional / bônus)
- [ ] 7. Limpeza com `terraform destroy` ("Destroy complete!")
