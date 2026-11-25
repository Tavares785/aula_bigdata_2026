# Checkpoint de Progresso - Aula 13: Análise e Construção de Modelos

## Análise/modelo implementado

Implementamos em `src/analise.py` (Spark MLlib) um modelo que **prevê se uma
entrega vai atrasar**, usando a camada silver da Aula 12 (`pedidos_itens`).
Foram usados 8.836 itens entregues ou devolvidos com atraso conhecido, dos
quais 22,3% atrasaram.

- **Variáveis:** estado, transportadora, centro de distribuição, categoria,
  canal, segmento do cliente, forma de pagamento, prazo estimado, quantidade,
  valor total, desconto e mês do pedido. Ficaram de fora `prazo_real_dias`,
  `atraso_dias` e a nota, porque só existem depois da entrega e vazariam a
  resposta.
- **Modelos:** Random Forest (100 árvores, profundidade 8) e Regressão
  Logística como comparação. Os dois usam peso maior para a classe "atrasou",
  que é rara. Divisão 80% treino e 20% teste, com semente fixa.
- **Análises descritivas:** relação entre atraso e nota de avaliação, e
  percentual de atraso por mês.

`build_model_or_analysis` treina e avalia os modelos e calcula as análises.
`summarize_results` devolve um resumo simples. O código foi executado
localmente com PySpark sobre a silver gerada pelo ETL da Aula 12; não gastou
crédito do Learner Lab.

## Principais resultados até agora

- **Atraso e nota:** itens atrasados têm nota média de 2,67 contra 4,12 dos
  entregues no prazo. A nota é baixa (1 ou 2) em 47,3% dos atrasados e em 9,9%
  dos pontuais. A correlação entre dias de atraso e nota é de −0,49.
- **Sazonalidade:** o atraso fica entre 15% e 20% de janeiro a outubro e sobe
  para 35,2% em novembro e 31,8% em dezembro, quando também há mais pedidos
  (1.086 e 1.120 itens, contra cerca de 650 nos outros meses).
- **Modelo (conjunto de teste):** o Random Forest teve AUC de 0,669, recall de
  53% e precisão de 32% para a classe "atrasou". A Regressão Logística teve
  AUC de 0,651. O Random Forest ficou um pouco melhor.
- **Variáveis mais importantes:** mês do pedido (0,18), prazo estimado (0,13),
  valor total (0,08) e desconto (0,06).

O modelo tem poder preditivo fraco. Por causa do peso nas classes, a acurácia
(66,8%) fica abaixo da de um modelo que sempre responde "no prazo" (79,2%).
Ele acerta mais os atrasos, mas gera muitos alarmes falsos (409 falsos
positivos contra 194 acertos no teste).

## Iterações e ajustes feitos

- **Vazamento de dados:** retiramos do modelo as colunas de prazo real, dias de
  atraso e nota, que só existem depois da entrega.
- **Classe desbalanceada:** com 22% de atrasos, o primeiro caminho natural era
  prever sempre "no prazo". Adicionamos peso proporcional à classe rara e
  passamos a olhar AUC, recall e precisão, e não só a acurácia.
- **Comparação de modelos:** testamos Regressão Logística como referência
  contra o Random Forest.
- **Ambiente:** o PySpark 3.3 precisou de `numpy` e `setuptools` no Python 3.12
  local. Os imports do Spark ficam dentro das funções para o CI, que só
  instala o pytest, conseguir ler o arquivo.
- **Não funcionou:** as variáveis de cadastro e logística sozinhas explicam
  pouco do atraso. O sinal mais forte é o mês, o que combina com o pico de
  novembro e dezembro.

## Próxima etapa (Aula 14)

- Montar os gráficos finais a partir da gold e dos resultados: nota por faixa
  de atraso, atraso por mês e atraso por estado e transportadora.
- Testar melhorias no modelo (ajuste de hiperparâmetros, validação cruzada,
  limiar de decisão diferente de 0,5 e variáveis de sazonalidade como Black
  Friday e Natal) para reduzir os falsos positivos.
- Escrever a conclusão com recomendações: reforçar a logística em novembro e
  dezembro e acompanhar os atrasos, que derrubam a nota.
