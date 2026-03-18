#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re

# ============================================================
# CAMINHO DO ARQUIVO
# ============================================================

caminho_load = "/home/matheus/Documentos/BtM-PV-estimating/Load.dss"

# ============================================================
# CONTADORES
# ============================================================

cont_A = 0
cont_B = 0
cont_C = 0

# ============================================================
# DADOS
# ============================================================

dados_A = []
dados_B = []
dados_C = []

# ============================================================
# LEITURA
# ============================================================

with open(caminho_load, "r") as f:
    linhas = f.readlines()

# ============================================================
# PROCESSAMENTO
# ============================================================

for linha in linhas:

    linha_strip = linha.strip()

    # pega só linhas de carga (mais robusto)
    if not linha_strip.lower().startswith("new  load"):
        continue

    # ----------------------------------
    # NÚMERO DO LOAD
    # ----------------------------------

    match_load = re.search(r"load[_\.](\d+)", linha_strip, re.IGNORECASE)

    if not match_load:
        continue

    numero_load = int(match_load.group(1))

    # ----------------------------------
    # FASES
    # ----------------------------------

    match_phases = re.search(r"phases\s*=\s*(\d+)", linha_strip, re.IGNORECASE)

    if match_phases:
        fases = int(match_phases.group(1))
    else:
        fases = None  # importante manter pra debug

    # ----------------------------------
    # REGISTRO
    # ----------------------------------

    registro = {
        "Load": numero_load,
        "Fases": fases
    }

    # ----------------------------------
    # CLASSIFICAÇÃO
    # ----------------------------------

    if 1000 < numero_load < 2000:
        cont_A += 1
        dados_A.append(registro)

    elif 2000 < numero_load < 3000:
        cont_B += 1
        dados_B.append(registro)

    elif numero_load > 3000:
        cont_C += 1
        dados_C.append(registro)

# ============================================================
# DATAFRAMES
# ============================================================

df_A = pd.DataFrame(dados_A)
df_B = pd.DataFrame(dados_B)
df_C = pd.DataFrame(dados_C)

# ============================================================
# SALVAR
# ============================================================

base_path = "/home/matheus/Documentos/BtM-PV-estimating/"

df_A.to_csv(base_path + "FeederA_loads.csv", index=False)
df_B.to_csv(base_path + "FeederB_loads.csv", index=False)
df_C.to_csv(base_path + "FeederC_loads.csv", index=False)

# ============================================================
# RESULTADOS
# ============================================================

print("\n====================================")
print("RESUMO POR ALIMENTADOR")
print("====================================")

print(f"Feeder A: {cont_A} cargas")
print(f"Feeder B: {cont_B} cargas")
print(f"Feeder C: {cont_C} cargas")

# ------------------------------------------------------------
# DISTRIBUIÇÃO DE FASES (AGORA NUMÉRICO)
# ------------------------------------------------------------

def resumo_fases(df, nome):
    if df.empty:
        print(f"\n{nome}: sem dados")
        return

    print(f"\n{nome} - distribuição de fases:")
    print(df["Fases"].value_counts().sort_index())

resumo_fases(df_A, "Feeder A")
resumo_fases(df_B, "Feeder B")
resumo_fases(df_C, "Feeder C")