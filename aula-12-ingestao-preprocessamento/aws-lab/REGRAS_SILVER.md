# Regras da camada silver — MercadoFácil

Os problemas abaixo foram **medidos** no `data/pedidos_mercadofacil.csv`
(10.000 linhas), não supostos. As contagens vêm de um perfil do arquivo
antes de escrever o ETL; cada regra trata um problema observado.

Princípio que vale para todas: **nada é descartado em silêncio.** Linha
que não pode virar fato vai para `quarentena/` com o motivo numa coluna.
Filtrar e seguir adiante esconderia exatamente o que precisa ser
investigado.

## Problemas encontrados e regra aplicada

| # | Problema | Evidência no raw | Regra na silver |
|---|---|---|---|
| 1 | **Cinco marcadores de ausência** convivendo na mesma coluna | `data_entrega`: 141 vazios, 129 `null`, 156 `-`, 136 `NULL`, 143 `N/A`. O padrão se repete em 8 colunas | Todos convertidos em `NULL` antes de qualquer cast. Tratar um e esquecer os outros deixa a coluna metade limpa, e o erro só aparece na agregação |
| 2 | **Dinheiro em três formatos na mesma coluna** | `preco_unitario`: 2.964 linhas `R$ 49,24`, 6.001 `49.24`, 934 `49,24` | Tira `R$`, remove o ponto de milhar **antes** de trocar a vírgula decimal, e converte para `DECIMAL(12,2)`. A ordem importa: inverter faz `1.647,40` virar `1.64740` |
| 3 | **Datas em três formatos, mais texto livre** | `data_pedido`: 7.155 ISO, 2.024 `DD/MM/YYYY`, 17 com a palavra `ontem`, algumas com timestamp | `coalesce` tentando ISO, `dd/MM/yyyy`, `dd-MM-yyyy` e os 10 primeiros caracteres do timestamp. `ontem` vira `NULL` — não há data de referência, e inventar uma seria fabricar fato |
| 4 | **Percentual com símbolo** | `desconto_pct`: 2.932 linhas como `10%`, o resto como `10` | Remove o `%` **antes** do cast; ausente vira `0`. Sem isso, 2.932 linhas virariam `NULL` e o desconto sumiria do cálculo |
| 5 | **Categorias truncadas e sem padrão de caixa** | `Beleza e Saúd`, `Casa e Cozinh`, `Eletrônico`, `Brinquedo` convivendo com as formas completas, e ainda `BELEZA E SAÚDE` em maiúscula | Comparação por chave (minúscula, sem acento, sem espaço) contra um dicionário canônico. O que não está no dicionário vai para quarentena, não para "Outros" — um balde de "Outros" esconderia categoria nova |
| 6 | **Status em dois idiomas** | `DELIVERED`, `canceled` e `returned` misturados a `entregue`, `cancelado`, `devolvido`, com variação de caixa e espaço à direita | Mapeados para o português canônico. O dump junta sistemas diferentes; manter os dois idiomas quebraria todo `GROUP BY status` |
| 7 | **Estado por extenso e com espaço nas pontas** | ` SP `, ` MG ` e também `Amazonas`, `Bahia`, `Ceará` | Dicionário nome → sigla; o que já é sigla passa por `trim` + `upper`. Sem isso, `SP` e ` SP ` viram dois estados diferentes no agrupamento |
| 8 | **200 itens duplicados** | 200 `item_id` repetidos, 200 linhas excedentes | `row_number` sobre janela por `item_id`, ficando com a linha **mais completa** (menos nulos em entrega, nota e atraso) e, no empate, a de entrega mais recente. `dropDuplicates` resolveria a contagem, mas a cópia escolhida seria arbitrária e duas execuções poderiam divergir |
| 9 | **Nota de avaliação fora da escala** | 57 linhas com nota fora de 1–5, incluindo `-1` e `99` | Vira `NULL`, e a linha **fica**. O pedido continua válido; só a avaliação não serve. Zerar seria pior: entraria na média como nota baixa |
| 10 | **Quantidade e valor negativos ou zero** | 37 `quantidade` negativas, 13 iguais a zero, 49 `valor_total` negativos (mínimo `-2545.80`) | Quarentena, com o motivo. Item vendido não tem quantidade negativa; manter isso na silver contaminaria qualquer soma de receita |
| 11 | **`atraso_dias` ausente com os dois prazos presentes** | 217 vazios e mais 928 em outros marcadores | Recalculado como `prazo_real_dias - prazo_estimado_dias`. É coluna **derivada**, não observada: guardar `NULL` perderia informação que está ali |
| 12 | **Dados pessoais no dump (LGPD)** | `cliente_nome`, `cliente_email` e `cliente_cpf` em todas as 10.000 linhas; o CPF ainda em dois formatos (4.887 pontuados, 5.113 não) e 678 e-mails sem `@` | Nome e e-mail **descartados**. CPF vira `SHA-256` em `cliente_hash`. A análise precisa distinguir clientes, e `cliente_id` já faz isso; o hash fica só para contagem de distintos sem guardar o dado pessoal |

## O que vai para a quarentena

Nesta ordem, parando no primeiro motivo que se aplica:

1. `item_id` ausente
2. `pedido_id` ausente
3. `data_pedido` ilegível (inclui `ontem`)
4. `quantidade` ausente
5. `quantidade` não positiva
6. `valor_total` ausente
7. `valor_total` negativo
8. `categoria` fora do domínio
9. `status_pedido` fora do domínio

A coluna `motivo_quarentena` guarda qual deles barrou a linha. Com ela, o
próximo passo é consultar `quarentena/` no Athena e decidir caso a caso —
em vez de descobrir meses depois que 3% dos pedidos sumiram.

## Decisões que valem registrar

**Inferência de esquema desligada.** O Spark leria `preco_unitario` como
texto numa partição e número em outra, conforme o que coubesse na amostra
de inferência. Toda coluna entra como texto e é convertida por regra
explícita.

**Categoria desconhecida vai para quarentena, não para "Outros".** Um
balde de "Outros" cresce silenciosamente e esconde categoria nova que o
dicionário ainda não conhece.

**Só pedidos `entregue` entram nas métricas de prazo da gold.** Cancelado
e devolvido não têm entrega; incluí-los puxaria a média de atraso para
baixo com linhas que nunca saíram do centro de distribuição.

## O que estas regras NÃO resolvem

- **`ontem` é perda real.** 17 linhas em `data_pedido` e 21 em
  `data_entrega` vão para quarentena. Resolver exigiria saber a data de
  extração do dump, que não temos.
- **Não validamos o dígito verificador do CPF.** O hash é calculado sobre
  o que veio; CPF inválido entra como hash igualmente válido.
- **Duplicata só é detectada por `item_id`.** Dois registros do mesmo
  item com ids diferentes passariam, e o arquivo não dá como distingui-los.
