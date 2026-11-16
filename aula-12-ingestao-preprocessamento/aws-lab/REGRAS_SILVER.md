# Regras da camada silver - MercadoFácil

Base de entrada: 10.000 linhas (1 linha = 1 item de pedido), todas como texto.
Resultado do ETL local: **9.509 linhas na silver** e **491 na quarentena**
(97 preço inválido, 52 data de pedido inválida, 149 quantidade inválida,
193 duplicados). A camada raw não é alterada.

## Problemas encontrados e regra aplicada

| # | Problema no raw | Regra aplicada na silver |
|---|---|---|
| 1 | **Duplicados**: 200 `item_id` repetidos (linhas idênticas) | Mantém 1 linha por `item_id` (`row_number`), escolhendo a mais completa. As demais vão para a quarentena com motivo `duplicado`. |
| 2 | **Datas em 3 formatos** (`yyyy-MM-dd`, `dd/MM/yyyy`, `yyyy-MM-dd HH:mm:ss`) e textos como `ontem` | Converte tudo para `date`. `data_pedido` que não converte vai para a quarentena (`data_pedido_invalida`). `data_entrega` inválida vira nula. |
| 3 | **Valores monetários em texto** (`R$ 1.234,56`, `49,24`, `49.24`) | Remove `R$` e separador de milhar, troca vírgula por ponto e converte para `double` (custo, preço e total). |
| 4 | **Status com grafias diferentes** (`DELIVERED`, `entregue `, `canceled`, `returned`) | Normaliza para 3 valores: `entregue`, `cancelado`, `devolvido`. Valor desconhecido vai para a quarentena. |
| 5 | **Caixa e espaços** em canal, segmento, transportadora e forma de pagamento (`APP`, `site `, `JADLOG`, `cartao credito`, `Cartão de Crédito`, `CREDITO`) | `trim` e minúsculas. Forma de pagamento mapeada para `cartao_credito`, `cartao_debito`, `pix`, `boleto`. Transportadora com `initcap`. |
| 6 | **Categorias, cidades, produtos e marcas inconsistentes**: caixa, acento perdido (`Eletronicos`), truncadas (`Mod`, `Esport`, `Casa e Cozinh`) e texto em maiúsculas com acento corrompido | Usa o valor mais frequente por `sku` (categoria, produto, marca, fornecedor) e por cidade sem acento e minúscula. Resultado: 8 categorias e 29 produtos. |
| 7 | **Estado** em minúsculas, com espaços ou por extenso (`São Paulo`, `Minas Gerais`) | Mapeia para a sigla da UF. Valor que não vira UF válida vai para a quarentena. |
| 8 | **Nulos disfarçados**: `N/A`, `NULL`, `null`, `-` e vazio | Todos viram nulo real. Segmento nulo vira `nao_informado`. Demais campos opcionais continuam nulos. |
| 9 | **Quantidade inválida** (`0`, `-1`, `-2`, nula) | Linha vai para a quarentena (`quantidade_invalida`). |
| 10 | **Preço inválido ou ausente** (texto como `erro`, `-`, vazio) | Linha vai para a quarentena (`preco_invalido`). |
| 11 | **Desconto** com `%` (`10%`) ou nulo | Remove `%` e converte para número. Nulo ou fora de 0 a 100 vira 0, com `flag_desconto_imputado = true`. |
| 12 | **`valor_total` inconsistente**: 243 linhas diferem de `preço x quantidade x (1 - desconto)` e outras vêm nulas | Recalcula o total quando difere em mais de R$ 0,02, ou quando está nulo, e marca `flag_valor_corrigido = true`. |
| 13 | **Nota de avaliação fora de 1 a 5** (`99`, `10`, `0`, `-1`) ou nula | Nota fora do intervalo vira nula. A linha continua na silver. |
| 14 | **Prazo real e atraso** em texto, nulos ou negativos (`-`, `N/A`, `-3`) | `atraso_dias` é recalculado como `max(prazo_real - prazo_estimado, 0)`. Se o prazo real falta, usa `data_entrega - data_pedido`. Sem nenhum dos dois fica nulo (ex.: cancelados). Cria a coluna `atrasado`. |
| 15 | **Parcelas** nulas ou em texto | Converte para inteiro. Nulo em pix, boleto ou débito vira 1. Nos demais casos fica nulo. |
| 16 | **Dados pessoais (LGPD)**: nome, e-mail e CPF, este com e sem máscara | A silver **não guarda** nome, e-mail nem CPF em claro. CPF (só dígitos) e e-mail (minúsculo) viram `SHA-256`. O nome é descartado. CPF com menos de 11 dígitos fica sem hash e com `cpf_valido = false`. Na quarentena, nome, e-mail e CPF também ficam com hash. |

## Quarentena

Linhas sem condição mínima de uso vão para `quarantine/pedidos_rejeitados/`
com todas as colunas originais (dados pessoais com hash) e a coluna `motivo`.
Nada é descartado em silêncio.

## Particionamento e tabelas

- Silver: `silver/pedidos_itens/` (Parquet).
- Gold: `gold/atraso_por_estado_transportadora/`, `gold/nota_por_faixa_atraso/`
  e `gold/vendas_mensais_categoria/` (Parquet).
- Calculadas sobre itens `entregue` e `devolvido` com atraso conhecido: as duas
  primeiras. A terceira usa todos os status.
