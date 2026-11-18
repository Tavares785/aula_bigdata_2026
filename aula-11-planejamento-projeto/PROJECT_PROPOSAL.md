# Proposta de Projeto de Big Data

> Preencha cada seção abaixo, substituindo o texto `<PREENCHER>` pelo
> conteúdo real do seu grupo. Não remova os títulos das seções (as
> linhas que começam com `##`).

## Integrantes do Grupo

David Gilmour Souza - RA 1524681

## Problema

O monitoramento de indicadores macroeconômicos (inflação oficial pelo IPCA
e taxa básica de juros pela Selic) é essencial para análises financeiras,
planejamento orçamentário e projeções de mercado. O dado chega de fontes
oficiais com formatos e granularidades diferentes — Selic é diária e IPCA é
mensal — o que dificulta a visualização cruzada e o acompanhamento em uma
única visão. Este projeto investiga como construir um pipeline de
engenharia de dados que canonicalize esses fluxos em camadas estruturadas,
disponibilizando métricas prontas para análise e dashboards.

## Objetivos

1. **Consumo automatizado:** consumir as séries da API do BCB (SGS) sem
   intervenção manual, com janela de 10 anos e reexecução idempotente.
2. **Padronização e qualidade:** normalizar datas (`DD/MM/AAAA` → `datetime`),
   tipos numéricos, tratar nulos e outliers, e manter um `gold` com a chave
   canônica (periodo, serie) para consulta direta.
3. **Agregação analítica:** gerar datasets prontos para dashboards —
   `ipca_yoy_monthly.csv`, `selic_daily.csv`, `macro_monthly_snapshot.parquet` —
   com métricas de cobertura e frescura definidas.
4. **Preparação para análise e modelagem (Aulas 13 e 14):** expor uma feature
   matrix limpa (lags, rolling stats, spread IPCA/Selic) no `gold`, pronta para
   análise robusta (Aula 13) e visualização corporativa (Aula 14).
5. **Reprodutibilidade:** pipeline parametrizável via CLI, com testes de smoke
   (resposta mockada) e metadados de execução no `gold`.

## Dataset(s) e Fonte

- **Fonte Oficial:** API de Séries Temporais do Banco Central do Brasil (BCB)
  / SGS (Sistema de Gerenciamento de Séries Temporais),
  `https://api.bcb.gov.br/`.
- **Endpoints:**
  - Taxa Selic Diária (Série 432): `https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial=17/11/2016&dataFinal=17/11/2026`
  - IPCA Mensal (Série 433): `https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json`
- **Volume e formato:** JSON por requisição GET; janela máxima de 10 anos por
  requisição; dados de até 10 anos, atualizados conforme o dia útil.

## Ferramentas de Big Data

| Ferramenta | Uso no projeto | Por que faz sentido |
|---|---|---|
| Python + requests/pandas | Ingestão e limpeza das séries | Coleta confiável de APIs REST, padrão de script de ETL |
| Apache Spark / PySpark | Transformação em camadas Bronze → Silver → Gold | Processamento em massa, conversão de tipos, agregações em janela |
| CSV/Parquet em camadas | Armazenamento do data lake | Separa os dados brutos da transformação e da entrega |
| Spark SQL | Consultas de diagnóstico no `silver` | Abstração SQL sobre tabelas temporárias no Spark |

## Cronograma

| Etapa | Prazo estimado | Entregável |
|---|---|---|
| 1 - Definição e exploração | Semana 1 | Proposta + teste de conexão com a BCB |
| 2 - Ingestão e limpeza (Bronze → Silver) | Semana 2 | Tabelas de bronze/silver com schema validado |
| 3 - Agregação e entrega (Silver → Gold) | Semana 3 | Datasets finais + métricas de cobertura |
| 4 - Validação automática | Semana 4 | `pytest -v` passando (CI) |
| 5 - Revisão cruzada com Aulas 12–14 | Semana 5 | Documentação do pipeline para as próximas fases |
