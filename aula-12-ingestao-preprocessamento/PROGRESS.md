# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

## O que foi feito nesta etapa

Construímos do zero o pipeline de dados da MercadoFácil na AWS usando Terraform
e PySpark. O pipeline cobre as três camadas da arquitetura medalhão:

- **raw (bronze)**: o CSV `pedidos_mercadofacil.csv` (10.000 linhas) é enviado
  para `s3://<bucket>/raw/` via Terraform sem nenhuma alteração.
- **silver**: o Glue Job lê o CSV, aplica 10 regras de qualidade documentadas em
  `REGRAS_SILVER.md` (padronização de strings, tipagem, deduplicação por
  `row_number`, quarentena de linhas inválidas e mascaramento de CPF/e-mail via
  SHA-256 para conformidade com a LGPD) e grava em Parquet em `s3://<bucket>/silver/`.
- **gold**: duas tabelas de negócio gravadas em Parquet em `s3://<bucket>/gold/`:
  1. `atraso_por_estado_categoria` — taxa e média de atraso por estado e categoria,
     para identificar onde os atrasos se concentram (Norte/Nordeste, Black Friday).
  2. `cancelamentos_devolucoes` — volume e valor perdido por mês, canal e categoria,
     para entender sazonalidade e canais problemáticos.

O Glue Crawler cataloga silver e gold no Glue Catalog (`db_mercadofacil`),
tornando as tabelas consultáveis via Athena.

## Ferramentas efetivamente usadas

- **Terraform** (provider AWS ~5.31): provisiona bucket via `terraform_data +
  local-exec` (AWS CLI), Glue Catalog Database, Glue Job e Glue Crawler.
- **AWS S3**: armazena raw, silver, gold, quarentena, scripts e arquivos temporários.
- **AWS Glue Job** (glueetl, Glue 4.0, PySpark): executa o ETL medalhão.
- **AWS Glue Crawler**: cataloga os dados Parquet da silver e gold.
- **AWS Athena**: consulta SQL sobre as tabelas catalogadas (gold).
- **PySpark**: transformações com DataFrame API, `Window`, `row_number`, `sha2`.

## Dificuldades encontradas

- O recurso `aws_s3_bucket` é bloqueado pelo SCP do Learner Lab
  (`GetBucketObjectLockConfiguration` negado): resolvido criando o bucket via
  `aws s3api create-bucket` dentro de um `terraform_data + local-exec`.
- A versão exata `5.31.0` do provider AWS não estava mais disponível no registry:
  resolvido usando o constraint `~> 5.31` (aceita patches da série 5.31.x).
- Credenciais do Learner Lab expiram a cada sessão: renovadas via
  "AWS Details → Show" e exportadas como variáveis de ambiente.

## Próxima etapa (Aula 13)

Na etapa de análise e modelagem, o grupo planeja:
- Treinar um modelo de Regressão Logística com Spark MLlib sobre a camada silver
  para prever `atrasado` a partir de features como `estado`, `categoria`,
  `transportadora`, `prazo_estimado_dias` e `canal`.
- Calcular métricas de acurácia, F1 e AUC-ROC para avaliar o modelo.
- Enriquecer a camada gold com uma tabela `previsao_atraso` contendo as
  predições e probabilidades por pedido.
- Gerar análises de sazonalidade (mês a mês) sobre cancelamentos e notas de
  avaliação para identificar o impacto da Black Friday e do Natal.
