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

## Como entregar

Uma PR por GRUPO. Veja o
[README principal](../README.md#como-entregar-um-lab).
