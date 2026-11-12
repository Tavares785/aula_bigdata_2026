# Regras da camada silver - MercadoFácil

Como o dado bruto (`raw/pedidos/pedidos_mercadofacil.csv`, 10.000 linhas,
1 linha = 1 item de pedido, tudo texto) é tratado pelo job
`aws-lab/job/etl_mercadofacil.py` antes de chegar à silver
(`silver/pedidos_itens/`, Parquet tipado).

Princípios:

- **O raw não é alterado.** Ele fica no S3 exatamente como chegou.
- **Nenhuma linha some sem explicação.** Toda linha do raw está na silver
  ou na quarentena (`quarentena/`), e a linha em quarentena traz o motivo em
  `motivo_quarentena`. O job registra o fechamento no log:
  `raw=10000 silver=9601 quarentena=399 soma_ok=True`.
- **Corrigir é melhor que descartar.** Se o valor pode ser recuperado de
  outra coluna ou de outras linhas, ele é imputado e a linha recebe uma flag
  (`*_imputado`, `*_divergente`). Só vai para a quarentena a linha que não
  serve para nenhuma análise.

## 1. Problemas encontrados no raw e regra aplicada

| # | Problema encontrado no raw | Exemplo | Regra aplicada na silver |
|---|---|---|---|
| 1 | **Linhas duplicadas**: 200 itens aparecem 2 vezes, idênticos | `PED0005147-1` duas vezes | Chave = `item_id`. Fica a 1ª ocorrência (`row_number` sobre `item_id`); as cópias vão para a quarentena com `item_duplicado`. Um `dropDuplicates(["item_id"])` final garante a unicidade. |
| 2 | **Vários marcadores de nulo** | `NULL`, `null`, `N/A`, `-`, `''`, espaços | Depois do `trim`, todos viram `null` de verdade (`clean_str`), em todas as colunas. |
| 3 | **Datas em 3 formatos** | `2025-03-02`, `02/03/2025`, `2025-03-02 00:00:00` | Cada formato é reconhecido por regex e convertido para `date`. Usamos `timeParserPolicy=CORRECTED`, então datas impossíveis viram null em vez de serem "ajustadas". |
| 4 | **Data do pedido inválida** (52 linhas) | `2025-13-45`, `31/02/2025`, `0000-00-00`, `ontem` | Sem data do pedido não há como calcular prazo nem sazonalidade: a linha vai para a quarentena com `data_pedido_invalida`. |
| 5 | **Valores monetários em formato BR e com símbolo** | `R$ 1.234,56`, `91,67`, `47.60` | Remove `R$`. Se tem vírgula, o ponto é separador de milhar e a vírgula é o decimal. Converte para `double`. Vale para `custo_unitario`, `preco_unitario` e `valor_total`. |
| 6 | **Quantidade inválida** (149 linhas) | `0`, `-1`, `-2`, nula | Quantidade ≤ 0 ou nula torna o item inutilizável (receita e margem): vai para a quarentena com `quantidade_invalida`. |
| 7 | **Preço unitário ausente** | `null`, `N/A` | Recalculado por `valor_total / (quantidade × (1 − desconto))` quando possível. Se não der (6 linhas), vai para a quarentena com `preco_invalido`. |
| 8 | **Desconto com `%` ou nulo** | `10%`, `10`, `N/A` | Tira o `%` e converte para inteiro. Se for nulo, é derivado de `valor_total` e `preco × quantidade`. Sem como derivar, assume 0. Flag `desconto_imputado`. |
| 9 | **`valor_total` inconsistente ou ausente** (195 divergentes) | total diferente de preço × qtd × (1 − desc) | O total é sempre recalculado a partir dos componentes (`round(preco × qtd × (1 − desc/100), 2)`). O informado só serve para gerar a flag `valor_total_divergente`. |
| 10 | **Categorias em caixa variada, sem acento ou truncadas** | `ELETRÔNICOS`, `Eletronicos`, `Eletrônico`, `Mod`, `Pe` | O SKU é a chave confiável (1 SKU → 1 categoria). Categoria, produto, marca e fornecedor recebem o **valor mais frequente de cada SKU**. Isso corrige caixa e truncamento e preenche nulos de `marca`/`fornecedor`. |
| 11 | **Estado (UF) em formatos diferentes** | `SP`, `sp`, `' SP '`, `São Paulo` | Sigla em maiúsculas. Nome por extenso é convertido para a sigla, via dicionário sem acento. Também é derivada a coluna `regiao` (Norte, Nordeste, …). |
| 12 | **Cidade com caixa e acentos variados** | `SÃO PAULO`, `Sao Paulo`, `são paulo` | A comparação é feita sem acento e em minúsculas, contra a lista de cidades canônicas (`São Paulo`, `Niterói`, …). Fora da lista usa `initcap`. |
| 13 | **Domínios com grafias diferentes** | canal `App`/`APP`/`app `; status `ENTREGUE`/`DELIVERED`/`canceled`/`returned`; pagamento `CREDITO`/`Cartão de Crédito`/`cartao_credito`; transportadora `LOGGI` | Cada domínio é mapeado para um vocabulário fechado: canal ∈ {app, site, marketplace_parceiro}; status ∈ {entregue, cancelado, devolvido}; pagamento ∈ {cartao_credito, cartao_debito, pix, boleto}; transportadora ∈ {Correios, Loggi, Jadlog, Entrega Própria}. Status desconhecido → quarentena (`status_desconhecido`). |
| 14 | **Segmento de cliente nulo/variado** | `VIP`, `' novo '`, `NULL` | Minúsculas + trim. Nulo ou fora de {novo, recorrente, vip} vira `nao_informado`, para não perder a linha. |
| 15 | **Centro de distribuição nulo** | `N/A`, `-` | Cada UF é atendida por um único CD. O nulo é preenchido com o CD mais frequente da UF de destino. |
| 16 | **`atraso_dias` inconsistente** (170 linhas) | atraso `-2`, ou diferente de real − estimado | O atraso é recalculado: `greatest(prazo_real − prazo_estimado, 0)`. O informado só gera a flag `atraso_divergente`. Atraso desconhecido fica `null` e não vira 0. |
| 17 | **Prazo real / data de entrega ausentes** | `prazo_real_dias = NULL`, `data_entrega = -` | Um completa o outro: `prazo_real = data_entrega − data_pedido` e `data_entrega = data_pedido + prazo_real`. Como a logística é a mesma em todos os itens do pedido, um item sem prazo herda o prazo dos outros itens do mesmo pedido. |
| 18 | **Pedido cancelado com dados de entrega** | — | Pedido cancelado não foi entregue: `prazo_real`, `data_entrega` e `atraso` ficam `null`, e a flag `entrega_em_pedido_cancelado` registra o caso. |
| 19 | **Nota fora da escala 1–5** (56 linhas) | `0`, `-1`, `10`, `99` | A nota vira `null` e a flag `nota_fora_da_faixa` registra o caso. A linha continua valendo para vendas e logística. |
| 20 | **Comentário com espaços extras e nulos disfarçados** | `'  Muito bom…  '`, `N/A` | Trim e colapso de espaços. Marcadores de nulo viram `null`. O texto original é mantido para a análise de NLP. |
| 21 | **Parcelas nulas** | `N/A` em pagamento à vista | Pix, boleto e débito são sempre `1` parcela. No cartão de crédito, o nulo é mantido (não dá para inferir). |

## 2. Dados pessoais (LGPD)

| Coluna | Tratamento |
|---|---|
| `cliente_nome` | **Removida** da silver, da gold e da quarentena. Não tem uso analítico. |
| `cliente_email` | **Removida**. Fica só a flag `cliente_email_valido`; 275 e-mails não têm `@`. |
| `cliente_cpf` | **Removido**. Fica só a flag `cliente_cpf_valido` (formato com 11 dígitos). |
| `cliente_id` | Mantido: é um identificador pseudônimo interno, necessário para análises de recorrência. |

Base legal e finalidade: as perguntas de negócio (atraso, nota,
cancelamento, sazonalidade) não precisam identificar a pessoa. Pelo
princípio da **minimização** (LGPD art. 6º, III), os identificadores diretos
são descartados logo na primeira camada tratada. O raw, que ainda tem PII, fica
num bucket privado, com bloqueio de acesso público e criptografia SSE-S3,
e é apagado no `terraform destroy`.

## 3. Quarentena

`s3://<bucket>/quarentena/` (tabela `quarentena` no Athena) guarda a **linha
original do raw, como texto**, sem as colunas de PII, mais
`motivo_quarentena` (os motivos separados por `;`), `id_linha_raw` e
`dt_processamento`.

| Motivo | Linhas na execução |
|---|---|
| `item_duplicado` | 200 |
| `quantidade_invalida` | 149 |
| `data_pedido_invalida` | 52 |
| `preco_invalido` | 6 |
| `chave_ausente`, `status_desconhecido`, `estado_desconhecido` | 0 (regras preventivas) |

## 4. Resultado na silver

- 9.601 itens, 42 colunas tipadas (`date`, `int`, `double`, `boolean`), sem
  duplicidade de `item_id`.
- Zero nulos em chaves, datas do pedido, status, canal, UF, região, cidade,
  categoria, produto, marca, fornecedor, CD, valores e prazo estimado.
- Os nulos que sobram têm significado: `atraso_dias` só é nulo nos 679 itens
  cancelados; `nota_avaliacao` é nula em 1.159 itens sem avaliação;
  `comentario` é opcional.
