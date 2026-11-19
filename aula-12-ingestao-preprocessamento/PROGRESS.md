# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## O que foi feito nesta etapa

Construímos do zero o pipeline de dados na AWS Academy usando Terraform e PySpark (Glue),
cobrindo as três camadas da arquitetura medalhão:

- **Raw (bronze):** o CSV `pedidos_mercadofacil.csv` (10.000 linhas) é carregado no S3
  sem nenhuma alteração, preservando o dado original como chegou.

- **Silver:** o Glue Job lê o CSV da camada raw e aplica 8 regras de limpeza documentadas
  em `REGRAS_SILVER.md` (normalização de datas, valores monetários, status do pedido,
  UF/cidade, pseudonimização de CPF via SHA-256 por LGPD, tratamento de nulos sentinela,
  deduplicação e validação de desconto). Linhas inválidas são separadas para uma área de
  quarentena (Parquet) com a coluna `motivo_quarentena`. Os dados aprovados são gravados
  em Parquet particionado por `estado`.

- **Gold:** três tabelas de negócio prontas para consumo no Athena:
  1. `atrasos_por_transportadora_estado` — % de entregas atrasadas e média de atraso por
     transportadora e UF, cruzado com nota de avaliação.
  2. `cancelamentos_devolucoes_por_categoria_canal` — taxa de cancelamento/devolução por
     categoria de produto e canal de venda, com valor total perdido.
  3. `sazonalidade_mensal` — volume de pedidos, receita, atraso médio e nota por mês,
     permitindo visualizar o impacto de Black Friday (nov) e Natal (dez).

A infraestrutura é provisionada inteiramente via Terraform: bucket S3 criado por AWS CLI
(`terraform_data` + `local-exec`), upload do CSV e do script ETL, Glue Catalog Database,
Glue Job (glueetl, Glue 4.0) e Glue Crawler apontando para silver e gold.

## Ferramentas efetivamente usadas

| Ferramenta / Serviço | Uso |
|---|---|
| **Terraform (5.31.0)** | Provisionar toda a infraestrutura AWS como código |
| **AWS CLI** | Criar e destruir o bucket S3 via `local-exec` (restrição do Learner Lab) |
| **Amazon S3** | Armazenar as camadas raw, silver, gold e quarentena em Parquet |
| **AWS Glue Job (PySpark, Glue 4.0)** | Executar o ETL raw → silver → gold |
| **AWS Glue Crawler** | Catalogar automaticamente os dados do S3 no Glue Catalog |
| **AWS Glue Catalog** | Registrar o banco de dados e as tabelas para consulta |
| **Amazon Athena** | Consultar as tabelas gold via SQL diretamente sobre o S3 |
| **PySpark** | Limpeza, tipagem, deduplicação, pseudonimização e agregações de negócio |

## Dificuldades encontradas

- **Qualidade dos dados:** o CSV continha múltiplos formatos de data, valores monetários
  com prefixo "R$" e vírgula decimal, sentinelas de nulo (`N/A`, `-`, `NULL`) espalhados
  por colunas diferentes e status do pedido em inglês e português com capitalização mista.
  Foram necessárias 8 regras de limpeza documentadas.

- **Restrições do Learner Lab:** o recurso `aws_s3_bucket` do Terraform não pode ser usado
  diretamente; a solução foi criar o bucket via `terraform_data` + `local-exec` com AWS CLI.
  Roles e policies IAM também são bloqueadas — usamos a LabRole existente por ARN.

- **LGPD:** o CPF é dado sensível e não pode ser armazenado em texto puro. Implementamos
  pseudonimização via hash SHA-256 (UDF PySpark), descartando a coluna original.

- **Credenciais temporárias:** as credenciais do Learner Lab expiram a cada 4 horas,
  exigindo reexportação das variáveis de ambiente antes de cada `terraform apply` ou
  execução de script AWS CLI.

## Próxima etapa (Aula 13)

Na etapa de análise e modelagem, o grupo planeja:

- Conectar o Athena a uma ferramenta de visualização (ex: Amazon QuickSight ou notebook
  local via PyAthena) para explorar as tabelas gold.
- Aprofundar a análise de atrasos: identificar padrões por região (Norte/Nordeste) e
  período sazonal (nov/dez) usando as tabelas `atrasos_por_transportadora_estado` e
  `sazonalidade_mensal`.
- Investigar a correlação entre atraso e nota de avaliação, e entre categoria de produto
  e taxa de devolução.
- Avaliar se é possível construir um modelo preditivo simples (ex: regressão logística)
  para prever risco de atraso com base em transportadora, estado, categoria e mês.
