# Evidências — Lab Aula 07 (Machine Learning com Spark MLlib na AWS)

## 1. Identificação

- **Nome:** Andreyh Rodrigues de Souza
- **RA:** 6325231
- **Branch:** aula-07-aws-6325231
- **Data:** 2026-11-09

---

> ⚠️ **Aviso importante sobre esta entrega**
>
> Meu acesso ao **AWS Academy Learner Lab expirou**, então **não consegui executar
> as etapas que dependem da AWS** (credenciais, `terraform apply`, Glue Job,
> leitura do S3 e `terraform destroy`). Esses itens estão marcados abaixo como
> **"não executado"**. Não há saídas inventadas.
>
> Para comprovar o trabalho, fiz o seguinte, tudo executado de verdade:
> - implementei os três TODOs em `job/ml_job.py` (`build_feature_vector`,
>   `train_classifier` e `evaluate_accuracy`);
> - executei **o mesmo fluxo do `main()`** numa SparkSession local (PySpark 3.5.1,
>   `local[2]`, no container Docker do lab com Java 21): lê `data/churn.csv`,
>   renomeia `churn → label`, split 70/30 com `seed=42`, treina a
>   `LogisticRegression`, calcula `accuracy` e `areaUnderROC` e grava `metrics` e
>   `predictions` em CSV. O script usado está em [`executar_local.py`](executar_local.py);
> - rodei `terraform init` + `terraform validate` na pasta `infra/` (não exige conta AWS).
>
> Se o acesso ao Learner Lab for reaberto, executo as etapas na AWS e completo
> este arquivo com as saídas reais.

---

## 2. Identidade AWS ativa

**Não executado.** Sem acesso ao Learner Lab não há credenciais válidas para
`aws sts get-caller-identity`.

---

## 3. `terraform apply` concluído

**`apply` não executado** (exige credenciais AWS). Como evidência da infra
(bucket via AWS CLI + Glue Job `job-aula07-ml-churn`), a configuração foi
inicializada e validada localmente:

**Onde:** `cd aws-lab/infra && terraform init && terraform validate && terraform fmt -check`

```text
Initializing the backend...

Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform
- Finding hashicorp/aws versions matching "5.31.0"...
- Installing hashicorp/aws v5.31.0...
- Installed hashicorp/aws v5.31.0 (signed by HashiCorp)

Terraform has been successfully initialized!

$ terraform validate
Success! The configuration is valid.

$ terraform fmt -check -recursive
terraform fmt -check: OK
```

---

## 4. Job com estado SUCCEEDED (Glue)

**Não executado na AWS** (sem `JobRunId`). Equivalente local: o fluxo rodou até o
fim e gravou o marcador `_SUCCESS` em `metrics/` e `predictions/` (ver item 5).

**Onde:** `cd aws-lab && python evidencias/6325231/executar_local.py data/churn.csv /tmp/output`

---

## 5. Resultado (métricas + amostra de previsões)

Saída real completa da execução local:

```text
linhas: total=40 treino=22 teste=18
=== Metricas (churn) ===
accuracy,1.0000
areaUnderROC,1.0000
=== Coeficientes da LogisticRegression ===
meses_ativo,-1.4197
gasto_mensal,0.0176
chamados_suporte,3.4549
atraso_pagamento,-3.4411
intercept,18.5801
Resultado gravado em: /tmp/output/metrics e /tmp/output/predictions
$ ls /tmp/output/metrics
_SUCCESS
part-00000-bbf9c9c5-09b7-4dd0-b12d-26c94fd1e643-c000.csv
$ cat /tmp/output/metrics/part-*.csv
metrica,valor
accuracy,1.0
areaUnderROC,1.0
$ ls /tmp/output/predictions
_SUCCESS
part-00000-a32955ce-ed91-4a40-b4aa-5e9e35053a09-c000.csv
$ cat /tmp/output/predictions/part-*.csv
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

Métricas:
```text
accuracy,1.0000
areaUnderROC,1.0000
```

Amostra de previsões (features, label, prediction): as 18 linhas do conjunto
de teste estão no bloco acima (`/tmp/output/predictions`). Todas têm
`prediction == label`.

---

## 6. Interpretação (2–3 frases)

> O modelo acertou todos os 18 clientes do teste (accuracy = 1.0) e separou
> perfeitamente quem cancela de quem fica (AUC = 1.0). Isso acontece porque o
> `churn.csv` é pequeno (40 linhas, 22 de treino e 18 de teste com o split 70/30 e
> `seed=42`) e quase linearmente separável: clientes que cancelam têm poucos
> `meses_ativo`, `gasto_mensal` baixo e muitos `chamados_suporte`, e quem fica é o
> oposto. Os coeficientes da `LogisticRegression` confirmam isso:
> `chamados_suporte` (+3,45) aumenta a chance de churn e `meses_ativo` (−1,42) a
> reduz. Já o sinal negativo de `atraso_pagamento` não deve ser interpretado.
> Com dados perfeitamente separáveis, os pesos ficam instáveis e essa variável
> é muito correlacionada com as outras. Em produção, com mais dados, seria preciso
> validação cruzada e regularização (`regParam`) antes de confiar nessas métricas.
> No Glue, o `VectorAssembler` e o `fit` rodariam distribuídos nos executors
> (2× `G.1X`), e o driver só coordenaria e imprimiria as métricas.

---

## 7. Logs do driver (opcional / bônus)

**Não executado** (CloudWatch exige a AWS). No modo local, a seção
`=== Metricas (churn) ===` impressa pelo driver aparece no item 5.

---

## 8. Limpeza (`terraform destroy`)

**Não executado / não necessário:** como o `apply` não foi feito, nenhum recurso
foi criado na AWS e não há nada para destruir.

---

## Testes automáticos da pasta `aws-lab/tests`

Rodei a suíte do lab localmente (Docker `lab-aula-07`), já com os TODOs implementados:

**Onde:** `cd aula-07-machine-learning && docker run --rm -v "$PWD":/lab lab-aula-07 pytest aws-lab/tests -q --tb=line`

```text
.....FFF.......                                                          [100%]
=========================== short test summary info ============================
FAILED aws-lab/tests/test_estado_inicial.py::test_build_feature_vector_estado_todo_levanta_not_implemented
FAILED aws-lab/tests/test_estado_inicial.py::test_train_classifier_estado_todo_levanta_not_implemented
FAILED aws-lab/tests/test_estado_inicial.py::test_evaluate_accuracy_estado_todo_levanta_not_implemented
3 failed, 12 passed in 387.99s (0:06:27)
```

As 3 falhas são **esperadas**. O `test_estado_inicial.py` verifica o *estado
inicial do exercício*, ou seja, que as três funções ainda levantam
`NotImplementedError`. Como os TODOs foram implementados, as funções não
levantam mais o erro e esses testes falham por definição. Os demais
testes (dataset, propriedades das métricas, previsões e acurácia) passam.

---

## Checklist de conferência

- [x] 1. Identificação preenchida (Nome, RA, Branch, Data)
- [ ] 2. Identidade AWS ativa (`aws sts get-caller-identity`) — *sem acesso ao Learner Lab*
- [ ] 3. `terraform apply` concluído — *apenas `init` + `validate` executados*
- [ ] 4. Job com estado `SUCCEEDED` (Glue) — *executado em Spark local*
- [x] 5. Resultado: métricas (`accuracy`, `areaUnderROC`) + amostra de previsões — *execução local*
- [x] 6. Interpretação das métricas (2–3 frases)
- [ ] 7. Logs do driver no CloudWatch (opcional / bônus)
- [ ] 8. Limpeza com `terraform destroy` — *nenhum recurso criado*
