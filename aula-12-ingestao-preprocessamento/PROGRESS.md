# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

## O que foi feito nesta etapa

Emar Cristian Silva Teruo Ito — RA 6325192. Pipeline MercadoFácil provisionado e executado no Learner Lab: raw CSV, silver e quarentena em Parquet, duas tabelas gold, Glue Crawler e consultas Athena. JobRunId: `jr_189d701a6819fd60e66f715a8dcfb261f94d319b4c4307c8cda7694d5e0f0ccb`. Evidências reais em `aws-lab/evidencias/`. Terraform destroy concluído e state conferido vazio.

## Ferramentas efetivamente usadas

Terraform com AWS provider 5.31.0 e AWS CLI provisionaram S3 privado, Glue Job 4.0, Glue Catalog e Crawler. PySpark tratou o CSV, conciliou registros e gerou Parquet. Athena consultou as tabelas catalogadas. Pytest validou os requisitos estruturais.

## Dificuldades encontradas

A base textual e desnormalizada exigiu tipagem, tratamento de ausências, validação de domínios e deduplicação por chave composta. Dados pessoais diretos foram excluídos nas camadas posteriores. A LabRole existente foi utilizada para evitar criação de IAM. A contagem de ausências e chaves repetidas está na evidência perfil-raw.txt.

## Próxima etapa (Aula 13)

Explorar a gold para comparar atrasos por estado, categorias e meses, avaliar notas e investigar padrões sem contar itens como pedidos independentes.
