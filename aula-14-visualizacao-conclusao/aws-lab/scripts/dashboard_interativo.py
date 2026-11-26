"""Dashboard interativo local da Aula 14 – MercadoFácil.

Gera HTML independente do servidor Python, com Chart.js via CDN.
Filtros de região e mês recalculam os KPIs e seis gráficos.
Execute na pasta aula-14-visualizacao-conclusao:
    python3 aws-lab/scripts/dashboard_interativo.py
"""
import csv
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV = BASE.parent / 'data' / 'pedidos_mercadofacil_tratado.csv'
CHUVA = BASE.parent / 'data' / 'chuva_diaria.csv'
SAIDA = BASE / 'dashboard_interativo.html'


def carregar():
    with CSV.open(encoding='utf-8-sig', newline='') as f:
        pedidos = list(csv.DictReader(f))
    with CHUVA.open(encoding='utf-8-sig', newline='') as f:
        chuva = {}
        for r in csv.DictReader(f):
            try:
                chuva[(r['cidade'], r['dia'])] = float(r['chuva_3d_mm'])
            except (ValueError, KeyError):
                pass
    campos = ('pedido_id', 'data_pedido', 'status_pedido', 'regiao', 'categoria',
              'valor_total', 'atraso_dias', 'nota_avaliacao', 'cidade')
    if not pedidos or any(c not in pedidos[0] for c in campos):
        raise ValueError('O CSV de pedidos esta vazio ou possui colunas ausentes.')

    def numero(v):
        try:
            return float(v) if v not in ('', None) else None
        except ValueError:
            return None

    linhas = []
    for r in pedidos:
        linhas.append({
            'pedido': r['pedido_id'], 'mes': r['data_pedido'][:7],
            'dia': r['data_pedido'][:10], 'regiao': r['regiao'],
            'categoria': r['categoria'], 'status': r['status_pedido'],
            'valor': numero(r['valor_total']), 'atraso': numero(r['atraso_dias']),
            'nota': numero(r['nota_avaliacao']),
            'chuva': chuva.get((r['cidade'], r['data_pedido'][:10]))
        })
    return linhas


HTML = r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MercadoFácil 2025 | Painel executivo</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js"></script>
<style>
:root{font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;color:#1c273a;background:#eef2f7}
*{box-sizing:border-box}body{margin:0}.wrap{max-width:1450px;margin:auto;padding:30px 24px 50px}
header{display:flex;justify-content:space-between;gap:24px;align-items:end;flex-wrap:wrap;margin-bottom:22px}
h1{font-size:29px;letter-spacing:-.04em;margin:5px 0}.sub{color:#64748b;margin:3px 0 0;font-size:14px}
.eyebrow{font-size:11px;font-weight:750;text-transform:uppercase;letter-spacing:.17em;color:#3974b8}
.filters{display:flex;gap:12px;flex-wrap:wrap}.filter{display:grid;gap:5px;font-size:12px;font-weight:700;color:#475569}
select{min-width:160px;border:1px solid #d9e1ec;border-radius:9px;background:white;padding:10px 12px;color:#243248;font:inherit;font-size:14px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:16px}
.kpi,.panel,.foot{background:#fff;border:1px solid #e3e9f1;border-radius:13px;box-shadow:0 3px 12px #20395707}
.kpi{padding:18px 20px}.kpi .label{font-size:12px;font-weight:650;color:#6b778a}.kpi .value{font-size:27px;font-weight:780;margin-top:8px;letter-spacing:-.04em}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.panel{padding:19px 20px 12px;min-width:0}
.panel h2{font-size:15px;margin:0 0 3px}.panel p{font-size:12px;color:#7a8697;margin:0 0 12px}
.graph{height:280px;position:relative}.foot{margin-top:16px;padding:15px 20px;font-size:12px;color:#66758a;line-height:1.55}
@media(max-width:850px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.wrap{padding:18px 13px}.graph{height:255px}}
@media(max-width:450px){.kpis{grid-template-columns:1fr}.kpi .value{font-size:24px}}
</style></head><body><main class="wrap">
<header><div><div class="eyebrow">Análise de dados · Aula 14</div><h1>MercadoFácil · Visão executiva</h1><p class="sub">Operação logística e comercial · janeiro a dezembro de 2025</p></div>
<div class="filters"><label class="filter">Região<select id="regiao"></select></label><label class="filter">Mês<select id="mes"></select></label></div></header>
<section id="kpis" class="kpis"></section>
<section class="grid">
<div class="panel"><h2>Receita de itens entregues por mês</h2><p>Valores em reais, sem cancelamentos/devoluções</p><div class="graph"><canvas id="c1"></canvas></div></div>
<div class="panel"><h2>Receita por categoria</h2><p>Produtos efetivamente entregues</p><div class="graph"><canvas id="c2"></canvas></div></div>
<div class="panel"><h2>Atraso médio por região</h2><p>Dias de atraso por item entregue, apenas prazos conhecidos</p><div class="graph"><canvas id="c3"></canvas></div></div>
<div class="panel"><h2>Avaliação por faixa de atraso</h2><p>Média de notas com avaliação e atraso conhecidos</p><div class="graph"><canvas id="c4"></canvas></div></div>
<div class="panel"><h2>Cancelamentos e devoluções por categoria</h2><p>Percentual de itens em cada situação, todas as situações no denominador</p><div class="graph"><canvas id="c5"></canvas></div></div>
<div class="panel"><h2>Chuva e atraso médio</h2><p>Chuva acumulada nos três dias, por cidade e data do pedido</p><div class="graph"><canvas id="c6"></canvas></div></div>
</section><div class="foot"><strong>Fonte:</strong> base tratada fornecida para a Aula 14 e arquivo de chuva disponibilizado no laboratório. Os filtros recalculam todos os indicadores e gráficos. Receita representa a soma de valores dos itens entregues, não a receita líquida contábil. O percentual de atraso é medido por itens entregues com prazo conhecido; não representa necessariamente pedidos únicos. Associação entre chuva, atraso e nota <strong>não demonstra causalidade</strong>. O HTML carrega Chart.js da internet.</div>
</main><script>
const ALL = __DADOS__;
const charts = {};
const brl = new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:2});
const dec = (v,n=1)=>new Intl.NumberFormat('pt-BR',{minimumFractionDigits:n,maximumFractionDigits:n}).format(v);
const unique = a => [...new Set(a)].sort();
const mean = a => a.length ? a.reduce((s,v)=>s+v,0)/a.length : null;
function selectOptions(id,values){const e=document.getElementById(id);e.innerHTML='<option value="">Todos</option>';for(const x of values){const o=document.createElement('option');o.value=x;o.textContent=x;e.appendChild(o)}}
selectOptions('regiao',unique(ALL.map(x=>x.regiao)));selectOptions('mes',unique(ALL.map(x=>x.mes)));
function make(id,type,labels,datasets,opts={}){
 if(charts[id])charts[id].destroy();
 charts[id]=new Chart(document.getElementById(id),{type,data:{labels,datasets},options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{display:datasets.length>1,position:'bottom'},tooltip:{mode:'index',intersect:false}},scales:{y:{beginAtZero:true}},...opts}})
}
function bucket(items,key,val){const m=new Map();for(const x of items){const k=key(x);if(!m.has(k))m.set(k,[]);m.get(k).push(val(x))}return m}
function render(){
 const reg=document.getElementById('regiao').value, mes=document.getElementById('mes').value;
 const rows=ALL.filter(r=>(!reg||r.regiao===reg)&&(!mes||r.mes===mes));
 const delivered=rows.filter(r=>r.status==='entregue');
 const withDelay=delivered.filter(r=>r.atraso!==null);
 const ratings=delivered.filter(r=>r.nota!==null);
 const revenue=delivered.reduce((s,r)=>s+(r.valor??0),0);
 const orders=new Set(delivered.map(r=>r.pedido)).size;
 const late=withDelay.length ? 100*withDelay.filter(r=>r.atraso>0).length/withDelay.length : 0;
 const note=mean(ratings.map(r=>r.nota));
 const ks=[['Receita (itens entregues)',brl.format(revenue)],['Pedidos entregues',orders.toLocaleString('pt-BR')],['Itens atrasados',dec(late)+'%'],['Nota média',note===null?'—':dec(note,2)]];
 document.getElementById('kpis').innerHTML=ks.map(([label,v])=>`<div class="kpi"><div class="label">${label}</div><div class="value">${v}</div></div>`).join('');
 const monthly=bucket(delivered,x=>x.mes,x=>x.valor??0),months=[...monthly.keys()].sort();
 make('c1','line',months,[{label:'Receita',data:months.map(m=>monthly.get(m).reduce((s,v)=>s+v,0)),borderColor:'#3879bc',backgroundColor:'#3879bc',tension:.3,fill:false}],{plugins:{legend:{display:false}}});
 const categories=bucket(delivered,x=>x.categoria,x=>x.valor??0),cats=[...categories.keys()].sort((a,b)=>categories.get(b).reduce((s,v)=>s+v,0)-categories.get(a).reduce((s,v)=>s+v,0));
 make('c2','bar',cats,[{label:'Receita',data:cats.map(c=>categories.get(c).reduce((s,v)=>s+v,0)),backgroundColor:'#35a38f'}],{plugins:{legend:{display:false}}});
 const byregion=bucket(withDelay,x=>x.regiao,x=>x.atraso),regions=[...byregion.keys()].sort();
 make('c3','bar',regions,[{label:'Dias',data:regions.map(r=>mean(byregion.get(r))),backgroundColor:'#d76e62'}],{plugins:{legend:{display:false}}});
 const bands=['0 (no prazo)','1–3 dias','4–7 dias','8+ dias'];
 const byband=bucket(delivered.filter(r=>r.atraso!==null&&r.nota!==null),x=>x.atraso<=0?bands[0]:x.atraso<=3?bands[1]:x.atraso<=7?bands[2]:bands[3],x=>x.nota);
 make('c4','bar',bands,[{label:'Nota',data:bands.map(b=>mean(byband.get(b)||[])),backgroundColor:'#e8a345'}],{plugins:{legend:{display:false}},scales:{y:{min:0,max:5}}});
 const bycat=bucket(rows,x=>x.categoria,x=>x.status),pCats=[...bycat.keys()].sort();
 make('c5','bar',pCats,[{label:'Cancelado (%)',data:pCats.map(c=>100*bycat.get(c).filter(s=>s==='cancelado').length/bycat.get(c).length),backgroundColor:'#9476bf'},{label:'Devolvido (%)',data:pCats.map(c=>100*bycat.get(c).filter(s=>s==='devolvido').length/bycat.get(c).length),backgroundColor:'#56a3c2'}],{scales:{x:{stacked:true},y:{stacked:true,beginAtZero:true}}});
 const rains=['< 5 mm','5–20 mm','20–40 mm','40+ mm'];
 const byrain=bucket(delivered.filter(r=>r.chuva!==null&&r.atraso!==null),x=>x.chuva<5?rains[0]:x.chuva<20?rains[1]:x.chuva<40?rains[2]:rains[3],x=>x.atraso);
 make('c6','bar',rains,[{label:'Atraso (dias)',data:rains.map(r=>mean(byrain.get(r)||[])),backgroundColor:'#6a97c8'}],{plugins:{legend:{display:false}}});
}
document.getElementById('regiao').addEventListener('change',render);document.getElementById('mes').addEventListener('change',render);
if(typeof Chart==='undefined'){document.querySelector('.grid').insertAdjacentHTML('beforebegin','<p style="color:#b91c1c">Chart.js não carregou. Confira a conexão com a internet.</p>')}else render();
</script></body></html>'''


def main():
    dados = carregar()
    SAIDA.write_text(HTML.replace('__DADOS__', json.dumps(dados, ensure_ascii=False)), encoding='utf-8')
    print(f'Gerado: {SAIDA}')
    print(f'Registros carregados: {len(dados)}')


if __name__ == '__main__':
    main()
