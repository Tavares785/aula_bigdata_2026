"""Análise descritiva do MercadoFácil a partir da camada Silver da Aula 12."""
from pyspark.sql import functions as F


def build_model_or_analysis(preprocessed_data):
    """Recebe DataFrame Spark Silver; agrega indicadores por unidade adequada."""
    silver = preprocessed_data
    required = {'pedido_id', 'estado', 'transportadora', 'centro_distribuicao',
                'atraso_dias', 'nota_avaliacao', 'categoria', 'data_pedido',
                'status_pedido', 'valor_total', 'quantidade'}
    missing = required - set(silver.columns)
    if missing:
        raise ValueError(f'Colunas ausentes: {sorted(missing)}')

    def orders_for(dim):
        # Um pedido por grupo, sem multiplicar a observação por número de itens.
        base = silver.fillna({dim: 'desconhecido'}) if dim else silver
        keys = ['pedido_id'] + ([dim] if dim else [])
        return base.groupBy(*keys).agg(
            F.max('atraso_dias').alias('atraso'),
            F.avg('nota_avaliacao').alias('nota'))

    def logistics(orders, dimension=None):
        grouped = orders.groupBy(*([dimension] if dimension else []))
        return grouped.agg(
            F.count('*').alias('pedidos'),
            F.count('atraso').alias('com_prazo'),
            F.sum(F.when(F.col('atraso') > 0, 1).otherwise(0)).alias('atrasados'),
            F.round(F.avg('atraso'), 4).alias('media_atraso_dias'),
            F.count('nota').alias('com_nota'),
            F.round(F.avg('nota'), 4).alias('media_nota')
        ).withColumn('taxa_atraso_pct', F.when(F.col('com_prazo') > 0,
            F.round(100.0 * F.col('atrasados') / F.col('com_prazo'), 4)))

    orders = orders_for(None)
    ratings = orders.withColumn('situacao', F.when(F.col('atraso').isNull(), 'prazo desconhecido')
        .when(F.col('atraso') > 0, 'atrasado').otherwise('pontual')).groupBy('situacao').agg(
            F.count('*').alias('pedidos'), F.count('nota').alias('com_nota'),
            F.round(F.avg('nota'), 4).alias('media_nota'))
    sales = silver.groupBy('categoria', F.date_format('data_pedido', 'yyyy-MM').alias('mes')).agg(
        F.count('*').alias('itens'), F.countDistinct('pedido_id').alias('pedidos'),
        F.sum('quantidade').alias('unidades'), F.sum('valor_total').alias('valor_bruto'),
        F.sum(F.when(F.col('status_pedido').isin('cancelado','cancelada','devolvido','devolvida'),
                     F.lit(0)).otherwise(F.col('valor_total'))).alias('valor_sem_cancelados_devolvidos'))
    sales = sales.withColumn('valor_cancelados_devolvidos',
        F.col('valor_bruto') - F.col('valor_sem_cancelados_devolvidos'))
    result = {'geral': logistics(orders), 'avaliacoes': ratings.orderBy('situacao'),
              'vendas_categoria_mes': sales.orderBy('mes', 'categoria')}
    for dim in ('estado','transportadora','centro_distribuicao'):
        result[dim] = logistics(orders_for(dim), dim).orderBy(F.desc_nulls_last('taxa_atraso_pct'), dim)
    return result


def summarize_results(analysis_output):
    """Materializa somente agregados pequenos; decimais monetários são strings exatas."""
    from decimal import Decimal
    def encode(value):
        if isinstance(value, Decimal):
            return format(value, 'f')
        return value
    return {key: [{k: encode(v) for k, v in row.asDict().items()}
                  for row in df.collect()] for key, df in analysis_output.items()}
