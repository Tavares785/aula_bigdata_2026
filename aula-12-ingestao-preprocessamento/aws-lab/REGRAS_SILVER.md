# REGRAS_SILVER - MercadoFacil (Aula 12)

Problemas de qualidade encontrados no dump raw de `pedidos_mercadofacil.csv`
(10.000 linhas, todas as colunas texto) e a regra aplicada em cada um na
camada **silver**. Linhas irrecuperáveis vão para a área de **quarentena**
(`quarentena/`, em Parquet, com a coluna `motivo`) — nada é descartado em
silêncio.

## Problemas encontrados e regras aplicadas

| # | Problema no raw | Exemplo observado | Regra aplicada na silver |
|---|---|---|---|
| 1 | Datas em dois formatos diferentes | `02/03/2025` e `2025-09-02` na mesma coluna | `coalesce(to_date(...,'dd/MM/yyyy'), to_date(...,'yyyy-MM-dd'))` → date ISO; não-parseável vai para quarentena (`data_pedido_invalida_ou_ausente`) |
| 2 | Moeda e separador decimal mistos | `R$ 49,24`, `91,67`, `47.60`, `-` | strip de `R$`/espaços, vírgula→ponto, cast `double`; `-` → null |
| 3 | Sentinelas de ausência (`-`, `N/A`) | `valor_total=-`, `nota_avaliacao=N/A` | cast com filtro explícito (`isin("-","N/A","")` → null); `valor_total` nulo em pedido `entregue` vai para quarentena |
| 4 | `status_pedido` inconsistente (caixa/idioma) | `entregue`, `ENTREGUE`, `DELIVERED` | lowercase/trim + mapa para enum canônica: `entregue`, `cancelado`, `devolvido`, `enviado`, `processando` |
| 5 | `forma_pagamento` sem padronização | `cartao credito`, `BOLETO BANCARIO`, `PIX` | lowercase + normalização para enum: `cartao_credito`, `cartao_debito`, `pix`, `boleto` |
| 6 | PII em texto puro (nome, e-mail, CPF) | `Vitor Araújo Santos`, `737.295.450-38` | **LGPD**: pseudonimização com `sha2(...,256)` — raw de nome/e-mail/CPF não sai da silver, só os hashes |
| 7 | Dados de pedido/cliente repetidos por item (1 linha = 1 item) | mesmo `pedido_id` em N linhas | dedup por chave natural `(pedido_id, item_id)` via `row_number` + `dropDuplicates` |
| 8 | Comentario com `N/A`/vazio | `N/A`, string vazia | `nullif(trim(...), 'N/A')` → null |

## Decisões adicionais

- **Quarentena em vez de descarte:** qualquer linha sem chave
  (`pedido_id`/`item_id`), sem `data_pedido` válida, com quantidade nula/≤ 0
  ou com `valor_total` inválido estando `entregue` é gravada em
  `quarentena/` com o `motivo` — audível no Athena pelo Crawler.
- **Categorias/estados/logística:** `initcap`/`upper`/trim para remover
  ruído de caixa e espaços (`categoria_v`, `estado_v`, `transportadora_v`,
  `centro_distribuicao_v`).
- **Campos numéricos de logística** (`prazo_*`, `atraso_dias`, `parcelas`):
  cast `int` com `-`/`N/A` → null, para permitir agregações com estatísticas.
