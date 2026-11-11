# Etapa do Projeto - Aula 12: Ingestão e Pré-processamento (Terraform na AWS)

## Cenário

A **MercadoFácil** é um e-commerce brasileiro de médio porte que vende pelo
app, pelo site e por parceiros de marketplace. Em 2025 a diretoria notou
**atrasos nas entregas** (principalmente no Norte/Nordeste e em nov/dez),
**avaliações baixas** concentradas em pedidos atrasados e **cancelamentos e
devoluções** acima da meta. O grupo é o time de dados contratado para
entender e reduzir esses problemas. Hoje vocês
**constroem, do zero, o pipeline de dados na AWS Academy usando Terraform**,
levando o dado da camada **raw** até a camada **gold**.

Exemplos de perguntas que a gold pode ajudar a responder: quais fatores mais
explicam o atraso? qual a relação entre atraso e nota? quais categorias,
canais e estados têm mais cancelamento/devolução? como a sazonalidade
(Black Friday, Natal) afeta vendas e logística?

## O que é fornecido (e só isso)

`data/pedidos_mercadofacil.csv`: **10.000 linhas**, um **dump bruto e
desnormalizado** (1 linha = 1 item de pedido). Uma única tabela traz pedido,
cliente, produto/fornecedor, pagamento, logística e avaliação; os dados do
pedido e do cliente se repetem em cada item. Todas as colunas chegam como texto.

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

**A base é suja de propósito**, como um dado real recém-chegado. Explorá-la,
descobrir os problemas de qualidade e decidir como tratá-los faz parte do
trabalho. Há dados pessoais fictícios (nome, e-mail, CPF): pensem em **LGPD**.

## Missão de hoje

Não há cronograma: **hoje** o grupo precisa ter o pipeline **provisionado e
executado** no AWS Academy Learner Lab. Toda a infra, o código do ETL e os
scripts são do grupo. Crie tudo dentro de `aws-lab/` (a pasta já tem um
`.gitignore` que protege `*.tfvars`, estado do Terraform e credenciais):

```
aws-lab/
  infra/            -> arquivos .tf (Terraform)
  job/              -> script PySpark do Glue
  scripts/          -> scripts para rodar/consultar (opcional)
  REGRAS_SILVER.md  -> problemas encontrados no raw e a regra aplicada em cada um
```

### Arquitetura alvo

```
S3 raw/ (CSV) -> Glue Job (PySpark) -> S3 silver/ + gold/ (Parquet)
                                          -> Glue Crawler/Catalog -> Athena
```

### Requisitos (o CI verifica os estruturais)

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
  **documenta** (em `REGRAS_SILVER.md`) as regras de limpeza, tipagem,
  deduplicação, padronização de categorias/códigos, tratamento de nulos e de
  valores inválidos, e o que fazer com dados pessoais. Linhas que não puderem
  ser aproveitadas devem ir para uma área de **quarentena** (com o motivo), e
  não ser descartadas em silêncio;
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

## Correção automática (CI)

O CI **não acessa a AWS** e verifica só a estrutura:

- infra Terraform: provider `us-east-1`, bucket via AWS CLI, upload do CSV,
  Glue database, Glue Job (`glueetl` + role), Glue Crawler com `s3_target` e
  pelo menos 3 outputs; sem `aws_s3_bucket` nem roles/policies IAM;
- `terraform fmt -check` e `terraform validate`;
- o ETL em `aws-lab/job/` é PySpark, lê CSV, grava Parquet em silver e gold e
  trata duplicados;
- `aws-lab/REGRAS_SILVER.md` lista pelo menos 6 problemas e regras;
- `PROGRESS.md` preenchido.

A execução real (apply + job + Athena) e a qualidade das regras são avaliadas
pelo professor na revisão da PR.

## O que entregar

- `aws-lab/infra/*.tf`, `aws-lab/job/`, `aws-lab/scripts/` e `aws-lab/REGRAS_SILVER.md`;
- `PROGRESS.md` preenchido;
- prints para o professor: `terraform apply` concluído, Glue Job `SUCCEEDED`
  com o `JobRunId`, uma consulta do Athena na gold e `terraform destroy`
  concluído. **Mascare credenciais nos prints.**

## Como rodar os testes localmente

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

(os testes falham até o grupo construir a infra, o ETL e a documentação)

## Como entregar

Uma PR por GRUPO. Veja o
[README principal](../README.md#como-entregar-um-lab).
