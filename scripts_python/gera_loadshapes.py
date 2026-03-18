#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os

# ============================================================
# CAMINHOS
# ============================================================

base_path = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/"
saida_path = base_path + "loadshapes_por_bus/"

os.makedirs(saida_path, exist_ok=True)

feeders = ["FeederA", "FeederB", "FeederC"]

# ============================================================
# RELATÓRIOS
# ============================================================

relatorio_base = []
relatorio_validacao = []

# ============================================================
# PROCESSAMENTO
# ============================================================

for feeder in feeders:

    print(f"\n==============================")
    print(f"Processando {feeder}")
    print(f"==============================")

    df_P = pd.read_csv(base_path + f"{feeder}_P.csv")
    df_Q = pd.read_csv(base_path + f"{feeder}_Q.csv")

    # ----------------------------------
    # COLUNAS = BUSES
    # ----------------------------------

    colunas = [c for c in df_P.columns if c != "Time"]

    n_original = len(df_P)

    print(f"Total de buses: {len(colunas)}")
    print(f"Pontos na série: {n_original}")

    # ----------------------------------
    # LOOP POR BUS
    # ----------------------------------

    for bus in colunas:

        # ----------------------------------
        # SÉRIES
        # ----------------------------------

        P = pd.to_numeric(df_P[bus], errors="coerce")
        Q = pd.to_numeric(df_Q[bus], errors="coerce")

        # ----------------------------------
        # VERIFICAÇÕES
        # ----------------------------------

        nulos_P = P.isna().sum()
        nulos_Q = Q.isna().sum()

        if nulos_P > 0 or nulos_Q > 0:
            print(f"⚠️ {feeder} - {bus}: NaNs → P={nulos_P}, Q={nulos_Q}")

        # ----------------------------------
        # POTÊNCIA BASE
        # ----------------------------------

        P_base = P.max()
        Q_base = Q.max()

        # evita problemas
        if P_base == 0 or np.isnan(P_base):
            print(f"❌ {feeder} - {bus}: P_base inválido")
            continue

        if Q_base == 0 or np.isnan(Q_base):
            print(f"❌ {feeder} - {bus}: Q_base inválido")
            continue

        # ----------------------------------
        # NORMALIZAÇÃO (PU)
        # ----------------------------------

        P_pu = P / P_base
        Q_pu = Q / Q_base

        # ----------------------------------
        # SALVAR LOADSHAPE (FORMATO TXT)
        # ----------------------------------

        nome_bus = bus.replace(" ", "_")

        caminho_P = saida_path + f"{feeder}_{nome_bus}_P.txt"
        caminho_Q = saida_path + f"{feeder}_{nome_bus}_Q.txt"

        np.savetxt(caminho_P, P_pu, fmt="%.6f")
        np.savetxt(caminho_Q, Q_pu, fmt="%.6f")

        # ----------------------------------
        # VALIDAÇÃO TAMANHO
        # ----------------------------------

        n_ls = len(P_pu)
        tamanho_ok = "OK" if n_ls == n_original else "ERRO"

        # ----------------------------------
        # RELATÓRIOS
        # ----------------------------------

        relatorio_base.append({
            "Feeder": feeder,
            "Bus": bus,
            "P_base (kW)": P_base,
            "Q_base (kvar)": Q_base
        })

        relatorio_validacao.append({
            "Feeder": feeder,
            "Bus": bus,
            "NaN_P": nulos_P,
            "NaN_Q": nulos_Q,
            "Pontos": n_ls,
            "Esperado": n_original,
            "Tamanho OK": tamanho_ok
        })

# ============================================================
# SALVAR RELATÓRIOS
# ============================================================

df_base = pd.DataFrame(relatorio_base)
df_validacao = pd.DataFrame(relatorio_validacao)

df_base.to_csv(saida_path + "potencias_base_por_bus.csv", index=False)
df_validacao.to_csv(saida_path + "validacao_por_bus.csv", index=False)

# ============================================================
# FINAL
# ============================================================

print("\n====================================")
print("PROCESSO FINALIZADO")
print("====================================")

print("\nResumo potências base:")
print(df_base.head())

print("\nResumo validação:")
print(df_validacao.head())