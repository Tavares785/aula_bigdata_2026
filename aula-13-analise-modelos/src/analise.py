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

from pyspark.sql import DataFrame
from pyspark.ml.feature import VectorAssembler, StandardScaler, StringIndexer
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml import Pipeline
from pyspark.sql.functions import col, count, avg, stddev, min as spark_min, max as spark_max


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
    
    # Analise exploratoria inicial
    data_stats = preprocessed_data.describe()
    total_records = preprocessed_data.count()
    
    # Identificar colunas numericas e categoricas
    numeric_cols = [field.name for field in preprocessed_data.schema.fields 
                   if str(field.dataType) in ['IntegerType', 'DoubleType', 'FloatType', 'LongType']]
    
    categorical_cols = [field.name for field in preprocessed_data.schema.fields 
                       if str(field.dataType) == 'StringType']
    
    # Preparar features para modelagem
    # Remove a coluna target se existir nas features
    feature_cols = [c for c in numeric_cols if c not in ['label', 'target', 'id']]
    
    # Se tiver colunas categoricas, fazer encoding
    indexers = []
    indexed_cols = []
    if categorical_cols:
        for cat_col in categorical_cols:
            if cat_col not in ['label', 'target', 'id']:
                indexer = StringIndexer(inputCol=cat_col, 
                                      outputCol=f"{cat_col}_indexed",
                                      handleInvalid="keep")
                indexers.append(indexer)
                indexed_cols.append(f"{cat_col}_indexed")
    
    # Combinar features
    all_feature_cols = feature_cols + indexed_cols
    
    # Criar pipeline de feature engineering
    assembler = VectorAssembler(inputCols=all_feature_cols, 
                                outputCol="raw_features",
                                handleInvalid="skip")
    
    scaler = StandardScaler(inputCol="raw_features", 
                           outputCol="features",
                           withStd=True, 
                           withMean=True)
    
    # Decidir tipo de modelo baseado nos dados
    has_label = 'label' in preprocessed_data.columns or 'target' in preprocessed_data.columns
    
    if has_label:
        # Problema supervisionado (classificacao)
        label_col = 'label' if 'label' in preprocessed_data.columns else 'target'
        
        # Verificar numero de classes
        n_classes = preprocessed_data.select(label_col).distinct().count()
        
        # Split treino/teste
        train_data, test_data = preprocessed_data.randomSplit([0.8, 0.2], seed=42)
        
        # Escolher modelo
        if n_classes == 2:
            # Classificacao binaria
            classifier = LogisticRegression(labelCol=label_col, 
                                          featuresCol="features",
                                          maxIter=100,
                                          regParam=0.01)
            evaluator = BinaryClassificationEvaluator(labelCol=label_col)
        else:
            # Classificacao multiclasse
            classifier = RandomForestClassifier(labelCol=label_col,
                                               featuresCol="features",
                                               numTrees=50,
                                               maxDepth=10,
                                               seed=42)
            evaluator = MulticlassClassificationEvaluator(labelCol=label_col,
                                                         predictionCol="prediction")
        
        # Criar e treinar pipeline
        pipeline_stages = indexers + [assembler, scaler, classifier]
        pipeline = Pipeline(stages=pipeline_stages)
        
        model = pipeline.fit(train_data)
        
        # Fazer predicoes
        train_predictions = model.transform(train_data)
        test_predictions = model.transform(test_data)
        
        # Avaliar modelo
        if n_classes == 2:
            train_metric = evaluator.evaluate(train_predictions, {evaluator.metricName: "areaUnderROC"})
            test_metric = evaluator.evaluate(test_predictions, {evaluator.metricName: "areaUnderROC"})
            metric_name = "AUC-ROC"
        else:
            train_metric = evaluator.evaluate(train_predictions, {evaluator.metricName: "accuracy"})
            test_metric = evaluator.evaluate(test_predictions, {evaluator.metricName: "accuracy"})
            metric_name = "Accuracy"
        
        # F1 Score para ambos os casos
        f1_evaluator = MulticlassClassificationEvaluator(labelCol=label_col,
                                                        predictionCol="prediction",
                                                        metricName="f1")
        train_f1 = f1_evaluator.evaluate(train_predictions)
        test_f1 = f1_evaluator.evaluate(test_predictions)
        
        results = {
            'model_type': 'supervised_classification',
            'n_classes': n_classes,
            'trained_model': model,
            'train_predictions': train_predictions,
            'test_predictions': test_predictions,
            'train_size': train_data.count(),
            'test_size': test_data.count(),
            'metrics': {
                'train': {metric_name: train_metric, 'F1': train_f1},
                'test': {metric_name: test_metric, 'F1': test_f1}
            },
            'data_stats': data_stats,
            'total_records': total_records,
            'feature_count': len(all_feature_cols)
        }
        
    else:
        # Problema nao-supervisionado (clustering)
        # Criar pipeline
        pipeline_stages = indexers + [assembler, scaler]
        pipeline = Pipeline(stages=pipeline_stages)
        
        # Aplicar transformacoes
        pipeline_model = pipeline.fit(preprocessed_data)
        transformed_data = pipeline_model.transform(preprocessed_data)
        
        # Determinar k otimo usando elbow method (testando alguns valores)
        k_values = [2, 3, 4, 5]
        inertias = []
        
        for k in k_values:
            kmeans = KMeans(k=k, seed=42, featuresCol="features")
            kmeans_model = kmeans.fit(transformed_data)
            inertias.append(kmeans_model.summary.trainingCost)
        
        # Usar k=3 como padrao (ou o melhor baseado no elbow)
        best_k = 3
        kmeans = KMeans(k=best_k, seed=42, featuresCol="features", predictionCol="cluster")
        kmeans_model = kmeans.fit(transformed_data)
        
        # Fazer predicoes
        predictions = kmeans_model.transform(transformed_data)
        
        # Estatisticas por cluster
        cluster_stats = predictions.groupBy("cluster").agg(
            count("*").alias("count"),
            *[avg(col(c)).alias(f"avg_{c}") for c in feature_cols[:3]]  # Primeiras 3 features
        ).orderBy("cluster")
        
        results = {
            'model_type': 'unsupervised_clustering',
            'k': best_k,
            'trained_model': kmeans_model,
            'predictions': predictions,
            'cluster_stats': cluster_stats,
            'inertia_by_k': dict(zip(k_values, inertias)),
            'data_stats': data_stats,
            'total_records': total_records,
            'feature_count': len(all_feature_cols),
            'cluster_centers': kmeans_model.clusterCenters()
        }
    
    return results


def summarize_results(analysis_output):
    """
    Receba o resultado de `build_model_or_analysis` e produza um
    resumo dos resultados (ex: metricas do modelo, principais insights
    encontrados, tabela de topicos mais frequentes, etc.) em um formato
    legivel -- pode ser uma string, um dicionario ou um DataFrame
    pequeno com os resultados finais.
    """
    
    model_type = analysis_output.get('model_type', 'unknown')
    total_records = analysis_output.get('total_records', 0)
    feature_count = analysis_output.get('feature_count', 0)
    
    summary = []
    summary.append("=" * 70)
    summary.append("RESUMO DA ANALISE DE DADOS - AULA 13")
    summary.append("=" * 70)
    summary.append(f"\nTotal de registros processados: {total_records:,}")
    summary.append(f"Numero de features utilizadas: {feature_count}")
    summary.append("")
    
    if model_type == 'supervised_classification':
        n_classes = analysis_output.get('n_classes', 0)
        metrics = analysis_output.get('metrics', {})
        train_size = analysis_output.get('train_size', 0)
        test_size = analysis_output.get('test_size', 0)
        
        summary.append(f"Tipo de Modelo: Classificacao Supervisionada")
        summary.append(f"Numero de Classes: {n_classes}")
        summary.append(f"Divisao: {train_size:,} treino / {test_size:,} teste")
        summary.append("")
        summary.append("METRICAS DE DESEMPENHO:")
        summary.append("-" * 70)
        
        train_metrics = metrics.get('train', {})
        test_metrics = metrics.get('test', {})
        
        for metric_name, value in train_metrics.items():
            summary.append(f"  {metric_name} (Treino): {value:.4f}")
        
        summary.append("")
        for metric_name, value in test_metrics.items():
            summary.append(f"  {metric_name} (Teste):  {value:.4f}")
        
        summary.append("")
        summary.append("INTERPRETACAO:")
        summary.append("-" * 70)
        
        # Analise de overfitting
        primary_metric = list(train_metrics.keys())[0]
        train_val = train_metrics[primary_metric]
        test_val = test_metrics[primary_metric]
        diff = abs(train_val - test_val)
        
        if diff < 0.05:
            summary.append("  ✓ Modelo bem balanceado (baixo overfitting)")
        elif diff < 0.10:
            summary.append("  ⚠ Pequeno overfitting detectado")
        else:
            summary.append("  ✗ Alto overfitting - considerar regularizacao")
        
        if test_val > 0.8:
            summary.append("  ✓ Excelente performance preditiva")
        elif test_val > 0.7:
            summary.append("  ✓ Boa performance preditiva")
        elif test_val > 0.6:
            summary.append("  ⚠ Performance moderada - pode melhorar")
        else:
            summary.append("  ✗ Performance baixa - revisar features ou modelo")
        
    elif model_type == 'unsupervised_clustering':
        k = analysis_output.get('k', 0)
        inertia_by_k = analysis_output.get('inertia_by_k', {})
        cluster_stats = analysis_output.get('cluster_stats')
        
        summary.append(f"Tipo de Modelo: Clustering Nao-Supervisionado (K-Means)")
        summary.append(f"Numero de Clusters: {k}")
        summary.append("")
        summary.append("INERCIA POR VALOR DE K (Elbow Method):")
        summary.append("-" * 70)
        
        for k_val, inertia in sorted(inertia_by_k.items()):
            summary.append(f"  k={k_val}: {inertia:.2f}")
        
        summary.append("")
        summary.append("DISTRIBUICAO DOS CLUSTERS:")
        summary.append("-" * 70)
        
        if cluster_stats is not None:
            cluster_data = cluster_stats.collect()
            for row in cluster_data:
                cluster_id = row['cluster']
                count = row['count']
                percentage = (count / total_records) * 100
                summary.append(f"  Cluster {cluster_id}: {count:,} registros ({percentage:.1f}%)")
        
        summary.append("")
        summary.append("INTERPRETACAO:")
        summary.append("-" * 70)
        summary.append(f"  • Dados segmentados em {k} grupos distintos")
        summary.append("  • Cada cluster representa um padrao de comportamento diferente")
        summary.append("  • Analise as features medias por cluster para interpretar os grupos")
    
    else:
        summary.append("Tipo de analise nao reconhecido.")
    
    summary.append("")
    summary.append("=" * 70)
    summary.append("Proximos passos: visualizacao e interpretacao de negocio (Aula 14)")
    summary.append("=" * 70)
    
    return "\n".join(summary)
