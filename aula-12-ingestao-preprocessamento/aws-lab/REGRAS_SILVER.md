# Regras da camada silver — MercadoFácil (Aula 12)

Arquitetura medalhão: **raw** (CSV intacto em `s3://<bucket>/raw/`) → **silver** (Parquet
confiável em `silver/pedidos/`) + **quarentena** (`quarentena/pedidos/`, com a coluna
`motivo`) → **gold** (4 tabelas em `gold/`). A implementação está em `job/etl_medalhao.py`.

## Problemas encontrados no raw e regra aplicada

| # | Problema encontrado | Regra aplicada na silver |
|---|---|---|
| 1 | **200 linhas duplicadas** (mesmo `item_id` repetido, linhas idênticas) | Mantém a 1ª ocorrência por `item_id` (`row_number`); as demais vão para a quarentena com motivo `duplicado_item_id` |
| 2 | **Tokens de nulo variados**: `''`, `-`, `N/A`, `NULL`, `null` (segmento, CD, parcelas, datas, nota, comentário...) | Após `trim`, todos viram `null` real. Segmento nulo vira `nao_informado`; demais campos permanecem nulos |
| 3 | **Status em 13 grafias** (`entregue `, `DELIVERED`, `canceled`, `returned`...) | Normaliza (trim, minúsculas, sem acento) para `ENTREGUE`, `CANCELADO` ou `DEVOLVIDO`; valor desconhecido → quarentena `status_invalido` |
| 4 | **Canal, transportadora, segmento** com caixa/espaços diferentes (`APP`, `app `, `CORREIOS`) | `trim` + minúsculas (canal, segmento); `initcap` na transportadora; CD em maiúsculas |
| 5 | **Estado** como sigla minúscula, com espaços ou por extenso (`sp`, ` SP `, `São Paulo`) | Converte tudo para UF de 2 letras (mapa das 27 UFs); não reconhecido → quarentena `estado_invalido` |
| 6 | **Categoria** com caixa, sem acento e **truncada** (`ELETRÔNICOS`, `Eletronicos`, `Mod`, `Esport`, `Casa e Cozinh`) | Compara sem acento/caixa e casa por prefixo com as 8 categorias canônicas; sem correspondência → quarentena `categoria_invalida` |
| 7 | **Forma de pagamento** em 13 variações (`CREDITO`, `cartao credito`, `Cartão de Crédito`, `BOLETO BANCARIO`) | Padroniza em `PIX`, `BOLETO`, `CARTAO_CREDITO`, `CARTAO_DEBITO` |
| 8 | **Datas em 3 formatos** (`2025-09-02`, `02/03/2025`, `2025-10-25 03:31:53`) e o texto `ontem` | Interpreta ISO e `dd/MM/yyyy` (descartando a hora) para `date`. `data_pedido` ilegível (`ontem`) → quarentena `data_pedido_invalida`; `data_entrega`/cadastro ilegível → `null` |
| 9 | **Moeda como texto** (`R$ 1.234,56`, `49,24`, `49.24`) | Remove `R$`/espaços; se há vírgula, ela é o decimal e o ponto é milhar; converte para `double` |
| 10 | **Desconto** como `10%` ou `10`; ausente em ~3% | Remove `%`. Se ausente, infere pelo `valor_total` (`1 − total/(preço×qtd)`), marcando `flag_desconto_inferido`; fora de 0–100 → quarentena `desconto_invalido` |
| 11 | **Quantidade** nula, `0` ou negativa; preço nulo | Quantidade ≤ 0/nula → quarentena `quantidade_invalida`; preço nulo/≤ 0 → `preco_invalido` |
| 12 | **`valor_total`** negativo, nulo ou incoerente com preço × qtd × (1 − desconto) | Sinal invertido é corrigido (valor absoluto); nulo é recalculado (`flag_valor_total_imputado`); diferença > R$ 0,02 após isso → quarentena `valor_total_incoerente` |
| 13 | **Nota de avaliação** fora de 1–5 (`99`, `10`, `0`, `-1`) | Valor inválido vira `null` (a linha é mantida; a nota não entra nas médias) |
| 14 | **`atraso_dias`** incoerente com os prazos (156 linhas) e nulo em ~11% | Recalcula `max(0, prazo_real − prazo_estimado)`; sem prazo real, usa o `atraso_dias` informado (mín. 0). Pedido `CANCELADO` não tem entrega: prazo real, data de entrega e atraso ficam `null` |
| 15 | **Dados pessoais** (nome, e-mail — alguns sem `@` —, CPF) | **Removidos** da silver, da quarentena e da gold (minimização LGPD). O vínculo com o cliente é só o `cliente_id` (pseudônimo). O raw mantém os dados originais e deve ter acesso restrito (bucket privado, sem acesso público) |

## Quarentena

Nenhuma linha é descartada em silêncio: toda rejeição vai para `quarentena/pedidos/` com
as colunas originais (sem PII) e o `motivo`. O job imprime no log a contagem por motivo.

## Gold (perguntas de negócio)

| Tabela | Pergunta |
|---|---|
| `gold_atraso_por_estado_transportadora` | Onde e com qual transportadora o atraso é maior? |
| `gold_nota_por_faixa_atraso` | Qual a relação entre atraso e nota de avaliação? |
| `gold_cancelamento_por_categoria_canal` | Quais categorias/canais têm mais cancelamento e devolução? |
| `gold_vendas_mensal` | Como a sazonalidade (Black Friday, Natal) afeta vendas, cancelamento e atraso? |
