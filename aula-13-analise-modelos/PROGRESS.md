# Checkpoint de Progresso - Aula 13: Análise e Construção de Modelos

**Grupo:** José Henrique Teixeira Luiz (3225002), Daniel de Oliveira
Tavares Júnior (6325032), Leandro Duarte (6325072)

## Análise/modelo implementado

A pergunta do cenário MercadoFácil é **quais fatores mais explicam o atraso na
entrega**. Implementamos duas leituras em `src/analise.py`, porque qualquer uma
delas sozinha engana.

**Um classificador.** Random Forest do Spark MLlib (100 árvores, profundidade
8) que prevê se um item entregue vai atrasar. Entram cinco atributos
categóricos — `estado`, `categoria`, `canal`, `transportadora`,
`centro_distribuicao` — passando por `StringIndexer` e `OneHotEncoder`, mais
`prazo_estimado_dias` e `quantidade`. A `featureImportances` da floresta ordena
os fatores.

**Medidas descritivas.** Taxa de atraso por recorte e correlação de Pearson
entre dias de atraso e nota da avaliação, calculadas direto da silver.

Três decisões de desenho que mudam o resultado:

**`prazo_real_dias` ficou de fora do modelo, de propósito.** O rótulo é
`prazo_real - prazo_estimado > 0`. Incluir o prazo real entregaria a resposta ao
modelo: o AUC iria perto de 1,0 e ele não teria aprendido nada. É vazamento de
rótulo — parece um resultado excelente e é erro de desenho.

**A métrica é AUC, não acurácia.** A base tem cerca de 23% de atrasos. Um modelo
que responde "não atrasou" para tudo já acerta 77%, e a acurácia premiaria esse
modelo inútil.

**Só itens com status `entregue`.** Cancelado e devolvido nunca tiveram entrega,
então não há atraso a prever. Incluí-los ensinaria o modelo a prever "não
atrasou" para quem nunca saiu do centro de distribuição.

## Principais resultados até agora

> **Como estes números foram obtidos.** O código do `analise.py` é PySpark e
> **não foi executado** — a máquina de desenvolvimento não tem Java, e a sessão
> do Learner Lab usada na Aula 12 já expirou. Para não apresentar resultados
> supostos, os números abaixo vêm de uma replicação das regras da silver feita
> com a biblioteca padrão do Python sobre o **mesmo CSV** de 10.000 linhas. São
> medições reais do dado; o que falta confirmar é a execução distribuída.

Base após deduplicar por `item_id`: 9.800 itens únicos (200 duplicados
removidos). Desfechos: 8.619 entregues, 695 cancelados, 486 devolvidos. Dos
entregues, 8.613 têm atraso calculável, e **2.002 atrasaram — 23,2%**.

**O centro de distribuição separa mais que a categoria.** Taxa de atraso por
recorte, com no mínimo 50 itens:

| Recorte | Maior | Menor | Amplitude |
|---|---|---|---|
| Estado | AM 42,7% (n=213) | DF 17,7% (n=316) | **25,0 p.p.** |
| Centro de distribuição | CD-NORTE 35,6% (n=357) | CD-CENTRO-OESTE 17,4% | **18,2 p.p.** |
| Canal | marketplace_parceiro 34,4% | App 19,0% | 15,4 p.p. |
| Transportadora | Correios 26,9% (n=3.157) | LOGGI 16,9% | 12,7 p.p. |
| **Categoria** | Esportes 25,8% | Beleza e Saúde 20,9% | **4,9 p.p.** |

A categoria é o fator que **menos** separa: 4,9 pontos percentuais entre o pior
e o melhor, contra 25,0 do estado. É um resultado útil justamente por ser
negativo — a hipótese intuitiva de que "produto X atrasa mais" não se sustenta
neste dado.

**Atraso e nota andam juntos, e forte.** Correlação de Pearson entre dias de
atraso e nota: **−0,527** (n = 8.149 avaliações válidas). A nota média é
**4,24** nos itens entregues no prazo e **2,76** nos atrasados — uma diferença
de 1,48 estrela.

**Sazonalidade confirmada em novembro e dezembro.** A taxa fica entre 16,6% e
22,2% de janeiro a outubro, e salta para **35,9% em novembro** e **31,2% em
dezembro**. Black Friday e Natal aparecem no dado.

## Iterações e ajustes feitos

**Primeiro erro: medir sem corte mínimo.** O primeiro ranking por recorte trouxe
vários 100% de atraso no topo. Pareciam o achado principal e eram recortes com
3 ou 4 itens. O corte em 50 itens por recorte entrou por isso — número
verdadeiro e conclusão falsa é pior que não medir.

**Segundo: o nome da coluna.** A primeira medição não produziu nada para a
relação atraso × nota, em silêncio. A coluna é `nota_avaliacao`, e o código
procurava `avaliacao_nota`. Não houve erro: a seção simplesmente não apareceu,
porque a lista ficou vazia. Trocar a ordem de duas palavras custou uma rodada
inteira.

**Terceiro, e o mais sério: datas impossíveis que a Aula 12 aceita.** A medição
por mês trouxe dois grupos que não deveriam existir: `0000-00` e **`2025-13`**.
No CSV bruto são **27 linhas com `0000-00-00`** e **24 com `2025-13-45`** — mês
13, dia 45.

A `para_data` da Aula 12 testa o formato com
`rlike("^\\d{4}-\\d{2}-\\d{2}")` antes de converter. Essa expressão aceita
`2025-13-45`: ela confere a **forma**, não o **intervalo**. O que acontece
depois, no `to_date` com a política estrita do Glue 4.0, é o que ainda não
sabemos — pode devolver `NULL` ou lançar exceção, como lançou no primeiro
`FAILED` daquela aula.

O job da Aula 12 terminou `SUCCEEDED`, o que sugere `NULL`. Mas essa é
exatamente a suposição que já quebrou aquele job uma vez, e não vamos repetir o
erro de afirmar sem medir. Fica como o primeiro item da Aula 14, para ser
resolvido com Spark na mão.

**Quarto: o que não entrou.** Consideramos um pipeline de NLP sobre a coluna
`comentario`, já que ela existe no dataset. Ficou de fora porque a pergunta do
cenário é sobre atraso, e análise de sentimento em comentário responderia outra
coisa. Preferimos uma análise que responde a pergunta feita a duas que a
tangenciam.

## Próxima etapa (Aula 14)

1. **Executar o `analise.py` de verdade**, com Spark, e comparar o AUC e o
   ranking de importância com as taxas descritivas medidas aqui. Se a floresta
   ordenar os fatores de forma muito diferente das taxas, a divergência é o
   achado — provavelmente o efeito conjunto entre estado e centro de
   distribuição.
2. **Resolver a dúvida das datas impossíveis.** Testar `to_date("2025-13-45")`
   no Spark do Glue e, conforme o resultado, acrescentar validação de intervalo
   à `para_data` ou mandar essas 51 linhas para a quarentena com o motivo.
3. **Separar estado de centro de distribuição.** Hoje o dado não distingue os
   dois efeitos. Uma tabela cruzada estado × CD, com o corte mínimo, mostraria
   se a taxa do AM se mantém alta dentro do mesmo centro.
4. **Visualização**, que é o foco da Aula 14: a sazonalidade de novembro e
   dezembro e a queda de nota por faixa de atraso são as duas que mais
   comunicam, porque têm contraste grande e leitura direta.
5. **Revisar a quarentena** da Aula 12 por `motivo_quarentena`, e decidir caso a
   caso o que dá para recuperar.

Uma ressalva que atravessa tudo: **nada aqui estabelece causa**. Nem a
importância de atributo da floresta, nem a correlação de −0,527. Estados do
Norte são atendidos pelo CD-NORTE, então a taxa alta do estado pode ser a do
centro. O que este dado sustenta é descrição e comparação; afirmação causal
exigiria um desenho que ele não tem.
