#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import random
import math
import matplotlib.pyplot as plt

# arquivos
arquivo_load = "/home/matheus/Documentos/BtM-PV-estimating/Load.dss"
arquivo_csv = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/FeederA/Pbase_FeederA.csv"
arquivo_saida = "load_saida.dss"
arquivo_fp = "fatores_potencia.csv"

# lê tabela de Pbase
df = pd.read_csv(arquivo_csv)

df["bus"] = df["bus"].str.lower()

# cria dicionário
pbase_dict = dict(zip(df["bus"], df["Pbase_kW"]))

# lista para armazenar fatores de potência
fp_lista = []

# contador de tempo
t = 0

# abre load.dss
with open(arquivo_load, "r") as f:
    linhas = f.readlines()

linhas_novas = []

for linha in linhas:

    if "bus1=" in linha:

        match = re.search(r"bus1=([^\s]+)", linha)

        if match:
            bus_full = match.group(1)

            bus = re.search(r"bus\d+", bus_full.lower())

            if bus:
                bus = bus.group(0)

                if bus in pbase_dict:

                    pbase = pbase_dict[bus]

                    # gera fp aleatório
                    fp = random.uniform(0.85, 0.95)

                    # salva fp com tempo
                    fp_lista.append({
                        "tempo": t,
                        "bus": bus,
                        "fp": fp
                    })

                    t += 1

                    # calcula kvar
                    kvar = pbase * math.tan(math.acos(fp))
                    kvar = round(kvar, 3)

                    # substitui kW
                    linha = re.sub(
                        r"kW\s*=\s*\S+",
                        f"kW={pbase}",
                        linha,
                        flags=re.IGNORECASE
                    )

                    # substitui kvar
                    linha = re.sub(
                        r"kvar\s*=\s*\S+",
                        f"kvar={kvar}",
                        linha,
                        flags=re.IGNORECASE
                    )

    linhas_novas.append(linha)

# salva novo load
with open(arquivo_saida, "w") as f:
    f.writelines(linhas_novas)

print("Arquivo atualizado salvo como:", arquivo_saida)

# salva fatores de potência
df_fp = pd.DataFrame(fp_lista)
df_fp.to_csv(arquivo_fp, index=False)

print("Fatores de potência salvos em:", arquivo_fp)

# gráfico FP x tempo
plt.figure(figsize=(10,5))
plt.plot(df_fp["tempo"], df_fp["fp"])
plt.title("Fator de Potência ao longo do tempo")
plt.xlabel("Tempo")
plt.ylabel("Fator de Potência")
plt.grid(True)
plt.show()