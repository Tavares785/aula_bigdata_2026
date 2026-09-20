# Evidências — Lab Aula 05 (Spark RDDs na AWS)

> Copie este arquivo para `evidencias/<SEU_RA>/EVIDENCIAS.md` e preencha.
> Salve os prints na mesma pasta e referencie-os no texto.

## Identificação

- **Nome:** Felipe Gomes Mariano
- **RA:** 3225014
- **Branch:** aula-05-aws-3225014
- **Data:** 20/09/2026

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
![alt text](01-identity.png)


Print (opcional):
```
print acima - mascarando as credenciais por segurança.
```

---

## 2. `terraform apply` concluído

Print ou trecho final do `terraform apply` mostrando **"Apply complete!"** e os
outputs (`bucket_nome`, `glue_job_nome`, `labrole_arn`). **NÃO** mostre credenciais.

**Onde:** `cd aws-lab/infra && terraform apply`

Cole aqui a saída:
```text
Não colado por motivos de segurança.
```

Print:
![alt text](terraform-apply.png)

---

## 3. Job com estado SUCCEEDED (Glue)

Print/saída final do `./run_job.sh` mostrando `estado: SUCCEEDED` e o `RUN_ID`.
(Alternativa: print do console **AWS Glue → Jobs → seu job → aba Runs** com status
**Succeeded**.)

**Onde:** `cd aws-lab/scripts && ./run_job.sh`

Cole aqui a saída:
```text
(cole a saída aqui)
```

Print:
![alt text](run_job.png)

---

## 4. Resultado do word count

Saída do `./ver_resultado.sh` (lista do output + conteúdo `palavra,contagem`).
Cole no bloco de código abaixo.

**Onde:** `cd aws-lab/scripts && ./ver_resultado.sh`

Cole aqui a saída:
```text
(cole a saída aqui)
```

Print (opcional):
![alt text](ver_resultados.png)

---

## 5. Top palavras / interpretação

Cole o **TOP 5** do word count e escreva **2–3 frases** interpretando o resultado
(ex.: por que "pedido/cliente/entrega" dominam, o que isso diz sobre o texto de
e-commerce). Relacione com os conceitos de **RDD / driver / executors** da aula.

Top 5:
```text
(cole o top 5 aqui — palavra,contagem)
```

Interpretação:

> (escreva aqui 2–3 frases)

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
(cole a saída aqui)
```

Print:
![alt text](terraform_destroy.png)

---

## Checklist de conferência

- [X] 1. Identidade AWS ativa (`aws sts get-caller-identity`)
- [X] 2. `terraform apply` concluído ("Apply complete!" + outputs)
- [-] 3. Job com estado `SUCCEEDED` (Glue) (+ `RUN_ID`)
- [?] 4. Resultado do word count (`./ver_resultado.sh`)
- [?] 5. Top palavras + interpretação (2–3 frases)
- [?] 6. Logs do driver (opcional / bônus)
- [X] 7. Limpeza com `terraform destroy` ("Destroy complete!")


## Notas pessoais:
- Dificuldades com objectLock - resolvido com um local-exec
- Problemas com o scrips rdd_job.py - incompatibilidade com a versão 25 do java?