# Checkpoint de Progresso - Aula 12: Ingestão e Pré-processamento

## O que foi feito nesta etapa

Construí a infraestrutura em Terraform e o ETL PySpark que leva os pedidos da
camada raw até a silver, a quarentena e quatro tabelas gold. O ETL foi executado
localmente na imagem oficial do AWS Glue 4.0: das 10.000 linhas do raw, 9.754
foram para a silver e 246 para a quarentena.

Pendente: executar o pipeline no AWS Academy Learner Lab (apply, Glue Job,
Crawler, Athena e destroy) e anexar os prints à PR.

## Ferramentas efetivamente usadas

- **Terraform**: provisiona o Glue Database, o Glue Job e o Glue Crawler, e aciona a AWS CLI.
- **AWS CLI**: cria e remove o bucket S3 privado e envia o CSV e o script.
- **PySpark no Glue 4.0**: faz a limpeza, a quarentena e as agregações.
- **Docker**: roda a imagem do Glue 4.0 para testar o ETL localmente.
- **Glue Crawler e Athena**: catalogam e consultam as tabelas (scripts prontos em `aws-lab/scripts/`).
- **pytest**: faz a verificação estrutural da entrega.

## Dificuldades encontradas

- **Permissões do Learner Lab**: a SCP impede o uso de `aws_s3_bucket`, então o bucket é criado pela AWS CLI com `terraform_data`.
- **Qualidade dos dados**: a mesma informação aparece com muitas grafias e formatos. Resolvi com mapas de valores canônicos e reconstruí campos ausentes a partir de colunas relacionadas.
- **Validação das regras**: a conferência da saída mostrou que `cartao_credito` e `cartao_debito` estavam fora do mapa de pagamentos, o que enviava linhas válidas para a quarentena. Corrigi o mapa e repeti a execução.
- **Atraso de pedidos cancelados**: o `greatest` do Spark ignora nulos e geraria atraso 0 nesses pedidos. A regra agora só calcula o atraso quando existe prazo real.

## Próxima etapa (Aula 13)

Usar a camada gold para analisar os fatores ligados ao atraso, à nota baixa e às
devoluções. A partir da silver, pretendo construir um modelo que estime o risco
de atraso usando estado, transportadora, categoria, canal e período do ano.
