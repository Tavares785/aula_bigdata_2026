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
<title>MercadoFacil - Relatorio de Entregas 2025</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  /* Paleta categorica validada (adjacent pairlist, modo claro e escuro).
     O WARN de contraste dos slots 3/4/5 e coberto pela tabela de cada grafico. */
  :root {
    color-scheme: light;
    --plano:        #f3f1ea;
    --superficie:   #fbfaf7;
    --tinta:        #0b0b0b;
    --tinta-2:      #52514e;
    --tinta-fraca:  #898781;
    --regua:        #e1e0d9;
    --eixo:         #c3c2b7;
    --anel:         rgba(11,11,11,0.10);
    --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#eda100; --s5:#e87ba4;
    --destaque:     #0b0b0b;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --plano:#0d0d0d; --superficie:#1a1a19; --tinta:#f0efec; --tinta-2:#c3c2b7;
      --tinta-fraca:#898781; --regua:#2c2c2a; --eixo:#383835; --anel:rgba(255,255,255,0.10);
      --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#d55181;
      --destaque:#f0efec;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --plano:#0d0d0d; --superficie:#1a1a19; --tinta:#f0efec; --tinta-2:#c3c2b7;
    --tinta-fraca:#898781; --regua:#2c2c2a; --eixo:#383835; --anel:rgba(255,255,255,0.10);
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#d55181;
    --destaque:#f0efec;
  }

  * { box-sizing:border-box; }
  body { margin:0; background:var(--plano); color:var(--tinta);
    font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
    -webkit-font-smoothing:antialiased; }
  .folha { max-width:1180px; margin:0 auto; padding:0 24px 72px; }

  /* Cabecalho editorial: regua dupla, nao caixa colorida */
  header { padding:52px 0 0; }
  .chapeu { font-size:11px; letter-spacing:.18em; text-transform:uppercase;
    color:var(--tinta-fraca); display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }
  h1 { font-size:clamp(28px,4.4vw,44px); line-height:1.08; letter-spacing:-.022em;
    margin:18px 0 10px; max-width:19ch; font-weight:600; }
  .linha-fina { font-size:16px; color:var(--tinta-2); max-width:62ch; margin:0 0 22px; }
  .regua-dupla { border-top:3px solid var(--tinta); border-bottom:1px solid var(--regua); height:5px; }

  /* Filtros: uma faixa unica acima de tudo que eles afetam */
  .filtros { display:flex; flex-wrap:wrap; gap:22px; align-items:flex-end;
    padding:18px 0 20px; border-bottom:1px solid var(--regua); margin-bottom:34px; }
  .campo label { display:block; font-size:10px; letter-spacing:.14em; text-transform:uppercase;
    color:var(--tinta-fraca); margin-bottom:6px; }
  select { background:var(--superficie); color:var(--tinta); border:1px solid var(--eixo);
    border-radius:3px; padding:7px 9px; font:13px/1.3 inherit; min-height:34px; }
  select[multiple] { min-width:168px; height:104px; }
  .acoes { margin-left:auto; display:flex; gap:10px; align-items:center; }
  button { background:none; color:var(--tinta); border:1px solid var(--eixo); border-radius:3px;
    padding:8px 12px; font:12px/1 inherit; cursor:pointer; min-height:34px; }
  button:hover { background:var(--superficie); }
  .contagem { font-size:12px; color:var(--tinta-fraca); font-variant-numeric:tabular-nums; }

  /* Tiles: o numero e o grafico */
  .tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(158px,1fr));
    gap:1px; background:var(--regua); border:1px solid var(--regua); margin-bottom:40px; }
  .tile { background:var(--superficie); padding:16px 18px 18px; }
  .tile .rot { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--tinta-fraca); }
  .tile .val { font-size:clamp(21px,2.1vw,29px); line-height:1.12; letter-spacing:-.02em;
    margin-top:8px; font-weight:600; white-space:nowrap; }
  .tile .nota { font-size:11px; color:var(--tinta-fraca); margin-top:5px; }

  /* Cartoes: sem sombra, so regua. Grafico primeiro, tabela atras. */
  .grade { display:grid; grid-template-columns:repeat(auto-fit,minmax(430px,1fr)); gap:1px;
    background:var(--regua); border:1px solid var(--regua); }
  .cartao { background:var(--superficie); padding:22px 22px 18px; display:flex; flex-direction:column; }
  .cartao.largo { grid-column:1/-1; }
  .cartao.preenche { padding:0; }   /* tapa a celula que sobra quando o numero de cartoes e impar */
  .cartao h2 { font-size:16px; letter-spacing:-.01em; margin:0 0 3px; font-weight:600; }
  .cartao .fonte { font-size:11px; color:var(--tinta-fraca); margin:0 0 16px;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  .caixa { position:relative; height:290px; }
  .cartao.largo .caixa { height:320px; }
  .rodape-cartao { display:flex; justify-content:space-between; align-items:center;
    gap:12px; margin-top:12px; padding-top:10px; border-top:1px solid var(--regua); }
  .leitura { font-size:12px; color:var(--tinta-2); margin:0; max-width:56ch; }
  .alterna { font-size:11px; letter-spacing:.08em; text-transform:uppercase;
    border:none; border-bottom:1px solid var(--eixo); border-radius:0; padding:3px 0;
    color:var(--tinta-fraca); flex:none; }
  .alterna:hover { background:none; color:var(--tinta); border-bottom-color:var(--tinta); }
  table { width:100%; border-collapse:collapse; font-size:12.5px; font-variant-numeric:tabular-nums; }
  th, td { text-align:right; padding:6px 8px; border-bottom:1px solid var(--regua); }
  th:first-child, td:first-child { text-align:left; font-variant-numeric:normal; }
  thead th { font-size:10px; letter-spacing:.1em; text-transform:uppercase;
    color:var(--tinta-fraca); font-weight:500; }
  .tabela-caixa { max-height:290px; overflow:auto; }
  [hidden] { display:none !important; }
  footer { margin-top:40px; padding-top:18px; border-top:1px solid var(--regua);
    font-size:12px; color:var(--tinta-fraca); }
  footer code { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  @media (max-width:620px){ .grade { grid-template-columns:1fr; } .folha { padding:0 16px 56px; } }
</style>
</head>
<body>
<div class="folha">
  <header>
    <div class="chapeu"><span>MercadoFacil &middot; Logistica 2025</span><span id="carimbo"></span></div>
    <h1>Onde e por que as entregas atrasam</h1>
    <p class="linha-fina">Dez mil itens de pedido cruzados com chuva diaria e feriados nacionais.
      As mesmas regras das views de <code>aws-lab/sql/</code>, recalculadas no navegador a cada filtro.</p>
    <div class="regua-dupla"></div>
  </header>

  <div class="filtros">
    <div class="campo"><label for="f-regiao">Regiao</label><select id="f-regiao" multiple></select></div>
    <div class="campo"><label for="f-categoria">Categoria</label><select id="f-categoria" multiple></select></div>
    <div class="campo"><label for="f-mes-de">Mes inicial</label><select id="f-mes-de"></select></div>
    <div class="campo"><label for="f-mes-ate">Mes final</label><select id="f-mes-ate"></select></div>
    <div class="acoes">
      <span class="contagem" id="f-resumo"></span>
      <button id="f-limpar">Limpar</button>
      <button id="f-tema">Tema</button>
    </div>
  </div>

  <section class="tiles" id="tiles"></section>

  <section class="grade">
    <article class="cartao largo" data-g="serie">
      <h2>Receita entregue por semana</h2><p class="fonte">vw_serie_diaria</p>
      <div class="caixa"><canvas id="c-serie"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">A semana da Black Friday e o pico isolado do ano.
        O numero de pedidos esta na tabela e no tooltip, nao num segundo eixo.</p>
        <button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="nota">
      <h2>A nota cai com o atraso</h2><p class="fonte">vw_atraso_nota</p>
      <div class="caixa"><canvas id="c-nota"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">Nota media de 1 a 5, so itens entregues que avaliaram.</p>
        <button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="estado">
      <h2>Onde atrasa mais</h2><p class="fonte">vw_logistica_estado</p>
      <div class="caixa"><canvas id="c-estado"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">Estados com 20 itens ou mais. O pior fica em tinta cheia,
        o resto recua.</p><button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="problemas">
      <h2>Cancelamento e devolucao por categoria</h2><p class="fonte">vw_problemas_categoria</p>
      <div class="caixa"><canvas id="c-problemas"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">Percentual sobre todos os itens da categoria,
        nao so os entregues.</p><button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="chuva">
      <h2>A chuva explica o atraso?</h2><p class="fonte">vw_atraso_chuva</p>
      <div class="caixa"><canvas id="c-chuva"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">chuva_3d_mm: dia do pedido mais os dois seguintes.
        O atraso medio em dias esta na tabela.</p><button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="chuva-regiao">
      <h2>O efeito sobrevive dentro de cada regiao</h2><p class="fonte">vw_atraso_chuva_regiao &middot; bonus</p>
      <div class="caixa"><canvas id="c-chuva-regiao"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">Se o gradiente se mantem dentro de cada regiao,
        a chuva nao era so um indicador da geografia. Faixas com menos de 15 itens ficam vazias.</p>
        <button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="feriado-vol">
      <h2>Feriado: movimento</h2><p class="fonte">vw_feriados</p>
      <div class="caixa"><canvas id="c-feriado-vol"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">Pedidos por dia, ja normalizado pelo numero de dias.</p>
        <button class="alterna">Tabela</button></div>
    </article>

    <article class="cartao" data-g="feriado-atraso">
      <h2>Feriado: atraso</h2><p class="fonte">vw_feriados</p>
      <div class="caixa"><canvas id="c-feriado-atraso"></canvas></div>
      <div class="tabela-caixa" hidden></div>
      <div class="rodape-cartao"><p class="leitura">Dias de atraso. Separado do movimento de proposito:
        duas medidas de escala diferente nunca dividem um eixo.</p><button class="alterna">Tabela</button></div>
    </article>
    <div class="cartao preenche" aria-hidden="true"></div>
  </section>

  <footer>Gerado por <code>aws-lab/scripts/dashboard_views.py</code>.
    No ambiente AWS os mesmos numeros saem das views do Athena lidas pelo Superset.</footer>
</div>
<script>
const LINHAS = __DADOS__;
document.getElementById('carimbo').textContent = LINHAS.length.toLocaleString('pt-BR') + ' itens de pedido';

const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const brl0 = (v) => v.toLocaleString('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0});
const uniq = (c) => [...new Set(LINHAS.map(r => r[c]))].sort();

const selRegiao=document.getElementById('f-regiao'), selCategoria=document.getElementById('f-categoria');
const selDe=document.getElementById('f-mes-de'), selAte=document.getElementById('f-mes-ate');
const meses = uniq('mes');
const encher=(s,v)=>{ s.innerHTML=''; v.forEach(x=>s.append(new Option(x,x))); };
encher(selRegiao, uniq('regiao')); encher(selCategoria, uniq('categoria'));
encher(selDe, meses); encher(selAte, meses);
selDe.value = meses[0]; selAte.value = meses[meses.length-1];
const escolhidos = (s) => [...s.selectedOptions].map(o => o.value);

function filtrar(){
  const rs=escolhidos(selRegiao), cs=escolhidos(selCategoria), de=selDe.value, ate=selAte.value;
  return LINHAS.filter(r => (rs.length===0||rs.includes(r.regiao)) &&
    (cs.length===0||cs.includes(r.categoria)) && r.mes>=de && r.mes<=ate);
}

const entregues = (f) => f.filter(r => r.status==='entregue');
function porChave(linhas, chave, calc){
  const g=new Map();
  linhas.forEach(r => { const k=chave(r); if(k==null) return; if(!g.has(k)) g.set(k,[]); g.get(k).push(r); });
  return [...g.entries()].sort((a,b)=>String(a[0]).localeCompare(String(b[0])))
    .map(([k,rs])=>({k, ...calc(rs)}));
}
const pctAtraso = (rs) => 100*rs.filter(r=>r.atraso>0).length/rs.length;
const semanaDe = (dia) => { const d=new Date(dia+'T00:00:00Z');
  d.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7)); return d.toISOString().slice(0,10); };

function tiles(f){
  const e=entregues(f);
  const receita=e.reduce((s,r)=>s+r.valor,0), pedidos=new Set(e.map(r=>r.pedido)).size;
  const notas=e.filter(r=>r.nota!==null);
  const cd=f.filter(r=>r.status!=='entregue').length;
  return [
    ['Receita entregue', receita?brl0(receita):'-', 'soma de valor_total'],
    ['Pedidos', pedidos.toLocaleString('pt-BR'), 'distintos, entregues'],
    ['Ticket medio', pedidos?brl0(receita/pedidos):'-', 'receita / pedidos'],
    ['Itens atrasados', e.length?(100*e.filter(r=>r.atraso>0).length/e.length).toFixed(1)+'%':'-', 'atraso_dias > 0'],
    ['Nota media', notas.length?(notas.reduce((s,r)=>s+r.nota,0)/notas.length).toFixed(2):'-', 'de 1 a 5'],
    ['Cancelado + devolvido', f.length?(100*cd/f.length).toFixed(1)+'%':'-', 'sobre todos os itens'],
  ];
}

/* --- Chart.js: um eixo por grafico, marcas finas, grade em fio de cabelo --- */
const graficos={};
function base(){
  return { responsive:true, maintainAspectRatio:false,
    interaction:{ mode:'index', intersect:false },
    plugins:{
      legend:{ display:false },
      tooltip:{ backgroundColor:css('--superficie'), titleColor:css('--tinta'),
        bodyColor:css('--tinta-2'), borderColor:css('--eixo'), borderWidth:1,
        padding:10, cornerRadius:3, displayColors:true, boxWidth:8, boxHeight:8, usePointStyle:true,
        titleFont:{size:12,weight:'600'}, bodyFont:{size:12} } },
    scales:{
      x:{ ticks:{ color:css('--tinta-fraca'), font:{size:11} },
          grid:{ display:false }, border:{ color:css('--eixo') } },
      y:{ beginAtZero:true, ticks:{ color:css('--tinta-fraca'), font:{size:11}, padding:6 },
          grid:{ color:css('--regua'), drawTicks:false },
          border:{ display:false } } } };
}
function legenda(op){ op.plugins.legend={ display:true, position:'top', align:'start',
  labels:{ color:css('--tinta-2'), boxWidth:10, boxHeight:10, usePointStyle:true,
           pointStyle:'rectRounded', font:{size:11}, padding:14 } }; return op; }

function desenhar(id, cfg){ if(graficos[id]) graficos[id].destroy();
  graficos[id]=new Chart(document.getElementById(id), cfg); }

function tabela(el, cabecalho, linhas){
  el.innerHTML = '<table><thead><tr>' + cabecalho.map(h=>`<th>${h}</th>`).join('') +
    '</tr></thead><tbody>' + linhas.map(l=>'<tr>'+l.map(c=>`<td>${c}</td>`).join('')+'</tr>').join('') +
    '</tbody></table>';
}
const alvo = (g) => document.querySelector(`[data-g="${g}"] .tabela-caixa`);

function render(){
  const f=filtrar();
  document.getElementById('f-resumo').textContent = f.length.toLocaleString('pt-BR')+' itens';
  document.getElementById('tiles').innerHTML = tiles(f).map(([r,v,n])=>
    `<div class="tile"><div class="rot">${r}</div><div class="val">${v}</div><div class="nota">${n}</div></div>`).join('');
  if(f.length===0){ Object.values(graficos).forEach(g=>g.destroy()); for(const k in graficos) delete graficos[k]; return; }
  const S=css('--superficie');

  // 1) serie semanal - UM eixo (receita). Pedidos vai para tooltip e tabela.
  const serie=porChave(entregues(f), r=>semanaDe(r.dia), rs=>({
    receita:rs.reduce((s,r)=>s+r.valor,0), pedidos:new Set(rs.map(r=>r.pedido)).size }));
  const op1=base();
  op1.plugins.tooltip.callbacks={ label:(c)=>[` Receita ${brl0(c.parsed.y)}`,
    ` ${serie[c.dataIndex].pedidos} pedidos na semana`] };
  op1.scales.y.ticks.callback=(v)=>(v/1000)+'k';
  op1.scales.x.ticks.maxTicksLimit=13;
  desenhar('c-serie',{ type:'line', data:{ labels:serie.map(d=>d.k), datasets:[{
      data:serie.map(d=>Math.round(d.receita)), borderColor:css('--s1'), backgroundColor:css('--s1'),
      borderWidth:2, tension:.25, pointRadius:0, pointHoverRadius:5,
      pointHoverBorderColor:S, pointHoverBorderWidth:2 }]}, options:op1 });
  tabela(alvo('serie'), ['Semana','Receita (R$)','Pedidos'],
    serie.map(d=>[d.k, Math.round(d.receita).toLocaleString('pt-BR'), d.pedidos]));

  // 2) nota por faixa de atraso - uma serie, um tom
  const nota=porChave(entregues(f).filter(r=>r.nota!==null), r=>r.fx_atraso, rs=>({
    nota:rs.reduce((s,r)=>s+r.nota,0)/rs.length, n:rs.length }));
  const op2=base(); op2.scales.y.max=5; op2.scales.y.ticks.stepSize=1;
  op2.plugins.tooltip.callbacks={ label:(c)=>[` Nota ${c.parsed.y.toFixed(2)}`,
    ` ${nota[c.dataIndex].n.toLocaleString('pt-BR')} avaliacoes`] };
  desenhar('c-nota',{ type:'bar', data:{ labels:nota.map(d=>d.k), datasets:[{
      data:nota.map(d=>+d.nota.toFixed(2)), backgroundColor:css('--s1'),
      borderRadius:{topLeft:4,topRight:4}, borderSkipped:'bottom', maxBarThickness:58 }]}, options:op2 });
  tabela(alvo('nota'), ['Faixa de atraso','Nota media','Avaliacoes'],
    nota.map(d=>[d.k, d.nota.toFixed(2), d.n.toLocaleString('pt-BR')]));

  // 3) estado - emfase no pior, o resto recua (nao e rampa de valor)
  const est=porChave(entregues(f), r=>r.estado, rs=>({ pct:pctAtraso(rs), n:rs.length }))
    .filter(d=>d.n>=20).sort((a,b)=>b.pct-a.pct);
  const op3=base();
  op3.plugins.tooltip.callbacks={ label:(c)=>[` ${c.parsed.y.toFixed(1)}% atrasados`,
    ` ${est[c.dataIndex].n.toLocaleString('pt-BR')} itens entregues`] };
  op3.scales.y.ticks.callback=(v)=>v+'%';
  desenhar('c-estado',{ type:'bar', data:{ labels:est.map(d=>d.k), datasets:[{
      data:est.map(d=>+d.pct.toFixed(1)),
      backgroundColor:est.map((_,i)=> i===0 ? css('--s2') : css('--s1')),
      borderRadius:{topLeft:4,topRight:4}, borderSkipped:'bottom', maxBarThickness:34 }]}, options:op3 });
  tabela(alvo('estado'), ['Estado','% atrasados','Itens'],
    est.map(d=>[d.k, d.pct.toFixed(1)+'%', d.n.toLocaleString('pt-BR')]));

  // 4) problemas por categoria - empilhado, 2px de superficie entre os segmentos
  const prob=porChave(f, r=>r.categoria, rs=>({
    canc:100*rs.filter(r=>r.status==='cancelado').length/rs.length,
    dev:100*rs.filter(r=>r.status==='devolvido').length/rs.length, n:rs.length }))
    .sort((a,b)=>(b.canc+b.dev)-(a.canc+a.dev));
  const op4=legenda(base());
  op4.scales.x.stacked=true; op4.scales.y.stacked=true;
  op4.scales.y.ticks.callback=(v)=>v+'%';
  desenhar('c-problemas',{ type:'bar', data:{ labels:prob.map(d=>d.k), datasets:[
      { label:'Cancelado', data:prob.map(d=>+d.canc.toFixed(2)), backgroundColor:css('--s1'),
        borderColor:S, borderWidth:{top:2}, maxBarThickness:46 },
      { label:'Devolvido', data:prob.map(d=>+d.dev.toFixed(2)), backgroundColor:css('--s2'),
        borderRadius:{topLeft:4,topRight:4}, borderSkipped:'bottom', maxBarThickness:46 }]}, options:op4 });
  tabela(alvo('problemas'), ['Categoria','% cancelado','% devolvido','Itens'],
    prob.map(d=>[d.k, d.canc.toFixed(2)+'%', d.dev.toFixed(2)+'%', d.n.toLocaleString('pt-BR')]));

  // 5) chuva - uma medida no eixo; o atraso em dias fica no tooltip e na tabela
  const chuva=porChave(entregues(f), r=>r.fx_chuva, rs=>({
    pct:pctAtraso(rs), atraso:rs.reduce((s,r)=>s+r.atraso,0)/rs.length, n:rs.length }));
  const op5=base();
  op5.plugins.tooltip.callbacks={ label:(c)=>[` ${c.parsed.y.toFixed(1)}% atrasados`,
    ` ${chuva[c.dataIndex].atraso.toFixed(2)} dia de atraso medio`,
    ` ${chuva[c.dataIndex].n.toLocaleString('pt-BR')} itens`] };
  op5.scales.y.ticks.callback=(v)=>v+'%';
  desenhar('c-chuva',{ type:'bar', data:{ labels:chuva.map(d=>d.k), datasets:[{
      data:chuva.map(d=>+d.pct.toFixed(1)), backgroundColor:css('--s1'),
      borderRadius:{topLeft:4,topRight:4}, borderSkipped:'bottom', maxBarThickness:58 }]}, options:op5 });
  tabela(alvo('chuva'), ['Faixa de chuva','% atrasados','Atraso medio (dias)','Itens'],
    chuva.map(d=>[d.k, d.pct.toFixed(1)+'%', d.atraso.toFixed(2), d.n.toLocaleString('pt-BR')]));

  // 6) chuva dentro de cada regiao - ate 5 series, cor fixa por regiao
  const REG=['Centro-Oeste','Nordeste','Norte','Sudeste','Sul'];
  const TOM={'Centro-Oeste':'--s1','Nordeste':'--s2','Norte':'--s3','Sudeste':'--s4','Sul':'--s5'};
  const faixas=[...new Set(entregues(f).map(r=>r.fx_chuva).filter(Boolean))].sort();
  const presentes=REG.filter(reg => entregues(f).some(r=>r.regiao===reg));
  const celula=(reg,fx)=>{ const rs=entregues(f).filter(r=>r.regiao===reg&&r.fx_chuva===fx);
    return rs.length>=15 ? {pct:+pctAtraso(rs).toFixed(1), n:rs.length} : {pct:null, n:rs.length}; };
  const matriz={}; presentes.forEach(reg=>{ matriz[reg]=faixas.map(fx=>celula(reg,fx)); });
  const op6=legenda(base());
  op6.scales.y.ticks.callback=(v)=>v+'%';
  op6.plugins.tooltip.callbacks={ label:(c)=> c.parsed.y==null ? null :
    ` ${c.dataset.label}: ${c.parsed.y}% (${matriz[c.dataset.label][c.dataIndex].n} itens)` };
  desenhar('c-chuva-regiao',{ type:'bar', data:{ labels:faixas, datasets:presentes.map(reg=>({
      label:reg, data:matriz[reg].map(c=>c.pct), backgroundColor:css(TOM[reg]),
      borderRadius:{topLeft:4,topRight:4}, borderSkipped:'bottom', maxBarThickness:22,
      borderColor:S, borderWidth:{left:1,right:1} }))}, options:op6 });
  tabela(alvo('chuva-regiao'), ['Regiao', ...faixas],
    presentes.map(reg=>[reg, ...matriz[reg].map(c=>c.pct==null?'—':c.pct+'%')]));

  // 7 e 8) feriado: duas medidas de escala diferente = dois graficos
  const fer=porChave(entregues(f), r=>(r.feriado?'feriado':'dia comum'), rs=>({
    pedPorDia:new Set(rs.map(r=>r.pedido)).size/new Set(rs.map(r=>r.dia)).size,
    atraso:rs.reduce((s,r)=>s+r.atraso,0)/rs.length, dias:new Set(rs.map(r=>r.dia)).size }));
  const mini=(id,campo,sufixo,casas)=>{ const op=base();
    op.plugins.tooltip.callbacks={ label:(c)=>[` ${c.parsed.y.toFixed(casas)}${sufixo}`,
      ` ${fer[c.dataIndex].dias} dias no filtro`] };
    desenhar(id,{ type:'bar', data:{ labels:fer.map(d=>d.k), datasets:[{
      data:fer.map(d=>+d[campo].toFixed(casas)),
      backgroundColor:fer.map(d=>d.k==='feriado'?css('--s2'):css('--s1')),
      borderRadius:{topLeft:4,topRight:4}, borderSkipped:'bottom', maxBarThickness:72 }]}, options:op }); };
  mini('c-feriado-vol','pedPorDia','',2);
  mini('c-feriado-atraso','atraso',' dia',2);
  tabela(alvo('feriado-vol'), ['Tipo de dia','Pedidos por dia','Dias'],
    fer.map(d=>[d.k, d.pedPorDia.toFixed(2), d.dias]));
  tabela(alvo('feriado-atraso'), ['Tipo de dia','Atraso medio (dias)','Dias'],
    fer.map(d=>[d.k, d.atraso.toFixed(2), d.dias]));
}

document.querySelectorAll('.alterna').forEach(b => b.addEventListener('click', () => {
  const c=b.closest('.cartao'), cx=c.querySelector('.caixa'), tb=c.querySelector('.tabela-caixa');
  const mostrandoTabela = cx.hidden;
  cx.hidden = !mostrandoTabela; tb.hidden = mostrandoTabela;
  b.textContent = mostrandoTabela ? 'Tabela' : 'Grafico';
}));
[selRegiao,selCategoria,selDe,selAte].forEach(s => s.addEventListener('change', render));
document.getElementById('f-limpar').addEventListener('click', () => {
  [...selRegiao.options,...selCategoria.options].forEach(o=>o.selected=false);
  selDe.value=meses[0]; selAte.value=meses[meses.length-1]; render(); });
document.getElementById('f-tema').addEventListener('click', () => {
  const escuro = document.documentElement.getAttribute('data-theme')==='dark';
  document.documentElement.setAttribute('data-theme', escuro?'light':'dark'); render(); });
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
