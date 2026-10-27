from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


def build_feature_vector(df, feature_cols):
    # O VectorAssembler recebe a lista de colunas (inputCols) e as condensa 
    # em uma única coluna vetorial chamada "features" (outputCol).
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    
    # O método transform aplica essa mudança ao DataFrame original.
    return assembler.transform(df)


def train_classifier(train_df, label_col="label"):
    # Instanciamos a Regressão Logística apontando onde estão as variáveis (features)
    # e onde está a resposta correta (label).
    lr = LogisticRegression(featuresCol="features", labelCol=label_col)
    
    # O método fit() faz o treinamento distribuído do modelo nos dados.
    return lr.fit(train_df)


def evaluate_accuracy(model, test_df, label_col="label"):
    # O modelo treinado usa o método transform() para gerar as previsões 
    # nos dados de teste (isso criará uma coluna "prediction").
    predictions = model.transform(test_df)
    
    # Configuramos o avaliador multiclasse pedindo especificamente a métrica "accuracy".
    evaluator = MulticlassClassificationEvaluator(
        labelCol=label_col, 
        predictionCol="prediction", 
        metricName="accuracy"
    )
    
    # Calculamos a métrica comparando o "label" real com o "prediction" gerado.
    return evaluator.evaluate(predictions)