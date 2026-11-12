# Regras de Transformação: RAW → SILVER

Este documento lista os problemas de qualidade encontrados nos dados brutos (raw) e as regras aplicadas na camada silver para cada um.

---

## 1. Formatos de Data Inconsistentes

**Problema:** O campo `data_pedido`, `data_entrega` e `cliente_data_cadastro` aparecem em múltiplos formatos:
- `dd/MM/yyyy` (ex: "02/03/2025")
- `yyyy-MM-dd` (ex: "2025-09-02")
- `yyyy-MM-dd HH:mm:ss` (ex: "2025-09-08 13:24:45")

**Regra aplicada:** Função `parse_date()` tenta converter usando `to_date()` com múltiplos formatos via `coalesce()`. Datas que não puderem ser parseadas ficam como `null` e o registro vai para quarentena com motivo "data_pedido inválida".

---

## 2. Valores Monetários em Formatos Diferentes

**Problema:** Campos `custo_unitario`, `preco_unitario` e `valor_total` têm múltiplos formatos:
- Com prefixo "R$" e espaços (ex: "R$ 49,24")
- Sem prefixo (ex: "28.81")
- Vírgula como separador decimal (ex: "91,67")
- Entre aspas (ex: "\"R$ 163,95\"")

**Regra aplicada:** Função `clean_money()` remove o prefixo "R$" e substitui vírgulas por pontos. Em seguida, converte para `DecimalType(10, 2)`. Valores que não puderem ser convertidos ficam como `null`.

---

## 3. Percentuais com e sem Símbolo "%"

**Problema:** O campo `desconto_pct` aparece de formas inconsistentes:
- Apenas número (ex: "10")
- Com símbolo "%" (ex: "10%")
- Valor "0%" ou "0"
- Valores vazios ou "N/A"

**Regra aplicada:** Remove o símbolo "%" via `regexp_replace()` e converte para `DecimalType(5, 2)`. Valores inválidos ou vazios se tornam `null`.

---

## 4. Padronização de Texto: Case Inconsistente

**Problema:** Vários campos de texto aparecem em casing diferente:
- `status_pedido`: "entregue", "ENTREGUE", "Entregue", "DELIVERED", "Devolvido"
- `estado`: "SP", "sp", "São Paulo", "Distrito Federal"
- `canal`: "app", "APP", "Site", "marketplace_parceiro"
- `forma_pagamento`: "PIX", "pix", "Cartão de Crédito", "cartao_credito"

**Regra aplicada:**
- `estado`: convertido para uppercase (`upper()`) e mapeado para siglas (ex: "São Paulo" → "SP")
- `status_pedido`: convertido para lowercase e mapeado para valores padrão ("delivered" → "entregue")
- `canal`, `categoria`, `cliente_segmento`: lowercase e trim
- `forma_pagamento`: uppercase e trim
- `cidade`, `transportadora`: `initcap()` (primeira letra maiúscula)

---

## 5. Espaços em Branco Extras

**Problema:** Diversos campos contêm espaços em branco no início/fim ou múltiplos espaços internos:
- `cliente_nome`: "  Marina Costa Souza  "
- `cliente_segmento`: " recorrente "
- `estado`: " RJ ", " SP "

**Regra aplicada:** Aplicação de `trim()` em todos os campos de texto para remover espaços nas pontas.

---

## 6. Valores Nulos Representados de Múltiplas Formas

**Problema:** Valores ausentes aparecem como:
- String vazia ("")
- "N/A"
- "null"
- "NULL"
- "-"

**Regra aplicada:** Durante a conversão de tipos (`cast()`), esses valores são automaticamente convertidos para `null` do Spark. Registros com campos críticos nulos (como `pedido_id`, `cliente_id`, `data_pedido`) são movidos para quarentena.

---

## 7. CPF em Formato Inválido ou Ausente

**Problema:** O campo `cliente_cpf` apresenta:
- Formatos com pontos e traços (ex: "737.295.450-38")
- Formato com 11 dígitos (ex: "26294206615")
- Valores "N/A"
- Valores vazios

**Regra aplicada:**
- Remove todos os caracteres não numéricos via `regexp_replace()`
- Valida que o CPF tem exatamente 11 dígitos (campo `cpf_valido`)
- CPFs inválidos (diferente de 11 dígitos) causam envio do registro para quarentena com motivo "cpf inválido"

---

## 8. Email em Formato Inválido

**Problema:** O campo `cliente_email` apresenta:
- Emails válidos (ex: "vitor.araujo.santos1677@exemplo.com")
- Emails sem "@" (ex: "diego.costa.souza600exemplo.com")
- Emails em maiúsculas/minúsculas misturadas
- Valores "N/A"

**Regra aplicada:**
- Converte para lowercase e aplica trim
- Valida que o email contém "@" (campo `email_valido`)
- Emails inválidos (sem "@") causam envio do registro para quarentena com motivo "email inválido"

---

## 9. Duplicatas de Registros

**Problema:** Alguns registros aparecem duplicados (mesmo `item_id`).

**Regra aplicada:** Deduplicação usando `row_number()` sobre janela particionada por `item_id` e ordenada por `data_pedido`. Mantém apenas a primeira ocorrência de cada `item_id`.

---

## 10. Dados Pessoais (LGPD)

**Problema:** A base contém dados pessoais fictícios: `cliente_nome`, `cliente_email`, `cliente_cpf` e `comentario` (que pode conter informações sensíveis).

**Regra aplicada:**
- Cria hash SHA-256 dos campos sensíveis: `cliente_nome_hash`, `cliente_email_hash`, `cliente_cpf_hash`
- Remove os campos originais (`cliente_nome`, `cliente_email`, `cliente_cpf`, `comentario`) da camada silver
- Isso permite análises agregadas por cliente (usando o hash como identificador) sem expor dados pessoais

---

## 11. Campos Numéricos em Formato Texto

**Problema:** Campos como `quantidade`, `parcelas`, `prazo_estimado_dias`, `prazo_real_dias`, `atraso_dias`, `nota_avaliacao` estão como string no CSV.

**Regra aplicada:** Conversão explícita para tipos numéricos (`IntegerType()`). Valores que não puderem ser convertidos ficam como `null`.

---

## 12. Valores Faltantes em Campos de Atraso

**Problema:** Para pedidos cancelados ou em andamento, os campos `prazo_real_dias`, `data_entrega` e `atraso_dias` podem estar vazios ou com valores inválidos.

**Regra aplicada:** Esses campos são convertidos para seus tipos corretos e valores inválidos se tornam `null`. A lógica de negócio na camada gold filtra apenas pedidos com `status_pedido = 'entregue'` quando analisa atrasos.

---

## 13. Registros Inválidos → Quarentena

**Problema:** Alguns registros têm problemas estruturais críticos que impedem seu processamento confiável.

**Regra aplicada:** Registros com os seguintes problemas são movidos para a pasta `quarantine/`:
- `pedido_id` nulo
- `data_pedido` inválida (não pode ser parseada)
- `cliente_id` nulo
- CPF inválido (quando presente, mas com formato errado)
- Email inválido (quando presente, mas sem "@")

Cada registro em quarentena recebe um campo `motivo_quarentena` explicando o problema. Isso permite revisão manual e eventual reprocessamento após correção na origem.

---

## Resumo das Transformações

| Campo Original | Problema | Transformação Silver |
|----------------|----------|---------------------|
| `data_pedido`, `data_entrega` | Múltiplos formatos | Parse com múltiplos formatos → `DateType` |
| `custo_unitario`, `preco_unitario`, `valor_total` | Formato monetário inconsistente | Remove "R$", substitui vírgula → `DecimalType(10,2)` |
| `desconto_pct` | Com/sem "%" | Remove "%" → `DecimalType(5,2)` |
| `estado` | Extenso/sigla, case | Uppercase + mapeamento para sigla |
| `status_pedido` | Case + termos em inglês | Lowercase + mapeamento para português |
| `cliente_cpf` | Formato com pontuação | Remove não numéricos + valida 11 dígitos |
| `cliente_email` | Case + sem "@" | Lowercase + valida presença de "@" |
| `cliente_nome`, `cliente_email`, `cliente_cpf` | Dados pessoais (LGPD) | Hash SHA-256 + remoção dos originais |
| Duplicatas por `item_id` | Registros repetidos | Deduplicação mantendo primeiro registro |
| Campos numéricos | Tipo string | Cast para `IntegerType` ou `DecimalType` |

---

## Métricas de Qualidade

Ao final do processamento, o job Glue exibe:
- Total de registros lidos do raw
- Total de registros válidos na silver
- Total de registros enviados para quarentena (com motivo)
- Total de registros após deduplicação
