#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

# ============================================================
# CAMINHOS
# ============================================================

base_path = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/"
saida_path = base_path + "loadshapes/"

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

    # ----------------------------------
    # LEITURA
    # ----------------------------------

    df_P = pd.read_csv(base_path + f"{feeder}_P.csv")
    df_Q = pd.read_csv(base_path + f"{feeder}_Q.csv")

    # ----------------------------------
    # GARANTIR QUE TODAS COLUNAS SÃO NUMÉRICAS
    # ----------------------------------

    colunas = [c for c in df_P.columns if c != "Time"]

    P = df_P[colunas].apply(pd.to_numeric, errors="coerce")
    Q = df_Q[colunas].apply(pd.to_numeric, errors="coerce")

    # ----------------------------------
    # VERIFICAÇÕES DE COLUNAS
    # ----------------------------------

    colunas_P = set(P.columns)
    colunas_Q = set(Q.columns)

    colunas_faltando = colunas_P.symmetric_difference(colunas_Q)

    if colunas_faltando:
        print(f"⚠️ Diferença entre colunas P e Q: {colunas_faltando}")

    # ----------------------------------
    # VERIFICAÇÃO DE NaN
    # ----------------------------------

    nulos_P = P.isna().sum().sum()
    nulos_Q = Q.isna().sum().sum()

    # ----------------------------------
    # POTÊNCIA TOTAL (SOMA DE TODOS OS BUSES)
    # ----------------------------------

    P_total = P.sum(axis=1)
    Q_total = Q.sum(axis=1)

    # ----------------------------------
    # POTÊNCIA BASE
    # ----------------------------------

    P_base = P_total.max()
    Q_base = Q_total.max()

    # ----------------------------------
    # NORMALIZAÇÃO (PU)
    # ----------------------------------

    P_pu = P_total / P_base
    Q_pu = Q_total / Q_base

    # ----------------------------------
    # SALVAR LOADSHAPES
    # ----------------------------------

    df_P_ls = pd.DataFrame({"mult": P_pu})
    df_Q_ls = pd.DataFrame({"mult": Q_pu})

    df_P_ls.to_csv(saida_path + f"{feeder}_P_loadshape.csv", index=False)
    df_Q_ls.to_csv(saida_path + f"{feeder}_Q_loadshape.csv", index=False)

    # ----------------------------------
    # VERIFICAÇÃO FINAL (PONTOS)
    # ----------------------------------

    n_original = len(df_P)
    n_ls_P = len(df_P_ls)
    n_ls_Q = len(df_Q_ls)

    pontos_ok = (n_original == n_ls_P) and (n_original == n_ls_Q)

    # ----------------------------------
    # RELATÓRIOS
    # ----------------------------------

    relatorio_base.append({
        "Feeder": feeder,
        "P_base (kW)": P_base,
        "Q_base (kvar)": Q_base
    })

    relatorio_validacao.append({
        "Feeder": feeder,
        "n_buses": len(colunas),
        "NaN em P": nulos_P,
        "NaN em Q": nulos_Q,
        "Pontos originais": n_original,
        "Pontos loadshape P": n_ls_P,
        "Pontos loadshape Q": n_ls_Q,
        "Tamanho OK": "OK" if pontos_ok else "ERRO"
    })

# ============================================================
# SALVAR RELATÓRIOS
# ============================================================

df_base = pd.DataFrame(relatorio_base)
df_validacao = pd.DataFrame(relatorio_validacao)

df_base.to_csv(saida_path + "potencias_base.csv", index=False)
df_validacao.to_csv(saida_path + "validacao_loadshapes.csv", index=False)

# ============================================================
# PRINT FINAL
# ============================================================

print("\n====================================")
print("POTÊNCIAS BASE")
print("====================================")
print(df_base)

print("\n====================================")
print("VALIDAÇÃO DOS LOADSHAPES")
print("====================================")
print(df_validacao)