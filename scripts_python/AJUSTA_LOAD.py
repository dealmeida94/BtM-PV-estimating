#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 17:38:51 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import random
import math

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

                    # calcula kvar
                    kvar = pbase * math.tan(math.acos(fp))

                    # arredonda
                    kvar = round(kvar, 3)

                    # substitui kW
                    linha = re.sub(r"kW\s*=\s*\S+", f"kW={pbase}", linha, flags=re.IGNORECASE)

                    # substitui kvar
                    linha = re.sub(r"Kvar\s*=\s*\S+", f"Kvar={kvar}", linha, flags=re.IGNORECASE)

    linhas_novas.append(linha)

# salva novo arquivo
with open(arquivo_saida, "w") as f:
    f.writelines(linhas_novas)

print("Arquivo atualizado salvo como:", arquivo_saida)

