"""PLANO B: gera um dashboard HTML local a partir do CSV (sem AWS, sem Superset).

Use se o Superset nao subir a tempo ou se o Learner Lab estiver instavel. O
resultado tambem serve de modelo do que o dashboard do Superset deve mostrar.
So usa a biblioteca padrao; o HTML carrega Chart.js de um CDN (precisa de
internet no navegador).

    python3 dashboard_local.py            # gera dashboard.html ao lado do script
    python3 dashboard_local.py --abrir    # e abre no navegador
"""
import csv
import json
import os
import sys
import webbrowser
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "..", "data", "pedidos_mercadofacil_tratado.csv")
CHUVA = os.path.join(AQUI, "..", "data", "chuva_diaria.csv")
SAIDA = os.path.join(AQUI, "dashboard.html")


def carregar():
    with open(CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def carregar_chuva():
    with open(CHUVA, encoding="utf-8") as f:
        return {(r["cidade"], r["dia"]): float(r["chuva_3d_mm"]) for r in csv.DictReader(f)}


def agregar(linhas):
    chuva = carregar_chuva()
    entregues = [r for r in linhas if r["status_pedido"] == "entregue"]

    por_mes = defaultdict(float)
    por_cat = defaultdict(float)
    for r in entregues:
        por_mes[r["data_pedido"][:7]] += float(r["valor_total"])
        por_cat[r["categoria"]] += float(r["valor_total"])

    atraso_regiao = defaultdict(list)
    for r in entregues:
        atraso_regiao[r["regiao"]].append(float(r["atraso_dias"]))

    faixas = {"0 (no prazo)": [], "1-3": [], "4-7": [], "8+": []}
    for r in entregues:
        if r["nota_avaliacao"] == "":
            continue
        a = int(r["atraso_dias"])
        chave = "0 (no prazo)" if a == 0 else "1-3" if a <= 3 else "4-7" if a <= 7 else "8+"
        faixas[chave].append(int(r["nota_avaliacao"]))

    problemas = defaultdict(lambda: [0, 0, 0])  # itens, cancelado, devolvido
    for r in linhas:
        p = problemas[r["categoria"]]
        p[0] += 1
        p[1] += r["status_pedido"] == "cancelado"
        p[2] += r["status_pedido"] == "devolvido"

    faixas_chuva = {"<5 mm": [], "5-20": [], "20-40": [], "40+": []}
    for r in entregues:
        mm = chuva[(r["cidade"], r["data_pedido"])]
        chave = "<5 mm" if mm < 5 else "5-20" if mm < 20 else "20-40" if mm < 40 else "40+"
        faixas_chuva[chave].append(float(r["atraso_dias"]))

    def media(v):
        return round(sum(v) / len(v), 2) if v else 0

    meses = sorted(por_mes)
    cats = sorted(por_cat, key=por_cat.get, reverse=True)
    regs = sorted(atraso_regiao)
    return {
        "kpis": {
            "receita": round(sum(por_mes.values()), 2),
            "pedidos": len({r["pedido_id"] for r in entregues}),
            "atrasados": round(100 * sum(float(r["atraso_dias"]) > 0 for r in entregues) / len(entregues), 1),
            "nota": media([int(r["nota_avaliacao"]) for r in entregues if r["nota_avaliacao"] != ""]),
        },
        "mes": {"x": meses, "y": [round(por_mes[m], 2) for m in meses]},
        "cat": {"x": cats, "y": [round(por_cat[c], 2) for c in cats]},
        "regiao": {"x": regs, "y": [media(atraso_regiao[g]) for g in regs]},
        "nota": {"x": list(faixas), "y": [media(v) for v in faixas.values()]},
        "chuva": {"x": list(faixas_chuva), "y": [media(v) for v in faixas_chuva.values()]},
        "problemas": {
            "x": cats,
            "cancel": [round(100 * problemas[c][1] / problemas[c][0], 2) for c in cats],
            "devol": [round(100 * problemas[c][2] / problemas[c][0], 2) for c in cats],
        },
    }


HTML = """<!doctype html><html lang="pt-br"><meta charset="utf-8">
<title>MercadoFacil - Dashboard (Plano B)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>body{font-family:sans-serif;margin:24px;background:#f5f6f8}
.kpis{display:flex;gap:16px;margin-bottom:16px}.kpi{background:#fff;padding:16px 24px;border-radius:8px}
.kpi b{display:block;font-size:26px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:#fff;padding:12px;border-radius:8px}</style>
<h1>MercadoFacil 2025 - visao executiva</h1>
<div class="kpis" id="kpis"></div>
<div class="grid">
<div class="card"><canvas id="c1"></canvas></div><div class="card"><canvas id="c2"></canvas></div>
<div class="card"><canvas id="c3"></canvas></div><div class="card"><canvas id="c4"></canvas></div>
<div class="card"><canvas id="c5"></canvas></div><div class="card"><canvas id="c6"></canvas></div></div>
<script>
const D = __DADOS__;
const k = D.kpis, fmt = new Intl.NumberFormat('pt-BR');
document.getElementById('kpis').innerHTML =
 `<div class=kpi>Receita (entregues)<b>R$ ${fmt.format(k.receita)}</b></div>`+
 `<div class=kpi>Pedidos<b>${fmt.format(k.pedidos)}</b></div>`+
 `<div class=kpi>Itens atrasados<b>${k.atrasados}%</b></div>`+
 `<div class=kpi>Nota media<b>${k.nota}</b></div>`;
function g(id,type,titulo,x,datasets){new Chart(document.getElementById(id),{type,
 data:{labels:x,datasets},options:{plugins:{title:{display:true,text:titulo}}}})}
g('c1','line','Receita por mes (R$)',D.mes.x,[{label:'receita',data:D.mes.y,borderColor:'#1f77b4'}]);
g('c2','bar','Receita por categoria (R$)',D.cat.x,[{label:'receita',data:D.cat.y,backgroundColor:'#2ca02c'}]);
g('c3','bar','Atraso medio (dias) por regiao',D.regiao.x,[{label:'dias',data:D.regiao.y,backgroundColor:'#d62728'}]);
g('c4','bar','Nota media por faixa de atraso (dias)',D.nota.x,[{label:'nota',data:D.nota.y,backgroundColor:'#ff7f0e'}]);
g('c5','bar','% cancelado e devolvido por categoria',D.problemas.x,[
 {label:'% cancelado',data:D.problemas.cancel,backgroundColor:'#9467bd'},
 {label:'% devolvido',data:D.problemas.devol,backgroundColor:'#8c564b'}]);
g('c6','bar','Atraso medio (dias) por chuva nos 3 dias (mm)',D.chuva.x,[{label:'dias',data:D.chuva.y,backgroundColor:'#17becf'}]);
</script></html>"""


def main():
    dados = agregar(carregar())
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(HTML.replace("__DADOS__", json.dumps(dados, ensure_ascii=False)))
    print(f"Gerado: {SAIDA}")
    if "--abrir" in sys.argv:
        webbrowser.open("file://" + SAIDA)


if __name__ == "__main__":
    main()
