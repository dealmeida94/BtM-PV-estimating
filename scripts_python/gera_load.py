#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import random
import re


# ==========================
# ARQUIVOS
# ==========================

arquivo_load_original = "/home/matheus/Documentos/BtM-PV-estimating/Load.dss"
arquivo_csv = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv"

arquivo_saida = "/home/matheus/Documentos/BtM-PV-estimating/Load_novo.dss"

pf_min = 0.8
pf_max = 0.9


# ==========================
# LER LOAD ORIGINAL
# ==========================

loads = []

with open(arquivo_load_original) as f:

    for linha in f:

        if "Load." not in linha:
            continue

        nome = re.search(r'Load\.([^\s]+)', linha, re.IGNORECASE)
        bus = re.search(r'bus1=([^\s]+)', linha, re.IGNORECASE)
        kv = re.search(r'kv=([0-9\.]+)', linha, re.IGNORECASE)
        phases = re.search(r'phases=([0-9]+)', linha, re.IGNORECASE)
        conn = re.search(r'conn=([^\s]+)', linha, re.IGNORECASE)

        loads.append({
            "name": nome.group(1) if nome else None,
            "bus": bus.group(1) if bus else None,
            "kv": kv.group(1) if kv else None,
            "phases": phases.group(1) if phases else None,
            "conn": conn.group(1) if conn else "wye"
        })


# ==========================
# LER SMART METER
# ==========================

df = pd.read_csv(arquivo_csv)

# limpa nomes das colunas
df.columns = df.columns.str.strip()


# ==========================
# GERAR NOVO LOAD.DSS
# ==========================

linhas_dss = []

for load in loads:

    bus_completo = load["bus"]

    # remove fases (.1.2.3 etc)
    bus = bus_completo.split(".")[0]

    # converte para formato do CSV
    bus = bus.replace("bus", "Bus ")
    bus = bus.replace("BUS", "Bus ")
    bus = bus.strip()

    if bus not in df.columns:
        continue

    serie = df[bus]

    Pbase = serie.max()

    if Pbase == 0:
        continue

    pf = random.uniform(pf_min, pf_max)

    kvar = Pbase * np.tan(np.arccos(pf))

    linha = (
        f"New Load.{load['name']} "
        f"phases={load['phases']} "
        f"conn={load['conn']} "
        f"bus1={load['bus']} "
        f"kV={load['kv']} "
        f"kW={Pbase:.3f} "
        f"kvar={kvar:.3f}"
    )

    linhas_dss.append(linha)


# ==========================
# SALVAR
# ==========================

with open(arquivo_saida, "w") as f:

    for linha in linhas_dss:
        f.write(linha + "\n")


print("\n=================================")
print("Novo Load.dss criado")
print("Loads recriados:", len(linhas_dss))
print("Arquivo:", arquivo_saida)
print("=================================\n")