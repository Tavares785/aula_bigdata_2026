# Checkpoint de Progresso - Aula 13: Análise e Construção de Modelos

> Preencha cada seção, substituindo `<PREENCHER>`. Não remova os
> títulos (`##`).

## Análise/modelo implementado

Implementamos em `src/analise.py` as duas funções da aula, aplicadas aos
pedidos da MercadoFácil (`pedidos_mercadofacil.csv`, 10.000 linhas):

- `build_model_or_analysis`: lê o CSV (ou uma lista de dicts) e aplica uma
  normalização mínima e idempotente (caixa e espaços, nulos em vários
  formatos, datas em 4 formatos, notas e quantidades inválidas, itens
  duplicados). Depois faz a **análise descritiva** (taxa de atraso por
  região, estado, transportadora, mês e segmento; relação atraso x nota;
  cancelamento/devolução por categoria e canal) e treina um **modelo de
  regressão logística** que estima a probabilidade de um item ser entregue
  com atraso. Features: região, transportadora, categoria, nov/dez, prazo
  estimado e quantidade. O split treino/teste (80/20) é feito por pedido,
  para que itens do mesmo pedido não fiquem nos dois lados.
- `summarize_results`: transforma o resultado em um relatório em texto com
  KPIs, tabelas de taxas, métricas do modelo e fatores de risco.

A regressão foi escrita só com a biblioteca padrão do Python (o
`requirements.txt` do CI tem apenas o pytest). No Glue/EMR o equivalente
seria `pyspark.ml.classification.LogisticRegression`. Para rodar:
`python src/analise.py`.

## Principais resultados até agora

Base: 10.000 linhas lidas, 200 itens duplicados removidos, 9.800 itens
únicos, dos quais 8.619 entregues.

- **Atraso:** 22,4% dos itens entregues chegam atrasados; quando atrasam,
  são 5,6 dias em média. **Cancelados: 7,1%; devolvidos: 5,0%.**
- **Região:** Norte (35,4%) e Nordeste (34,3%) atrasam bem mais que
  Sudeste (19,4%), Sul (19,0%) e Centro-Oeste (16,6%). Estados mais
  críticos: AM (41,6%), BA (35,2%), PE (34,1%) e CE (33,4%).
- **Sazonalidade:** novembro (34,6%) e dezembro (31,0%) ficam bem acima dos
  demais meses (16% a 21%).
- **Segmentos:** Norte/Nordeste em nov/dez chega a 46,1% de atraso, contra
  15,6% nas demais regiões fora da época de pico. Os dois fatores se somam.
- **Transportadora:** Correios tem a maior taxa (26,1%) e Loggi a menor
  (18,5%). Ainda não controlamos esse número por região.
- **Atraso x nota:** a nota média é 4,24 no prazo e 2,70 com atraso. A
  correlação entre dias de atraso e nota é -0,545 (forte e negativa). Por
  faixa: 3,40 (1 a 3 dias), 2,56 (4 a 7 dias) e 2,22 (8 dias ou mais).
- **Cancelamento + devolução:** fica entre 11% e 14% em todas as categorias
  (Livros 13,7%, Pet 11,1%) e entre 11,2% e 12,2% nos canais. Essas
  diferenças são pequenas e não parecem explicar o problema.
- **Modelo de atraso:** acurácia de 79,3% no teste, praticamente igual ao
  baseline de sempre prever "no prazo" (79,1%), e AUC de 0,638. Os fatores
  que mais aumentam o risco são nov (+0,70), dez (+0,48) e Nordeste (+0,20);
  os que mais reduzem são Loggi (-0,40), Sul (-0,37) e Centro-Oeste (-0,28).

## Iterações e ajustes feitos

- Na primeira execução, a categoria "Eletronicos" (sem acento) apareceu
  separada de "Eletrônicos". Passamos a comparar categorias sem acento e
  sem diferenciar caixa, e as variantes se juntaram.
- Removemos os 200 itens duplicados e descartamos notas inválidas (0, -1,
  10 e 99). O atraso passou a ser calculado como prazo real menos prazo
  estimado, em vez de confiar só em `atraso_dias`, que tem muitos nulos.
- Testamos adicionar interações ao modelo (Norte/Nordeste x nov/dez,
  Correios x nov/dez e prazo estimado curto). Nenhuma mudou o resultado
  (AUC continuou em 0,638), porque os efeitos de região e de época se
  somam. Mantivemos o modelo simples.
- O modelo ficou fraco: só com essas variáveis, ele ordena o risco de
  atraso melhor que o acaso (AUC 0,64), mas não prevê bem item a item.
  Usamos o modelo para identificar **fatores de risco**, não como
  previsor em produção.
- A camada gold do pipeline da Aula 12 (Glue/Athena) não está neste
  repositório. Por isso a análise roda sobre o CSV bruto com a
  normalização mínima acima. Ela também aceita os dados já tratados, se
  exportarmos a gold.

## Próxima etapa (Aula 14)

- Montar a visualização final: barras de atraso por região, estado e mês,
  nota média por faixa de atraso e a tabela de segmentos de risco.
- Cruzar transportadora com região, para saber se a diferença dos Correios
  vem da transportadora ou do destino.
- Melhorar o modelo com variáveis que ainda não usamos (distância ao centro
  de distribuição, histórico da transportadora, volume diário de pedidos).
- Escrever a conclusão com recomendações: reforçar a logística no
  Norte/Nordeste, ampliar o prazo estimado nesses destinos e em nov/dez, e
  revisar a operação dos Correios.
- Se der tempo, repetir a análise sobre a gold no Athena/Spark.
