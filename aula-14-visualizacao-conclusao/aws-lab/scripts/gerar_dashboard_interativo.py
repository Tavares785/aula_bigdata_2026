"""Gera o dashboard interativo MercadoFácil 2025 em HTML puro.

Sem dependências externas — só biblioteca padrão. O HTML gerado carrega
Chart.js de um CDN; o navegador precisa de internet apenas para isso.

    python3 gerar_dashboard_interativo.py           # gera dashboard_interativo.html
    python3 gerar_dashboard_interativo.py --abrir   # gera e abre no navegador
"""
import csv
import json
import os
import sys
import webbrowser
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV_PEDIDOS = os.path.join(AQUI, "..", "data", "pedidos_mercadofacil_tratado.csv")
CSV_CHUVA = os.path.join(AQUI, "..", "data", "chuva_diaria.csv")
CSV_FERIADOS = os.path.join(AQUI, "..", "data", "feriados.csv")
SAIDA = os.path.join(AQUI, "dashboard_interativo.html")


def carregar_pedidos():
    with open(CSV_PEDIDOS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def carregar_chuva():
    with open(CSV_CHUVA, encoding="utf-8") as f:
        return {(r["cidade"], r["dia"]): float(r["chuva_3d_mm"]) for r in csv.DictReader(f)}


def carregar_feriados():
    with open(CSV_FERIADOS, encoding="utf-8") as f:
        return {r["dia"]: r["nome"] for r in csv.DictReader(f)}


def media(lst):
    return round(sum(lst) / len(lst), 2) if lst else 0


def construir_dados(pedidos, chuva_map, feriados_map):
    entregues = [r for r in pedidos if r["status_pedido"] == "entregue"]

    # ── Filtros disponíveis ──────────────────────────────────────────────────
    regioes = sorted({r["regiao"] for r in pedidos})
    categorias = sorted({r["categoria"] for r in pedidos})
    meses = sorted({r["data_pedido"][:7] for r in pedidos})

    # ── KPIs globais ─────────────────────────────────────────────────────────
    receita_total = round(sum(float(r["valor_total"]) for r in entregues), 2)
    pedidos_unicos = len({r["pedido_id"] for r in entregues})
    pct_atraso = round(
        100 * sum(float(r["atraso_dias"]) > 0 for r in entregues) / len(entregues), 1
    )
    notas = [int(r["nota_avaliacao"]) for r in entregues if r["nota_avaliacao"]]
    nota_media = media(notas)
    ticket_medio = round(receita_total / pedidos_unicos, 2) if pedidos_unicos else 0
    pct_devol = round(100 * sum(r["status_pedido"] == "devolvido" for r in pedidos) / len(pedidos), 1)

    # ── Série diária (receita + volume) para gráfico de linha ────────────────
    receita_dia = defaultdict(float)
    volume_dia = defaultdict(int)
    for r in entregues:
        d = r["data_pedido"]
        receita_dia[d] += float(r["valor_total"])
        volume_dia[d] += 1

    dias_ord = sorted(receita_dia)
    # marca Black Friday (última sexta de novembro 2025 = 28/nov) e Natal
    eventos = {}
    for d in dias_ord:
        if d in feriados_map:
            eventos[d] = feriados_map[d]
        elif d == "2025-11-28":
            eventos[d] = "Black Friday"

    # ── Receita por mês ───────────────────────────────────────────────────────
    receita_mes = defaultdict(float)
    for r in entregues:
        receita_mes[r["data_pedido"][:7]] += float(r["valor_total"])

    # ── Atraso x nota (gráfico de barras paired) ──────────────────────────────
    faixas_atraso = ["0 dias (no prazo)", "1-3 dias", "4-7 dias", "8+ dias"]
    notas_por_faixa = {f: [] for f in faixas_atraso}
    pct_atraso_faixa = {f: 0 for f in faixas_atraso}
    contagem_faixa = defaultdict(int)
    for r in entregues:
        a = int(r["atraso_dias"])
        chave = (
            "0 dias (no prazo)" if a == 0
            else "1-3 dias" if a <= 3
            else "4-7 dias" if a <= 7
            else "8+ dias"
        )
        contagem_faixa[chave] += 1
        if r["nota_avaliacao"]:
            notas_por_faixa[chave].append(int(r["nota_avaliacao"]))

    total_entregues = len(entregues)
    for f in faixas_atraso:
        pct_atraso_faixa[f] = round(100 * contagem_faixa[f] / total_entregues, 1)

    # ── Atraso por região / transportadora ────────────────────────────────────
    atraso_regiao = defaultdict(list)
    atraso_transp = defaultdict(list)
    for r in entregues:
        atraso_regiao[r["regiao"]].append(float(r["atraso_dias"]))
        atraso_transp[r["transportadora"]].append(float(r["atraso_dias"]))

    transportadoras = sorted(atraso_transp)

    # ── Problemas por categoria ───────────────────────────────────────────────
    total_cat = defaultdict(int)
    cancel_cat = defaultdict(int)
    devol_cat = defaultdict(int)
    for r in pedidos:
        total_cat[r["categoria"]] += 1
        if r["status_pedido"] == "cancelado":
            cancel_cat[r["categoria"]] += 1
        if r["status_pedido"] == "devolvido":
            devol_cat[r["categoria"]] += 1

    cats_ord = sorted(total_cat, key=total_cat.get, reverse=True)

    # ── Chuva x atraso ────────────────────────────────────────────────────────
    faixas_chuva = ["<5 mm", "5-20 mm", "20-40 mm", "40+ mm"]
    atraso_chuva = {f: [] for f in faixas_chuva}
    vol_chuva = {f: 0 for f in faixas_chuva}
    for r in entregues:
        key = (r["cidade"], r["data_pedido"])
        mm = chuva_map.get(key, 0)
        chave = (
            "<5 mm" if mm < 5
            else "5-20 mm" if mm < 20
            else "20-40 mm" if mm < 40
            else "40+ mm"
        )
        atraso_chuva[chave].append(float(r["atraso_dias"]))
        vol_chuva[chave] += 1

    # ── Feriados: volume de pedidos no dia e dias adjacentes ─────────────────
    feriados_analise = []
    for dia, nome in sorted(feriados_map.items()):
        vol = volume_dia.get(dia, 0)
        ant = volume_dia.get(_dia_offset(dia, -1), 0)
        pos = volume_dia.get(_dia_offset(dia, 1), 0)
        feriados_analise.append({"nome": nome[:20], "dia": dia, "vol": vol, "ant": ant, "pos": pos})

    # ── Receita e atraso por canal ────────────────────────────────────────────
    receita_canal = defaultdict(float)
    atraso_canal = defaultdict(list)
    for r in entregues:
        receita_canal[r["canal"]] += float(r["valor_total"])
        atraso_canal[r["canal"]].append(float(r["atraso_dias"]))

    canais = sorted(receita_canal, key=receita_canal.get, reverse=True)

    # ── Dados por combinação (para filtro JS) ─────────────────────────────────
    # Cada linha filtrada tem: regiao, categoria, mes, atraso_dias, nota,
    # valor_total, status, canal, transportadora, chuva_3d_mm
    linhas_js = []
    for r in pedidos:
        key = (r["cidade"], r["data_pedido"])
        mm = chuva_map.get(key, 0)
        linhas_js.append({
            "regiao": r["regiao"],
            "categoria": r["categoria"],
            "mes": r["data_pedido"][:7],
            "status": r["status_pedido"],
            "canal": r["canal"],
            "transp": r["transportadora"],
            "atraso": float(r["atraso_dias"]) if r["atraso_dias"] else 0,
            "nota": int(r["nota_avaliacao"]) if r["nota_avaliacao"] else None,
            "valor": float(r["valor_total"]),
            "chuva": round(mm, 1),
        })

    return {
        "meta": {
            "regioes": regioes,
            "categorias": categorias,
            "meses": meses,
        },
        "kpis": {
            "receita": receita_total,
            "pedidos": pedidos_unicos,
            "pct_atraso": pct_atraso,
            "nota": nota_media,
            "ticket": ticket_medio,
            "pct_devol": pct_devol,
        },
        "serie_mensal": {
            "x": sorted(receita_mes),
            "receita": [round(receita_mes[m], 2) for m in sorted(receita_mes)],
        },
        "atraso_nota": {
            "faixas": faixas_atraso,
            "notas": [media(notas_por_faixa[f]) for f in faixas_atraso],
            "pct": [pct_atraso_faixa[f] for f in faixas_atraso],
        },
        "logistica": {
            "regioes": regioes,
            "atraso_regiao": [media(atraso_regiao[r]) for r in regioes],
            "transportadoras": transportadoras,
            "atraso_transp": [media(atraso_transp[t]) for t in transportadoras],
        },
        "problemas": {
            "cats": cats_ord,
            "cancel_pct": [round(100 * cancel_cat[c] / total_cat[c], 2) for c in cats_ord],
            "devol_pct": [round(100 * devol_cat[c] / total_cat[c], 2) for c in cats_ord],
        },
        "chuva": {
            "faixas": faixas_chuva,
            "atraso_medio": [media(atraso_chuva[f]) for f in faixas_chuva],
            "volume": [vol_chuva[f] for f in faixas_chuva],
        },
        "feriados": feriados_analise[:12],
        "canais": {
            "nomes": canais,
            "receita": [round(receita_canal[c], 2) for c in canais],
            "atraso": [media(atraso_canal[c]) for c in canais],
        },
        "linhas": linhas_js,
    }


def _dia_offset(dia_str, delta):
    import datetime
    d = datetime.date.fromisoformat(dia_str) + datetime.timedelta(days=delta)
    return d.isoformat()


# ── Template HTML ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MercadoFácil 2025 — Dashboard Executivo</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #f0f2f5;
    --card: #ffffff;
    --brand: #0a2342;
    --accent: #e63946;
    --accent2: #2a9d8f;
    --accent3: #e9c46a;
    --text: #1a1a2e;
    --muted: #6c757d;
    --border: #dee2e6;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); }

  /* ── Header ── */
  header {
    background: var(--brand);
    color: #fff;
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  header h1 { font-size: 1.4rem; font-weight: 700; letter-spacing: .5px; }
  header small { font-size: .8rem; opacity: .7; }

  /* ── Filtros ── */
  #filtros {
    background: #fff;
    border-bottom: 1px solid var(--border);
    padding: 12px 32px;
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
  }
  #filtros label { font-size: .82rem; color: var(--muted); font-weight: 600; }
  #filtros select {
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 5px 10px;
    font-size: .88rem;
    color: var(--text);
    background: #fff;
    cursor: pointer;
  }
  #filtros select:focus { outline: 2px solid var(--brand); }
  #btn-limpar {
    margin-left: auto;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: .85rem;
    cursor: pointer;
    font-weight: 600;
  }
  #btn-limpar:hover { opacity: .88; }

  /* ── Layout ── */
  main { padding: 24px 32px; }

  /* ── KPIs ── */
  .kpis { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 24px; }
  .kpi {
    background: var(--card);
    border-radius: 10px;
    padding: 16px 18px;
    border-top: 4px solid var(--brand);
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .kpi.vermelho { border-top-color: var(--accent); }
  .kpi.verde { border-top-color: var(--accent2); }
  .kpi.amarelo { border-top-color: var(--accent3); }
  .kpi span { font-size: .75rem; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
  .kpi b { display: block; font-size: 1.55rem; font-weight: 700; margin-top: 4px; color: var(--text); }
  .kpi small { font-size: .72rem; color: var(--muted); }

  /* ── Grid de gráficos ── */
  .grid { display: grid; gap: 18px; }
  .grid-2 { grid-template-columns: 1fr 1fr; }
  .grid-3 { grid-template-columns: 2fr 1fr; }
  .card {
    background: var(--card);
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .card h3 { font-size: .88rem; font-weight: 700; color: var(--brand); margin-bottom: 12px; }
  .card p.sub { font-size: .74rem; color: var(--muted); margin-top: 8px; }
  .card canvas { max-height: 240px; }

  /* ── Insight box ── */
  .insights { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 20px; }
  .insight {
    background: var(--brand);
    color: #fff;
    border-radius: 10px;
    padding: 16px 18px;
    font-size: .84rem;
    line-height: 1.55;
  }
  .insight strong { display: block; font-size: .95rem; margin-bottom: 6px; color: var(--accent3); }

  /* ── Footer ── */
  footer { text-align: center; padding: 20px; font-size: .75rem; color: var(--muted); }

  @media (max-width: 1100px) {
    .kpis { grid-template-columns: repeat(3, 1fr); }
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
    .insights { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<header>
  <div>
    <h1>🛒 MercadoFácil — Dashboard Executivo</h1>
    <small>Dados de jan–dez/2025 · Atualizado em tempo real via filtros</small>
  </div>
  <div style="text-align:right">
    <small id="lbl-filtro-ativo" style="color:#aaa">Sem filtros ativos</small>
  </div>
</header>

<div id="filtros">
  <label>Região</label>
  <select id="f-regiao"><option value="">Todas</option></select>
  <label>Categoria</label>
  <select id="f-cat"><option value="">Todas</option></select>
  <label>Mês</label>
  <select id="f-mes"><option value="">Todos</option></select>
  <label>Canal</label>
  <select id="f-canal"><option value="">Todos</option></select>
  <button id="btn-limpar">✕ Limpar filtros</button>
</div>

<main>
  <!-- KPIs -->
  <div class="kpis">
    <div class="kpi verde">
      <span>Receita Total</span><b id="k-receita">—</b><small>pedidos entregues</small>
    </div>
    <div class="kpi">
      <span>Pedidos</span><b id="k-pedidos">—</b><small>únicos entregues</small>
    </div>
    <div class="kpi">
      <span>Ticket Médio</span><b id="k-ticket">—</b><small>por pedido</small>
    </div>
    <div class="kpi verde">
      <span>Nota Média</span><b id="k-nota">—</b><small>avaliação 1–5</small>
    </div>
    <div class="kpi vermelho">
      <span>Itens Atrasados</span><b id="k-atraso">—</b><small>do total entregue</small>
    </div>
    <div class="kpi amarelo">
      <span>% Devolvidos</span><b id="k-devol">—</b><small>do total de itens</small>
    </div>
  </div>

  <!-- Linha 1: série mensal + atraso x nota -->
  <div class="grid grid-2" style="margin-bottom:18px">
    <div class="card">
      <h3>📈 Receita Mensal — Black Friday e Natal em destaque</h3>
      <canvas id="c-serie"></canvas>
      <p class="sub">Fonte: vw_serie_diaria · Filtros: região, categoria, mês, canal</p>
    </div>
    <div class="card">
      <h3>⭐ Nota Média por Faixa de Atraso</h3>
      <canvas id="c-nota"></canvas>
      <p class="sub">Fonte: vw_atraso_nota · Quanto o atraso derruba a satisfação?</p>
    </div>
  </div>

  <!-- Linha 2: logística (região + transportadora) -->
  <div class="grid grid-2" style="margin-bottom:18px">
    <div class="card">
      <h3>🗺️ Atraso Médio por Região (dias)</h3>
      <canvas id="c-regiao"></canvas>
      <p class="sub">Fonte: vw_logistica_estado</p>
    </div>
    <div class="card">
      <h3>🚚 Atraso Médio por Transportadora (dias)</h3>
      <canvas id="c-transp"></canvas>
      <p class="sub">Fonte: vw_logistica_estado</p>
    </div>
  </div>

  <!-- Linha 3: problemas por categoria + chuva -->
  <div class="grid grid-2" style="margin-bottom:18px">
    <div class="card">
      <h3>📦 % Cancelamentos e Devoluções por Categoria</h3>
      <canvas id="c-problemas"></canvas>
      <p class="sub">Fonte: vw_problemas_categoria</p>
    </div>
    <div class="card">
      <h3>🌧️ Atraso Médio vs. Chuva Acumulada (3 dias, mm)</h3>
      <canvas id="c-chuva"></canvas>
      <p class="sub">Fonte: vw_atraso_chuva · Correlação ≠ causalidade isolada</p>
    </div>
  </div>

  <!-- Linha 4: canal -->
  <div class="grid grid-2" style="margin-bottom:18px">
    <div class="card">
      <h3>📊 Receita por Canal de Venda</h3>
      <canvas id="c-canal-rec"></canvas>
      <p class="sub">Fonte: vw_serie_diaria</p>
    </div>
    <div class="card">
      <h3>📊 Atraso Médio por Canal de Venda</h3>
      <canvas id="c-canal-atr"></canvas>
      <p class="sub">Fonte: vw_logistica_estado</p>
    </div>
  </div>

  <!-- Insights -->
  <div class="insights">
    <div class="insight">
      <strong>💡 Insight 1 — Atraso destrói nota</strong>
      Itens entregues no prazo têm nota média de <span id="ins-nota-ok">—</span>/5.
      Com 8+ dias de atraso, a nota despenca para <span id="ins-nota-ruim">—</span>/5.
      Reduzir atrasos é a alavanca mais direta para melhorar CSAT.
    </div>
    <div class="insight">
      <strong>💡 Insight 2 — Norte precisa de atenção</strong>
      A região Norte concentra o maior atraso médio (<span id="ins-norte">—</span> dias),
      enquanto o Sudeste opera com <span id="ins-sudeste">—</span> dias.
      Revisar a cobertura logística no Norte pode reduzir devoluções nessa região.
    </div>
    <div class="insight">
      <strong>💡 Insight 3 — Chuva correlaciona com atraso</strong>
      Com mais de 40 mm de chuva nos 3 dias seguintes ao pedido, o atraso médio chega a
      <span id="ins-chuva-alto">—</span> dias, ante <span id="ins-chuva-baixo">—</span> dias em dias secos.
      Isso sugere adicionar buffer no prazo estimado em períodos chuvosos.
    </div>
  </div>
</main>

<footer>MercadoFácil 2025 · Projeto Big Data — Aula 14 · Fonte: pedidos_mercadofacil_tratado.csv + Open-Meteo + BrasilAPI</footer>

<script>
// ── Dados injetados pelo Python ───────────────────────────────────────────────
const RAW = __DADOS__;

// ── Utilitários ───────────────────────────────────────────────────────────────
const fmt  = new Intl.NumberFormat('pt-BR');
const fmtR = new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL', maximumFractionDigits:0});
function media(arr){ return arr.length ? +(arr.reduce((a,b)=>a+b,0)/arr.length).toFixed(2) : 0; }
function pct(n, total){ return total ? +(100*n/total).toFixed(1) : 0; }

// ── Filtros ───────────────────────────────────────────────────────────────────
const selReg  = document.getElementById('f-regiao');
const selCat  = document.getElementById('f-cat');
const selMes  = document.getElementById('f-mes');
const selCan  = document.getElementById('f-canal');

RAW.meta.regioes.forEach(v => selReg.add(new Option(v, v)));
RAW.meta.categorias.forEach(v => selCat.add(new Option(v, v)));
RAW.meta.meses.forEach(v => selMes.add(new Option(v, v)));
// canais dinâmicos
[...new Set(RAW.linhas.map(r=>r.canal))].sort().forEach(v => selCan.add(new Option(v, v)));

function getFiltros(){
  return {reg: selReg.value, cat: selCat.value, mes: selMes.value, can: selCan.value};
}

function filtrarLinhas(f){
  return RAW.linhas.filter(r =>
    (!f.reg || r.regiao === f.reg) &&
    (!f.cat || r.categoria === f.cat) &&
    (!f.mes || r.mes === f.mes) &&
    (!f.can || r.canal === f.can)
  );
}

// ── Instâncias Chart.js ───────────────────────────────────────────────────────
const charts = {};

function mkChart(id, type, data, options){
  const ctx = document.getElementById(id).getContext('2d');
  if(charts[id]) charts[id].destroy();
  charts[id] = new Chart(ctx, {type, data, options: Object.assign({
    responsive: true,
    plugins:{ legend:{position:'bottom', labels:{font:{size:11}}}, tooltip:{} },
    scales: type === 'bar' || type === 'line' ? {
      x:{ ticks:{font:{size:10}} },
      y:{ ticks:{font:{size:10}} }
    } : {}
  }, options||{})});
}

const CORES = {
  azul:  '#0a2342', verde: '#2a9d8f', vermelho: '#e63946',
  laranja: '#f4a261', amarelo: '#e9c46a', roxo: '#7b2d8b', ciano: '#17becf',
  azulClaro: 'rgba(10,35,66,.15)'
};

// ── Renderização ──────────────────────────────────────────────────────────────
function renderizar(){
  const f = getFiltros();
  const linhas = filtrarLinhas(f);
  const entregues = linhas.filter(r => r.status === 'entregue');

  // label filtro ativo
  const ativos = [f.reg, f.cat, f.mes, f.can].filter(Boolean);
  document.getElementById('lbl-filtro-ativo').textContent =
    ativos.length ? '🔍 Filtros: ' + ativos.join(' · ') : 'Sem filtros ativos';

  // ── KPIs ──
  const receita = entregues.reduce((s,r)=>s+r.valor,0);
  const pedUnicos = new Set(entregues.map(r=>r.pedido_id||r.valor+'_'+r.mes)).size; // aproximação
  // usamos contagem direta de linhas como itens entregues (1 linha = 1 item)
  const nItens = entregues.length;
  const notas  = entregues.filter(r=>r.nota!==null).map(r=>r.nota);
  const nAtraso = entregues.filter(r=>r.atraso>0).length;
  const nDevol  = linhas.filter(r=>r.status==='devolvido').length;

  document.getElementById('k-receita').textContent = fmtR.format(Math.round(receita));
  document.getElementById('k-pedidos').textContent = fmt.format(nItens);
  document.getElementById('k-ticket').textContent  = fmtR.format(nItens ? Math.round(receita/nItens) : 0);
  document.getElementById('k-nota').textContent    = media(notas).toFixed(2);
  document.getElementById('k-atraso').textContent  = pct(nAtraso, nItens) + '%';
  document.getElementById('k-devol').textContent   = pct(nDevol, linhas.length) + '%';

  // ── Série mensal ──
  const recMes = {};
  RAW.meta.meses.forEach(m => recMes[m] = 0);
  entregues.forEach(r => { if(recMes[r.mes]!==undefined) recMes[r.mes]+=r.valor; });
  const mesesFilt = f.mes ? [f.mes] : RAW.meta.meses;
  mkChart('c-serie','line',{
    labels: mesesFilt,
    datasets:[{
      label:'Receita (R$)', data: mesesFilt.map(m=>+recMes[m].toFixed(2)),
      borderColor: CORES.azul, backgroundColor: CORES.azulClaro,
      fill:true, tension:.35, pointRadius:4,
    }]
  },{scales:{y:{ticks:{callback:v=>fmtR.format(v)}}}});

  // ── Atraso x nota ──
  const faixasN = ['0 dias','1-3 dias','4-7 dias','8+ dias'];
  const buckets = {
    '0 dias': [], '1-3 dias': [], '4-7 dias': [], '8+ dias': []
  };
  entregues.forEach(r => {
    if(r.nota === null) return;
    const a = r.atraso;
    const k = a===0?'0 dias': a<=3?'1-3 dias': a<=7?'4-7 dias':'8+ dias';
    buckets[k].push(r.nota);
  });
  const notasMedia = faixasN.map(k => media(buckets[k]));

  mkChart('c-nota','bar',{
    labels: faixasN,
    datasets:[{
      label:'Nota média', data: notasMedia,
      backgroundColor:[CORES.verde, CORES.amarelo, CORES.laranja, CORES.vermelho]
    }]
  },{scales:{y:{min:0, max:5}}});

  // preenche insights
  document.getElementById('ins-nota-ok').textContent   = (notasMedia[0]||'—');
  document.getElementById('ins-nota-ruim').textContent = (notasMedia[3]||'—');

  // ── Atraso por região ──
  const regioes = RAW.meta.regioes;
  const atrasoReg = regioes.map(reg => {
    const vals = entregues.filter(r=>r.regiao===reg).map(r=>r.atraso);
    return media(vals);
  });
  mkChart('c-regiao','bar',{
    labels: regioes,
    datasets:[{label:'Atraso médio (dias)', data: atrasoReg, backgroundColor: CORES.vermelho}]
  },{});

  // insight norte / sudeste
  const idxNorte   = regioes.indexOf('Norte');
  const idxSudeste = regioes.indexOf('Sudeste');
  document.getElementById('ins-norte').textContent   = atrasoReg[idxNorte]  ?? '—';
  document.getElementById('ins-sudeste').textContent = atrasoReg[idxSudeste] ?? '—';

  // ── Atraso por transportadora ──
  const transpSet = [...new Set(RAW.linhas.map(r=>r.transp))].sort();
  const atrasoTr = transpSet.map(t => {
    const vals = entregues.filter(r=>r.transp===t).map(r=>r.atraso);
    return media(vals);
  });
  mkChart('c-transp','bar',{
    labels: transpSet,
    datasets:[{label:'Atraso médio (dias)', data: atrasoTr,
      backgroundColor: [CORES.azul, CORES.verde, CORES.amarelo, CORES.roxo]}]
  },{});

  // ── Problemas por categoria ──
  const catsSet = [...new Set(RAW.linhas.map(r=>r.categoria))];
  const pCancel = catsSet.map(c => {
    const sub = linhas.filter(r=>r.categoria===c);
    return pct(sub.filter(r=>r.status==='cancelado').length, sub.length);
  });
  const pDevol = catsSet.map(c => {
    const sub = linhas.filter(r=>r.categoria===c);
    return pct(sub.filter(r=>r.status==='devolvido').length, sub.length);
  });
  mkChart('c-problemas','bar',{
    labels: catsSet,
    datasets:[
      {label:'% cancelado',  data: pCancel, backgroundColor: CORES.roxo},
      {label:'% devolvido',  data: pDevol,  backgroundColor: CORES.laranja},
    ]
  },{});

  // ── Chuva x atraso ──
  const fChuva = ['<5 mm','5-20 mm','20-40 mm','40+ mm'];
  const bktChuva = {'<5 mm':[],'5-20 mm':[],'20-40 mm':[],'40+ mm':[]};
  entregues.forEach(r => {
    const mm = r.chuva;
    const k = mm<5?'<5 mm': mm<20?'5-20 mm': mm<40?'20-40 mm':'40+ mm';
    bktChuva[k].push(r.atraso);
  });
  const atrasoC = fChuva.map(k=>media(bktChuva[k]));

  mkChart('c-chuva','bar',{
    labels: fChuva,
    datasets:[{label:'Atraso médio (dias)', data: atrasoC, backgroundColor: CORES.ciano}]
  },{});

  document.getElementById('ins-chuva-alto').textContent = atrasoC[3] ?? '—';
  document.getElementById('ins-chuva-baixo').textContent = atrasoC[0] ?? '—';

  // ── Canal ──
  const canaisSet = [...new Set(RAW.linhas.map(r=>r.canal))].sort();
  const recCan  = canaisSet.map(c => entregues.filter(r=>r.canal===c).reduce((s,r)=>s+r.valor,0));
  const atrCan  = canaisSet.map(c => media(entregues.filter(r=>r.canal===c).map(r=>r.atraso)));

  mkChart('c-canal-rec','bar',{
    labels: canaisSet,
    datasets:[{label:'Receita (R$)', data: recCan.map(v=>+v.toFixed(2)),
      backgroundColor:[CORES.azul, CORES.verde, CORES.amarelo]}]
  },{scales:{y:{ticks:{callback:v=>fmtR.format(v)}}}});

  mkChart('c-canal-atr','bar',{
    labels: canaisSet,
    datasets:[{label:'Atraso médio (dias)', data: atrCan,
      backgroundColor:[CORES.azul, CORES.verde, CORES.amarelo]}]
  },{});
}

// ── Eventos ───────────────────────────────────────────────────────────────────
[selReg, selCat, selMes, selCan].forEach(s => s.addEventListener('change', renderizar));
document.getElementById('btn-limpar').addEventListener('click', () => {
  [selReg, selCat, selMes, selCan].forEach(s => s.value = '');
  renderizar();
});

renderizar();
</script>
</body>
</html>
"""


def main():
    print("Carregando dados...")
    pedidos = carregar_pedidos()
    chuva_map = carregar_chuva()
    feriados_map = carregar_feriados()

    print("Calculando agregações...")
    dados = construir_dados(pedidos, chuva_map, feriados_map)

    html = HTML_TEMPLATE.replace("__DADOS__", json.dumps(dados, ensure_ascii=False))
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard gerado: {SAIDA}")
    if "--abrir" in sys.argv:
        webbrowser.open("file://" + SAIDA)


if __name__ == "__main__":
    main()
