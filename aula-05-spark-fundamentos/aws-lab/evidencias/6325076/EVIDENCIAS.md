# Evidências — Aula 05 — Spark Fundamentals com AWS Glue

**RA:** 6325076
**Aluno:** Pablo Augusto Ramos Sobral
**Disciplina:** Big Data
**Laboratório:** Spark Fundamentals — AWS Glue

## Execução

- Região: us-east-1
- Bucket S3: lab-aula05-glue-6325076-pablo-20260925
- Glue Job: job-aula05-wordcount
- JobRunId: jr_f74aea5bc34ba84705799525c50f25ccc3d4686d2ac1960a197b0b77331a3aa9
- Status: SUCCEEDED

## Processamento RDD

O job utilizou Apache Spark com RDDs, incluindo parallelize, flatMap, map, reduceByKey e collect.

## Resultado

O resultado foi gravado no S3 em:
s3://lab-aula05-glue-6325076-pablo-20260925/output/wordcount/

Arquivo gerado:

part-00000-0ded4601-bd72-41dd-a456-77b72d324661-c000.csv

## Principais resultados

palavra,contagem

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

## Conclusão

O laboratório foi executado com sucesso no AWS Glue utilizando Apache Spark e RDDs. O job terminou com status SUCCEEDED e o resultado do Word Count foi persistido no Amazon S3.
