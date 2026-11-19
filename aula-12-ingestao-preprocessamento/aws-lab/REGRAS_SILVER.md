# Regras Silver — MercadoFácil

Documento que descreve os problemas encontrados na camada raw (`pedidos_mercadofacil.csv`)
e as regras de limpeza aplicadas na camada silver.

---

## Problema 1 — Formatos de data inconsistentes

**Coluna(s):** `data_pedido`, `data_entrega`, `cliente_data_cadastro`

**Evidências no CSV:**
- `02/03/2025` (DD/MM/YYYY)
- `2025-09-02` (YYYY-MM-DD)
- `2025-09-08 13:24:45` (YYYY-MM-DD HH:MM:SS)
- `06/05/2025` (DD/MM/YYYY)

**Regra aplicada:**
Converter todos os valores para o tipo `DateType` (ou `TimestampType` quando há hora).
Tentativa 1: parse `yyyy-MM-dd`. Tentativa 2: parse `dd/MM/yyyy`. Tentativa 3: parse `yyyy-MM-dd HH:mm:ss`.
Linhas que não se enquadram em nenhum formato vão para **quarentena** com motivo `"data_invalida"`.

---

## Problema 2 — Valores monetários com formatação de texto

**Coluna(s):** `preco_unitario`, `custo_unitario`, `valor_total`

**Evidências no CSV:**
- `"R$ 49,24"` — prefixo "R$ " e vírgula decimal
- `"R$ 1.517,01"` — separador de milhar ponto, decimal vírgula
- `"170,55"` — vírgula decimal sem prefixo
- `44.32` — ponto decimal (padrão numérico)

**Regra aplicada:**
Remover prefixo `R$` e espaços, trocar ponto-separador-de-milhar por vazio e vírgula-decimal por ponto.
Converter para `DoubleType`. Valores que não convertam após a limpeza vão para quarentena com motivo `"valor_monetario_invalido"`.

---

## Problema 3 — Coluna `desconto_pct` com formatos mistos e valores nulos/inválidos

**Coluna(s):** `desconto_pct`

**Evidências no CSV:**
- `10%` — string com símbolo de porcentagem
- `10` — número puro
- `0%` — zero com símbolo
- `N/A` — sentinela textual de nulo
- `-` — traço representando ausência

**Regra aplicada:**
Remover `%`, converter para `DoubleType`. Tratar `N/A`, `-`, `null`, string vazia como `NULL`.
Aceitar valores entre 0 e 100; valores fora desse intervalo vão para quarentena com motivo `"desconto_fora_de_range"`.

---

## Problema 4 — `status_pedido` com capitalização e valores inconsistentes

**Coluna(s):** `status_pedido`

**Evidências no CSV:**
- `entregue`, `ENTREGUE`, `Entregue`, `DELIVERED` (inglês)
- `Cancelado`, `CANCELADO`, `cancelado`
- `Devolvido`, `devolvido`, `DELIVERED` (usado erroneamente para devolvido)
- `entregue ` (com espaço à direita)

**Regra aplicada:**
Normalizar para minúsculas com `strip()`. Mapear variantes em inglês:
`delivered` → `entregue`. Valores não reconhecidos (fora de `entregue`, `cancelado`,
`devolvido`, `em_transito`, `processando`) vão para quarentena com motivo `"status_desconhecido"`.

---

## Problema 5 — Nulos representados como strings sentinela

**Coluna(s):** múltiplas — `cliente_cpf`, `nota_avaliacao`, `atraso_dias`, `fornecedor`, `prazo_real_dias`, `parcelas`, `comentario`

**Evidências no CSV:**
- `N/A`, `null`, `NULL`, `-`, string vazia `""`, espaços em branco

**Regra aplicada:**
Substituir todos os sentinelas (`N/A`, `null`, `NULL`, `-`, `""`, `"  "`) por `NULL` nativo do Spark
em todas as colunas. Registros em que colunas obrigatórias (`pedido_id`, `item_id`, `cliente_id`,
`data_pedido`, `valor_total`) sejam nulas vão para quarentena com motivo `"campo_obrigatorio_nulo"`.

---

## Problema 6 — Dados pessoais sem padronização (LGPD)

**Coluna(s):** `cliente_nome`, `cliente_email`, `cliente_cpf`

**Evidências no CSV:**
- Nomes com caixa mista: `"EDUARDA GOMES ARAÚJO"`, `"  Marina Costa Souza  "` (espaços)
- E-mails em caixa alta: `"MARINA.COSTA.MARTINS684@EXEMPLO.COM"`
- CPFs em três formatos: `737.295.450-38` (formatado), `88377435404` (só dígitos), `26294206615` (sem zeros à esq.)
- E-mails inválidos (sem `@`): `diego.costa.souza600exemplo.com`, `marina.pereira.pereira1074exemplo.com`

**Regra aplicada (LGPD):**
- `cliente_nome`: aplicar `trim()` + `initcap()` para padronização. **Não pseudonimizar** (nome não é sensível para análises internas).
- `cliente_email`: converter para minúsculas + `trim()`. Validar presença de `@`; e-mails inválidos → quarentena com motivo `"email_invalido"`.
- `cliente_cpf`: **pseudonimizar** via hash SHA-256 — CPF é dado pessoal sensível pela LGPD. Remover formatação antes do hash. CPFs com menos de 11 dígitos numéricos são marcados como inválidos antes do hash mas ainda pseudonimizados.

---

## Problema 7 — `estado` e `cidade` com capitalização inconsistente e valores por extenso

**Coluna(s):** `estado`, `cidade`

**Evidências no CSV:**
- `rj`, `RJ`, `SP`, `sp` — siglas com capitalização mista
- `"Distrito Federal"` — por extenso em vez de `DF`
- `São Paulo` no campo `estado` (deveria ser `SP`)
- Cidades em caixa alta: `"CAXIAS DO SUL"`, `"SÃO PAULO"`; caixa baixa: `"niterói"`, `"porto alegre"`

**Regra aplicada:**
- `estado`: converter para maiúsculas + `trim()`. Mapear `"Distrito Federal"` → `DF`, `"São Paulo"` (por extenso) → `SP`, `"pa"` → `PA`, etc. Estados que após normalização não correspondam a nenhuma UF brasileira vão para quarentena com motivo `"uf_invalida"`.
- `cidade`: aplicar `trim()` + `initcap()` para padronização de exibição.

---

## Problema 8 — `atraso_dias` com valores negativos e inconsistências lógicas

**Coluna(s):** `atraso_dias`, `prazo_estimado_dias`, `prazo_real_dias`

**Evidências no CSV:**
- `atraso_dias = -2` (entrega antes do prazo gera negativo)
- `atraso_dias = -` (sentinela, já tratado no Problema 5)
- Pedidos cancelados com `prazo_real_dias = NULL` mas `atraso_dias` preenchido

**Regra aplicada:**
- Converter para `IntegerType` após tratar sentinelas.
- Valores negativos de `atraso_dias` são **válidos** (entrega antecipada) — mantê-los.
- Para pedidos com `status_pedido IN ('cancelado', 'devolvido')` e `prazo_real_dias NULL`, preencher `atraso_dias` com `NULL` (não faz sentido calcular atraso sem entrega).
- Verificar consistência: `atraso_dias` deve ser igual a `prazo_real_dias - prazo_estimado_dias` quando ambos existem; discrepâncias maiores que 1 dia são sinalizadas com coluna `flag_atraso_inconsistente = true` (linha permanece na silver).

---

## Resumo — Destino das linhas

| Destino | Critério |
|---|---|
| **silver** | Passou em todas as validações após limpeza |
| **quarentena** | Falhou em pelo menos uma validação obrigatória (campo nulo obrigatório, e-mail inválido, UF inválida, status desconhecido, valor monetário inválido, data inválida) |

A quarentena é gravada em `s3://<bucket>/quarentena/` como Parquet com a coluna extra `motivo_quarentena`.
