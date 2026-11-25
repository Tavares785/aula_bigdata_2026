"""Busca dados PUBLICOS de apoio (sem chave de API) e grava CSVs em ../data/.

  - Open-Meteo Archive : chuva diaria (mm) de cada cidade de destino, 2025
  - BrasilAPI          : feriados nacionais de 2025

Saidas:
  data/chuva_diaria.csv  cidade,dia,chuva_mm,chuva_3d_mm
        (chuva_3d_mm = soma do proprio dia + os 2 dias seguintes)
  data/feriados.csv      dia,nome,tipo

Os dois CSVs ja vem prontos no repositorio. Rode este script so se quiser
buscar de novo (precisa de internet). Usa apenas a biblioteca padrao.

    python3 buscar_apis.py
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request

ANO = 2025
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# cidade -> (latitude, longitude). Mesmas cidades de destino dos pedidos.
CIDADES = {
    "São Paulo": (-23.55, -46.63), "Campinas": (-22.91, -47.06),
    "Santos": (-23.96, -46.33), "Sorocaba": (-23.50, -47.45),
    "Rio de Janeiro": (-22.91, -43.17), "Niterói": (-22.88, -43.10),
    "Petrópolis": (-22.51, -43.18), "Belo Horizonte": (-19.92, -43.94),
    "Uberlândia": (-18.92, -48.28), "Juiz de Fora": (-21.76, -43.35),
    "Porto Alegre": (-30.03, -51.23), "Caxias do Sul": (-29.17, -51.18),
    "Curitiba": (-25.43, -49.27), "Londrina": (-23.31, -51.16),
    "Recife": (-8.05, -34.88), "Olinda": (-8.01, -34.86),
    "Salvador": (-12.97, -38.51), "Feira de Santana": (-12.27, -38.97),
    "Fortaleza": (-3.73, -38.53), "Sobral": (-3.69, -40.35),
    "Brasília": (-15.79, -47.88), "Manaus": (-3.12, -60.02),
    "Belém": (-1.46, -48.50),
}


def get_json(url, tentativas=4):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "aula14-bigdata/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # rede/limite de taxa: espera e tenta de novo
            if i == tentativas - 1:
                raise
            print(f"  falhou ({e}); tentando de novo...")
            time.sleep(5 * (i + 1))


def buscar_chuva():
    linhas = []
    for cidade, (lat, lon) in CIDADES.items():
        qs = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon,
            "start_date": f"{ANO}-01-01", "end_date": f"{ANO}-12-31",
            "daily": "precipitation_sum", "timezone": "America/Sao_Paulo",
        })
        d = get_json(f"https://archive-api.open-meteo.com/v1/archive?{qs}")["daily"]
        dias, mm = d["time"], [v or 0.0 for v in d["precipitation_sum"]]
        for i, dia in enumerate(dias):
            soma3 = sum(mm[i:i + 3])
            linhas.append((cidade, dia, round(mm[i], 1), round(soma3, 1)))
        print(f"chuva: {cidade} ok")
        time.sleep(1)
    with open(os.path.join(DATA, "chuva_diaria.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cidade", "dia", "chuva_mm", "chuva_3d_mm"])
        w.writerows(linhas)
    print(f"chuva_diaria.csv: {len(linhas)} linhas")


def buscar_feriados():
    fer = get_json(f"https://brasilapi.com.br/api/feriados/v1/{ANO}")
    with open(os.path.join(DATA, "feriados.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dia", "nome", "tipo"])
        for x in fer:
            w.writerow([x["date"], x["name"], x["type"]])
    print(f"feriados.csv: {len(fer)} linhas")


if __name__ == "__main__":
    buscar_feriados()
    buscar_chuva()
