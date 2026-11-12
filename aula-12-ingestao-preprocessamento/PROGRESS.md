# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

**Grupo:** José Henrique Teixeira Luiz (3225002), Daniel de Oliveira
Tavares Júnior (6325032), Leandro Duarte (6325072)

## O que foi feito nesta etapa

Construímos o pipeline completo em arquitetura medalhão: `S3 raw` → Glue
Job (PySpark) → `silver/` e `gold/` em Parquet → Glue Crawler → Athena.

**Infraestrutura** (`aws-lab/infra/`): provider AWS fixado em `5.31.0` na
`us-east-1`, bucket criado pela CLI com `terraform_data` + `local-exec`,
upload do CSV e do script pelo próprio Terraform, `aws_glue_catalog_database`,
`aws_glue_job` (`glueetl`, Glue 4.0, LabRole por ARN) e `aws_glue_crawler`
com dois `s3_target` (silver e gold). Cinco outputs. `terraform fmt -check`
e `terraform validate` passam.

**ETL** (`aws-lab/job/etl_mercadofacil.py`): PySpark lendo o CSV sem
inferência de esquema, aplicando as 12 regras documentadas em
`REGRAS_SILVER.md`, mandando o que não vira fato para `quarentena/` com o
motivo, deduplicando por `item_id` com `row_number`, e gravando duas
tabelas gold — `atraso_por_recorte` e `desfecho_por_canal`.

**Antes de escrever uma linha de ETL, perfilamos o CSV.** As 12 regras
saem de problemas medidos, não supostos: 200 `item_id` duplicados, cinco
marcadores de nulo diferentes na mesma coluna, dinheiro em três formatos,
datas em três formatos mais a palavra `ontem`, categorias truncadas
(`Beleza e Saúd`), status em dois idiomas (`DELIVERED` ao lado de
`entregue`), estados por extenso, 57 notas fora da escala 1–5, 37
quantidades negativas e 49 valores totais negativos.

### O que ainda NÃO rodou

**O `terraform apply` não foi executado.** A infraestrutura está escrita e
validada, mas `terraform validate` confere apenas sintaxe e tipos — ele
não diz se a SCP do Learner Lab permite cada chamada. O pipeline precisa
do lab aberto para `apply`, execução do Glue Job até `SUCCEEDED`, Crawler
e consulta no Athena. Os prints exigidos na entrega serão anexados quando
isso acontecer.

Registramos isso em vez de afirmar execução: já aconteceu, em outro
projeto desta turma, de uma configuração validada falhar no `apply`
porque a SCP negava uma API — `aws_s3_bucket` é exatamente esse caso, e
é por isso que o bucket aqui é criado pela CLI.

## Ferramentas efetivamente usadas

| Ferramenta | Para quê |
|---|---|
| **Terraform 5.31.0** | Toda a infra: bucket, uploads, Glue database, job e crawler. Versão fixada porque provider novo muda o formato do state sem avisar |
| **AWS CLI** | Criação do bucket, via `local-exec`. Não por preferência: o recurso `aws_s3_bucket` quebra no Learner Lab, porque a SCP nega `s3:GetBucketObjectLockConfiguration` e o provider chama essa API em toda leitura |
| **S3** | As quatro camadas — `raw/`, `silver/`, `gold/`, `quarentena/` — mais `scripts/` e os resultados do Athena |
| **AWS Glue Job (PySpark, Glue 4.0)** | O ETL. O EMR Serverless é bloqueado no lab; o Spark gerenciado que funciona é o Glue |
| **AWS Glue Crawler + Data Catalog** | Cataloga silver e gold. A raw fica de fora de propósito: é CSV sujo, e catalogá-la convidaria alguém a consultar dado não tratado achando que é o oficial |
| **Athena** | Consulta das tabelas gold, pelo `scripts/consultar_athena.sh` |
| **LabRole** | Identidade do Job e do Crawler. Não criamos role nem policy: o lab bloqueia |
| **Python/`csv` local** | O perfil do CSV que originou as 12 regras |

## Dificuldades encontradas

**A base é mais suja do que parece à primeira leitura.** A primeira linha
já mostra quatro problemas, mas os que custaram mais foram os que só
aparecem no agregado: `SP` e ` SP ` viram dois estados num `GROUP BY`, e
`Beleza e Saúd` vira uma sexta categoria. Achamos isso perfilando o
arquivo inteiro, não lendo as primeiras linhas.

**A ordem das conversões importa e erra em silêncio.** Trocar a vírgula
decimal antes de remover o ponto de milhar faz `1.647,40` virar
`1.64740` — número válido, valor errado, nenhum erro levantado. O mesmo
com `desconto_pct`: remover o `%` depois do cast transformaria 2.932
linhas em `NULL` e o desconto sumiria da conta sem aviso.

**Decidir entre `dropDuplicates` e `row_number`.** O `dropDuplicates`
resolve a contagem, mas a cópia que sobrevive é arbitrária, e duas
execuções podem divergir. Optamos por `row_number` com critério
explícito: fica a linha mais completa e, no empate, a de entrega mais
recente.

**O que fazer com o que não dá para salvar.** A tentação é filtrar e
seguir. Criamos a `quarentena/` com a coluna `motivo_quarentena` porque
descartar em silêncio esconde justamente o que precisa ser investigado —
e três por cento de pedidos sumindo é o tipo de coisa que se descobre
meses depois.

**Restrições do Learner Lab.** Duas moldaram a infra inteira: não usar
`aws_s3_bucket` e não criar IAM. Ambas estão comentadas no `main.tf`,
para ninguém "padronizar" depois e reintroduzir a falha.

## Próxima etapa (Aula 13)

A partir da gold, responder as perguntas do cenário com análise, não só
com agregação:

1. **Quais fatores mais explicam o atraso.** Temos `estado`, `categoria`,
   `transportadora`, `centro_distribuicao`, `canal` e mês. A pergunta é
   quais pesam, e o primeiro passo é medir a correlação antes de tentar
   qualquer modelo.
2. **A relação entre atraso e nota.** A gold já traz `atraso_medio_dias`
   e `nota_media` no mesmo recorte; falta medir a associação e separar o
   efeito do atraso do efeito da categoria.
3. **Sazonalidade.** Black Friday e Natal, pela coluna `ano_mes`.
4. **Revisar a quarentena.** Consultar `quarentena/` por
   `motivo_quarentena` e decidir, caso a caso, o que dá para recuperar.

Uma ressalva que vamos carregar: correlação entre categoria e atraso não
diz que a categoria causa o atraso. O que a gold sustenta é descrição e
comparação; afirmação causal exigiria desenho que este dado não tem.
