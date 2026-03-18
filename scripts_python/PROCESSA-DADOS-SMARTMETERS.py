#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# ARQUIVO DE ENTRADA
# ============================================================

arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados_brutos/smart_meter_data.xlsx"

abas = {
    "FeederA_Smart Meter Data": "FeederA_clean.csv",
    "FeederB_Smart Meter Data": "FeederB_clean.csv",
    "FeederC_Smart Meter Data": "FeederC_clean.csv"
}

base_path = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/"

relatorio = []
dataframes_processados = {}

# ============================================================
# PROCESSAMENTO
# ============================================================

for aba, nome_do_arquivo in abas.items():

    df = pd.read_excel(
        arquivo,
        sheet_name=aba,
        header=0
    )

    df.rename(columns={df.columns[0]: "Time"}, inplace=True)
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

    ##############################################
    # DATAFRAMES SEPARADOS
    ##############################################

    # Dicionários temporários
    dados_P = {}
    dados_Q = {}
    dados_FP = {}
    
    for col in df.columns[1:]:
    
        P = df[col].astype(float)
    
        FP = np.random.uniform(0.85, 0.95, len(P))
        Q = P * np.tan(np.arccos(FP))
    
        dados_P[col] = P
        dados_Q[col] = Q
        dados_FP[col] = FP
    
    # Criação dos DataFrames de uma vez (sem fragmentação)
    df_P = pd.DataFrame(dados_P)
    df_Q = pd.DataFrame(dados_Q)
    df_FP = pd.DataFrame(dados_FP)
    
    # Adiciona o tempo depois
    df_P.insert(0, "Time", df["Time"])
    df_Q.insert(0, "Time", df["Time"])
    df_FP.insert(0, "Time", df["Time"])

    ##############################################
    # VERIFICAÇÕES (usando P como base)
    ##############################################

    possui_nan = df_P.isna().any().any()
    linhas = len(df_P)
    duplicados = df_P["Time"].duplicated().sum()
    nulos = df_P.isna().sum().sum()

    relatorio.append({
        "Planilha": aba,
        "nº linhas": linhas,
        "nº linhas = 8760": "OK" if linhas == 8760 else "ERRO",
        "Datas duplicadas": duplicados,
        "Valores nulos": nulos,
        "Possui NaN": "Sim" if possui_nan else "Não"
    })

    ##############################################
    # SALVANDO ARQUIVOS SEPARADOS
    ##############################################

    nome_base = nome_do_arquivo.replace("_clean.csv", "")

    df_P.to_csv(base_path + f"{nome_base}_P.csv", index=False)
    df_Q.to_csv(base_path + f"{nome_base}_Q.csv", index=False)
    df_FP.to_csv(base_path + f"{nome_base}_FP.csv", index=False)

    ##############################################
    # ARMAZENAR PARA USO
    ##############################################

    dataframes_processados[aba] = {
        "P": df_P,
        "Q": df_Q,
        "FP": df_FP
    }

print("\nProcessamento concluído.\n")

tabela = pd.DataFrame(relatorio)

print("Verificações:\n")
print(tabela.to_string(index=False))

# ============================================================
# GRÁFICOS
# ============================================================

feeders = ["FeederA", "FeederB", "FeederC"]

P_feeders = {}
Q_feeders = {}

for nome in feeders:

    df_P = pd.read_csv(base_path + f"{nome}_P.csv")
    df_Q = pd.read_csv(base_path + f"{nome}_Q.csv")

    colunas_P = [c for c in df_P.columns if c != "Time"]
    colunas_Q = [c for c in df_Q.columns if c != "Time"]

    P_total = df_P[colunas_P].sum(axis=1)
    Q_total = df_Q[colunas_Q].sum(axis=1)

    P_feeders[nome] = P_total
    Q_feeders[nome] = Q_total

# ============================================================
# TOTAL DA REDE
# ============================================================

P_total_rede = sum(P_feeders.values())
Q_total_rede = sum(Q_feeders.values())

FP_total_rede = P_total_rede / np.sqrt(P_total_rede**2 + Q_total_rede**2)

# ============================================================
# PLOT POR FEEDER
# ============================================================

for feeder in feeders:

    P = P_feeders[feeder]
    Q = Q_feeders[feeder]
    FP = P / np.sqrt(P**2 + Q**2)

    plt.figure(figsize=(10,5))
    plt.plot(P, label="P (kW)")
    plt.plot(Q, label="Q (kvar)")
    plt.title(f"Potência - {feeder}")
    plt.legend()
    plt.grid()
    plt.show()

    plt.figure(figsize=(10,4))
    plt.plot(FP)
    plt.ylim(0.84, 0.96)
    plt.title(f"Fator de Potência - {feeder}")
    plt.grid()
    plt.show()

# ============================================================
# PLOT TOTAL
# ============================================================

plt.figure(figsize=(10,5))
plt.plot(P_total_rede, label="P total")
plt.plot(Q_total_rede, label="Q total")
plt.title("Potência Total da Rede")
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(10,4))
plt.plot(FP_total_rede)
plt.ylim(0.84, 0.96)
plt.title("Fator de Potência Total da Rede")
plt.grid()
plt.show()