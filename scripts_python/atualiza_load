#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 16:18:01 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import random
import re


# ==========================
# ARQUIVOS
# ==========================

arquivo_load_original = "/home/matheus/Documentos/BtM-PV-estimating/elementos/Load.dss"

arquivo_pbase = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/FeederA/Pbase_FeederA.csv"

arquivo_saida = "/home/matheus/Documentos/BtM-PV-estimating/Load_atualizado.dss"


# intervalo de fator de potência
pf_min = 0.85
pf_max = 0.99


# ==========================
# LER PBASE
# ==========================

df_pbase = pd.read_csv(arquivo_pbase)

mapa_pbase = dict(zip(df_pbase["bus"], df_pbase["Pbase_kW"]))


# ==========================
# PROCESSAR LOAD.DSS
# ==========================

linhas_saida = []

with open(arquivo_load_original) as f:

    for linha in f:

        if "Load." not in linha:
            continue

        nome = re.search(r'Load\.([^\s]+)', linha, re.IGNORECASE)
        bus = re.search(r'bus1=([^\s]+)', linha, re.IGNORECASE)
        kv = re.search(r'kv=([0-9\.]+)', linha, re.IGNORECASE)
        phases = re.search(r'phases=([0-9]+)', linha, re.IGNORECASE)
        conn = re.search(r'conn=([^\s]+)', linha, re.IGNORECASE)

        if not bus:
            continue

        bus_completo = bus.group(1)

        # remove fases
        bus_limpo = bus_completo.split(".")[0]

        # ajusta formato para CSV
        bus_csv = bus_limpo.replace("bus", "Bus ")
        bus_csv = bus_csv.replace("BUS", "Bus ")

        if bus_csv not in mapa_pbase:
            continue

        Pbase = mapa_pbase[bus_csv]

        pf = random.uniform(pf_min, pf_max)

        kvar = Pbase * np.tan(np.arccos(pf))

        linha_nova = (
            f"New Load.{nome.group(1)} "
            f"phases={phases.group(1)} "
            f"conn={conn.group(1)} "
            f"bus1={bus_completo} "
            f"kV={kv.group(1)} "
            f"kW={Pbase:.3f} "
            f"kvar={kvar:.3f}"
        )

        linhas_saida.append(linha_nova)


# ==========================
# SALVAR
# ==========================

with open(arquivo_saida, "w") as f:

    for linha in linhas_saida:
        f.write(linha + "\n")


print("\n=================================")
print("Load atualizado criado")
print("Loads atualizados:", len(linhas_saida))
print("Arquivo:", arquivo_saida)
print("=================================\n")