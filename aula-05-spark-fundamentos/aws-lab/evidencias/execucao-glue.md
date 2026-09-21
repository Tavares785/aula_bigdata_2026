# Evidência - Execução AWS Glue

## Job executado

- Serviço: AWS Glue
- Job: `job-aula05-wordcount`
- JobRunId: `jr_7f6fc62c4715bdf57688f088f39d166cbece570fe5011aa993b2e2a9230ec6d8`
- Região: `us-east-1`
- Status: `SUCCEEDED`
- Início: `21/09/2026 19:47:47 (-03:00)`
- Conclusão: `21/09/2026 19:49:33 (-03:00)`
- Duração aproximada: `1 minuto e 46 segundos`
- Data: `21/09/2026`

## Processamento

O job executou o processamento de Word Count utilizando RDDs do Spark.

O arquivo de entrada utilizado foi:

`s3://lab-aula05-glue-3925000-carollini/input/sample_lines.txt`

O resultado foi gravado em:

`s3://lab-aula05-glue-3925000-carollini/output/wordcount/`

Foram gerados 4 arquivos de saída:

- `part-00000`
- `part-00001`
- `part-00002`
- `part-00003`

## Principais resultados

| Palavra | Contagem |
|---|---:|
| o | 60 |
| a | 22 |
| e | 19 |
| pedido | 19 |
| cliente | 18 |
| entrega | 17 |
| do | 16 |
| produto | 16 |
| estoque | 14 |
| pagamento | 11 |

## Interpretação

O processamento de Word Count realizado com RDDs no AWS Glue mostrou que as palavras "o", "a", "e", "pedido" e "cliente" aparecem com maior frequência no conjunto de dados.

Os resultados também destacam termos relacionados às atividades de pedidos, entregas, produtos, estoque e pagamentos, indicando que esses assuntos possuem maior presença nos textos analisados.

## Resultado

A execução do AWS Glue foi concluída com sucesso (`SUCCEEDED`), demonstrando o funcionamento do processamento RDD no ambiente gerenciado do AWS Glue.
