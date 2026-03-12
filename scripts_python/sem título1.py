#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 16:51:06 2026

@author: matheus
"""

import pandas as pd
import re

# arquivos
arquivo_load = "/home/matheus/Documentos/BtM-PV-estimating/Load.dss"
arquivo_csv = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/FeederA/Pbase_FeederA.csv"
arquivo_saida = "load_saida.dss"

# lê tabela de Pbase
df = pd.read_csv(arquivo_csv)

# garante que o nome do barramento está em minúsculo
df["bus"] = df["bus"].str.lower()

# cria dicionário: bus -> Pbase
pbase_dict = dict(zip(df["bus"], df["Pbase_kW"]))

# abre load.dss
with open(arquivo_load, "r") as f:
    linhas = f.readlines()

linhas_novas = []

for linha in linhas:

    if "bus1=" in linha:

        # pega valor do bus
        match = re.search(r"bus1=([^\s]+)", linha)

        if match:
            bus_full = match.group(1)

            # extrai apenas bus1003
            bus = re.search(r"bus\d+", bus_full.lower())

            if bus:
                bus = bus.group(0)

                if bus in pbase_dict:

                    pbase = pbase_dict[bus]
                    print(pbase)
                    # substitui kw existente
                    linha = re.sub(r"kW=\S+", f"kW={pbase}", linha)
                    print (linha)

    linhas_novas.append(linha)

# salva novo arquivo
with open(arquivo_saida, "w") as f:
    f.writelines(linhas_novas)

print("Arquivo atualizado salvo como:", arquivo_saida)