import sys
from pyspark.sql import SparkSession, functions as F, Window


def transform(spark, raw_path, silver_path, gold_path, quarantine_path):
    spark.conf.set('spark.sql.ansi.enabled', 'false')
    spark.conf.set('spark.sql.legacy.timeParserPolicy', 'CORRECTED')
    raw = spark.read.option('header', True).option('mode', 'FAILFAST').csv(raw_path)
    required = {'pedido_id','item_id','data_pedido','estado','categoria','canal','status_pedido','quantidade','preco_unitario','valor_total','prazo_estimado_dias','prazo_real_dias','atraso_dias','nota_avaliacao'}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f'Colunas ausentes: {sorted(missing)}')
    # Remove identifiers and free text before any downstream write.
    df = raw.drop('cliente_nome','cliente_email','cliente_cpf','cliente_id','comentario')
    for name in df.columns:
        cleaned = F.trim(F.col(name))
        df = df.withColumn(name, F.when(F.lower(cleaned).isin('', 'null', 'none', 'n/a', 'nan', 'na'), None).otherwise(cleaned))
    for name in ('estado','sku','pedido_id','item_id'):
        if name in df.columns:
            df = df.withColumn(name, F.upper(F.col(name)))
    for name in ('categoria','canal','status_pedido','forma_pagamento','cliente_segmento','transportadora','centro_distribuicao'):
        if name in df.columns:
            df = df.withColumn(name, F.lower(F.regexp_replace(F.col(name), r'\s+', ' ')))
    for name in ('data_pedido','data_entrega','cliente_data_cadastro'):
        if name in df.columns:
            c=F.col(name)
            df=df.withColumn(name,F.coalesce(F.to_date(c,'yyyy-MM-dd'),F.to_date(c,'dd/MM/yyyy'),F.to_date(c,'yyyy/MM/dd')))
    for name in ('preco_unitario','custo_unitario','desconto_pct','valor_total','quantidade','parcelas','prazo_estimado_dias','prazo_real_dias','atraso_dias','nota_avaliacao'):
        if name in df.columns:
            c=F.col(name)
            normalized=F.when(c.contains(',') & c.contains('.'),F.when(F.instr(c,',')>F.instr(c,'.'),F.regexp_replace(F.regexp_replace(c,r'\.', ''),',','.')).otherwise(F.regexp_replace(c,',',''))).otherwise(F.regexp_replace(c,',','.'))
            df=df.withColumn(name,normalized.cast('decimal(18,4)'))
    ufs='AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
    invalid = F.concat_ws('; ',
        F.when(F.col('pedido_id').isNull() | F.col('item_id').isNull(),'identificador ausente'),
        F.when(F.col('data_pedido').isNull(),'data pedido invalida'),
        F.when(F.col('estado').isNull() | ~F.col('estado').isin(ufs),'UF invalida'),
        F.when(F.col('quantidade').isNull() | (F.col('quantidade')<=0) | (F.col('quantidade')!=F.floor('quantidade')),'quantidade invalida'),
        F.when(F.col('preco_unitario').isNull() | (F.col('preco_unitario')<0),'preco invalido'),
        F.when(F.col('valor_total').isNull() | (F.col('valor_total')<0),'valor invalido'),
        F.when(F.col('prazo_estimado_dias')<0,'prazo estimado negativo'),
        F.when(F.col('prazo_real_dias')<0,'prazo real negativo'),
        F.when((F.col('nota_avaliacao')<1)|(F.col('nota_avaliacao')>5),'nota fora de 1 a 5'))
    df=df.withColumn('motivo_quarentena',invalid)
    bad=df.filter(F.length('motivo_quarentena')>0)
    good=df.filter(F.length('motivo_quarentena')==0)
    # A repeated item key with different payload is ambiguous: quarantine all conflicting copies.
    payload=[c for c in good.columns if c!='motivo_quarentena']
    good=good.withColumn('_hash',F.sha2(F.to_json(F.struct(*payload)),256))
    keys=['pedido_id','item_id']
    conflicts=good.groupBy(*keys).agg(F.countDistinct('_hash').alias('versions')).filter('versions > 1').select(*keys)
    ambiguous=good.join(conflicts,keys,'inner').drop('_hash').withColumn('motivo_quarentena',F.lit('chave de item com conteudos conflitantes'))
    good=good.join(conflicts,keys,'left_anti')
    w=Window.partitionBy(*keys).orderBy('_hash')
    ranked=good.withColumn('_rn',F.row_number().over(w))
    duplicates=ranked.filter('_rn > 1').drop('_rn','_hash').withColumn('motivo_quarentena',F.lit('copia duplicada do item'))
    silver=ranked.filter('_rn = 1').drop('_rn','_hash','motivo_quarentena')
    for name in ('categoria','canal','status_pedido'):
        silver=silver.fillna({name:'desconhecido'})
    # Delay recalculated only when both nonnegative durations exist; no unknown-as-zero imputation.
    silver=silver.withColumn('atraso_dias',F.when(F.col('prazo_real_dias').isNotNull() & F.col('prazo_estimado_dias').isNotNull(),F.greatest(F.lit(0),F.col('prazo_real_dias')-F.col('prazo_estimado_dias'))))
    quarantine=bad.unionByName(ambiguous).unionByName(duplicates)
    silver=silver.cache(); quarantine=quarantine.cache()
    n_raw=raw.count(); n_good=silver.count(); n_bad=quarantine.count()
    if n_raw != n_good+n_bad or n_good==0:
        raise ValueError(f'Falha conciliacao: raw={n_raw}, silver={n_good}, quarentena={n_bad}')
    print(f'CONTAGENS: raw={n_raw}, silver={n_good}, quarentena={n_bad}')
    silver.write.mode('overwrite').parquet(silver_path)
    quarantine.write.mode('overwrite').parquet(quarantine_path)
    # One row per order/state avoids weighting delays by number of items.
    order=silver.groupBy('pedido_id','estado').agg(F.max('atraso_dias').alias('atraso'),F.avg('nota_avaliacao').alias('nota'))
    delays=order.groupBy('estado').agg(F.count('*').alias('pedidos'),F.count('atraso').alias('pedidos_com_prazo'),F.sum(F.when(F.col('atraso')>0,1).otherwise(0)).alias('pedidos_atrasados'),F.avg('atraso').alias('media_atraso_dias'),F.avg('nota').alias('media_nota'))
    delays=delays.withColumn('taxa_atraso',F.when(F.col('pedidos_com_prazo')>0,F.col('pedidos_atrasados')/F.col('pedidos_com_prazo')))
    sales=silver.groupBy('categoria',F.date_format('data_pedido','yyyy-MM').alias('mes')).agg(F.count('*').alias('itens'),F.countDistinct('pedido_id').alias('pedidos'),F.sum('quantidade').alias('unidades'),F.sum(F.when(F.col('status_pedido').isin('cancelado','cancelada','devolvido','devolvida'),F.lit(0)).otherwise(F.col('valor_total'))).alias('valor_sem_cancelados_devolvidos'),F.sum('valor_total').alias('valor_bruto'))
    delays.write.mode('overwrite').parquet(gold_path.rstrip('/')+'/atrasos_estado')
    sales.write.mode('overwrite').parquet(gold_path.rstrip('/')+'/vendas_categoria')
    silver.unpersist(); quarantine.unpersist()


if __name__=='__main__':
    from awsglue.utils import getResolvedOptions
    from awsglue.context import GlueContext
    from awsglue.job import Job
    from pyspark.context import SparkContext
    args=getResolvedOptions(sys.argv,['JOB_NAME','RAW_PATH','SILVER_PATH','GOLD_PATH','QUARANTINE_PATH'])
    context=GlueContext(SparkContext.getOrCreate())
    job=Job(context); job.init(args['JOB_NAME'],args)
    transform(context.spark_session,args['RAW_PATH'],args['SILVER_PATH'],args['GOLD_PATH'],args['QUARANTINE_PATH'])
    job.commit()
