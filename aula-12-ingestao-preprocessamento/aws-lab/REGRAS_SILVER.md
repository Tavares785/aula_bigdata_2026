# Regras da camada silver - MercadoFácil

O raw tem 10.000 linhas. Depois do ETL, **9.754 linhas vão para a silver** e
**246 vão para a quarentena**. O job falha se a soma das duas não fechar com o raw.

## Problemas encontrados e regra aplicada

| # | Coluna(s) | Problema no raw | Regra na silver |
|---|---|---|---|
| 1 | linha inteira | 200 linhas repetidas com o mesmo `item_id` | Mantém a primeira ocorrência (`row_number`) e envia as demais à quarentena |
| 2 | várias | Ausência escrita como vazio, `-`, `N/A`, `NULL`, `null` | Converte todos os marcadores para nulo |
| 3 | texto em geral | Espaços nas pontas (`' SP '`, `'entregue '`) | Remove os espaços antes de comparar |
| 4 | `data_pedido` | Três formatos e 48 datas impossíveis (`ontem`, `0000-00-00`, `31/02/2025`, `2025-13-45`) | Converte para `date`. Data inválida herda a de outro item do pedido; sem referência, vai à quarentena |
| 5 | `custo_unitario`, `preco_unitario`, `valor_total` | Formatos `99.90`, `99,90`, `R$ 1.234,56` | Converte para `decimal(12,2)` |
| 6 | `preco_unitario` | Valor ausente | Deriva de total, quantidade e desconto, aceitando só de 1,2 a 2,5 vezes o custo. Fora disso, vai à quarentena |
| 7 | `quantidade` | Ausente, zero ou negativa | Deriva do total se resultar em inteiro de 1 a 4. Caso contrário, vai à quarentena |
| 8 | `desconto_pct` | Com e sem `%`, ou ausente | Mantém o domínio 0, 5, 10, 15, 20, 30 e 40. Valor ausente é derivado do total; se sair do domínio, vai à quarentena |
| 9 | `valor_total` | Negativo, ausente ou diferente de preço x quantidade x (1 - desconto) | Recalcula pela fórmula e marca `valor_total_recalculado` |
| 10 | `categoria` | 34 grafias (caixa, sem acento, truncadas como `Mod` e `Pe`) | Padroniza em 8 categorias |
| 11 | `status_pedido` | 13 grafias, em português e inglês | Padroniza em `entregue`, `cancelado` e `devolvido` |
| 12 | `forma_pagamento` | 13 grafias | Padroniza em `cartao_credito`, `cartao_debito`, `pix` e `boleto` |
| 13 | `canal`, `transportadora` | 12 grafias em cada coluna | Padroniza em 3 canais e 4 transportadoras |
| 14 | `estado`, `cidade` | 44 grafias de estado (sigla e nome) e 75 de cidade | Padroniza em 11 UFs e 23 cidades, e cria a coluna `regiao` |
| 15 | `cliente_segmento` | Caixa variada e valores ausentes | Usa o segmento conhecido do mesmo cliente. Sem nenhum registro, grava `nao_informado` |
| 16 | `produto`, `marca`, `fornecedor` | Caixa variada e valores ausentes | Usa o valor conhecido do mesmo `sku` |
| 17 | `centro_distribuicao` | Valores ausentes | Preenche pela UF, pois cada UF é atendida por um único CD |
| 18 | `parcelas` | Valores ausentes | Usa outro item do pedido. Pagamento que não é crédito recebe 1; crédito sem referência fica nulo |
| 19 | `data_entrega`, `prazo_real_dias` | Formatos variados, datas inválidas e ausências | Um campo é reconstruído a partir do outro. Pedido cancelado fica sem dados de entrega |
| 20 | `atraso_dias` | Negativo, ausente ou incoerente com os prazos | Recalcula como `max(prazo_real - prazo_estimado, 0)` |
| 21 | `nota_avaliacao` | Fora da escala (`99`, `10`, `0`, `-1`) | Troca por nulo e marca `nota_invalida_removida`, sem descartar a venda |

## Quarentena

As linhas rejeitadas ficam em `quarentena/itens_rejeitados/`, com o conteúdo
original e a coluna `motivo_quarentena`. Uma linha pode ter mais de um motivo,
separados por `;`.

| Motivo | Linhas |
|---|---:|
| `duplicado_item_id` | 200 |
| `data_pedido_invalida` | 24 |
| `desconto_irrecuperavel` | 6 |
| `quantidade_irrecuperavel;desconto_irrecuperavel` | 5 |
| `quantidade_irrecuperavel` | 4 |
| `preco_irrecuperavel;quantidade_irrecuperavel` | 3 |
| `preco_irrecuperavel` | 2 |
| `preco_irrecuperavel;desconto_irrecuperavel` | 2 |

## Rastreabilidade

A coluna `qualidade_flags` indica o que foi alterado em cada linha da silver.

| Flag | Linhas |
|---|---:|
| `atraso_recalculado` | 595 |
| `valor_total_recalculado` | 288 |
| `desconto_derivado` | 283 |
| `quantidade_derivada` | 136 |
| `preco_derivado` | 92 |
| `nota_invalida_removida` | 57 |
| `logistica_incompleta` | 2 |

## Dados pessoais (LGPD)

- `cliente_nome`, `cliente_email` e `cliente_cpf` não entram na silver, na gold nem na quarentena, porque as análises não precisam deles.
- `cliente_id` é substituído por `cliente_hash`, um SHA-256 com salt, que permite contar clientes sem identificá-los.
- O salt é informado na execução por `TF_VAR_lgpd_salt` e não fica versionado.
- O CSV original só existe em `raw/`, no bucket privado, que é removido no `terraform destroy`.
