"""Reproduz o ETL original localmente e salva apenas indicadores agregados."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from decimal import Decimal
from pyspark.sql import SparkSession
from analise import build_model_or_analysis, summarize_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--etl', required=True)
    parser.add_argument('--raw', required=True)
    parser.add_argument('--work', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--previous-commit', required=True)
    args = parser.parse_args()
    work, out = Path(args.work), Path(args.output)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('etl_aula12', args.etl)
    etl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etl)
    spark = (SparkSession.builder.master('local[2]').appName('MercadoFacil-Aula13')
             .config('spark.sql.shuffle.partitions', '4').config('spark.ui.enabled', 'false').getOrCreate())
    spark.sparkContext.setLogLevel('ERROR')
    try:
        etl.transform(spark, args.raw, str(work/'silver'), str(work/'gold'), str(work/'quarentena'))
        silver = spark.read.parquet(str(work/'silver')).cache()
        counts = {'raw': spark.read.option('header', True).csv(args.raw).count(),
                  'silver': silver.count(), 'quarentena': spark.read.parquet(str(work/'quarentena')).count()}
        assert counts['raw'] == counts['silver'] + counts['quarentena']
        assert not {'cliente_nome','cliente_cpf','cliente_email','cliente_id','comentario'}.intersection(silver.columns)
        result = summarize_results(build_model_or_analysis(silver))
        # Confronto integral com as duas Gold reproduzidas pelo ETL original.
        gold_delays = {r.estado: r.asDict() for r in spark.read.parquet(str(work/'gold/atrasos_estado')).collect()}
        assert set(gold_delays) == {r['estado'] for r in result['estado']}
        for r in result['estado']:
            g = gold_delays[r['estado']]
            assert (r['pedidos'],r['com_prazo'],r['atrasados']) == (g['pedidos'],g['pedidos_com_prazo'],g['pedidos_atrasados'])
            if g['taxa_atraso'] is not None:
                assert abs(r['taxa_atraso_pct'] - 100*g['taxa_atraso']) < 0.000051
        gold_sales = {(r.categoria,r.mes):r.asDict() for r in spark.read.parquet(str(work/'gold/vendas_categoria')).collect()}
        assert set(gold_sales) == {(r['categoria'],r['mes']) for r in result['vendas_categoria_mes']}
        for r in result['vendas_categoria_mes']:
            g = gold_sales[r['categoria'],r['mes']]
            assert r['itens']==g['itens'] and r['pedidos']==g['pedidos']
            for k in ('unidades','valor_bruto','valor_sem_cancelados_devolvidos'):
                assert Decimal(r[k]) == g[k]
        total = result['geral'][0]
        assert total['atrasados'] <= total['com_prazo'] <= total['pedidos']
        assert sum(r['pedidos'] for r in result['avaliacoes']) == total['pedidos']
        assert sum(r['itens'] for r in result['vendas_categoria_mes']) == counts['silver']
        print('VALIDACAO REAL: conciliacao, privacidade, indicadores e duas Gold OK')
        metadata = {'commit_aula12':args.previous_commit,'sha256_raw':hashlib.sha256(Path(args.raw).read_bytes()).hexdigest(),
                    'spark':spark.version,'contagens':counts,'validacao':'Gold de atrasos e vendas conciliadas integralmente'}
        (out/'resumo.json').write_text(json.dumps({'metadados':metadata, **result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for key, rows in result.items():
            with (out/f'{key}.csv').open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        print(json.dumps({'metadados':metadata,'geral':result['geral'],'avaliacoes':result['avaliacoes']},ensure_ascii=False,indent=2))
    finally:
        spark.stop()

if __name__ == '__main__':
    main()
