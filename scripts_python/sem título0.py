#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 15:41:56 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ============================================================
# CAMINHOS
# ============================================================

planilha_dados_brutos = "/home/matheus/Documentos/BtM-PV-estimating/dados_brutos/Calculated Nodal P&Q.xlsx"

caminho_saida = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/"
caminho_figuras = "/home/matheus/Documentos/BtM-PV-estimating/resultados/processamento_dos_dados_brutos/"

arquivo_saida = os.path.join(caminho_saida, "dados_processados.xlsx")

# ============================================================
# CONFIGURAÇÃO
# ============================================================

feeders = ["FeederA", "FeederB", "FeederC"]

relatorio = []
dataframes_processados = {}

# ============================================================
# FUNÇÃO FP
# ============================================================

def calcula_fp(P, Q):
    S = np.sqrt(P**2 + Q**2)
    return np.divide(P, S, out=np.zeros_like(P), where=S!=0)

# ============================================================
# PROCESSAMENTO
# ============================================================

for feeder in feeders:

    aba_P = f"{feeder}_P"
    aba_Q = f"{feeder}_Q"

    # -------------------------
    # LEITURA
    # -------------------------
    df_P = pd.read_excel(planilha_dados_brutos, sheet_name=aba_P)
    df_Q = pd.read_excel(planilha_dados_brutos, sheet_name=aba_Q)

    # -------------------------
    # PADRONIZAÇÃO
    # -------------------------
    df_P.rename(columns={df_P.columns[0]: "Time"}, inplace=True)
    df_Q.rename(columns={df_Q.columns[0]: "Time"}, inplace=True)

    df_P["Time"] = pd.to_datetime(df_P["Time"], errors="coerce")
    df_Q["Time"] = pd.to_datetime(df_Q["Time"], errors="coerce")

    # -------------------------
    # MERGE
    # -------------------------
    df = pd.merge(df_P, df_Q, on="Time", suffixes=("_P", "_Q"))

    # -------------------------
    # CALCULA FP (TODAS AS COLUNAS)
    # -------------------------
    colunas_P = [c for c in df.columns if "_P" in c]
    colunas_Q = [c for c in df.columns if "_Q" in c]

    df_FP = pd.DataFrame()
    df_FP["Time"] = df["Time"]

    for p_col, q_col in zip(colunas_P, colunas_Q):
        nome_base = p_col.replace("_P", "")
        df_FP[nome_base] = calcula_fp(df[p_col], df[q_col])

    # -------------------------
    # VERIFICAÇÕES
    # -------------------------
    numero_de_linhas_df = len(df)
    numero_de_linhas_P = len(df_P)
    numero_de_linhas_Q = len(df_Q)

    resultado_NaN_P = df_P.isna().any().any()
    resultado_NaN_Q = df_Q.isna().any().any()
    resultado_NaN_FP = df_FP.isna().any().any()

    nulos_P = df_P.isna().sum().sum()
    nulos_Q = df_Q.isna().sum().sum()
    nulos_FP = df_FP.isna().sum().sum()

    # -------------------------
    # ARMAZENAMENTO
    # -------------------------
    dataframes_processados[f"{feeder}_P"] = df_P
    dataframes_processados[f"{feeder}_Q"] = df_Q
    dataframes_processados[f"{feeder}_FP"] = df_FP

    # -------------------------
    # RELATÓRIO
    # -------------------------
    relatorio.append({
        "Feeder": feeder,
        "Linhas": numero_de_linhas_df,
        "8760 OK": "OK" if numero_de_linhas_df == 8760 else "ERRO",
        "NaN P": "Sim" if resultado_NaN_P else "Não",
        "NaN Q": "Sim" if resultado_NaN_Q else "Não",
        "NaN FP": "Sim" if resultado_NaN_FP else "Não",
        "Nulos P": nulos_P,
        "Nulos Q": nulos_Q,
        "Nulos FP": nulos_FP
    })

# ============================================================
# EXPORTAÇÃO (UM ÚNICO EXCEL)
# ============================================================

with pd.ExcelWriter(arquivo_saida) as writer:
    for nome_aba, df in dataframes_processados.items():
        df.to_excel(writer, sheet_name=nome_aba, index=False)

    df_relatorio = pd.DataFrame(relatorio)
    df_relatorio.to_excel(writer, sheet_name="Relatorio", index=False)

print("\nPlanilha salva em:", arquivo_saida)

# ============================================================
# CÁLCULO DAS POTÊNCIAS DOS FEEDERS
# ============================================================

P_feeders = {}
Q_feeders = {}

for feeder in feeders:

    df_P = dataframes_processados[f"{feeder}_P"]
    df_Q = dataframes_processados[f"{feeder}_Q"]

    colunas_P = [c for c in df_P.columns if c != "Time"]
    colunas_Q = [c for c in df_Q.columns if c != "Time"]

    P_total = df_P[colunas_P].sum(axis=1)
    Q_total = df_Q[colunas_Q].sum(axis=1)

    P_feeders[feeder] = P_total
    Q_feeders[feeder] = Q_total

# ============================================================
# TOTAL DA REDE
# ============================================================

P_total_rede = sum(P_feeders.values())
Q_total_rede = sum(Q_feeders.values())

FP_total_rede = calcula_fp(P_total_rede, Q_total_rede)

# ============================================================
# GRÁFICOS
# ============================================================

FP_min, FP_max = 0.5, 1.0

for feeder in feeders:

    P = P_feeders[feeder]
    Q = Q_feeders[feeder]
    FP = calcula_fp(P, Q)

    plt.figure(figsize=(10,5))
    plt.plot(P, label="P")
    plt.plot(Q, label="Q")
    plt.title(f"{feeder} - Potências")
    plt.legend()
    plt.grid()
    plt.savefig(caminho_figuras + f"{feeder}_P_Q.png")
    plt.close()

    plt.figure(figsize=(10,4))
    plt.plot(FP)
    plt.ylim(FP_min, FP_max)
    plt.title(f"{feeder} - FP")
    plt.grid()
    plt.savefig(caminho_figuras + f"{feeder}_FP.png")
    plt.close()

# ============================================================
# DIA ALEATÓRIO
# ============================================================

dia = np.random.randint(0, 365)

for feeder in feeders:

    P = P_feeders[feeder]
    Q = Q_feeders[feeder]
    FP = calcula_fp(P, Q)

    inicio = dia * 24
    fim = inicio + 24

    horas = range(24)

    plt.figure(figsize=(10,5))
    plt.plot(horas, P.iloc[inicio:fim])
    plt.plot(horas, Q.iloc[inicio:fim])
    plt.title(f"{feeder} - Dia {dia}")
    plt.grid()
    plt.savefig(caminho_figuras + f"{feeder}_dia_{dia}_P_Q.png")
    plt.close()

    plt.figure(figsize=(10,4))
    plt.plot(horas, FP.iloc[inicio:fim])
    plt.ylim(FP_min, FP_max)
    plt.title(f"{feeder} - FP Dia {dia}")
    plt.grid()
    plt.savefig(caminho_figuras + f"{feeder}_dia_{dia}_FP.png")
    plt.close()

print(f"\nGráficos salvos em: {caminho_figuras}")