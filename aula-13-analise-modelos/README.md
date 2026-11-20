# Etapa do Projeto - Aula 13: Análise e Construção de Modelos

## Objetivo

Aplicar técnicas de análise de dados, Machine Learning ou NLP aos dados
pré-processados na Aula 12, usando Spark MLlib, Spark NLP ou outra
ferramenta relevante para o problema do seu grupo.

## O que o CI verifica (e o que não verifica)

Assim como na Aula 12, o CI **não executa** sua análise contra dados
reais — ele verifica apenas se `build_model_or_analysis` e
`summarize_results`, em `src/analise.py`, foram de fato implementadas, e
se o `PROGRESS.md` foi preenchido. A qualidade dos resultados é avaliada
pelo professor.

## O que você precisa fazer

1. Implemente `build_model_or_analysis` e `summarize_results` em
   `src/analise.py`.
2. Preencha o `PROGRESS.md` com a análise implementada, os resultados
   preliminares, os ajustes feitos e o plano para a Aula 14.

## Como rodar os testes localmente

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## Como rodar a análise (MercadoFácil, RAs 6325226, 6325149, 6325269)

A análise precisa de Spark 3.3 (a mesma versão do Glue 4.0) e de JDK 11. O
`pyspark` não está no `requirements.txt` porque o CI só verifica a
estrutura.

```bash
pip install pyspark==3.3.4
# A silver vem do ETL da Aula 12 (Glue ou local):
python src/analise.py --SILVER_PATH <.../silver/pedidos_itens> --OUTPUT_PATH resultados
```

A saída da última execução está em `resultados/`. Os resultados estão
discutidos no `PROGRESS.md`.

## Como entregar

Uma PR por GRUPO. Veja o
[README principal](../README.md#como-entregar-um-lab).
