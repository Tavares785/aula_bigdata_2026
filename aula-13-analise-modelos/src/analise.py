"""
Aula 13 - Analise e Construcao de Modelos em Larga Escala

Projeto: MercadoFacil (e-commerce) -- entender e reduzir atrasos nas
entregas, avaliacoes baixas e cancelamentos/devolucoes.

Esta etapa faz duas coisas sobre os pedidos ja pre-processados (Aula 12):

1. Analise descritiva: taxa de atraso por regiao/estado/transportadora/
   mes, relacao entre atraso e nota de avaliacao, e taxa de cancelamento
   e devolucao por categoria e canal.
2. Modelo preditivo: regressao logistica (implementada do zero, so com a
   biblioteca padrao) que estima a probabilidade de um item ser entregue
   com atraso. Em producao no Glue/EMR o equivalente seria
   pyspark.ml.classification.LogisticRegression; aqui a versao em Python
   puro mantem o CI leve (requirements.txt so tem pytest) e permite
   rodar a analise localmente.

Como rodar:
    python src/analise.py [caminho_do_csv]

Se nenhum caminho for passado, usa o CSV da Aula 12.
"""
import csv
import math
import os
import sys
import unicodedata
import zlib
from collections import Counter, defaultdict
from datetime import datetime

CSV_PADRAO = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "aula-12-ingestao-preprocessamento",
    "data",
    "pedidos_mercadofacil.csv",
)

NULOS = {"", "-", "n/a", "na", "null", "none", "nan"}

REGIOES = {
    "Norte": {"AC", "AP", "AM", "PA", "RO", "RR", "TO"},
    "Nordeste": {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"},
    "Centro-Oeste": {"DF", "GO", "MT", "MS"},
    "Sudeste": {"ES", "MG", "RJ", "SP"},
    "Sul": {"PR", "RS", "SC"},
}
UF_PARA_REGIAO = {uf: regiao for regiao, ufs in REGIOES.items() for uf in ufs}


# ---------------------------------------------------------------------------
# Normalizacao minima (idempotente: aplicar em dado ja limpo nao muda nada)
# ---------------------------------------------------------------------------
def _texto(valor):
    if valor is None:
        return None
    s = str(valor).strip()
    return None if s.lower() in NULOS else s


def _numero(valor):
    s = _texto(valor)
    if s is None:
        return None
    s = s.replace("R$", "").replace("%", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _inteiro(valor):
    n = _numero(valor)
    return None if n is None else int(round(n))


def _status(valor):
    s = (_texto(valor) or "").lower()
    if "entreg" in s or "deliver" in s:
        return "entregue"
    if "cancel" in s:
        return "cancelado"
    if "devolv" in s or "return" in s:
        return "devolvido"
    return None


def _mes(valor):
    s = _texto(valor)
    if s is None:
        return None
    try:
        if "/" in s:
            return datetime.strptime(s[:10], "%d/%m/%Y").month
        return datetime.strptime(s[:10], "%Y-%m-%d").month
    except ValueError:
        return None


def _chave(texto):
    """Chave de comparacao: sem acentos, minuscula, sem espacos nas pontas."""
    sem_acento = unicodedata.normalize("NFKD", texto.strip())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.casefold()


def _rotulos_canonicos(linhas, coluna):
    """Mapeia cada variante (sem acento, minuscula) para a grafia mais
    frequente, ex: 'ELETRONICOS'/'eletronicos'/'Eletronicos' -> 'Eletrônicos'."""
    por_chave = defaultdict(Counter)
    for linha in linhas:
        s = _texto(linha.get(coluna))
        if s is not None:
            por_chave[_chave(s)][s.strip()] += 1
    return {chave: contagem.most_common(1)[0][0] for chave, contagem in por_chave.items()}


def _carrega_linhas(preprocessed_data):
    if isinstance(preprocessed_data, (str, os.PathLike)):
        with open(preprocessed_data, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    return list(preprocessed_data)


def _prepara(preprocessed_data):
    """Converte as linhas em registros tipados, removendo itens duplicados.
    Retorna (registros, resumo_da_preparacao)."""
    linhas = _carrega_linhas(preprocessed_data)
    cat_map = _rotulos_canonicos(linhas, "categoria")
    transp_map = _rotulos_canonicos(linhas, "transportadora")

    registros, vistos = [], set()
    duplicados = 0
    for linha in linhas:
        item_id = _texto(linha.get("item_id")) or _texto(linha.get("pedido_id"))
        if item_id in vistos:
            duplicados += 1
            continue
        vistos.add(item_id)

        estado = (_texto(linha.get("estado")) or "").upper()
        estado = estado if estado in UF_PARA_REGIAO else None

        prazo_est = _inteiro(linha.get("prazo_estimado_dias"))
        prazo_real = _inteiro(linha.get("prazo_real_dias"))
        if prazo_est is not None and prazo_real is not None:
            atraso = max(0, prazo_real - prazo_est)
        else:
            atraso = _inteiro(linha.get("atraso_dias"))
            atraso = None if atraso is None else max(0, atraso)

        nota = _inteiro(linha.get("nota_avaliacao"))
        nota = nota if nota is not None and 1 <= nota <= 5 else None

        qtd = _inteiro(linha.get("quantidade"))
        qtd = qtd if qtd is not None and qtd > 0 else None

        categoria = _texto(linha.get("categoria"))
        transp = _texto(linha.get("transportadora"))
        canal = _texto(linha.get("canal"))
        cd = _texto(linha.get("centro_distribuicao"))

        registros.append(
            {
                "item_id": item_id,
                "pedido_id": _texto(linha.get("pedido_id")) or item_id,
                "status": _status(linha.get("status_pedido")),
                "canal": canal.lower() if canal else None,
                "categoria": cat_map.get(_chave(categoria)) if categoria else None,
                "estado": estado,
                "regiao": UF_PARA_REGIAO.get(estado),
                "transportadora": transp_map.get(_chave(transp)) if transp else None,
                "cd": cd.upper() if cd else None,
                "mes": _mes(linha.get("data_pedido")),
                "prazo_est": prazo_est,
                "atraso": atraso,
                "nota": nota,
                "qtd": qtd,
            }
        )
    return registros, {"linhas_lidas": len(linhas), "duplicados_removidos": duplicados}


# ---------------------------------------------------------------------------
# Estatistica basica
# ---------------------------------------------------------------------------
def _media(valores):
    valores = list(valores)
    return sum(valores) / len(valores) if valores else None


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _taxa_por_grupo(registros, chave, predicado_alvo, min_n=30):
    """Para cada valor de `chave`, retorna (n, taxa) onde taxa e a fracao
    de registros que satisfazem `predicado_alvo`. Ignora grupos pequenos."""
    grupos = defaultdict(list)
    for r in registros:
        if r[chave] is not None:
            grupos[r[chave]].append(predicado_alvo(r))
    saida = {g: (len(v), sum(v) / len(v)) for g, v in grupos.items() if len(v) >= min_n}
    return dict(sorted(saida.items(), key=lambda kv: kv[1][1], reverse=True))


# ---------------------------------------------------------------------------
# Regressao logistica (descida do gradiente, representacao esparsa)
# ---------------------------------------------------------------------------
def _sigmoide(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def _monta_features(registros):
    """Features: one-hot de regiao, transportadora, categoria, mes de
    pico (nov/dez) + prazo estimado e quantidade padronizados."""
    nomes = []
    for chave in ("regiao", "transportadora", "categoria"):
        for valor in sorted({r[chave] for r in registros if r[chave] is not None}):
            nomes.append((chave, valor))
    nomes += [("mes", "nov"), ("mes", "dez"), ("num", "prazo_estimado"), ("num", "quantidade")]
    indice = {n: i for i, n in enumerate(nomes)}

    prazos = [r["prazo_est"] for r in registros if r["prazo_est"] is not None]
    qtds = [r["qtd"] for r in registros if r["qtd"] is not None]
    mp, mq = _media(prazos), _media(qtds)
    dp = math.sqrt(_media((p - mp) ** 2 for p in prazos)) or 1.0
    dq = math.sqrt(_media((q - mq) ** 2 for q in qtds)) or 1.0

    def vetor(r):
        ativos = []
        for chave in ("regiao", "transportadora", "categoria"):
            if r[chave] is not None:
                ativos.append((indice[(chave, r[chave])], 1.0))
        if r["mes"] == 11:
            ativos.append((indice[("mes", "nov")], 1.0))
        if r["mes"] == 12:
            ativos.append((indice[("mes", "dez")], 1.0))
        ativos.append((indice[("num", "prazo_estimado")], ((r["prazo_est"] or mp) - mp) / dp))
        ativos.append((indice[("num", "quantidade")], ((r["qtd"] or mq) - mq) / dq))
        return ativos

    return nomes, vetor


def _treina_logistica(X, y, dim, epocas=200, lr=0.5, l2=1e-3):
    w = [0.0] * dim
    b = 0.0
    n = len(X)
    for _ in range(epocas):
        grad = [0.0] * dim
        gb = 0.0
        for ativos, alvo in zip(X, y):
            z = b + sum(w[i] * v for i, v in ativos)
            erro = _sigmoide(z) - alvo
            gb += erro
            for i, v in ativos:
                grad[i] += erro * v
        b -= lr * gb / n
        for i in range(dim):
            w[i] -= lr * (grad[i] / n + l2 * w[i])
    return w, b


def _auc(probs, y):
    pares = sorted(zip(probs, y))
    pos = sum(y)
    neg = len(y) - pos
    if pos == 0 or neg == 0:
        return None
    soma_ranks_pos, i = 0.0, 0
    while i < len(pares):
        j = i
        while j < len(pares) and pares[j][0] == pares[i][0]:
            j += 1
        rank_medio = (i + 1 + j) / 2
        soma_ranks_pos += rank_medio * sum(p[1] for p in pares[i:j])
        i = j
    return (soma_ranks_pos - pos * (pos + 1) / 2) / (pos * neg)


def _modelo_atraso(entregues):
    """Treina e avalia o modelo de probabilidade de atraso. O split
    treino/teste e feito por pedido (hash do pedido_id), para que itens
    do mesmo pedido nunca fiquem nos dois lados (evita vazamento)."""
    base = [r for r in entregues if r["atraso"] is not None and r["prazo_est"] is not None]
    nomes, vetor = _monta_features(base)
    treino = [r for r in base if zlib.crc32(r["pedido_id"].encode()) % 5 != 0]
    teste = [r for r in base if zlib.crc32(r["pedido_id"].encode()) % 5 == 0]

    X_tr = [vetor(r) for r in treino]
    y_tr = [1 if r["atraso"] > 0 else 0 for r in treino]
    w, b = _treina_logistica(X_tr, y_tr, len(nomes))

    X_te = [vetor(r) for r in teste]
    y_te = [1 if r["atraso"] > 0 else 0 for r in teste]
    probs = [_sigmoide(b + sum(w[i] * v for i, v in ativos)) for ativos in X_te]
    acertos = sum((p >= 0.5) == bool(t) for p, t in zip(probs, y_te))
    majoritaria = max(sum(y_te), len(y_te) - sum(y_te)) / len(y_te)

    coefs = sorted(zip(nomes, w), key=lambda kv: kv[1], reverse=True)
    return {
        "n_treino": len(treino),
        "n_teste": len(teste),
        "acuracia_teste": acertos / len(y_te),
        "acuracia_baseline": majoritaria,
        "auc_teste": _auc(probs, y_te),
        "coeficientes": [(f"{c}={v}", round(peso, 3)) for (c, v), peso in coefs],
    }


# ---------------------------------------------------------------------------
# Funcoes exigidas pela aula
# ---------------------------------------------------------------------------
def build_model_or_analysis(preprocessed_data):
    """
    Executa a analise principal do projeto MercadoFacil.

    `preprocessed_data` pode ser o caminho de um CSV ou uma lista de
    dicts (uma linha por item de pedido, mesmas colunas da Aula 12). A
    funcao aplica uma normalizacao minima e idempotente (caixa/espacos,
    nulos, datas, valores invalidos, itens duplicados), entao funciona
    tanto no CSV bruto quanto na camada silver/gold exportada.

    Retorna um dicionario com os KPIs, as tabelas de taxas por grupo, a
    relacao atraso x nota e o modelo de risco de atraso treinado.
    """
    registros, prep = _prepara(preprocessed_data)

    entregues = [r for r in registros if r["status"] == "entregue"]
    com_atraso = [r for r in entregues if r["atraso"] is not None]
    atrasou = lambda r: r["atraso"] > 0  # noqa: E731

    # segmentos de risco: regiao (Norte/Nordeste vs demais) x epoca (nov/dez vs resto)
    for r in com_atraso:
        if r["regiao"] is not None and r["mes"] is not None:
            regiao_txt = "Norte/Nordeste" if r["regiao"] in ("Norte", "Nordeste") else "demais regioes"
            epoca_txt = "nov/dez" if r["mes"] in (11, 12) else "jan-out"
            r["segmento"] = f"{regiao_txt} em {epoca_txt}"
        else:
            r["segmento"] = None

    # relacao atraso x nota (apenas entregues com nota valida e atraso conhecido)
    par = [(r["atraso"], r["nota"]) for r in com_atraso if r["nota"] is not None]
    nota_atrasado = [n for a, n in par if a > 0]
    nota_no_prazo = [n for a, n in par if a == 0]
    faixas = {"no prazo": (0, 0), "1-3 dias": (1, 3), "4-7 dias": (4, 7), "8+ dias": (8, 10**6)}
    nota_por_faixa = {}
    for nome, (lo, hi) in faixas.items():
        notas = [n for a, n in par if lo <= a <= hi]
        nota_por_faixa[nome] = (len(notas), _media(notas))

    # cancelamento / devolucao
    com_status = [r for r in registros if r["status"] is not None]
    ruim = lambda r: r["status"] in ("cancelado", "devolvido")  # noqa: E731

    return {
        "preparacao": prep,
        "kpis": {
            "itens_unicos": len(registros),
            "itens_entregues": len(entregues),
            "taxa_atraso": _media(1 if atrasou(r) else 0 for r in com_atraso),
            "atraso_medio_dias_quando_atrasa": _media(r["atraso"] for r in com_atraso if atrasou(r)),
            "taxa_cancelado": _media(1 if r["status"] == "cancelado" else 0 for r in com_status),
            "taxa_devolvido": _media(1 if r["status"] == "devolvido" else 0 for r in com_status),
        },
        "atraso_por_regiao": _taxa_por_grupo(com_atraso, "regiao", atrasou),
        "atraso_por_estado": _taxa_por_grupo(com_atraso, "estado", atrasou),
        "atraso_por_transportadora": _taxa_por_grupo(com_atraso, "transportadora", atrasou),
        "atraso_por_cd": _taxa_por_grupo(com_atraso, "cd", atrasou),
        "atraso_por_mes": dict(sorted(_taxa_por_grupo(com_atraso, "mes", atrasou).items())),
        "atraso_por_segmento": _taxa_por_grupo(com_atraso, "segmento", atrasou),
        "nota": {
            "n_avaliacoes": len(par),
            "media_atrasado": _media(nota_atrasado),
            "media_no_prazo": _media(nota_no_prazo),
            "correlacao_atraso_nota": _pearson([a for a, _ in par], [n for _, n in par]),
            "por_faixa_de_atraso": nota_por_faixa,
        },
        "ruim_por_categoria": _taxa_por_grupo(com_status, "categoria", ruim),
        "ruim_por_canal": _taxa_por_grupo(com_status, "canal", ruim),
        "modelo_atraso": _modelo_atraso(entregues),
    }


def _pct(x):
    return "n/d" if x is None else f"{x * 100:.1f}%"


def _num(x, casas=2):
    return "n/d" if x is None else f"{x:.{casas}f}"


def _tabela(titulo, dados, n_max=None):
    linhas = [titulo]
    itens = list(dados.items())[:n_max]
    for grupo, (n, taxa) in itens:
        linhas.append(f"  - {grupo}: {_pct(taxa)} (n={n})")
    return "\n".join(linhas)


def summarize_results(analysis_output):
    """
    Recebe o dicionario de `build_model_or_analysis` e devolve um
    relatorio em texto com os principais resultados (KPIs, onde o atraso
    se concentra, impacto na nota, cancelamento/devolucao e metricas do
    modelo).
    """
    k = analysis_output["kpis"]
    prep = analysis_output["preparacao"]
    nota = analysis_output["nota"]
    m = analysis_output["modelo_atraso"]

    partes = [
        "RESUMO - MercadoFacil (Aula 13)",
        f"Base: {prep['linhas_lidas']} linhas lidas, {prep['duplicados_removidos']} itens duplicados "
        f"removidos, {k['itens_unicos']} itens unicos ({k['itens_entregues']} entregues).",
        "",
        "KPIs",
        f"  - Taxa de atraso (entregues): {_pct(k['taxa_atraso'])}; "
        f"quando atrasa, em media {_num(k['atraso_medio_dias_quando_atrasa'], 1)} dias",
        f"  - Cancelados: {_pct(k['taxa_cancelado'])} | Devolvidos: {_pct(k['taxa_devolvido'])}",
        "",
        _tabela("Taxa de atraso por regiao", analysis_output["atraso_por_regiao"]),
        _tabela("Taxa de atraso por transportadora", analysis_output["atraso_por_transportadora"]),
        _tabela("Taxa de atraso por mes (numero do mes)", analysis_output["atraso_por_mes"]),
        _tabela("5 estados com maior taxa de atraso", analysis_output["atraso_por_estado"], 5),
        _tabela("Taxa de atraso por segmento (regiao x epoca)", analysis_output["atraso_por_segmento"]),
        "",
        "Atraso x nota de avaliacao",
        f"  - Nota media: {_num(nota['media_no_prazo'])} no prazo vs "
        f"{_num(nota['media_atrasado'])} atrasado (n={nota['n_avaliacoes']} avaliacoes validas)",
        f"  - Correlacao de Pearson (dias de atraso x nota): {_num(nota['correlacao_atraso_nota'], 3)}",
    ]
    for faixa, (n, media) in nota["por_faixa_de_atraso"].items():
        partes.append(f"  - {faixa}: nota media {_num(media)} (n={n})")

    partes += [
        "",
        _tabela("Cancelamento+devolucao por categoria", analysis_output["ruim_por_categoria"]),
        _tabela("Cancelamento+devolucao por canal", analysis_output["ruim_por_canal"]),
        "",
        "Modelo de risco de atraso (regressao logistica, split por pedido)",
        f"  - Treino: {m['n_treino']} itens | Teste: {m['n_teste']} itens",
        f"  - Acuracia no teste: {_pct(m['acuracia_teste'])} "
        f"(baseline = classe majoritaria: {_pct(m['acuracia_baseline'])})",
        f"  - AUC no teste: {_num(m['auc_teste'], 3)}",
        "  - Fatores que mais aumentam o risco: "
        + ", ".join(f"{nome} ({peso:+})" for nome, peso in m["coeficientes"][:4]),
        "  - Fatores que mais reduzem o risco: "
        + ", ".join(f"{nome} ({peso:+})" for nome, peso in m["coeficientes"][-3:]),
    ]
    return "\n".join(partes)


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else CSV_PADRAO
    print(summarize_results(build_model_or_analysis(caminho)))
