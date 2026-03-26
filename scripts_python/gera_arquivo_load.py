#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re

# ============================================================
# CAMINHOS
# ============================================================

base_path = "/home/matheus/Documentos/BtM-PV-estimating/"

arquivo_A = base_path + "FeederA_loads.csv"
arquivo_B = base_path + "FeederB_loads.csv"
arquivo_C = base_path + "FeederC_loads.csv"

arquivo_potencias = base_path + "dados_processados/loadshapes_por_bus/potencias_base_por_bus.csv"

saida_dss = base_path + "Load_reconstruido.dss"

# ============================================================
# LEITURA
# ============================================================

df_A = pd.read_csv(arquivo_A)
df_B = pd.read_csv(arquivo_B)
df_C = pd.read_csv(arquivo_C)

df_pot = pd.read_csv(arquivo_potencias)

# ============================================================
# TRATAMENTO DO CSV DE POTÊNCIA
# ============================================================

# Extrai número do bus (ex: "Bus 1003" → 1003)
df_pot["bus_num"] = df_pot["Bus"].apply(lambda x: int(re.search(r"\d+", str(x)).group()))

# Renomeia colunas para facilitar
df_pot.rename(columns={
    "P_base (kW)": "kw",
    "Q_base (kvar)": "kvar"
}, inplace=True)

# ============================================================
# FUNÇÃO DE BUSCA
# ============================================================

def busca_potencia(numero_load):

    linha = df_pot[df_pot["bus_num"] == numero_load]

    if linha.empty:
        return 0.0, 0.0

    kw = float(linha.iloc[0]["kw"])
    kvar = float(linha.iloc[0]["kvar"])

    return kw, kvar

# ============================================================
# GERADOR DE LOAD
# ============================================================

def gerar_linha_load(row):

    numero = int(row["Load"])
    fases = int(row["Fases"]) if not pd.isna(row["Fases"]) else 3
    conn = row["Conn"] if pd.notna(row["Conn"]) else "wye"

    # potência
    kw, kvar = busca_potencia(numero)

    # fases no bus
    if fases == 1:
        fases_bus = "1"
    elif fases == 2:
        fases_bus = "1.2"
    else:
        fases_bus = "1.2.3"

    # conexão define neutro
    if conn == "delta":
        bus = f"T_bus{numero}_L.{fases_bus}"
    else:
        bus = f"T_bus{numero}_L.{fases_bus}.0"

    # kV padrão
    kv = 0.208 if fases == 3 else 0.120

    return (
        f"New  Load.Load_{numero}  phases={fases}  conn={conn}  "
        f"bus1={bus}  kV={kv}  kW={kw}  Kvar={kvar}"
    )

# ============================================================
# ESCRITA DSS
# ============================================================

with open(saida_dss, "w") as f:

    f.write("// This file is to define loads with a variety of phase configurations.\n\n")

    # FEEDER A
    f.write("//***************************************************************************************//\n")
    f.write("//                                             Feeder A\n")
    f.write("//***************************************************************************************//\n")
    f.write("//----------------------------------------------------------------------------------------------------------------------//\n")

    for _, row in df_A.iterrows():
        f.write(gerar_linha_load(row) + "\n")

    # FEEDER B
    f.write("\n//***************************************************************************************//\n")
    f.write("//                                             Feeder B\n")
    f.write("//***************************************************************************************//\n")
    f.write("//----------------------------------------------------------------------------------------------------------------------//\n")

    for _, row in df_B.iterrows():
        f.write(gerar_linha_load(row) + "\n")

    # FEEDER C
    f.write("\n//***************************************************************************************//\n")
    f.write("//                                             Feeder C\n")
    f.write("//***************************************************************************************//\n")
    f.write("//----------------------------------------------------------------------------------------------------------------------//\n")

    for _, row in df_C.iterrows():
        f.write(gerar_linha_load(row) + "\n")

print("\n====================================")
print("DSS gerado com potências corretas!")
print(f"Local: {saida_dss}")
print("====================================")