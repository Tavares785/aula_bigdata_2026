# Regras da Camada Silver — MercadoFácil

Documento as transformações aplicadas ao dado bruto (`raw/`) para gerar a
camada `silver/` confiável e padronizada.

## Problemas encontrados e regras aplicadas

| # | Problema encontrado no raw | Regra aplicada na silver |
|---|---|---|
| R01 | Strings com espaços extras e mistura de maiúsculas/minúsculas em colunas categóricas (`status_pedido`, `canal`, `categoria`, `estado`, `transportadora`, `forma_pagamento`, `cliente_segmento`) | `F.trim(F.lower(...))` em todas as colunas categóricas |
| R02 | Todas as colunas chegam como `string` no CSV, incluindo numéricas (`preco_unitario`, `quantidade`, `valor_total`, `atraso_dias`, `nota_avaliacao`, etc.) | Cast explícito para `double`, `int` conforme o domínio de cada coluna; valores não conversíveis resultam em `null` |
| R03 | Datas (`data_pedido`, `data_entrega`, `cliente_data_cadastro`) chegam como string em formato misto | `F.to_date(...)` com inferência automática de formato; strings inválidas viram `null` |
| R04 | Campos obrigatórios nulos ou vazios (`pedido_id`, `item_id`, `cliente_id`, `sku`, `preco_unitario`, `quantidade`, `valor_total`, etc.) — tornam a linha inutilizável | Linha enviada para **quarentena** com `motivo = campo_obrigatorio_nulo` |
| R05 | Valores negativos ou zero em `preco_unitario`, `quantidade` e `valor_total` (erros de digitação ou falhas de integração) | Linha enviada para **quarentena** com `motivo = valor_negativo_ou_zero` |
| R06 | Valores de `status_pedido` fora do domínio esperado (`entregue`, `cancelado`, `devolvido`, `em_transito`, `processando`) | Linha enviada para **quarentena** com `motivo = status_invalido` |
| R07 | Duplicatas de `(pedido_id, item_id)` — o dump pode conter reenvios do mesmo evento | `row_number()` sobre `(pedido_id, item_id)` ordenado por `data_pedido DESC`; mantém apenas a linha mais recente |
| R08 | Dados pessoais (`cliente_cpf`, `cliente_email`) presentes em claro, violando LGPD | Substituição por hash SHA-256 (`F.sha2(..., 256)`); o dado original não é armazenado na silver |
| R09 | Ausência de flag explícita de atraso para análise — `atraso_dias` existe mas não é booleano | Coluna derivada `atrasado` (`True` quando `atraso_dias > 0`) |
| R10 | Inconsistência entre `valor_total` (campo original) e o valor recalculado por `preco_unitario * quantidade * (1 - desconto_pct/100)` | Coluna derivada `valor_total_calculado` para auditoria; o campo original é mantido |

## Destino das linhas rejeitadas

Linhas que não passam nas regras R04, R05 ou R06 **não são descartadas em silêncio**:
vão para a área de quarentena em `s3://<bucket>/quarentena/pedidos_rejeitados/` (Parquet)
com a coluna `motivo_quarentena` indicando o primeiro problema encontrado.
