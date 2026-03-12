#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 18:09:17 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados_brutos/smart_meter_data.xlsx"

abas = {
    "FeederA_Smart Meter Data": "FeederA_clean.csv",
    "FeederB_Smart Meter Data": "FeederB_clean.csv",
    "FeederC_Smart Meter Data": "FeederC_clean.csv"
}

relatorio = []
dataframes_processados = {}

for aba, nome_do_arquivo in abas.items():

    df = pd.read_excel(
        arquivo,
        sheet_name=aba,
        header=0
    )

    df.rename(columns={df.columns[0]: "Time"}, inplace=True)
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

# =============================================================================
#     for col in df.columns[1:]:
#         df[col] = (
#             df[col]
#             .astype(str)
#             .str.replace(",", ".", regex=False)
#             .astype(float)
#         )
# 
# =============================================================================
    ##############################################
    # GERA FP E POTÊNCIA REATIVA
    ##############################################

    df_saida = pd.DataFrame()
    df_saida["Time"] = df["Time"]

    for col in df.columns[1:]:

        P = df[col].astype(float)

        # FP aleatório por tempo
        FP = np.random.uniform(0.85, 0.95, len(P))

        # cálculo Q
        Q = P * np.tan(np.arccos(FP))

        df_saida[f"{col}_P"] = P
        df_saida[f"{col}_Q"] = Q
        df_saida[f"{col}_FP"] = FP

    ##############################################
    # VERIFICAÇÕES
    ##############################################

    possui_nan = df_saida.isna().any().any()
    linhas = len(df_saida)
    duplicados = df_saida["Time"].duplicated().sum()
    nulos = df_saida.isna().sum().sum()

    relatorio.append({
        "Planilha": aba,
        "nº linhas": linhas,
        "nº linhas = 8760": "OK" if linhas == 8760 else "ERRO",
        "Datas duplicadas": duplicados,
        "Valores nulos": nulos,
        "Possui NaN": "Sim" if possui_nan else "Não"
    })

    caminho_do_arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/" + nome_do_arquivo
    df_saida.to_csv(caminho_do_arquivo, index=False)

    dataframes_processados[aba] = df_saida

print("\nProcessamento concluído.\n")

tabela = pd.DataFrame(relatorio)

print("Verificações:\n")
print(tabela.to_string(index=False))


# ============================================================
# GRÁFICOS
# ============================================================

feeders = {
    "FeederA": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv",
    "FeederB": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederB_clean.csv",
    "FeederC": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederC_clean.csv"
}

P_feeders = {}
Q_feeders = {}

for nome, caminho in feeders.items():

    df = pd.read_csv(caminho)

    colunas_P = [c for c in df.columns if "_P" in c]
    colunas_Q = [c for c in df.columns if "_Q" in c]

    P_total = df[colunas_P].sum(axis=1)
    Q_total = df[colunas_Q].sum(axis=1)

    P_feeders[nome] = P_total
    Q_feeders[nome] = Q_total


# soma rede
P_total_rede = sum(P_feeders.values())
Q_total_rede = sum(Q_feeders.values())

FP_total_rede = P_total_rede / np.sqrt(P_total_rede**2 + Q_total_rede**2)


# ============================================================
# PLOT POR FEEDER
# ============================================================

for feeder in feeders.keys():

    P = P_feeders[feeder]
    Q = Q_feeders[feeder]
    FP = P / np.sqrt(P**2 + Q**2)

    plt.figure(figsize=(10,5))
    plt.plot(P,label="P (kW)")
    plt.plot(Q,label="Q (kvar)")
    plt.title(f"Potência - {feeder}")
    plt.legend()
    plt.grid()
    plt.show()

    plt.figure(figsize=(10,4))
    plt.plot(FP)
    plt.ylim(0.84,0.96)
    plt.title(f"Fator de Potência - {feeder}")
    plt.grid()
    plt.show()


# ============================================================
# PLOT TOTAL
# ============================================================

plt.figure(figsize=(10,5))
plt.plot(P_total_rede,label="P total")
plt.plot(Q_total_rede,label="Q total")
plt.title("Potência Total da Rede")
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(FP_total_rede)
plt.ylim(0.84,0.96)
plt.title("Fator de Potência Total da Rede")
plt.grid()
plt.show()