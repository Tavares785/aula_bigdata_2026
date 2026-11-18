"""
Aula 13 - Analise e Construcao de Modelos em Larga Escala
Etapa do projeto: implemente aqui a analise, o modelo de Machine
Learning ou o pipeline de NLP do seu grupo, usando os dados ja
pre-processados na Aula 12.

Assim como no arquivo da Aula 12, o CI verifica apenas se as funcoes
abaixo foram implementadas (estrutura), nao se os RESULTADOS estao
corretos -- isso depende do dataset e do problema escolhidos pelo seu
grupo, e e avaliado pelo professor na revisao da PR.
"""


def build_model_or_analysis(preprocessed_data):
    """
    Implemente aqui a analise principal do seu projeto: pode ser o
    treinamento de um modelo de classificacao/clustering/regressao com
    Spark MLlib, um pipeline de NLP (analise de sentimento, topicos),
    ou outra tecnica de analise de dados em larga escala vista no
    curso.

    Retorne o resultado da analise (ex: um modelo treinado, um
    DataFrame com os resultados, etc.) -- o formato fica a criterio do
    seu grupo, desde que `summarize_results` (abaixo) saiba lidar com
    ele.
    """
    raise NotImplementedError("Implemente a analise/modelo do seu projeto")


def summarize_results(analysis_output):
    """
    Receba o resultado de `build_model_or_analysis` e produza um
    resumo dos resultados (ex: metricas do modelo, principais insights
    encontrados, tabela de topicos mais frequentes, etc.) em um formato
    legivel -- pode ser uma string, um dicionario ou um DataFrame
    pequeno com os resultados finais.
    """
    raise NotImplementedError("Implemente o resumo dos resultados do seu projeto")
