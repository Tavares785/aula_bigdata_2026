# Evidências — Lab Aula 06 (Spark SQL / DataFrames na AWS)

## Identificação

- **Nome:** Andreyh Rodrigues de Souza
- **RA:** 6325231
- **Branch:** aula-06-aws-6325231
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
> - implementei os dois TODOs em `job/dataframe_job.py` (`total_revenue_by_category`
>   e `top_n_customers_by_spend`);
> - executei **o mesmo código** numa SparkSession local (PySpark 3.5.1, `local[2]`,
>   em container Docker com Java 21), lendo os mesmos `data/pedidos.csv` (60 pedidos)
>   e `data/clientes.csv` (15 clientes) e gravando o TOP-5 em CSV com header, como
>   faz o `main()` do Glue. O script usado está em [`executar_local.py`](executar_local.py);
> - a pasta `infra/` desta aula só tinha o `terraform.tfvars.example`. Adicionei
>   `main.tf`, `outputs.tf`, `variables.tf` e `versions.tf` (mesma infra pronta do lab:
>   bucket via AWS CLI + Glue Job `job-aula06-topn-clientes`) e rodei
>   `terraform init` + `terraform validate`, que não exigem conta AWS.
>
> Se o acesso ao Learner Lab for reaberto, executo as etapas na AWS e completo
> este arquivo com as saídas reais.

---

## 1. Identidade AWS ativa

**Não executado.** Sem acesso ao Learner Lab não há credenciais válidas para
`aws sts get-caller-identity`.

---

## 2. `terraform apply` concluído

**`apply` não executado** (exige credenciais AWS). Como evidência da infra, a
configuração foi inicializada e validada localmente:

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

## 3. Job com estado SUCCEEDED (Glue)

**Não executado na AWS.** Equivalente local: o job rodou até o fim na SparkSession
local e gravou o marcador `_SUCCESS` no diretório de saída (ver item 4).

**Onde:** `cd aws-lab && python evidencias/6325231/executar_local.py data/pedidos.csv data/clientes.csv /tmp/out/top_clientes 5`

---

## 4. Resultado do TOP-N de clientes

Saída real da execução local (inclui também o resultado do TODO 1, receita por
categoria):

```text
=== Receita total por categoria (category,total_revenue) ===
+-----------+------------------+
|category   |total_revenue     |
+-----------+------------------+
|eletronicos|32995.54          |
|moveis     |9865.3            |
|vestuario  |2008.7900000000002|
|livros     |1149.0999999999997|
+-----------+------------------+

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

C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
Resultado gravado em: /tmp/out/top_clientes
$ ls /tmp/out/top_clientes
_SUCCESS
part-00000-077c486b-0a6c-4661-b1c1-47defc4910ce-c000.csv
$ cat /tmp/out/top_clientes/part-*.csv
customer_id,customer_name,total_spend
C009,Isabela Nunes,12928.099999999999
C004,Diego Ferreira,9862.4
C001,Ana Souza,3612.0900000000006
C007,Gabriela Lima,2739.0
C002,Bruno Almeida,2721.4
```

---

## 5. Interpretação do TOP-N

Top-N:
```text
C009,Isabela Nunes,12928.10
C004,Diego Ferreira,9862.40
C001,Ana Souza,3612.09
C007,Gabriela Lima,2739.00
C002,Bruno Almeida,2721.40
```

Interpretação:

> O gasto é bem concentrado: os dois primeiros clientes (Isabela Nunes e Diego
> Ferreira) somam cerca de R$ 22,8 mil, perto de metade dos ~R$ 46 mil de receita
> total. Isso combina com o fato de a categoria "eletronicos" sozinha render
> ~R$ 33 mil, já que poucos pedidos de alto valor puxam o ranking. Para chegar
> nesse resultado o `join` por `customer_id` traz o nome do cliente para cada
> pedido, o `groupBy(customer_id, customer_name)` + `F.sum("value")` soma o gasto
> por cliente e `orderBy(desc).limit(5)` gera o TOP-N. Tudo isso é declarado na
> API de DataFrames e otimizado pelo Catalyst. O driver monta o plano e os
> executors fazem o *shuffle* do join e da agregação em paralelo nas partições.
> Os valores com muitas casas (ex.: `12928.099999999999`) vêm da soma em ponto
> flutuante (`double`). Para exibição, bastaria um `F.round(..., 2)`.

---

## 6. Logs do driver (opcional / bônus)

**Não executado** (CloudWatch exige a AWS). No modo local, o `show(...)`/`print(...)`
do driver aparece direto no terminal, como mostrado no item 4.

---

## 7. Limpeza (`terraform destroy`)

**Não executado / não necessário:** como o `apply` não foi feito, nenhum recurso
foi criado na AWS e não há nada para destruir.

---

## Checklist de conferência

- [ ] 1. Identidade AWS ativa (`aws sts get-caller-identity`) — *sem acesso ao Learner Lab*
- [ ] 2. `terraform apply` concluído — *apenas `init` + `validate` executados*
- [ ] 3. Job com estado `SUCCEEDED` (Glue) — *executado em Spark local*
- [x] 4. Resultado do TOP-N de clientes — *saída da execução local*
- [x] 5. Interpretação do TOP-N (2–3 frases)
- [ ] 6. Logs do driver (opcional / bônus)
- [ ] 7. Limpeza com `terraform destroy` — *nenhum recurso criado*
