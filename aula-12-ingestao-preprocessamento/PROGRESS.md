# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## O que foi feito nesta etapa

Construímos do zero o pipeline medalhão da MercadoFácil na AWS, com Terraform
e PySpark:

- **Infra (`aws-lab/infra/`)**: provider `aws` 5.31.0 em `us-east-1`. O bucket
  S3 privado é criado via AWS CLI (`terraform_data` + `local-exec`, com
  bloqueio de acesso público e SSE-S3), e o `destroy` esvazia e remove o
  bucket. O próprio Terraform faz o upload do CSV para `raw/pedidos/` e do
  script para `scripts/`. Também cria o Glue Database `mercadofacil_db`, o
  Glue Job (`glueetl`, Glue 4.0, 2 × G.1X, LabRole por ARN, caminhos das
  camadas passados como argumentos) e um Glue Crawler com um `s3_target` por
  tabela. São 10 outputs. Nenhuma role/policy IAM é criada, e o
  `terraform.tfvars` com o ARN e o nome do bucket não é versionado.
- **ETL (`aws-lab/job/etl_mercadofacil.py`)**:
  - **raw**: o CSV intocado.
  - **silver**: `silver/pedidos_itens` com 9.601 itens tipados, padronizados e
    deduplicados, sem PII.
  - **quarentena**: `quarentena/` com 399 linhas e o motivo de cada uma.
  - **gold**: 5 tabelas. `entregas_estado_mes` e `atraso_transportadora_cd`
    explicam o atraso. `atraso_vs_nota` mostra a relação entre atraso e nota.
    `cancelamento_devolucao` cobre cancelamentos e devoluções.
    `vendas_mensais_categoria` mostra a sazonalidade (Black Friday e Natal).
  - As 21 regras de limpeza e o tratamento LGPD estão em
    `aws-lab/REGRAS_SILVER.md`.
- **Scripts (`aws-lab/scripts/`)**:
  - `run_pipeline.sh` limpa os prefixos, roda o job até `SUCCEEDED` (imprime o
    `JobRunId`), roda o crawler e lista as tabelas.
  - `query_athena.sh` executa no Athena as consultas de `consultas_gold.sql`.

**Executado de ponta a ponta no AWS Academy Learner Lab em 2026-11-12:**
`terraform apply` (6 recursos) → Glue Job `SUCCEEDED` em 133 s
(JobRunId `jr_0d3b17c24abb09e1461bb437ca15bac801efbaea40cb51772b40b3073023ac5d`)
→ Crawler `SUCCEEDED` (7 tabelas no `mercadofacil_db`) → consultas no Athena
→ `terraform destroy` (6 recursos removidos, bucket conferido como inexistente).
O log do job no CloudWatch fecha as contagens:
`raw=10000 silver=9601 quarentena=399 soma_ok=True`. Antes, o mesmo script
foi testado localmente com Spark 3.3, a mesma versão do Glue 4.0. Os prints
estão em `aws-lab/prints/` (credenciais e ID da conta mascarados).

Primeiros achados da gold (Athena):

- Nordeste (35,1%) e Norte (31,6%) atrasam quase o dobro do Sudeste/Sul (~19%).
  O pior par é Correios + CD-NORDESTE, com 39,9% dos pedidos atrasados.
- Nov (Black Friday) e dez (Natal) têm 34% e 32% de itens atrasados,
  contra 15–20% no resto do ano.
- A nota média cai de 4,12 (no prazo) para 2,21 (8+ dias de atraso). Com
  8+ dias de atraso, 65% das notas são 1 ou 2.
- Eletrônicos concentram a maior receita perdida com cancelamento e
  devolução (R$ 147,6 mil).

## Ferramentas efetivamente usadas

- **Terraform** (provider AWS 5.31.0): toda a infraestrutura como código
  (`terraform_data`, `aws_s3_object`, `aws_glue_catalog_database`,
  `aws_glue_job`, `aws_glue_crawler`).
- **AWS CLI**: cria e remove o bucket (o `aws_s3_bucket` é bloqueado no
  Learner Lab) e dispara job, crawler e consultas do Athena pelos scripts.
- **Amazon S3**: data lake com os prefixos `raw/`, `silver/`, `gold/`,
  `quarentena/`, `scripts/` e `athena-results/`.
- **AWS Glue Job (PySpark / Spark 3.3)**: transformação raw → silver +
  quarentena → gold, com saída em Parquet.
- **AWS Glue Crawler + Data Catalog**: cria as tabelas a partir dos Parquet.
- **Amazon Athena**: consultas SQL de validação e de negócio sobre a gold.
- **CloudWatch Logs**: logs do job (`/aws-glue/jobs/output`), incluindo o
  resumo de qualidade (contagens por camada e por motivo de quarentena).
- **PySpark local + JDK 11**: teste do mesmo script antes de subir para a AWS.

## Dificuldades encontradas

- **Restrições do Learner Lab**: o `aws_s3_bucket` não funciona (SCP nega
  `GetBucketObjectLockConfiguration`), então o bucket é criado via CLI, com
  um provisioner de destroy que o esvazia. Também não podemos criar IAM: job
  e crawler usam a LabRole, recebida por variável.
- **Datas sujas**: o Spark 3 lança `SparkUpgradeException` com datas como
  `31/02/2025`. Resolvemos com `spark.sql.legacy.timeParserPolicy=CORRECTED`
  e um regex por formato antes do `to_date`, assim datas impossíveis viram
  null e vão para a quarentena.
- **Nulos disfarçados e `greatest()`**: no 1º teste, o atraso de itens sem
  prazo real saiu 0 e não null, porque `greatest()` ignora null. Isso
  inflaria a taxa de "no prazo". Corrigimos e passamos a impor que só os
  cancelados tenham atraso nulo.
- **Granularidade**: o CSV é por item, mas a logística é por pedido e a nota
  é por item. Verificamos na silver que transportadora, prazos e status não
  variam dentro do pedido, mas a nota varia. Por isso as métricas de entrega
  são calculadas por pedido e a relação atraso × nota, por item.
- **Categorias truncadas** (`Mod`, `Pe`, `Eletrônico`): em vez de um
  dicionário de erros, usamos o SKU como chave e o valor mais frequente por
  SKU, o que também preenche marca e fornecedor nulos.

## Próxima etapa (Aula 13)

- Quantificar os fatores do atraso: modelo (regressão logística / árvore no
  Spark MLlib ou Athena + Python) com `entregue_com_atraso` como alvo e
  região, CD, transportadora, mês, categoria e prazo estimado como
  variáveis.
- Medir o impacto do atraso na nota e na devolução, controlando por
  categoria e canal.
- Investigar se o pico de atraso em nov/dez é um gargalo de capacidade (volume
  × atraso por CD) e simular o efeito de aumentar o prazo estimado no
  Norte/Nordeste.
- Usar o `comentario` da silver (análise de sentimento/NLP, como na aula 8)
  para separar reclamações de entrega das de produto.
- Montar um dashboard (Athena/QuickSight ou Streamlit) sobre a gold.
