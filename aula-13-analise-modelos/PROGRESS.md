# Checkpoint de Progresso - Aula 13: Análise e Construção de Modelos

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## Análise/modelo implementado

Projeto MercadoFácil. Grupo: Weslley Lucas (RA 6325226), Gabriel Reis
Cunha (RA 6325149) e Sirlande Martins (RA 6325269). A entrada é a silver
`silver/pedidos_itens` da Aula 12 (9.601 itens, Parquet, sem PII). A análise
fica em `src/analise.py` e roda em Spark 3.3, a mesma versão do Glue 4.0:

```bash
python src/analise.py --SILVER_PATH <.../silver/pedidos_itens> --OUTPUT_PATH resultados
```

`build_model_or_analysis` recebe o DataFrame da silver e executa quatro
análises. `summarize_results` devolve um dicionário serializável em JSON e um
resumo em texto. A saída da execução está em `resultados/resultados.txt` e
`resultados/resultados.json`.

- **A. Modelo de risco de atraso (Spark MLlib).**
  - Unidade: 1 linha = 1 pedido entregue (6.492 pedidos). O alvo é `atraso_dias > 0`.
  - Variáveis: só as conhecidas na hora da compra. São elas região, CD,
    transportadora, canal, categoria principal, forma de pagamento, segmento do
    cliente, mês, prazo estimado, nº de itens e valor. Prazo real, nota e
    status ficam de fora para não vazar o resultado.
  - Pipeline: `StringIndexer` + `OneHotEncoder` + `VectorAssembler`, depois
    `LogisticRegression` e `RandomForestClassifier`.
  - Pesos de classe compensam o desbalanceamento (22% de atrasos).
  - Divisão em 5 folds pelo hash do `pedido_id`. O fold 0 é o teste
    (20%), e os 5 folds são usados na validação cruzada.
  - Métricas: AUC-ROC, AUC-PR, precisão, recall, F1 e lift dos 20% de maior
    risco. Também calculamos a importância das variáveis (RF) e os odds ratios
    (LR).
- **B. Impacto do atraso.**
  - Nível do item, porque a nota é dada por item.
  - Regressão linear: nota ~ dias de atraso + categoria + canal.
  - Regressão logística: devolução ~ dias de atraso + categoria + canal.
- **C. NLP dos comentários.**
  - Pipeline Spark: `RegexTokenizer` + `StopWordsRemover` (português), depois
    de baixar a caixa e tirar os acentos.
  - O sentimento vem de um léxico positivo/negativo. "não recomendo" é
    tratado como um único token negativo.
  - Os temas são entrega, produto e atendimento.
  - O léxico é validado contra a nota que o próprio cliente deu.
- **D. Capacidade e cenário.**
  - Correlação entre volume e taxa de atraso por CD e mês.
  - Simulação de +2 dias no prazo prometido para o Norte/Nordeste. O prazo
    real não muda.

## Principais resultados até agora

Execução local em 2026-11-18 (Spark 3.3.4, JDK 11). A silver foi regenerada
pelo ETL da Aula 12 com as mesmas contagens do Glue:
`raw=10000 silver=9601 quarentena=399`.

**A. Risco de atraso (teste = fold 0, 1.298 pedidos, 21,3% atrasados)**

| Modelo | AUC-ROC (teste) | AUC-ROC 5-fold | AUC-PR | Precisão | Recall | F1 | Atraso nos 20% de maior risco |
|---|---|---|---|---|---|---|---|
| Regressão logística | 0,682 | 0,659 ± 0,026 | 0,377 | 0,327 | 0,635 | 0,432 | 39,8% (lift 1,86) |
| Random forest | 0,661 | 0,652 ± 0,019 | 0,336 | 0,319 | 0,545 | 0,402 | 35,5% (lift 1,66) |
| Baseline "nunca atrasa" | 0,500 | – | – | – | 0,000 | – | 21,3% |

- O poder preditivo é modesto, mas real. A AUC-PR fica em 0,38, contra 0,21
  do acaso. Entre os 20% de pedidos de maior risco, 39,8% atrasam, quase o
  dobro da média. O modelo serve para priorizar pedidos (alerta, prazo
  maior, transportadora alternativa), não para prever cada atraso.
- Os fatores são os mesmos nos dois modelos.
  - Na importância do RF, o mês (0,21) vem primeiro. Depois vêm CD (0,13),
    prazo estimado (0,12), canal (0,12), região (0,12) e transportadora (0,08).
  - Maiores odds ratios da LR: novembro 1,81×, `marketplace_parceiro` 1,72×,
    dezembro 1,63×, Correios 1,27×, Nordeste / CD-NORDESTE 1,23×.
- Cada dia a mais de prazo estimado aumenta a chance de atraso em 6,2%
  (OR 1,062). Pedidos com prazo longo são justamente os de rota difícil.

**B. Impacto do atraso**

- Cada dia de atraso tira **0,235 ponto** da nota, controlando categoria e
  canal (R² = 0,24). A nota média cai de 4,12 (no prazo) para 3,32 (1–3 dias),
  2,54 (4–7 dias) e 2,21 (8+ dias).
- O atraso **não** aumenta a devolução (OR 0,96 por dia). A devolução parece
  ligada ao produto, não à entrega.

**C. NLP (5.545 comentários)**

- O léxico concorda com a nota. Os comentários negativos têm nota média 1,53,
  os neutros 3,0 e os positivos 4,51.
- Entre os 1.022 negativos, os três temas aparecem em proporções parecidas:
  entrega 608, produto 595 e atendimento 597. Um comentário pode citar mais de
  um tema.
- Achado importante: o tema "entrega" aparece em 59% dos negativos **com ou
  sem atraso real**. O texto acompanha a nota, mas não distingue a causa. Para
  medir o efeito do atraso, a métrica certa é o atraso real da silver, não o
  comentário.

**D. Capacidade e cenário**

- Dentro de cada CD, os meses de mais volume são os de mais atraso.
  - Correlação volume × taxa de atraso: CD-SUDESTE 0,93, CD-SUL 0,69,
    CD-NORDESTE 0,66, CD-NORTE 0,49.
  - No conjunto, a correlação é −0,10. É um paradoxo de Simpson: o
    CD-SUDESTE tem muito volume e pouco atraso.
  - Isso indica um gargalo de capacidade no pico de nov/dez, não só uma
    questão de rota.
- +2 dias de prazo prometido no Norte/Nordeste:
  - O atraso percebido no Nordeste cai de 35,1% para 28,4%. No Norte, cai de
    31,6% para 26,2%.
  - No total, cai de 22,4% para 21,0%, sem mexer na operação.

## Iterações e ajustes feitos

- **Vazamento evitado.** A primeira ideia era usar a silver inteira. Tiramos
  `prazo_real_dias`, `data_entrega`, a nota e o status, porque só existem
  depois da entrega e dariam AUC artificialmente perto de 1.
- **Granularidade.** O modelo de atraso é por pedido (a logística é do
  pedido), com a categoria de maior valor como "categoria principal". Já
  nota e devolução são por item, como na gold da Aula 12.
- **Split instável.** A 1ª versão usava `randomSplit(seed=42)`. Mesmo com
  seed, o conjunto de teste mudava entre execuções, porque a ordem das linhas
  depois do `groupBy` não é fixa. A AUC da LR oscilou entre 0,62 e 0,67 só
  por causa disso. Trocamos por folds fixos pelo hash do `pedido_id`
  (`pmod(xxhash64(pedido_id), 5)`) e passamos a reportar a validação cruzada
  5-fold. Duas execuções seguidas agora dão resultados idênticos.
- **Desbalanceamento.** Sem pesos, a LR quase nunca prevê atraso: o recall
  médio no 5-fold é 0,058. Com `weightCol` balanceado, a AUC fica igual
  (0,660 → 0,659), mas o recall da classe "atrasou" sobe para 0,596.
- **Comparação de variações (AUC-ROC média no 5-fold).** Todas ficaram entre
  0,640 e 0,661:
  - LR com `regParam` 0,001 / 0,01 / 0,1: 0,659 / 0,659 / 0,660.
  - Com `estado` além da região: 0,660.
  - Trocando o mês por "pico vs regular": 0,661.
  - Só com região, mês, transportadora, canal e prazo: 0,656.
  - RF com profundidade 4 / 6 / 8: 0,651 / 0,652 / 0,649.
  - GBT (profundidade 3, 40 iterações): 0,640.

  As diferenças são menores que o desvio entre folds (~0,02). Isso indica um
  teto da informação disponível na compra, não do algoritmo. Mantivemos a LR
  (interpretável) e o RF (importâncias) com parâmetros simples.
- **NLP.**
  - Um léxico ingênuo contaria "recomendo" como positivo também em "Não
    recomendo". Por isso a negação vira um token só (`nao_recomendo`).
  - Os acentos e a caixa (há comentários todos em MAIÚSCULAS) são
    normalizados antes da tokenização.
  - O dataset tem só 17 frases-modelo distintas. Por isso escolhemos um léxico
    validado pela nota, e não um modelo de sentimento treinado.
- **Correlação de capacidade.** A correlação agregada (−0,10) escondia o
  efeito. Calculamos por CD, o que revelou o paradoxo de Simpson.

## Próxima etapa (Aula 14)

- Gravar na gold as saídas da análise, para que Athena e o dashboard leiam
  direto do data lake:
  - `previsao_atraso`, com o risco por pedido;
  - `cenario_prazo`;
  - `sentimento_comentarios`.
  Rodar `analise.py` como Glue Job no mesmo Terraform da Aula 12.
- Montar o dashboard final (Streamlit ou QuickSight sobre o Athena) com:
  - mapa de atraso por região/CD;
  - sazonalidade nov/dez × capacidade;
  - curva atraso × nota;
  - simulador de prazo extra por região;
  - temas e sentimento dos comentários.
- Fechar a conclusão de negócio. O atraso concentra-se no Norte/Nordeste
  (Correios + CD-NORDESTE) e no pico de nov/dez. Ele derruba a nota, mas não a
  devolução. Recomendações:
  - prometer prazos realistas por região (ganho rápido, de −1,4 p.p. no
    total);
  - reforçar a capacidade dos CDs no pico;
  - rever o SLA do canal `marketplace_parceiro`.
- Registrar as limitações: AUC ~0,66 com as variáveis da compra, comentários
  sintéticos e pouco informativos, e dados de um único ano.
