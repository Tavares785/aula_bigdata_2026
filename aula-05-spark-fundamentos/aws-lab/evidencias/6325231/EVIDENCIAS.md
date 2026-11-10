# Evidências — Lab Aula 05 (Spark RDDs na AWS)

## Identificação

- **Nome:** Andreyh Rodrigues de Souza
- **RA:** 6325231
- **Branch:** aula-05-aws-6325231
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
> - implementei os dois TODOs em `job/rdd_job.py` (`word_count_rdd` e `top_n_palavras`);
> - executei **o mesmo código** num Spark local (PySpark 3.5.1, `local[2]`, em
>   container Docker com Java 21), lendo o mesmo `data/sample_lines.txt` e gravando
>   a saída com `saveAsTextFile`, como faz o `main()` do Glue. O script usado está em
>   [`executar_local.py`](executar_local.py);
> - rodei `terraform init` + `terraform validate` na pasta `infra/` (não exige conta AWS).
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

**Não executado na AWS.** Equivalente local: o job rodou até o fim no Spark local
e gravou o marcador `_SUCCESS` no diretório de saída (ver item 4).

**Onde:** `cd aws-lab && python evidencias/6325231/executar_local.py data/sample_lines.txt /tmp/out/wordcount`

---

## 4. Resultado do word count

Saída real da execução local (as 30 primeiras de 167 palavras distintas; ordenadas
por contagem decrescente e, em empate, ordem alfabética):

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
...
Resultado gravado em: /tmp/out/wordcount
```

Conteúdo do diretório de saída (`saveAsTextFile`, uma linha `palavra,contagem` por registro):

```text
$ ls /tmp/out/wordcount
_SUCCESS
part-00000
part-00001

$ cat /tmp/out/wordcount/part-* | head -5
o,60
a,22
e,19
pedido,19
cliente,18
```

---

## 5. Top palavras / interpretação

Top 5 (`top_n_palavras(sc, linhas, 5)`):
```text
o,60
a,22
e,19
pedido,19
cliente,18
```

Interpretação:

> As três primeiras posições são *stopwords* ("o", "a", "e"): o word count puro não
> filtra palavras sem significado, e por isso elas dominam o ranking. Logo depois
> aparecem os termos do domínio de e-commerce: "pedido", "cliente", "entrega",
> "produto", "estoque" e "pagamento". Isso mostra que o texto descreve o ciclo de
> um pedido (compra → pagamento → separação no estoque → entrega). No Spark,
> o `flatMap`/`map` rodam em paralelo nas partições do RDD, cada uma num
> executor. O `reduceByKey` faz um *shuffle* para juntar as contagens de cada
> palavra, e o driver só recebe o resultado final no `collect`. Aqui havia 2
> partições (`local[2]`), daí os dois arquivos `part-00000` e `part-00001`.

---

## 6. Logs do driver (opcional / bônus)

**Não executado** (CloudWatch exige a AWS). No modo local, o `print(...)` do driver
aparece direto no terminal, como mostrado no item 4.

---

## 7. Limpeza (`terraform destroy`)

**Não executado / não necessário:** como o `apply` não foi feito, nenhum recurso
foi criado na AWS e não há nada para destruir.

---

## Checklist de conferência

- [ ] 1. Identidade AWS ativa (`aws sts get-caller-identity`) — *sem acesso ao Learner Lab*
- [ ] 2. `terraform apply` concluído — *apenas `init` + `validate` executados*
- [ ] 3. Job com estado `SUCCEEDED` (Glue) — *executado em Spark local*
- [x] 4. Resultado do word count — *saída da execução local*
- [x] 5. Top palavras + interpretação (2–3 frases)
- [ ] 6. Logs do driver (opcional / bônus)
- [ ] 7. Limpeza com `terraform destroy` — *nenhum recurso criado*
