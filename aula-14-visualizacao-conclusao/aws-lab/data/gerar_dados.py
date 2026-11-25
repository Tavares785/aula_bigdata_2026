"""Gera data/pedidos_mercadofacil_tratado.csv (10.000 linhas).

Dado de apoio da Aula 14: a mesma MercadoFácil da Aula 12, mas JÁ TRATADO
(equivalente a uma camada silver/gold bem feita): tipos corretos, categorias
padronizadas, sem duplicados e SEM dados pessoais (nome, e-mail, CPF).

O atraso depende da chuva REAL de 2025 no destino (chuva_diaria.csv, obtida
na Open-Meteo por scripts/buscar_apis.py) e feriados (feriados.csv, BrasilAPI),
alem de regiao, transportadora e epoca do ano. Os alunos descobrem isso
cruzando as tabelas no Athena.

Os alunos NÃO precisam rodar este script: o CSV já vem pronto. Ele está aqui
para o professor regerar a base (a semente é fixa, então a saída é sempre a
mesma). Usa só a biblioteca padrão.

    python3 gerar_dados.py
"""
import csv
import os
import random
from datetime import date, timedelta

SEED = 14
N_LINHAS = 10_000
N_CLIENTES = 2_600
CHUVA_CSV = os.path.join(os.path.dirname(__file__), "chuva_diaria.csv")
FERIADOS_CSV = os.path.join(os.path.dirname(__file__), "feriados.csv")
SAIDA = os.path.join(os.path.dirname(__file__), "pedidos_mercadofacil_tratado.csv")

# (sku, categoria, produto, marca, preco_medio, custo_medio) -- catálogo da Aula 12
CATALOGO = [
    ("SKU-0001", "Eletrônicos", "Fone Bluetooth", "SonicPro", 189.9, 98.0),
    ("SKU-0002", "Eletrônicos", "Smartwatch", "FitTime", 329.9, 190.0),
    ("SKU-0003", "Eletrônicos", "Caixa de Som", "SonicPro", 249.9, 130.0),
    ("SKU-0004", "Eletrônicos", "Carregador Turbo", "VoltMax", 79.9, 32.0),
    ("SKU-0005", "Eletrônicos", "Tablet 10 pol", "Nexa", 1199.0, 760.0),
    ("SKU-0006", "Casa e Cozinha", "Air Fryer", "CozinhaMax", 429.9, 250.0),
    ("SKU-0007", "Casa e Cozinha", "Jogo de Panelas", "Chef Casa", 259.9, 140.0),
    ("SKU-0008", "Casa e Cozinha", "Liquidificador", "CozinhaMax", 169.9, 85.0),
    ("SKU-0009", "Casa e Cozinha", "Cafeteira", "Chef Casa", 219.9, 115.0),
    ("SKU-0010", "Moda", "Camiseta Básica", "UrbanWear", 49.9, 28.8),
    ("SKU-0011", "Moda", "Tênis Casual", "PassoCerto", 219.9, 115.0),
    ("SKU-0012", "Moda", "Jaqueta Jeans", "UrbanWear", 279.9, 150.0),
    ("SKU-0013", "Moda", "Mochila", "PassoCerto", 139.9, 70.0),
    ("SKU-0014", "Beleza e Saúde", "Perfume 100ml", "Aurora", 259.9, 120.0),
    ("SKU-0015", "Beleza e Saúde", "Kit Skincare", "Aurora", 164.0, 91.7),
    ("SKU-0016", "Beleza e Saúde", "Secador de Cabelo", "VoltMax", 149.9, 75.0),
    ("SKU-0017", "Livros", "Livro Técnico", "Editora Prisma", 105.8, 69.6),
    ("SKU-0018", "Livros", "Romance", "Editora Prisma", 47.6, 29.0),
    ("SKU-0019", "Livros", "Livro Infantil", "Editora Brilho", 39.9, 22.0),
    ("SKU-0020", "Esporte", "Bicicleta Ergométrica", "FitTime", 1399.0, 820.0),
    ("SKU-0021", "Esporte", "Kit Halteres", "FitTime", 199.9, 105.0),
    ("SKU-0022", "Esporte", "Bola de Futebol", "GolMax", 89.9, 45.0),
    ("SKU-0023", "Esporte", "Tapete de Yoga", "Zen", 94.9, 48.0),
    ("SKU-0024", "Brinquedos", "Bloco de Montar", "Brinca Mais", 119.9, 62.0),
    ("SKU-0025", "Brinquedos", "Boneca", "Brinca Mais", 99.9, 50.0),
    ("SKU-0026", "Brinquedos", "Carrinho RC", "Turbo Kids", 179.9, 95.0),
    ("SKU-0027", "Pet", "Ração 10kg", "PetVida", 149.9, 92.0),
    ("SKU-0028", "Pet", "Cama para Pet", "PetVida", 129.9, 62.0),
    ("SKU-0029", "Pet", "Arranhador", "PetVida", 109.9, 52.0),
]
# peso de venda por categoria (reflete a Aula 12)
PESO_CATEGORIA = {
    "Eletrônicos": 24, "Moda": 20, "Casa e Cozinha": 17, "Esporte": 10,
    "Beleza e Saúde": 8, "Livros": 6, "Brinquedos": 5, "Pet": 3.5,
}

# estado: (peso, regiao, centro_distribuicao, prazo_base, cidades)
ESTADOS = {
    "SP": (31, "Sudeste", "CD-SUDESTE", 3, ["São Paulo", "Campinas", "Santos", "Sorocaba"]),
    "RJ": (13, "Sudeste", "CD-SUDESTE", 4, ["Rio de Janeiro", "Niterói", "Petrópolis"]),
    "MG": (12, "Sudeste", "CD-SUDESTE", 4, ["Belo Horizonte", "Uberlândia", "Juiz de Fora"]),
    "RS": (7.5, "Sul", "CD-SUL", 5, ["Porto Alegre", "Caxias do Sul"]),
    "PR": (7, "Sul", "CD-SUL", 5, ["Curitiba", "Londrina"]),
    "PE": (6, "Nordeste", "CD-NORDESTE", 7, ["Recife", "Olinda"]),
    "BA": (5.5, "Nordeste", "CD-NORDESTE", 7, ["Salvador", "Feira de Santana"]),
    "CE": (4.5, "Nordeste", "CD-NORDESTE", 7, ["Fortaleza", "Sobral"]),
    "DF": (3.2, "Centro-Oeste", "CD-CENTRO-OESTE", 7, ["Brasília"]),
    "AM": (2.3, "Norte", "CD-NORTE", 11, ["Manaus"]),
    "PA": (1.6, "Norte", "CD-NORTE", 11, ["Belém"]),
}
CANAIS = [("app", 44), ("site", 34), ("marketplace_parceiro", 22)]
TRANSPORTADORAS = [("Correios", 40), ("Loggi", 25), ("Jadlog", 20), ("Entrega Própria", 15)]
PAGAMENTOS = [("cartao_credito", 60), ("pix", 25), ("boleto", 10), ("cartao_debito", 5)]
SEGMENTOS = [("recorrente", 44), ("novo", 36), ("vip", 20)]

# efeito de cada transportadora no atraso (dias extras esperados)
EFEITO_TRANSP = {"Correios": 1.0, "Loggi": -0.3, "Jadlog": 0.4, "Entrega Própria": -0.8}
EFEITO_REGIAO = {"Sudeste": 0.0, "Sul": 0.3, "Centro-Oeste": 0.6, "Nordeste": 1.0, "Norte": 1.6}


def carregar_apoio():
    """chuva[(cidade, 'AAAA-MM-DD')] = chuva_3d_mm ; feriados = set de datas."""
    chuva = {}
    with open(CHUVA_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            chuva[(r["cidade"], r["dia"])] = float(r["chuva_3d_mm"])
    with open(FERIADOS_CSV, encoding="utf-8") as f:
        feriados = {r["dia"] for r in csv.DictReader(f)}
    return chuva, feriados


def escolhe(rng, pares):
    return rng.choices([p[0] for p in pares], weights=[p[1] for p in pares])[0]


def sorteia_data(rng, feriados):
    """Data do pedido em 2025 com sazonalidade (Black Friday, Natal)."""
    dias = [date(2025, 1, 1) + timedelta(days=i) for i in range(365)]
    pesos = []
    for d in dias:
        w = 1.0
        if d.month == 11:
            w = 1.6
        if d.month == 12 and d.day <= 24:
            w = 1.9
        if d == date(2025, 11, 28):
            w = 9.0  # Black Friday
        if d.month == 5 and d.day <= 11:
            w = 1.3  # Dia das Mães
        if d.isoformat() in feriados:
            w *= 1.3
        pesos.append(w)
    return rng.choices(dias, weights=pesos)[0]


def main():
    rng = random.Random(SEED)
    chuva, feriados = carregar_apoio()

    clientes = {}
    for i in range(1, N_CLIENTES + 1):
        clientes[f"CLI{i:06d}"] = escolhe(rng, SEGMENTOS)
    ids_clientes = list(clientes)

    pesos_prod = [PESO_CATEGORIA[p[1]] for p in CATALOGO]
    nomes_estados = list(ESTADOS)
    pesos_estados = [ESTADOS[e][0] for e in nomes_estados]

    linhas = []
    n_pedido = 0
    while len(linhas) < N_LINHAS:
        n_pedido += 1
        pedido_id = f"PED{n_pedido:07d}"
        d_pedido = sorteia_data(rng, feriados)
        cliente = rng.choice(ids_clientes)
        segmento = clientes[cliente]
        uf = rng.choices(nomes_estados, weights=pesos_estados)[0]
        _, regiao, cd, prazo_base, cidades = ESTADOS[uf]
        cidade = rng.choice(cidades)
        canal = escolhe(rng, CANAIS)
        transp = escolhe(rng, TRANSPORTADORAS)
        pagamento = escolhe(rng, PAGAMENTOS)
        parcelas = 1
        if pagamento == "cartao_credito":
            parcelas = rng.choices([1, 2, 3, 6, 10, 12], weights=[45, 10, 12, 12, 10, 11])[0]

        pico = d_pedido.month in (11, 12)
        n_itens = rng.choices([1, 2, 3], weights=[70, 22, 8])[0]

        # estado do pedido (vale para todos os itens)
        prazo_est = max(2, prazo_base + rng.choice([-1, 0, 0, 1, 2]))
        mm3 = chuva[(cidade, d_pedido.isoformat())]
        extra_chuva = min(mm3, 60.0) / 20.0  # 0 a 3: chuva forte nos 3 dias da expedicao
        extra = (
            EFEITO_REGIAO[regiao]
            + EFEITO_TRANSP[transp]
            + (1.6 if pico else 0.0)
            + extra_chuva
            + (0.8 if d_pedido.isoformat() in feriados else 0.0)
        )
        p_atraso = min(0.85, 0.07 + 0.06 * extra)
        if rng.random() < p_atraso:
            atraso = max(1, round(rng.gauss(2.5 + extra * 0.9, 2.0)))
        else:
            atraso = 0
        atraso = min(atraso, 18)
        prazo_real = prazo_est + atraso

        p_cancel = 0.035 + (0.01 if canal == "marketplace_parceiro" else 0.0)
        p_devol = 0.025 + 0.012 * min(atraso, 8) + (0.02 if pico else 0.0)
        r = rng.random()
        if r < p_cancel:
            status = "cancelado"
        elif r < p_cancel + p_devol:
            status = "devolvido"
        else:
            status = "entregue"

        d_entrega = ""
        if status == "cancelado":
            prazo_real_s = atraso_s = ""
        else:
            d_entrega = (d_pedido + timedelta(days=prazo_real)).isoformat()
            prazo_real_s, atraso_s = prazo_real, atraso

        for k in range(1, n_itens + 1):
            if len(linhas) >= N_LINHAS:
                break
            sku, cat, prod, marca, preco_m, custo_m = rng.choices(CATALOGO, weights=pesos_prod)[0]
            preco = round(preco_m * rng.uniform(0.9, 1.1), 2)
            custo = round(custo_m * rng.uniform(0.95, 1.05), 2)
            qtd = rng.choices([1, 2, 3, 4], weights=[74, 17, 6, 3])[0]
            if d_pedido == date(2025, 11, 28):
                desc = rng.choice([15, 20, 30, 40, 40])
            elif pico:
                desc = rng.choice([0, 5, 10, 15, 20])
            else:
                desc = rng.choices([0, 5, 10, 15], weights=[45, 20, 20, 15])[0]
            valor = round(preco * qtd * (1 - desc / 100), 2)

            if status == "cancelado":
                nota = ""
            else:
                base = 4.5 - 0.42 * atraso + rng.gauss(0, 0.8)
                if status == "devolvido":
                    base -= 1.4
                nota = min(5, max(1, round(base)))
                if rng.random() < 0.10:  # nem todo cliente avalia
                    nota = ""

            linhas.append({
                "pedido_id": pedido_id,
                "item_id": f"{pedido_id}-{k}",
                "data_pedido": d_pedido.isoformat(),
                "cliente_id": cliente,
                "cliente_segmento": segmento,
                "estado": uf,
                "regiao": regiao,
                "cidade": cidade,
                "canal": canal,
                "categoria": cat,
                "sku": sku,
                "produto": prod,
                "marca": marca,
                "transportadora": transp,
                "centro_distribuicao": cd,
                "forma_pagamento": pagamento,
                "parcelas": parcelas,
                "quantidade": qtd,
                "custo_unitario": f"{custo:.2f}",
                "preco_unitario": f"{preco:.2f}",
                "desconto_pct": desc,
                "valor_total": f"{valor:.2f}",
                "status_pedido": status,
                "prazo_estimado_dias": prazo_est,
                "prazo_real_dias": prazo_real_s,
                "atraso_dias": atraso_s,
                "data_entrega": d_entrega,
                "nota_avaliacao": nota,
            })

    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"{len(linhas)} linhas, {n_pedido} pedidos -> {SAIDA}")


if __name__ == "__main__":
    main()
