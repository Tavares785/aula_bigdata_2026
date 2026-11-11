# Etapa do Projeto - Aula 11: Definição e Planejamento

## Cenário: MercadoFácil (e-commerce)

A **MercadoFácil** é um e-commerce brasileiro de médio porte que vende
pelo app, pelo site e por parceiros de marketplace. Em 2025 a diretoria
notou três sintomas:

- aumento de **atrasos nas entregas**, principalmente no Norte/Nordeste
  e em novembro/dezembro;
- **avaliações baixas** e comentários negativos concentrados em pedidos
  atrasados;
- **cancelamentos e devoluções** acima da meta, sem saber quais
  categorias, canais ou regiões mais pesam.

Vocês são o time de dados contratado para **planejar um projeto de Big
Data** que ajude a diretoria a entender e reduzir esses problemas. Ao
longo das Aulas 12 a 14, o grupo vai implementar o que planejar aqui.

Exemplos de perguntas que o projeto pode responder (escolham as suas):

- Quais fatores mais explicam o atraso na entrega? Dá para **prever**
  pedidos com risco de atraso (MLlib)?
- Qual a relação entre atraso e nota de avaliação? O que os comentários
  negativos dizem (NLP / análise de sentimento)?
- Quais categorias, canais e estados têm mais cancelamento/devolução?
- Como a sazonalidade (Black Friday, Natal) afeta vendas e logística?
- Como seria uma versão em **streaming** para alertar atrasos em tempo
  real (Kafka + Spark Streaming)?

## A base de dados (RAW, 10.000 linhas)

`data/pedidos_mercadofacil.csv` é um **dump bruto e desnormalizado** dos
sistemas da MercadoFácil (ano de 2025) e é o **único material fornecido**.
Uma única tabela traz juntos: pedido, **cliente**, **produto/fornecedor**,
pagamento, **logística** e **avaliação**. 1 linha = 1 item de pedido; um
pedido pode ter vários itens, e os dados do pedido e do cliente se repetem
em cada item.

Colunas (todas chegam como texto):

| Grupo | Colunas |
|---|---|
| Pedido | `pedido_id`, `item_id`, `data_pedido`, `status_pedido`, `canal` |
| Cliente | `cliente_id`, `cliente_nome`, `cliente_email`, `cliente_cpf`, `cliente_segmento`, `cliente_data_cadastro` |
| Entrega (destino) | `estado`, `cidade` |
| Produto | `categoria`, `sku`, `produto`, `marca`, `fornecedor`, `custo_unitario` |
| Valores | `preco_unitario`, `quantidade`, `desconto_pct`, `valor_total` |
| Pagamento | `forma_pagamento`, `parcelas` |
| Logística | `transportadora`, `centro_distribuicao`, `prazo_estimado_dias`, `prazo_real_dias`, `data_entrega`, `atraso_dias` |
| Avaliação | `nota_avaliacao` (1 a 5), `comentario` |

**Atenção: a base é suja de propósito**, como um dado real que acabou de
chegar. Explorá-la, descobrir os problemas de qualidade e decidir como
tratá-los faz parte do trabalho (e dos critérios de avaliação). Há dados
pessoais fictícios (nome, e-mail, CPF): pensem em **LGPD** ao levá-los para
as camadas seguintes.

## Missão de hoje: construir o pipeline na AWS Academy via Terraform

Não há cronograma: **hoje** o grupo precisa **construir, do zero**, e ter
**executado** no AWS Academy Learner Lab o pipeline da MercadoFácil, usando
**Terraform**. A única coisa fornecida é a base `data/pedidos_mercadofacil.csv`
(10.000 linhas); toda a infra, o código do ETL e os scripts são do grupo.

Crie tudo dentro de `aws-lab/` (a pasta já tem um `.gitignore` que protege
`*.tfvars`, estado e credenciais):

```
aws-lab/
  infra/    -> arquivos .tf (Terraform)
  job/      -> script PySpark do Glue
  scripts/  -> scripts para rodar/consultar (opcional)
```

### Arquitetura alvo

```
S3 raw/ (CSV) -> Glue Job (PySpark) -> S3 silver/ + gold/ (Parquet)
                                          -> Glue Crawler/Catalog -> Athena
```

### Requisitos (o CI verifica os de Terraform)

Terraform (`aws-lab/infra/`):
1. Provider `aws` na região `us-east-1`, versão do provider **fixada em `5.31.0`**.
2. **Bucket S3 privado criado via AWS CLI** (`terraform_data` + `local-exec`,
   com `destroy` que o esvazia/remove). **Não use o recurso `aws_s3_bucket`**.
3. O próprio Terraform envia o CSV para `raw/` e o script do ETL para `scripts/`.
4. Um `aws_glue_catalog_database`.
5. Um `aws_glue_job` (`glueetl`, Glue 4.0) usando a **LabRole** por ARN, com o
   script no S3 e os caminhos de entrada/saída passados como argumentos.
6. Um `aws_glue_crawler` com `s3_target` apontando para os dados gerados.
7. Pelo menos 3 `output`s úteis, variáveis para o que muda por aluno (ARN da
   LabRole, nome do bucket) e **nenhum segredo versionado**.
8. **Não crie roles/policies IAM** (o Learner Lab bloqueia): use a LabRole.
9. `terraform fmt -check` e `terraform validate` passam.

ETL (`aws-lab/job/`), PySpark rodando no Glue, em **arquitetura medalhão**:
- **raw (bronze)**: o CSV exatamente como chega, sem alterações;
- **silver**: dado confiável e padronizado (Parquet). O grupo decide e
  **documenta** as regras de limpeza, tipagem, deduplicação, padronização de
  categorias/códigos, tratamento de nulos e de valores inválidos, e o que fazer
  com dados pessoais. Linhas que não puderem ser aproveitadas devem ir para uma
  área de **quarentena** (com o motivo), e não ser descartadas em silêncio;
- **gold**: tabelas de negócio prontas para consumo, com **pelo menos duas
  tabelas** que respondam às perguntas de negócio escolhidas pelo grupo.

Execução e consulta:
- rodar o Glue Job até `SUCCEEDED`, rodar o Crawler e **consultar as tabelas no
  Athena** (console ou CLI);
- terminar com `terraform destroy`.

### Dicas do Learner Lab

- Credenciais: **AWS Details → Show**, via variáveis de ambiente
  (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`); elas expiram.
- ARN da LabRole: `aws iam get-role --role-name LabRole --query Role.Arn --output text`.
- Nome de bucket S3 é global: inclua o identificador do grupo.
- O EMR Serverless é bloqueado; o Spark gerenciado que funciona é o **Glue**.
- A escrita Spark no S3 falha/duplica se o prefixo de saída já existe: limpe o
  prefixo antes de rodar de novo.
- Logs do job: CloudWatch `/aws-glue/jobs/output` e `/aws-glue/jobs/error`.
- Documentação dos recursos (provider 5.31.0):
  [`aws_glue_job`](https://registry.terraform.io/providers/hashicorp/aws/5.31.0/docs/resources/glue_job),
  [`aws_glue_crawler`](https://registry.terraform.io/providers/hashicorp/aws/5.31.0/docs/resources/glue_crawler),
  [`aws_glue_catalog_database`](https://registry.terraform.io/providers/hashicorp/aws/5.31.0/docs/resources/glue_catalog_database).

## Proposta do projeto

O cenário e o dataset são **os mesmos para todos**, mas **não há resposta
certa** para a proposta: cada grupo escolhe qual(is) pergunta(s) de negócio
atacar e como evoluir o pipeline nas Aulas 12 a 14. Edite
`PROJECT_PROPOSAL.md`, substituindo cada `<PREENCHER: ...>` nas seções:

- Integrantes do Grupo
- Problema
- Objetivos
- Dataset(s) e Fonte
- Ferramentas de Big Data
- Arquitetura do Pipeline (o que vocês provisionaram hoje)

**Não apague os títulos das seções** (as linhas com `##`) — o CI usa eles.

## Correção automática (CI)

O CI verifica a **conformidade estrutural**, não a "resposta certa":

- a proposta está preenchida (sem `<PREENCHER>` e com conteúdo mínimo);
- a infra Terraform tem provider `us-east-1`, bucket via AWS CLI, upload do CSV,
  Glue database, Glue Job (`glueetl` + role), Glue Crawler com `s3_target` e
  pelo menos 3 outputs;
- não há `aws_s3_bucket` nem roles/policies IAM;
- `terraform fmt -check` e `terraform validate` passam.

O CI **não acessa a AWS**: a execução real (apply + job + Athena) é conferida
pelo professor.

## O que entregar

- `PROJECT_PROPOSAL.md` preenchido;
- `aws-lab/infra/*.tf`, `aws-lab/job/` e `aws-lab/scripts/` (o que o grupo construiu);
- `aws-lab/REGRAS_SILVER.md`: lista dos problemas de qualidade encontrados no raw e da regra aplicada em cada um;
- prints para o professor: `terraform apply` concluído (Apply complete), Glue
  Job `SUCCEEDED` com o `JobRunId`, saída do `ver_resultado.sh` e
  `terraform destroy` concluído. **Mascare credenciais nos prints.**

## Como rodar os testes localmente

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

(os testes de Terraform falham até os TODOs serem completados)

## Como entregar a PR

Cada GRUPO faz UMA PR (não uma por pessoa). Veja o
[README principal](../README.md#como-entregar-um-lab) para o fluxo de
fork → branch → PR, e coloque o nome de todos os integrantes no título
ou na descrição da PR.
