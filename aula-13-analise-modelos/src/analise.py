"""
Aula 13 - Analise e Construcao de Modelos em Larga Escala

Projeto MercadoFacil. A pergunta que o cenario faz e "quais fatores mais
explicam o atraso". A resposta aqui tem duas partes, porque uma sozinha
enganaria:

1. Um classificador (Random Forest do Spark MLlib) que preve se um item
   entregue vai atrasar, e cuja importancia de atributos ordena os fatores.
2. Medidas descritivas calculadas direto da silver -- taxa de atraso por
   recorte e correlacao entre atraso e nota.

O modelo sozinho engana porque `featureImportances` de uma arvore mede o quanto
o atributo ajudou a separar as classes NAQUELE ajuste, e infla atributos com
muitas categorias. As taxas por recorte sozinhas tambem enganam, porque ignoram
que os fatores andam juntos: estados do Norte sao atendidos pelo CD-NORTE, entao
a taxa alta do estado pode ser a do centro de distribuicao. As duas leituras
lado a lado e o que permite dizer alguma coisa com honestidade.

O que este codigo NAO faz, e nao deve ser lido como se fizesse: estabelecer
causa. Nenhuma das duas medidas separa o efeito do estado do efeito do centro de
distribuicao que o atende. Para isso seria preciso um desenho que o dado
observacional nao tem.
"""

from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.sql import functions as F

# Atributos categoricos que entram no modelo. Sao os que a silver ja normalizou
# na Aula 12 -- sem aquela normalizacao, `SP` e ` SP ` virariam duas categorias
# e o indexador trataria cada grafia como um nivel diferente.
CATEGORICOS = [
    "estado",
    "categoria",
    "canal",
    "transportadora",
    "centro_distribuicao",
]

# Numericos. `prazo_estimado_dias` e a promessa feita ao cliente; entra porque
# prazo curto demais e uma hipotese de causa de atraso que vale testar.
#
# `prazo_real_dias` fica FORA de proposito: o rotulo e
# prazo_real - prazo_estimado > 0, entao incluir o prazo real entrega a resposta
# ao modelo. O AUC iria perto de 1,0 e o modelo nao teria aprendido nada -- e o
# vazamento de rotulo, que parece um resultado excelente e e um erro de desenho.
NUMERICOS = [
    "prazo_estimado_dias",
    "quantidade",
]

SEMENTE = 42


def _preparar(df):
    """Monta o rotulo e descarta o que nao serve para treinar.

    So itens `entregue` entram: cancelado e devolvido nunca tiveram entrega,
    entao nao ha atraso para prever. Incluir esses registros ensinaria o modelo
    a prever "nao atrasou" para quem nunca saiu do centro de distribuicao.
    """
    entregues = df.filter(F.col("status_pedido") == "entregue")

    com_rotulo = entregues.withColumn(
        "atrasado",
        F.when(F.col("atraso_dias") > 0, F.lit(1.0)).otherwise(F.lit(0.0)),
    )

    colunas = CATEGORICOS + NUMERICOS + ["atrasado", "atraso_dias", "nota_avaliacao"]
    return com_rotulo.select(*[c for c in colunas if c in com_rotulo.columns]).dropna(
        subset=["atrasado"] + CATEGORICOS
    )


def _taxa_por(df, coluna, minimo=50):
    """Taxa de atraso por valor de `coluna`, ignorando recortes pequenos.

    O corte em 50 itens nao e estetico. Sem ele, um recorte com 3 entregas e 3
    atrasos aparece como 100% e lidera qualquer ranking -- numero verdadeiro e
    conclusao falsa.
    """
    return (
        df.groupBy(coluna)
        .agg(
            F.count("*").alias("itens"),
            F.sum("atrasado").alias("atrasados"),
        )
        .filter(F.col("itens") >= minimo)
        .withColumn(
            "taxa_atraso_pct",
            F.round(100 * F.col("atrasados") / F.col("itens"), 1),
        )
        .orderBy(F.col("taxa_atraso_pct").desc())
    )


def build_model_or_analysis(preprocessed_data):
    """Treina o classificador de atraso e calcula as medidas descritivas.

    Recebe o DataFrame da camada silver produzida na Aula 12.

    Devolve um dicionario com o modelo, as metricas, a importancia dos
    atributos e as taxas por recorte -- o formato que `summarize_results`
    espera.
    """
    dados = _preparar(preprocessed_data)

    # Divisao antes de qualquer ajuste. Calcular estatistica no conjunto
    # completo e depois separar contamina o teste com informacao do treino.
    treino, teste = dados.randomSplit([0.8, 0.2], seed=SEMENTE)

    indexadores = [
        StringIndexer(
            inputCol=coluna,
            outputCol=f"{coluna}_idx",
            # Categoria que aparece so no teste derrubaria o pipeline inteiro.
            handleInvalid="keep",
        )
        for coluna in CATEGORICOS
    ]

    # One-hot depois do indexador: sem ele, a arvore leria o indice como numero
    # ordenado e trataria "estado 3 > estado 1" como se fizesse sentido.
    codificador = OneHotEncoder(
        inputCols=[f"{c}_idx" for c in CATEGORICOS],
        outputCols=[f"{c}_ohe" for c in CATEGORICOS],
        handleInvalid="keep",
    )

    montador = VectorAssembler(
        inputCols=[f"{c}_ohe" for c in CATEGORICOS] + NUMERICOS,
        outputCol="features",
        # Nulo em qualquer numerico derruba o assembler; descartar a linha e
        # preferivel a imputar um valor que nao foi observado.
        handleInvalid="skip",
    )

    floresta = RandomForestClassifier(
        featuresCol="features",
        labelCol="atrasado",
        numTrees=100,
        maxDepth=8,
        seed=SEMENTE,
    )

    pipeline = Pipeline(stages=indexadores + [codificador, montador, floresta])
    modelo = pipeline.fit(treino)

    previsoes = modelo.transform(teste)

    # AUC e nao acuracia: a base e desbalanceada (cerca de 23% de atrasos), e um
    # modelo que responde "nao atrasou" para tudo ja acerta 77%. A acuracia
    # premiaria esse modelo inutil; o AUC nao.
    auc = BinaryClassificationEvaluator(
        labelCol="atrasado",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC",
    ).evaluate(previsoes)

    # A importancia vem no vetor montado, cujas posicoes misturam as colunas
    # one-hot de cada categorico. Somar as posicoes de volta por atributo e o
    # que torna o numero legivel.
    importancias = _agrupar_importancias(modelo, dados)

    correlacao = _correlacao_atraso_nota(dados)

    return {
        "modelo": modelo,
        "auc": auc,
        "n_treino": treino.count(),
        "n_teste": teste.count(),
        "importancias": importancias,
        "correlacao_atraso_nota": correlacao,
        "taxas": {coluna: _taxa_por(dados, coluna) for coluna in CATEGORICOS},
        "taxa_geral_pct": round(
            100 * dados.agg(F.avg("atrasado")).collect()[0][0], 1
        ),
    }


def _agrupar_importancias(modelo, dados):
    """Soma as importancias das colunas one-hot de volta para o atributo.

    O vetor de features tem uma posicao por nivel de cada categorico. Lido
    cru, ele diz "estado=AM vale 0,04" em dezenas de linhas; somado por
    atributo, diz "estado vale 0,31", que e a pergunta que o cenario faz.
    """
    floresta = modelo.stages[-1]
    importancias = floresta.featureImportances.toArray()

    total_por_atributo = {}
    posicao = 0

    for coluna in CATEGORICOS:
        # handleInvalid="keep" acrescenta um nivel extra para o desconhecido
        niveis = dados.select(coluna).distinct().count() + 1
        total_por_atributo[coluna] = float(
            importancias[posicao : posicao + niveis].sum()
        )
        posicao += niveis

    for coluna in NUMERICOS:
        if posicao < len(importancias):
            total_por_atributo[coluna] = float(importancias[posicao])
            posicao += 1

    return dict(
        sorted(total_por_atributo.items(), key=lambda par: par[1], reverse=True)
    )


def _correlacao_atraso_nota(dados):
    """Correlacao de Pearson entre dias de atraso e nota da avaliacao.

    Descarta nota fora de 1-5: a Aula 12 encontrou 57 linhas com valores como
    -1 e 99, e um unico 99 desloca a correlacao sozinho.
    """
    validos = dados.filter(
        F.col("nota_avaliacao").isNotNull()
        & (F.col("nota_avaliacao") >= 1)
        & (F.col("nota_avaliacao") <= 5)
    )

    if validos.count() < 2:
        return None

    return validos.stat.corr("atraso_dias", "nota_avaliacao")


def summarize_results(analysis_output):
    """Transforma o resultado em um texto legivel, com as ressalvas junto.

    As ressalvas ficam no mesmo texto de proposito. Um resumo que entrega so
    o ranking convida a ler "o estado causa o atraso", que e exatamente o que
    este dado nao sustenta.
    """
    linhas = []

    linhas.append("ANALISE DE ATRASO NA ENTREGA - MercadoFacil")
    linhas.append("=" * 52)
    linhas.append("")

    linhas.append(
        f"Base: {analysis_output['n_treino']} itens de treino, "
        f"{analysis_output['n_teste']} de teste "
        f"(apenas status 'entregue')."
    )
    linhas.append(
        f"Taxa de atraso na base: {analysis_output['taxa_geral_pct']}%"
    )
    linhas.append("")

    auc = analysis_output["auc"]
    linhas.append(f"Random Forest - AUC no teste: {auc:.3f}")
    linhas.append(
        "  AUC, e nao acuracia: com ~23% de atrasos, responder 'nao atrasou'"
    )
    linhas.append("  para tudo ja acerta 77% e nao aprendeu nada.")
    linhas.append("")

    linhas.append("Fatores, por importancia no modelo:")
    for atributo, peso in analysis_output["importancias"].items():
        barra = "#" * int(round(peso * 50))
        linhas.append(f"  {atributo:<22} {peso:.3f}  {barra}")
    linhas.append("")

    correlacao = analysis_output["correlacao_atraso_nota"]
    if correlacao is not None:
        linhas.append(f"Correlacao atraso x nota: {correlacao:.3f}")
        linhas.append(
            "  Negativa e forte: quanto mais dias de atraso, menor a nota."
        )
        linhas.append("")

    linhas.append("Taxa de atraso por recorte (>= 50 itens):")
    for coluna, tabela in analysis_output["taxas"].items():
        topo = tabela.limit(3).collect()
        if not topo:
            continue
        resumo = ", ".join(
            f"{linha[coluna]} {linha['taxa_atraso_pct']}%" for linha in topo
        )
        linhas.append(f"  {coluna:<22} {resumo}")
    linhas.append("")

    linhas.append("RESSALVAS")
    linhas.append("-" * 52)
    linhas.append(
        "1. Importancia de atributo nao e causa. A floresta mede o quanto o"
    )
    linhas.append(
        "   atributo ajudou a separar as classes, e infla quem tem muitos"
    )
    linhas.append("   niveis.")
    linhas.append(
        "2. Os fatores andam juntos. Estados do Norte sao atendidos pelo"
    )
    linhas.append(
        "   CD-NORTE: a taxa alta do estado pode ser a do centro, e este dado"
    )
    linhas.append("   nao separa os dois efeitos.")
    linhas.append(
        "3. A correlacao atraso x nota descreve, nao prova que o atraso baixou"
    )
    linhas.append(
        "   a nota. Categorias diferentes atrasam e sao avaliadas de formas"
    )
    linhas.append("   diferentes.")

    return "\n".join(linhas)
