# Regras da Camada Silver — MercadoFácil

Documento que descreve cada problema de qualidade encontrado no CSV bruto
(`data/pedidos_mercadofacil.csv`) e a regra de tratamento aplicada na camada
silver pelo ETL PySpark.

---

## Tabela de Problemas e Regras

| # | Coluna(s) afetada(s) | Problema encontrado | Exemplos no raw | Regra aplicada na silver |
|---|---|---|---|---|
| 1 | `data_pedido`, `cliente_data_cadastro`, `data_entrega` | **Formatos de data mistos** — três padrões diferentes convivem no mesmo campo: `dd/MM/yyyy`, `yyyy-MM-dd` e `yyyy-MM-dd HH:mm:ss`. | `02/03/2025`, `2025-09-02`, `2025-12-28 05:35:49` | Tentativa sequencial com `coalesce(to_date(..., 'dd/MM/yyyy'), to_date(..., 'yyyy-MM-dd'), to_date(..., 'yyyy-MM-dd HH:mm:ss'))`. Registros que não parseiam em nenhum formato vão para **quarentena** com motivo `data_pedido invalida`. |
| 2 | `custo_unitario`, `preco_unitario`, `valor_total` | **Valores monetários com prefixo "R$ " e vírgula decimal** — alguns campos chegam como `"R$ 49,24"` ou `"91,67"` (vírgula no lugar do ponto), outros já chegam como `44.32`. | `"R$ 163,95"`, `"91,67"`, `44.32` | Remove o prefixo `R$` com `regexp_replace`, substitui `,` por `.` e converte para `DoubleType`. Valores nulos ou zero após a conversão vão para **quarentena**. |
| 3 | `desconto_pct` | **Percentual com símbolo `%` ou representações de nulo** — o campo ora traz `10%`, ora `10`, ora `N/A` ou `-`. | `10%`, `30%`, `0%`, `N/A`, `-` | Remove o `%` com `regexp_replace`, trata `N/A` e `-` como `null` real e converte para `DoubleType`. |
| 4 | `status_pedido` | **Capitalização e idioma inconsistentes** — o mesmo status aparece em inglês (`DELIVERED`), português maiúsculo (`ENTREGUE`), minúsculo (`entregue`) e com espaço final (`entregue `). | `DELIVERED`, `entregue`, `Entregue`, `ENTREGUE`, `entregue ` | Normaliza com `upper + trim` e mapeamento explícito para valores canônicos em português: `entregue`, `cancelado`, `devolvido`, `em_transito`, `pendente`. |
| 5 | `cliente_email` | **E-mails malformados** — parte dos registros tem e-mails sem `@` (ex.: `...@exemplo.com` faltando o domínio, ou endereço sem separador). | `diego.costa.souza600exemplo.com`, `diego.pereira.martins1545exemplo.com` | Validação com `contains("@")`. Registros sem `@` recebem o valor `email_invalido` e são enviados para **quarentena** com motivo `email sem @`. |
| 6 | `estado` | **Sigla de UF em minúsculas ou com espaços** — alguns registros trazem `rj`, `sp`, `rj` em vez de `RJ`, `SP`. | `rj`, `sp`, ` RJ ` | Aplica `upper(trim(...))` para padronizar todas as siglas em maiúsculas sem espaços. |
| 7 | `cliente_cpf` | **CPF sem formatação, com formatação e representações de nulo** — três padrões: com pontuação (`737.295.450-38`), só dígitos (`88377435404`) e `N/A`. Além disso, **dado pessoal sensível (LGPD)**. | `737.295.450-38`, `88377435404`, `N/A` | Remove formatação com `regexp_replace`, trata `N/A` como `null`. Aplica **pseudonimização LGPD**: exibe apenas os 3 últimos dígitos no padrão `***.***.***-XX`. |
| 8 | `atraso_dias` | **Nulos representados por `-`** — quando o pedido foi cancelado ou ainda não entregue, o campo vem como `-` em vez de `null` ou `0`. | `-`, `0`, `7`, `9` | Substitui `-` (e outras strings nulas) por `0` (inteiro), pois a ausência de atraso é semanticamente `0`. Converte para `IntegerType`. |
| 9 | `cliente_nome` | **Nomes em caixa alta, caixa baixa ou com espaços extras** — falta de padronização de capitalização e presença de espaços no início/fim. | `EDUARDA GOMES ARAÚJO`, `  Marina Costa Souza  ` | Aplica `initcap(trim(...))` para converter para Título Case e remover espaços. |
| 10 | `forma_pagamento` | **Múltiplas grafias para o mesmo meio de pagamento** — `cartao credito`, `Cartão de Crédito`, `cartao_credito`, `CREDITO` referem-se ao mesmo método; mesmo padrão para débito e boleto. | `cartao credito`, `Cartão de Crédito`, `CREDITO`, `BOLETO BANCARIO` | Mapeamento explícito via `when/otherwise` para 4 valores canônicos: `cartao_credito`, `cartao_debito`, `pix`, `boleto`. |
| 11 | `cliente_segmento` | **Espaços extras e capitalização mista** — valor `" recorrente "` (com espaço) e `"NOVO"` (maiúsculo) precisam ser normalizados. | `" recorrente "`, `"NOVO"`, `"vip"` | Aplica `lower(trim(...))` para padronizar todos os segmentos em minúsculas sem espaços. |
| 12 | Múltiplas | **Nulos mascarados por strings literais** — os valores `N/A`, `null`, `NULL`, `-` e string vazia aparecem em diversas colunas como representação de ausência de dado. | `N/A`, `null`, `NULL`, `-`, `""` | Função `normalize_null()` centralizada que detecta todas essas representações via `upper(trim(...)).isin(...)` e retorna `null` real do Spark. |

---

## Política de Quarentena

Linhas que falham em qualquer das regras abaixo **não são descartadas**: são
gravadas em `silver/quarentena/` em formato Parquet, com a coluna adicional
`motivo_quarentena` descrevendo o(s) problema(s) encontrado(s).

Critérios de envio à quarentena:

- `pedido_id` nulo após limpeza
- `data_pedido` não parseável em nenhum dos formatos conhecidos
- `preco_unitario` nulo ou ≤ 0 após conversão
- `quantidade` nula ou ≤ 0 após conversão
- `cliente_email` sem `@` (campo marcado como `email_invalido`)

---

## Considerações LGPD

Os campos `cliente_cpf`, `cliente_email` e `cliente_nome` são dados pessoais
conforme a Lei nº 13.709/2018 (LGPD). O tratamento aplicado é:

- **CPF**: pseudonimizado — apenas os 3 últimos dígitos são preservados (`***.***.***-XX`).
- **E-mail**: pseudonimizado — apenas o domínio é preservado (`***@dominio.com`).
- **Nome**: mantido como Título Case para fins analíticos (identificação de duplicatas de cliente); recomenda-se avaliar a remoção ou hashing na camada gold conforme o caso de uso.
- O campo `cliente_id` (identificador opaco) é suficiente para análises agregadas; os campos pessoais não aparecem nas tabelas gold.
