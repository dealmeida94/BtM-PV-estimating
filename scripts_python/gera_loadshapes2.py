#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# feeders
feeders = {
    "FeederA": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv",
    "FeederB": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederB_clean.csv",
    "FeederC": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederC_clean.csv"
}

caminho = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"

numero_de_pontos = 8760
intervalo = 1

P_total_rede = None
Q_total_rede = None

for feeder, arquivo in feeders.items():

    df = pd.read_csv(arquivo, parse_dates=["Time"])

    tempo = df["Time"]

    dss_lines = []
    carga_zero = []
    bases = []

    # dataframes das séries
    df_P = pd.DataFrame()
    df_Q = pd.DataFrame()
    df_FP = pd.DataFrame()

    df_P["Time"] = tempo
    df_Q["Time"] = tempo
    df_FP["Time"] = tempo

    P_total = np.zeros(len(df))
    Q_total = np.zeros(len(df))

    n_colunas_carga = len(df.columns) - 1
    loadshapes_criados = 0

    for col in df.columns[1:]:

        serie_P = df[col].values

        P_base = serie_P.max()

        if P_base == 0:
            carga_zero.append(col)
            continue

        fp = np.random.uniform(0.85, 0.95, len(serie_P))

        serie_Q = serie_P * np.tan(np.arccos(fp))

        Q_base = serie_Q.max()

        # salvar séries por bus
        df_P[col] = serie_P
        df_Q[col] = serie_Q
        df_FP[col] = fp

        bases.append({
            "bus": col.replace(' ', ''),
            "Pbase_kW": P_base,
            "Qbase_kvar": Q_base
        })

        PU_P = serie_P / P_base
        PU_Q = serie_Q / Q_base

        nome = col.replace(' ', '')

        nome_P = f"Loadshape_P_{nome}"
        nome_Q = f"Loadshape_Q_{nome}"

        arquivo_P = f"{caminho}{feeder}/{nome_P}.txt"
        arquivo_Q = f"{caminho}{feeder}/{nome_Q}.txt"

        pd.Series(PU_P).to_csv(arquivo_P, index=False, header=False)
        pd.Series(PU_Q).to_csv(arquivo_Q, index=False, header=False)

        linha_P = (
            f"New Loadshape.{nome_P} "
            f"npts={numero_de_pontos} interval={intervalo} "
            f"mult=(file={arquivo_P})"
        )

        linha_Q = (
            f"New Loadshape.{nome_Q} "
            f"npts={numero_de_pontos} interval={intervalo} "
            f"mult=(file={arquivo_Q})"
        )

        dss_lines.append(linha_P)
        dss_lines.append(linha_Q)

        P_total += serie_P
        Q_total += serie_Q

        loadshapes_criados += 1

    ####################################################################
    # salvar séries tratadas

    df_P.to_csv(f"{caminho}{feeder}/{feeder}_P.csv", index=False)
    df_Q.to_csv(f"{caminho}{feeder}/{feeder}_Q.csv", index=False)
    df_FP.to_csv(f"{caminho}{feeder}/{feeder}_FP.csv", index=False)

    ####################################################################
    # salvar arquivo DSS

    arquivo_dss = f"{caminho}{feeder}/Loadshape_{feeder}.dss"

    with open(arquivo_dss, "w") as f:
        for linha in dss_lines:
            f.write(linha + "\n")

    ####################################################################
    # salvar bases

    df_bases = pd.DataFrame(bases)

    arquivo_bases = f"{caminho}{feeder}/Pbase_{feeder}.csv"

    df_bases.to_csv(arquivo_bases, index=False)

    ####################################################################
    # calcular FP do feeder

    S = np.sqrt(P_total**2 + Q_total**2)
    FP = P_total / S

    ####################################################################
    # gráfico P e Q

    plt.figure(figsize=(12,6))
    plt.plot(tempo, P_total, label="P (kW)")
    plt.plot(tempo, Q_total, label="Q (kvar)")
    plt.title(f"Potência ativa e reativa - {feeder}")
    plt.legend()
    plt.grid()
    plt.show()

    ####################################################################
    # gráfico FP

    plt.figure(figsize=(12,4))
    plt.plot(tempo, FP)
    plt.ylim(0.84, 0.96)
    plt.title(f"Fator de potência - {feeder}")
    plt.ylabel("FP")
    plt.grid()
    plt.show()

    ####################################################################
    # soma na rede total

    if P_total_rede is None:
        P_total_rede = P_total
        Q_total_rede = Q_total
    else:
        P_total_rede += P_total
        Q_total_rede += Q_total

    ####################################################################

    print("\n###############################################")
    print(f"\nAlimentador: {feeder}")
    print(f"\nColunas na planilha original: {n_colunas_carga}")
    print(f"\nLoadshapes criados: {loadshapes_criados}")

    if carga_zero:
        print("\nNós com carga nula:")
        print(f"\t{carga_zero}")

    print(f"\nArquivo DSS salvo como: {arquivo_dss}")
    print(f"\nArquivo de potências base salvo como: {arquivo_bases}")

####################################################################
# gráficos totais da rede

S_total = np.sqrt(P_total_rede**2 + Q_total_rede**2)
FP_total = P_total_rede / S_total

plt.figure(figsize=(12,6))
plt.plot(P_total_rede, label="P total (kW)")
plt.plot(Q_total_rede, label="Q total (kvar)")
plt.title("Potência total da rede")
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(12,4))
plt.plot(FP_total)
plt.ylim(0.84, 0.96)
plt.title("Fator de potência total da rede")
plt.ylabel("FP")
plt.grid()
plt.show()