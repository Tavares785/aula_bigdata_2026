"""Dashboard local das views da Aula 14 (Plano B estendido).

Gera um HTML interativo com os 7 graficos do dashboard e um filtro de regiao,
mes e categoria que afeta TODOS eles, aplicando as mesmas regras das views de
aws-lab/sql/ sobre os mesmos CSVs. Serve de evidencia quando o Learner Lab nao
esta disponivel e de especificacao do que montar no Superset.

Diferenca em relacao ao dashboard_local.py do template: aquele agrega no Python
e desenha 3 graficos fixos; aqui as linhas vao para o navegador e a agregacao
acontece em JavaScript a cada mudanca do filtro, que e o que torna o filtro
interativo de verdade.

So usa a biblioteca padrao. O HTML carrega Chart.js de um CDN.

    python3 dashboard_views.py           # gera dashboard-views.html ao lado
    python3 dashboard_views.py --abrir   # e abre no navegador
"""
import csv
import json
import os
import sys
import webbrowser

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "..", "data")
SAIDA = os.path.join(AQUI, "dashboard-views.html")

# Mesmas faixas das views E e BONUS (fechadas a esquerda, abertas a direita).
FAIXAS_CHUVA = (
    (5, "1) sem chuva (<5 mm)"),
    (20, "2) fraca (5-20)"),
    (40, "3) forte (20-40)"),
    (float("inf"), "4) muito forte (40+)"),
)


def faixa_chuva(mm):
    for limite, rotulo in FAIXAS_CHUVA:
        if mm < limite:
            return rotulo
    return FAIXAS_CHUVA[-1][1]


def faixa_atraso(dias):
    """Mesmo CASE da view vw_atraso_nota."""
    if dias <= 0:
        return "1) 0 - no prazo"
    if dias <= 3:
        return "2) 1-3 dias"
    if dias <= 7:
        return "3) 4-7 dias"
    return "4) 8+ dias"


def carregar():
    def ler(nome):
        with open(os.path.join(DADOS, nome), encoding="utf-8") as f:
            return list(csv.DictReader(f))

    chuva = {(r["cidade"], r["dia"]): float(r["chuva_3d_mm"]) for r in ler("chuva_diaria.csv")}
    feriados = {r["dia"] for r in ler("feriados.csv")}

    linhas = []
    for r in ler("pedidos_mercadofacil_tratado.csv"):
        dia = r["data_pedido"]
        mm = chuva.get((r["cidade"], dia))
        atraso = int(r["atraso_dias"]) if r["atraso_dias"] != "" else None
        linhas.append({
            "dia": dia,
            "mes": dia[:7],
            "regiao": r["regiao"],
            "estado": r["estado"],
            "categoria": r["categoria"],
            "canal": r["canal"],
            "transportadora": r["transportadora"],
            "status": r["status_pedido"],
            "pedido": r["pedido_id"],
            "valor": float(r["valor_total"]),
            "atraso": atraso,
            "nota": int(r["nota_avaliacao"]) if r["nota_avaliacao"] != "" else None,
            # None so se a cidade nao tiver serie de chuva; na base atual nunca acontece
            "fx_chuva": faixa_chuva(mm) if mm is not None else None,
            "fx_atraso": faixa_atraso(atraso) if atraso is not None else None,
            "feriado": dia in feriados,
        })
    return linhas


HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MercadoFacil - Dashboard da Aula 14</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root { --bg:#0f1115; --card:#181b22; --linha:#262b36; --txt:#e8eaee; --fraco:#9aa3b2; --ok:#4ea1ff; }
  * { box-sizing:border-box; }
  body { margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--txt);
         font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:1280px; margin:0 auto; }
  h1 { font-size:22px; margin:0 0 4px; }
  .sub { color:var(--fraco); margin:0 0 20px; font-size:13px; }
  .filtros { background:var(--card); border:1px solid var(--linha); border-radius:10px;
             padding:14px 16px; margin-bottom:20px; display:flex; flex-wrap:wrap; gap:16px; align-items:flex-end; }
  .filtros label { display:block; font-size:12px; color:var(--fraco); margin-bottom:4px; }
  select, button { background:#11141a; color:var(--txt); border:1px solid var(--linha);
                   border-radius:6px; padding:7px 9px; font-size:13px; }
  select[multiple] { min-width:150px; height:96px; }
  button { cursor:pointer; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:20px; }
  .kpi { background:var(--card); border:1px solid var(--linha); border-radius:10px; padding:14px 16px; }
  .kpi .rot { font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--fraco); }
  .kpi .val { font-size:26px; font-weight:600; margin-top:6px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:16px; }
  .card { background:var(--card); border:1px solid var(--linha); border-radius:10px; padding:16px; }
  .card h2 { font-size:15px; margin:0 0 2px; }
  .card p { font-size:12px; color:var(--fraco); margin:0 0 12px; }
  .card .box { position:relative; height:300px; }
  .nota { font-size:12px; color:var(--fraco); margin-top:24px; }
  @media (max-width:600px){ .grid { grid-template-columns:1fr; } .card .box { height:260px; } }
</style>
</head>
<body>
<div class="wrap">
  <h1>MercadoFacil - onde e por que as entregas atrasam</h1>
  <p class="sub">Plano B local da Aula 14. Mesmas regras das views de <code>aws-lab/sql/</code>
     aplicadas a <span id="n-linhas"></span> itens de pedido de 2025. O filtro abaixo afeta os sete graficos.</p>

  <div class="filtros">
    <div><label for="f-regiao">Regiao (Cmd/Ctrl para varias)</label><select id="f-regiao" multiple></select></div>
    <div><label for="f-categoria">Categoria</label><select id="f-categoria" multiple></select></div>
    <div><label for="f-mes-de">Mes de</label><select id="f-mes-de"></select></div>
    <div><label for="f-mes-ate">Mes ate</label><select id="f-mes-ate"></select></div>
    <div><button id="f-limpar">Limpar filtros</button></div>
    <div style="color:var(--fraco);font-size:12px" id="f-resumo"></div>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="grid">
    <div class="card"><h2>Receita e pedidos por semana</h2>
      <p>vw_serie_diaria - a Black Friday e o Natal aparecem?</p><div class="box"><canvas id="c-serie"></canvas></div></div>
    <div class="card"><h2>Nota media por faixa de atraso</h2>
      <p>vw_atraso_nota - o atraso derruba a nota?</p><div class="box"><canvas id="c-nota"></canvas></div></div>
    <div class="card"><h2>Atraso por estado</h2>
      <p>vw_logistica_estado - onde atrasa mais?</p><div class="box"><canvas id="c-estado"></canvas></div></div>
    <div class="card"><h2>Cancelamento e devolucao por categoria</h2>
      <p>vw_problemas_categoria - barras empilhadas, % sobre todos os itens</p><div class="box"><canvas id="c-problemas"></canvas></div></div>
    <div class="card"><h2>Atraso por faixa de chuva</h2>
      <p>vw_atraso_chuva - a chuva explica o atraso?</p><div class="box"><canvas id="c-chuva"></canvas></div></div>
    <div class="card"><h2>Chuva dentro de cada regiao</h2>
      <p>vw_atraso_chuva_regiao (bonus) - o efeito sobrevive ao controle por regiao?</p><div class="box"><canvas id="c-chuva-regiao"></canvas></div></div>
    <div class="card"><h2>Feriado x dia comum</h2>
      <p>vw_feriados - pedidos por dia e atraso medio</p><div class="box"><canvas id="c-feriados"></canvas></div></div>
  </div>

  <p class="nota">Gerado por <code>aws-lab/scripts/dashboard_views.py</code>. No ambiente AWS os mesmos
     numeros saem das views do Athena lidas pelo Superset.</p>
</div>
<script>
const LINHAS = __DADOS__;
document.getElementById('n-linhas').textContent = LINHAS.length.toLocaleString('pt-BR');

const CORES = ['#4ea1ff','#ff8a5c','#5ddc9a','#c792ea','#ffd166','#ef5d8f','#64d2ff','#b0bec5'];
const uniq = (c) => [...new Set(LINHAS.map(r => r[c]))].sort();
const brl = (v) => v.toLocaleString('pt-BR', {style:'currency', currency:'BRL', maximumFractionDigits:0});

function preencher(sel, valores, todos) {
  sel.innerHTML = '';
  if (todos) sel.append(new Option('(todos)', ''));
  valores.forEach(v => sel.append(new Option(v, v)));
}
const selRegiao = document.getElementById('f-regiao');
const selCategoria = document.getElementById('f-categoria');
const selDe = document.getElementById('f-mes-de');
const selAte = document.getElementById('f-mes-ate');
const meses = uniq('mes');
preencher(selRegiao, uniq('regiao'), false);
preencher(selCategoria, uniq('categoria'), false);
preencher(selDe, meses, false);
preencher(selAte, meses, false);
selDe.value = meses[0];
selAte.value = meses[meses.length - 1];

function escolhidos(sel) { return [...sel.selectedOptions].map(o => o.value); }

function filtrar() {
  const rs = escolhidos(selRegiao), cs = escolhidos(selCategoria);
  const de = selDe.value, ate = selAte.value;
  return LINHAS.filter(r =>
    (rs.length === 0 || rs.includes(r.regiao)) &&
    (cs.length === 0 || cs.includes(r.categoria)) &&
    r.mes >= de && r.mes <= ate);
}

// --- agregacoes: as mesmas regras das views -------------------------------
const entregues = (f) => f.filter(r => r.status === 'entregue');

function kpis(f) {
  const e = entregues(f);
  const receita = e.reduce((s, r) => s + r.valor, 0);
  const pedidos = new Set(e.map(r => r.pedido)).size;
  const atrasados = e.filter(r => r.atraso > 0).length;
  const notas = e.filter(r => r.nota !== null);
  const cd = f.filter(r => r.status === 'cancelado' || r.status === 'devolvido').length;
  return [
    ['Receita (entregue)', brl(receita)],
    ['Pedidos', pedidos.toLocaleString('pt-BR')],
    ['Ticket medio', pedidos ? brl(receita / pedidos) : '-'],
    ['% itens atrasados', e.length ? (100 * atrasados / e.length).toFixed(1) + '%' : '-'],
    ['Nota media', notas.length ? (notas.reduce((s, r) => s + r.nota, 0) / notas.length).toFixed(2) : '-'],
    ['% canc. + devol.', f.length ? (100 * cd / f.length).toFixed(1) + '%' : '-'],
  ];
}

function porChave(linhas, chave, calc) {
  const g = new Map();
  linhas.forEach(r => {
    const k = chave(r);
    if (k === null || k === undefined) return;
    if (!g.has(k)) g.set(k, []);
    g.get(k).push(r);
  });
  return [...g.entries()].sort((a, b) => String(a[0]).localeCompare(String(b[0])))
         .map(([k, rs]) => ({ k, ...calc(rs) }));
}
const pctAtraso = (rs) => 100 * rs.filter(r => r.atraso > 0).length / rs.length;
const semanaDe = (dia) => { const d = new Date(dia + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7)); return d.toISOString().slice(0, 10); };

// --- graficos -------------------------------------------------------------
const graficos = {};
function desenhar(id, config) {
  if (graficos[id]) { graficos[id].destroy(); }
  graficos[id] = new Chart(document.getElementById(id), config);
}
const COMUM = { responsive:true, maintainAspectRatio:false,
  plugins:{ legend:{ labels:{ color:'#9aa3b2', boxWidth:12, font:{size:11} } } },
  scales:{ x:{ ticks:{ color:'#9aa3b2', font:{size:10} }, grid:{ color:'#262b36' } },
           y:{ ticks:{ color:'#9aa3b2', font:{size:10} }, grid:{ color:'#262b36' } } } };
const clone = (o) => JSON.parse(JSON.stringify(o));

function render() {
  const f = filtrar();
  document.getElementById('f-resumo').textContent = f.length.toLocaleString('pt-BR') + ' itens no filtro';
  document.getElementById('kpis').innerHTML = kpis(f)
    .map(([rot, val]) => `<div class="kpi"><div class="rot">${rot}</div><div class="val">${val}</div></div>`).join('');

  if (f.length === 0) { Object.values(graficos).forEach(g => g.destroy()); Object.keys(graficos).forEach(k => delete graficos[k]); return; }

  // 1) serie semanal: receita (barras) + pedidos (linha)
  const serie = porChave(entregues(f), r => semanaDe(r.dia), rs => ({
    receita: rs.reduce((s, r) => s + r.valor, 0), pedidos: new Set(rs.map(r => r.pedido)).size }));
  desenhar('c-serie', { data:{ labels: serie.map(d => d.k), datasets:[
      { type:'bar', label:'Receita (R$)', data: serie.map(d => Math.round(d.receita)), backgroundColor:CORES[0], yAxisID:'y' },
      { type:'line', label:'Pedidos', data: serie.map(d => d.pedidos), borderColor:CORES[1], backgroundColor:CORES[1], yAxisID:'y1', tension:.3, pointRadius:0 } ]},
    options:{ ...clone(COMUM), scales:{ x:{ ...clone(COMUM.scales.x), ticks:{ color:'#9aa3b2', font:{size:9}, maxTicksLimit:12 } },
      y:{ ...clone(COMUM.scales.y), position:'left', title:{ display:true, text:'Receita (R$)', color:'#9aa3b2' } },
      y1:{ ...clone(COMUM.scales.y), position:'right', grid:{ drawOnChartArea:false }, title:{ display:true, text:'Pedidos', color:'#9aa3b2' } } } } });

  // 2) nota por faixa de atraso (so entregues com nota, como na view)
  const nota = porChave(entregues(f).filter(r => r.nota !== null), r => r.fx_atraso, rs => ({
    nota: rs.reduce((s, r) => s + r.nota, 0) / rs.length, n: rs.length }));
  desenhar('c-nota', { type:'bar', data:{ labels: nota.map(d => d.k), datasets:[
      { label:'Nota media (1 a 5)', data: nota.map(d => +d.nota.toFixed(2)), backgroundColor:CORES[2] } ]},
    options:{ ...clone(COMUM), plugins:{ ...clone(COMUM.plugins), tooltip:{ callbacks:{ afterLabel:(c) => nota[c.dataIndex].n + ' avaliacoes' } } },
      scales:{ ...clone(COMUM.scales), y:{ ...clone(COMUM.scales.y), min:0, max:5 } } } });

  // 3) atraso por estado
  const est = porChave(entregues(f), r => r.estado, rs => ({ pct: pctAtraso(rs), n: rs.length }))
    .filter(d => d.n >= 20).sort((a, b) => b.pct - a.pct);
  desenhar('c-estado', { type:'bar', data:{ labels: est.map(d => d.k), datasets:[
      { label:'% itens atrasados', data: est.map(d => +d.pct.toFixed(1)), backgroundColor:CORES[3] } ]},
    options:{ ...clone(COMUM), plugins:{ ...clone(COMUM.plugins), tooltip:{ callbacks:{ afterLabel:(c) => est[c.dataIndex].n + ' itens entregues' } } } } });

  // 4) problemas por categoria: barras empilhadas sobre TODOS os status
  const prob = porChave(f, r => r.categoria, rs => ({
    canc: 100 * rs.filter(r => r.status === 'cancelado').length / rs.length,
    dev: 100 * rs.filter(r => r.status === 'devolvido').length / rs.length, n: rs.length }))
    .sort((a, b) => (b.canc + b.dev) - (a.canc + a.dev));
  desenhar('c-problemas', { type:'bar', data:{ labels: prob.map(d => d.k), datasets:[
      { label:'% cancelado', data: prob.map(d => +d.canc.toFixed(2)), backgroundColor:CORES[4] },
      { label:'% devolvido', data: prob.map(d => +d.dev.toFixed(2)), backgroundColor:CORES[5] } ]},
    options:{ ...clone(COMUM), scales:{ x:{ ...clone(COMUM.scales.x), stacked:true }, y:{ ...clone(COMUM.scales.y), stacked:true } } } });

  // 5) atraso por faixa de chuva
  const chuva = porChave(entregues(f), r => r.fx_chuva, rs => ({
    pct: pctAtraso(rs), atraso: rs.reduce((s, r) => s + r.atraso, 0) / rs.length, n: rs.length }));
  desenhar('c-chuva', { data:{ labels: chuva.map(d => d.k), datasets:[
      { type:'bar', label:'% itens atrasados', data: chuva.map(d => +d.pct.toFixed(1)), backgroundColor:CORES[0], yAxisID:'y' },
      { type:'line', label:'Atraso medio (dias)', data: chuva.map(d => +d.atraso.toFixed(2)), borderColor:CORES[1], backgroundColor:CORES[1], yAxisID:'y1', tension:.3 } ]},
    options:{ ...clone(COMUM), plugins:{ ...clone(COMUM.plugins), tooltip:{ callbacks:{ afterLabel:(c) => chuva[c.dataIndex].n + ' itens' } } },
      scales:{ x:clone(COMUM.scales.x), y:{ ...clone(COMUM.scales.y), position:'left', title:{ display:true, text:'% atrasados', color:'#9aa3b2' } },
      y1:{ ...clone(COMUM.scales.y), position:'right', grid:{ drawOnChartArea:false }, title:{ display:true, text:'dias', color:'#9aa3b2' } } } } });

  // 6) chuva dentro de cada regiao (o bonus)
  const faixas = [...new Set(entregues(f).map(r => r.fx_chuva).filter(Boolean))].sort();
  const regioes = [...new Set(entregues(f).map(r => r.regiao))].sort();
  desenhar('c-chuva-regiao', { type:'bar', data:{ labels: faixas, datasets: regioes.map((reg, i) => ({
      label: reg, backgroundColor: CORES[i % CORES.length],
      data: faixas.map(fx => { const rs = entregues(f).filter(r => r.regiao === reg && r.fx_chuva === fx);
        return rs.length >= 15 ? +pctAtraso(rs).toFixed(1) : null; }) })) },
    options:{ ...clone(COMUM), plugins:{ ...clone(COMUM.plugins),
        subtitle:{ display:true, text:'faixas com menos de 15 itens ficam vazias', color:'#9aa3b2', font:{size:10} } },
      scales:{ x:clone(COMUM.scales.x), y:{ ...clone(COMUM.scales.y), title:{ display:true, text:'% atrasados', color:'#9aa3b2' } } } } });

  // 7) feriado x dia comum
  const fer = porChave(entregues(f), r => (r.feriado ? 'feriado' : 'dia comum'), rs => ({
    pedPorDia: new Set(rs.map(r => r.pedido)).size / new Set(rs.map(r => r.dia)).size,
    atraso: rs.reduce((s, r) => s + r.atraso, 0) / rs.length, dias: new Set(rs.map(r => r.dia)).size }));
  desenhar('c-feriados', { data:{ labels: fer.map(d => d.k), datasets:[
      { type:'bar', label:'Pedidos por dia', data: fer.map(d => +d.pedPorDia.toFixed(2)), backgroundColor:CORES[6], yAxisID:'y' },
      { type:'bar', label:'Atraso medio (dias)', data: fer.map(d => +d.atraso.toFixed(2)), backgroundColor:CORES[1], yAxisID:'y1' } ]},
    options:{ ...clone(COMUM), plugins:{ ...clone(COMUM.plugins), tooltip:{ callbacks:{ afterLabel:(c) => fer[c.dataIndex].dias + ' dias no filtro' } } },
      scales:{ x:clone(COMUM.scales.x), y:{ ...clone(COMUM.scales.y), position:'left', title:{ display:true, text:'pedidos/dia', color:'#9aa3b2' } },
      y1:{ ...clone(COMUM.scales.y), position:'right', grid:{ drawOnChartArea:false }, title:{ display:true, text:'dias de atraso', color:'#9aa3b2' } } } } });
}

[selRegiao, selCategoria, selDe, selAte].forEach(s => s.addEventListener('change', render));
document.getElementById('f-limpar').addEventListener('click', () => {
  [...selRegiao.options].forEach(o => o.selected = false);
  [...selCategoria.options].forEach(o => o.selected = false);
  selDe.value = meses[0]; selAte.value = meses[meses.length - 1]; render();
});
render();
</script>
</body>
</html>
"""


def main():
    linhas = carregar()
    html = HTML.replace("__DADOS__", json.dumps(linhas, ensure_ascii=False, separators=(",", ":")))
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Gerado: {SAIDA} ({len(linhas)} itens, {os.path.getsize(SAIDA) // 1024} KB)")
    if "--abrir" in sys.argv:
        webbrowser.open("file://" + os.path.abspath(SAIDA))


if __name__ == "__main__":
    main()
