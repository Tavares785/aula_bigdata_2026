"""Cria datasets, graficos e o dashboard MercadoFacil no Superset 3.1 via API REST.

Alternativa reprodutivel a montar o dashboard clicando (Missao 3). Depois de criar
as views do 03_views_atividade.sql no Athena:

    SUPERSET_SENHA=... python3 superset_dashboard.py http://<ip-da-ec2>:8088
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

U = sys.argv[1]
PW = os.environ["SUPERSET_SENHA"]  # mesma senha do terraform.tfvars
SCHEMA = "mercadofacil_aula14"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
H = {"Content-Type": "application/json"}


def call(method, path, body=None):
    req = urllib.request.Request(U + path, method=method, headers=H,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with opener.open(req) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:800]}")


tok = call("POST", "/api/v1/security/login",
           {"username": "admin", "password": PW, "provider": "db", "refresh": True})["access_token"]
H["Authorization"] = "Bearer " + tok
H["X-CSRFToken"] = call("GET", "/api/v1/security/csrf_token/")["result"]
H["Referer"] = U

# --- limpa execucao anterior (idempotente) ---
for d in call("GET", "/api/v1/dashboard/?q=(page_size:100)")["result"]:
    call("DELETE", f"/api/v1/dashboard/{d['id']}")
for c in call("GET", "/api/v1/chart/?q=(page_size:100)")["result"]:
    call("DELETE", f"/api/v1/chart/{c['id']}")

# --- datasets ---
views = ["vw_kpis", "vw_serie_diaria", "vw_atraso_nota", "vw_logistica_estado",
         "vw_problemas_categoria", "vw_atraso_chuva", "vw_atraso_chuva_regiao",
         "vw_feriados", "vw_transportadora"]
existing = {d["table_name"]: d["id"] for d in
            call("GET", "/api/v1/dataset/?q=(page_size:100)")["result"]}
ds = {}
for v in views:
    ds[v] = existing.get(v) or call("POST", "/api/v1/dataset/",
                                    {"database": 1, "schema": SCHEMA, "table_name": v})["id"]
print("datasets", ds)


def sql_metric(expr, label):
    return {"expressionType": "SQL", "sqlExpression": expr, "label": label,
            "hasCustomLabel": True, "optionName": "m_" + label.replace(" ", "_")}


def chart(name, viz, view, params):
    p = {"datasource": f"{ds[view]}__table", "viz_type": viz, "adhoc_filters": [],
         "row_limit": 10000, **params}
    cid = call("POST", "/api/v1/chart/", {
        "slice_name": name, "viz_type": viz, "datasource_id": ds[view],
        "datasource_type": "table", "params": json.dumps(p),
        "query_context_generation": True})["id"]
    print(cid, name)
    return cid


def big(name, col, fmt):
    return chart(name, "big_number_total", "vw_kpis", {
        "metric": sql_metric(f"MAX({col})", name), "subheader": "",
        "y_axis_format": fmt, "header_font_size": 0.4, "subheader_font_size": 0.15})


def bar(name, view, x, metrics, groupby=None, stack=False, xlab="", ylab="", fmt="SMART_NUMBER",
        sort_x=True):
    return chart(name, "echarts_timeseries_bar", view, {
        "x_axis": x, "metrics": metrics, "groupby": groupby or [],
        "stack": "Stack" if stack else None, "orientation": "vertical",
        "x_axis_title": xlab, "x_axis_title_margin": 30, "y_axis_title": ylab,
        "y_axis_title_margin": 40, "y_axis_title_position": "Left",
        "y_axis_format": fmt, "show_legend": True, "legendType": "scroll",
        "legendOrientation": "top", "show_value": True, "rich_tooltip": True,
        "x_axis_sort_asc": True, "x_axis_sort_series": "name", "x_axis_sort": x if sort_x else None,
        "truncate_metric": True, "only_total": True, "xAxisLabelRotation": 0})


ids = {}
ids["receita"] = big("Receita total (R$, entregues)", "receita_total", ",.2f")
ids["pedidos"] = big("Pedidos entregues", "pedidos", ",d")
ids["ticket"] = big("Ticket medio (R$)", "ticket_medio", ",.2f")
ids["atraso"] = big("% itens atrasados", "pct_itens_atrasados", ".1f")
ids["nota"] = big("Nota media (1 a 5)", "nota_media", ".2f")
ids["probl"] = big("% itens cancelados ou devolvidos", "pct_cancelado_devolvido", ".1f")

ids["serie"] = chart("Pedidos por dia em 2025: pico na Black Friday (28/11) e no Natal",
                     "echarts_timeseries_line", "vw_serie_diaria", {
    "x_axis": "dia", "time_grain_sqla": "P1D", "granularity_sqla": "dia",
    "time_range": "No filter",
    "metrics": [sql_metric("SUM(pedidos)", "Pedidos entregues")],
    "x_axis_title": "Dia do pedido", "x_axis_title_margin": 30,
    "y_axis_title": "Pedidos", "y_axis_title_margin": 40, "y_axis_title_position": "Left",
    "show_legend": False, "rich_tooltip": True, "markerEnabled": False,
    "zoomable": True, "y_axis_format": "SMART_NUMBER"})

ids["nota_atraso"] = bar("O atraso derruba a nota: nota media por faixa de atraso", "vw_atraso_nota",
                         "faixa_atraso", [sql_metric("MAX(nota_media)", "Nota media")],
                         xlab="Faixa de atraso", ylab="Nota media (1 a 5)", fmt=".2f")

ids["regiao"] = bar("Atraso medio (dias) por regiao e transportadora", "vw_logistica_estado",
                    "regiao", [sql_metric("SUM(itens_entregues * atraso_medio_dias) / SUM(itens_entregues)",
                                          "Atraso medio (dias)")],
                    groupby=["transportadora"], xlab="Regiao", ylab="Atraso medio (dias)", fmt=".2f")

ids["problemas"] = bar("% de itens cancelados e devolvidos por categoria", "vw_problemas_categoria",
                       "categoria", [
                           sql_metric("SUM(itens * pct_cancelado) / SUM(itens)", "% cancelado"),
                           sql_metric("SUM(itens * pct_devolvido) / SUM(itens)", "% devolvido")],
                       stack=True, xlab="Categoria", ylab="% dos itens", fmt=".2f")

ids["chuva"] = bar("Atraso medio (dias) por chuva nos 3 dias apos o pedido", "vw_atraso_chuva",
                   "faixa_chuva", [sql_metric("MAX(atraso_medio_dias)", "Atraso medio (dias)")],
                   xlab="Chuva acumulada no destino (mm, 3 dias)", ylab="Atraso medio (dias)", fmt=".2f")

ids["chuva_reg"] = bar("Chuva ou regiao? Atraso medio por faixa de chuva em cada regiao",
                       "vw_atraso_chuva_regiao", "faixa_chuva",
                       [sql_metric("SUM(itens * atraso_medio_dias) / SUM(itens)", "Atraso medio (dias)")],
                       groupby=["regiao"], xlab="Chuva acumulada no destino (mm, 3 dias)",
                       ylab="Atraso medio (dias)", fmt=".2f")

ids["feriado"] = bar("Feriado x dia comum: pedidos por dia", "vw_feriados", "tipo_dia",
                     [sql_metric("MAX(pedidos_por_dia)", "Pedidos por dia")],
                     xlab="Tipo de dia", ylab="Pedidos por dia", fmt=".1f")

ids["transp"] = bar("Bonus: % de itens atrasados por transportadora", "vw_transportadora",
                    "transportadora",
                    [sql_metric("SUM(itens * pct_atrasados) / SUM(itens)", "% atrasados")],
                    xlab="Transportadora", ylab="% itens atrasados", fmt=".1f")

# --- layout do dashboard ---
pos = {"DASHBOARD_VERSION_KEY": "v2",
       "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
       "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
       "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID",
                     "meta": {"text": "MercadoFacil 2025 - atraso, nota e sazonalidade"}}}
rows = [
    [("receita", 2), ("pedidos", 2), ("ticket", 2), ("atraso", 2), ("nota", 2), ("probl", 2)],
    [("serie", 12)],
    [("nota_atraso", 6), ("regiao", 6)],
    [("problemas", 6), ("chuva", 6)],
    [("chuva_reg", 6), ("transp", 4), ("feriado", 2)],
]
names = {}
for r_i, row in enumerate(rows):
    rid = f"ROW-{r_i}"
    pos["GRID_ID"]["children"].append(rid)
    pos[rid] = {"type": "ROW", "id": rid, "children": [], "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {"background": "BACKGROUND_TRANSPARENT"}}
    for key, width in row:
        cid = f"CHART-{key}"
        pos[rid]["children"].append(cid)
        pos[cid] = {"type": "CHART", "id": cid, "children": [],
                    "parents": ["ROOT_ID", "GRID_ID", rid],
                    "meta": {"chartId": ids[key], "width": width,
                             "height": 30 if r_i == 0 else 60}}

regiao_charts = [ids["regiao"], ids["chuva_reg"], ids["transp"]]
native = [{
    "id": "NATIVE_FILTER-regiao", "name": "Regiao", "filterType": "filter_select",
    "type": "NATIVE_FILTER",
    "targets": [{"datasetId": ds["vw_logistica_estado"], "column": {"name": "regiao"}}],
    "controlValues": {"multiSelect": True, "enableEmptyFilter": False, "defaultToFirstItem": False,
                      "inverseSelection": False, "searchAllOptions": False},
    "defaultDataMask": {"filterState": {}, "extraFormData": {}, "ownState": {}},
    "cascadeParentIds": [], "scope": {"rootPath": ["ROOT_ID"],
                                      "excluded": [i for i in ids.values() if i not in regiao_charts]},
    "chartsInScope": regiao_charts, "tabsInScope": [], "description": ""}, {
    "id": "NATIVE_FILTER-categoria", "name": "Categoria", "filterType": "filter_select",
    "type": "NATIVE_FILTER",
    "targets": [{"datasetId": ds["vw_problemas_categoria"], "column": {"name": "categoria"}}],
    "controlValues": {"multiSelect": True, "enableEmptyFilter": False, "defaultToFirstItem": False,
                      "inverseSelection": False, "searchAllOptions": False},
    "defaultDataMask": {"filterState": {}, "extraFormData": {}, "ownState": {}},
    "cascadeParentIds": [], "scope": {"rootPath": ["ROOT_ID"],
                                      "excluded": [i for i in ids.values() if i != ids["problemas"]]},
    "chartsInScope": [ids["problemas"]], "tabsInScope": [], "description": ""}]

dash = call("POST", "/api/v1/dashboard/", {
    "dashboard_title": "MercadoFacil 2025 - atraso, nota e sazonalidade",
    "slug": "mercadofacil", "published": True,
    "position_json": json.dumps(pos),
    "json_metadata": json.dumps({"native_filter_configuration": native,
                                 "color_scheme": "supersetColors", "refresh_frequency": 0,
                                 "timed_refresh_immune_slices": [], "expanded_slices": {},
                                 "label_colors": {}, "shared_label_colors": {},
                                 "cross_filters_enabled": True})})
did = dash["id"]
for cid in ids.values():
    call("PUT", f"/api/v1/chart/{cid}", {"dashboards": [did]})
print("dashboard", did, U + "/superset/dashboard/mercadofacil/")
