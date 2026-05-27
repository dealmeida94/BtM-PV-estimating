#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 26 22:13:12 2026

@author: matheus
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))
import configs as cfg

# =========================================================
# CONFIGURAÇÕES

LIMIAR_IRRADIANCIA = 50

# percentis para puxar os pontos para as extremidades
PERCENTIL_NASCER = 5
PERCENTIL_POR = 95

# =========================================================
# LEITURA DOS DADOS

df = pd.read_csv(
    cfg.DADOS_CLIMA,
    sep=";",
    decimal=",",
    encoding="utf-8"
)

# =========================================================
# TRATAMENTO INICIAL DA RADIAÇÃO

# força numérico
df["radiacao_kj_m2"] = pd.to_numeric(
    df["Radiacao (KJ/m²)"],
    errors="coerce"
)

# substitui NaN por 0
df["radiacao_kj_m2"] = (
    df["radiacao_kj_m2"].fillna(0)
)

# =========================================================
# AJUSTE DOS HORÁRIOS

def ajusta_hora(h):
    h = str(h).zfill(4)
    return f"{h[:2]}:{h[2:]}"

df["Hora_formatada"] = (
    df["Hora (UTC)"].apply(ajusta_hora)
)

df["datetime_utc"] = pd.to_datetime(
    df["Data"] + " " + df["Hora_formatada"],
    format="%d/%m/%Y %H:%M",
    errors="coerce"
)

# UTC → horário local
df["datetime_local"] = (
    df["datetime_utc"] - pd.Timedelta(hours=3)
)

# =========================================================
# FILTRO DO ANO

inicio = pd.to_datetime("2017-01-01 01:00")
fim = pd.to_datetime("2018-01-01 00:00")

df = df[
    (df["datetime_local"] >= inicio) &
    (df["datetime_local"] <= fim)
]

df = df.reset_index(drop=True)

# =========================================================
# TEMPERATURA

df["temperatura"] = pd.to_numeric(
    df["Temp. Ins. (C)"],
    errors="coerce"
).astype(float)

# =========================================================
# PLOT DA RADIAÇÃO ORIGINAL

df["hora"] = (
    df["datetime_local"].dt.hour +
    df["datetime_local"].dt.minute / 60
)

df["data"] = df["datetime_local"].dt.date

plt.figure()

for d, g in df.groupby("data"):

    plt.plot(
        g["hora"],
        g["radiacao_kj_m2"],
        alpha=0.1
    )

plt.title("Radiação diária (curvas sobrepostas)")
plt.xlabel("Hora do dia")
plt.ylabel("Radiação (kJ/m²)")
plt.xlim(0, 24)
plt.grid()

plt.show()

# =========================================================
# CONVERSÃO PARA IRRADIÂNCIA

df["irradiancia_W_m2"] = (
    df["radiacao_kj_m2"] * 1000
) / 3600

# elimina ruído muito pequeno
df.loc[
    df["irradiancia_W_m2"] < 1,
    "irradiancia_W_m2"
] = 0

# =========================================================
# NaN ANTES

nan_antes = df[[
    "temperatura",
    "irradiancia_W_m2"
]].isna().sum()

# =========================================================
# INTERPOLAÇÃO

df["irradiancia_W_m2"] = (
    df["irradiancia_W_m2"].interpolate()
)

if pd.isna(df.loc[0, "irradiancia_W_m2"]):

    df.loc[0, "irradiancia_W_m2"] = (
        df.loc[1, "irradiancia_W_m2"]
    )

if pd.isna(df.loc[len(df)-1, "irradiancia_W_m2"]):

    df.loc[len(df)-1, "irradiancia_W_m2"] = (
        df.loc[len(df)-2, "irradiancia_W_m2"]
    )

# temperatura
df["temperatura"] = (
    df["temperatura"].interpolate()
)

if pd.isna(df.loc[0, "temperatura"]):

    df.loc[0, "temperatura"] = (
        df.loc[1, "temperatura"]
    )

if pd.isna(df.loc[len(df)-1, "temperatura"]):

    df.loc[len(df)-1, "temperatura"] = (
        df.loc[len(df)-2, "temperatura"]
    )

# =========================================================
# NaN DEPOIS

nan_depois = df[[
    "temperatura",
    "irradiancia_W_m2"
]].isna().sum()

# =========================================================
# INFORMAÇÕES

print("Número de linhas:", len(df))

print("\nNaN antes do tratamento:")
print(nan_antes)

print("\nNaN após tratamento:")
print(nan_depois)

irr_max = df["irradiancia_W_m2"].max()
irr_min = df["irradiancia_W_m2"].min()

temp_max = df["temperatura"].max()
temp_min = df["temperatura"].min()

print(f"\nIrradiância máxima: {irr_max:.2f} W/m²")
print(f"Irradiância mínima: {irr_min:.2f} W/m²")

print(f"\nTemperatura máxima: {temp_max:.2f} °C")
print(f"Temperatura mínima: {temp_min:.2f} °C")

# =========================================================
# NASCER E PÔR DO SOL

df_saida = df[[
    "datetime_local",
    "temperatura",
    "irradiancia_W_m2"
]].copy()

# hora decimal
df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

nascer = []
por = []
datas = []

for d, g in df_saida.groupby(
    df_saida["datetime_local"].dt.date
):

    g = g.sort_values("datetime_local")

    irr = g["irradiancia_W_m2"].values
    horas = g["hora"].values

    nascer_h = None
    por_h = None

    # =====================================================
    # NASCER DO SOL

    for i in range(len(irr)):

        if irr[i] > LIMIAR_IRRADIANCIA:

            nascer_h = horas[i]
            break

    # =====================================================
    # PÔR DO SOL

    for i in range(len(irr)-1, -1, -1):

        if irr[i] > LIMIAR_IRRADIANCIA:

            por_h = horas[i]
            break

    # =====================================================

    if nascer_h is not None and por_h is not None:

        nascer.append(nascer_h)
        por.append(por_h)
        datas.append(d)

# =========================================================
# PERCENTIS

media_nascer = np.percentile(
    nascer,
    PERCENTIL_NASCER
)

media_por = np.percentile(
    por,
    PERCENTIL_POR
)

# =========================================================
# CONVERSÃO PARA HH:MM

def hora_decimal_para_hhmm(h):

    horas = int(h)

    minutos = int(
        round((h - horas) * 60)
    )

    return f"{horas:02d}:{minutos:02d}"

nascer_str = hora_decimal_para_hhmm(
    media_nascer
)

por_str = hora_decimal_para_hhmm(
    media_por
)

# =========================================================
# RESULTADOS

print("\nHorários característicos:")

print(
    f"\n\tNascer do sol: {nascer_str}"
)

print(
    f"\n\tPôr do sol: {por_str}"
)

# =========================================================
# PLOT DAS CURVAS SOBREPOSTAS

plt.figure(figsize=(8, 6))

# cria coluna data
df_saida["data"] = (
    df_saida["datetime_local"].dt.date
)

# hora decimal
df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

# =========================================================
# CURVAS

for d, g in df_saida.groupby("data"):

    plt.plot(
        g["hora"],
        g["irradiancia_W_m2"],
        alpha=0.1
    )

# =========================================================
# PONTOS DE NASCER/PÔR
# =========================================================
# NASCER E PÔR DO SOL

LIMIAR_IRRADIANCIA = 50

df_saida = df[[
    "datetime_local",
    "temperatura",
    "irradiancia_W_m2"
]].copy()

# hora decimal
df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

nascer = []
por = []
datas = []

for d, g in df_saida.groupby(
    df_saida["datetime_local"].dt.date
):

    g = g.sort_values("datetime_local")

    irr = g["irradiancia_W_m2"].values
    horas = g["hora"].values

    nascer_h = None
    por_h = None

    # =====================================================
    # NASCER DO SOL

    for i in range(len(irr)):

        if irr[i] > LIMIAR_IRRADIANCIA:

            nascer_h = horas[i]
            break

    # =====================================================
    # PÔR DO SOL

    for i in range(len(irr)-1, -1, -1):

        if irr[i] > LIMIAR_IRRADIANCIA:

            por_h = horas[i]
            break

    # =====================================================

    if nascer_h is not None and por_h is not None:

        nascer.append(nascer_h)
        por.append(por_h)
        datas.append(d)

# =========================================================
# MÉDIAS

media_nascer = np.mean(nascer)
media_por = np.mean(por)

# =========================================================
# MÁXIMOS E MÍNIMOS

nascer_min = np.min(nascer)
nascer_max = np.max(nascer)

por_min = np.min(por)
por_max = np.max(por)

# =========================================================
# CONVERSÃO HH:MM

def hora_decimal_para_hhmm(h):

    horas = int(h)

    minutos = int(
        round((h - horas) * 60)
    )

    return f"{horas:02d}:{minutos:02d}"

nascer_str = hora_decimal_para_hhmm(
    media_nascer
)

por_str = hora_decimal_para_hhmm(
    media_por
)

# =========================================================
# PRINTS

print("\nHorários médios:")

print(
    f"\n\tNascer do sol médio: {nascer_str}"
)

print(
    f"\n\tPôr do sol médio: {por_str}"
)

# =========================================================
# PLOT 1
# CURVAS SOBREPOSTAS + MÉDIAS

plt.figure(figsize=(9, 6))

df_saida["data"] = (
    df_saida["datetime_local"].dt.date
)

# curvas
for d, g in df_saida.groupby("data"):

    plt.plot(
        g["hora"],
        g["irradiancia_W_m2"],
        alpha=0.1
    )

# =========================================================
# PONTO MÉDIO NASCER

plt.scatter(
    media_nascer,
    0,
    color="red",
    s=220,
    zorder=20,
    label=(
        f"Nascer médio "
        f"({nascer_str})"
    )
)

# linha vertical
plt.axvline(
    media_nascer,
    color="red",
    linestyle="--",
    alpha=0.8
)

# =========================================================
# PONTO MÉDIO PÔR

plt.scatter(
    media_por,
    0,
    color="blue",
    s=220,
    zorder=20,
    label=(
        f"Pôr médio "
        f"({por_str})"
    )
)

# linha vertical
plt.axvline(
    media_por,
    color="blue",
    linestyle="--",
    alpha=0.8
)

# =========================================================
# GRÁFICO

plt.title(
    "Irradiância diária (curvas sobrepostas)"
)

plt.xlabel("Hora do dia")

plt.ylabel("Irradiância (W/m²)")

plt.xlim(0, 24)

plt.grid()

plt.legend()

plt.show()

# =========================================================
# PLOT 2
# HORÁRIOS DE NASCER E PÔR DO SOL

plt.figure(figsize=(12, 6))

# =========================================================
# CURVAS

plt.plot(
    datas,
    nascer,
    label="Nascer do sol",
    alpha=0.8
)

plt.plot(
    datas,
    por,
    label="Pôr do sol",
    alpha=0.8
)

# =========================================================
# MÉDIAS

plt.axhline(
    media_nascer,
    linestyle="--",
    linewidth=2,
    alpha=0.9,
    label=f"Média nascer ({nascer_str})"
)

plt.axhline(
    media_por,
    linestyle="--",
    linewidth=2,
    alpha=0.9,
    label=f"Média pôr ({por_str})"
)

# =========================================================
# LIMITES NASCER

plt.axhline(
    nascer_min,
    linestyle=":",
    linewidth=2,
    alpha=0.8,
    label=(
        "Nascer mínimo "
        f"({hora_decimal_para_hhmm(nascer_min)})"
    )
)

plt.axhline(
    nascer_max,
    linestyle=":",
    linewidth=2,
    alpha=0.8,
    label=(
        "Nascer máximo "
        f"({hora_decimal_para_hhmm(nascer_max)})"
    )
)

# =========================================================
# LIMITES PÔR

plt.axhline(
    por_min,
    linestyle=":",
    linewidth=2,
    alpha=0.8,
    label=(
        "Pôr mínimo "
        f"({hora_decimal_para_hhmm(por_min)})"
    )
)

plt.axhline(
    por_max,
    linestyle=":",
    linewidth=2,
    alpha=0.8,
    label=(
        "Pôr máximo "
        f"({hora_decimal_para_hhmm(por_max)})"
    )
)

# =========================================================
# GRÁFICO

plt.title(
    "Horários de nascer e pôr do sol ao longo do ano"
)

plt.xlabel("Data")

plt.ylabel("Hora do dia")

plt.grid()

plt.legend()

plt.show()

#%%
# =========================================================
# K-MEANS DAS CURVAS DE IRRADIÂNCIA
# 3 CENTROIDES

from sklearn.cluster import KMeans

# =========================================================
# MATRIZ DAS CURVAS

curvas = []
datas_validas = []

# garante ordenação temporal
df_saida = df_saida.sort_values("datetime_local")

for d, g in df_saida.groupby("data"):

    g = g.sort_values("datetime_local")

    curva = g["irradiancia_W_m2"].values

    # garante mesmo tamanho para todas as curvas
    if len(curva) == 24:

        curvas.append(curva)
        datas_validas.append(d)

# =========================================================
# CONVERTE PARA ARRAY

X = np.array(curvas)

print("\nShape matriz KMeans:")
print(X.shape)

# =========================================================
# K-MEANS

N_CLUSTERS = 3

kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=42,
    n_init=20
)

labels = kmeans.fit_predict(X)

# centroides
centroides = kmeans.cluster_centers_

# =========================================================
# HORAS

horas = np.arange(24)

# =========================================================
# PLOT DAS CURVAS POR CLUSTER

plt.figure(figsize=(12, 7))

for cluster in range(N_CLUSTERS):

    idx_cluster = np.where(labels == cluster)[0]

    # curvas do cluster
    for idx in idx_cluster:

        plt.plot(
            horas,
            X[idx],
            alpha=0.05
        )

    # centróide
    plt.plot(
        horas,
        centroides[cluster],
        linewidth=4,
        label=f"Centróide {cluster + 1}"
    )

# =========================================================
# GRÁFICO

plt.title(
    "K-Means das curvas de irradiância"
)

plt.xlabel("Hora do dia")

plt.ylabel("Irradiância (W/m²)")

plt.xlim(0, 23)

plt.grid()

plt.legend()

plt.show()

# =========================================================
# PLOT SOMENTE DOS CENTROIDES

plt.figure(figsize=(10, 6))

for cluster in range(N_CLUSTERS):

    plt.plot(
        horas,
        centroides[cluster],
        linewidth=4,
        label=f"Centróide {cluster + 1}"
    )

plt.title(
    "Centróides das curvas de irradiância"
)

plt.xlabel("Hora do dia")

plt.ylabel("Irradiância (W/m²)")

plt.xlim(0, 23)

plt.grid()

plt.legend()

plt.show()

# =========================================================
# QUANTIDADE DE DIAS EM CADA CLUSTER

print("\nQuantidade de curvas por cluster:\n")

for cluster in range(N_CLUSTERS):

    qtd = np.sum(labels == cluster)

    print(
        f"Cluster {cluster + 1}: "
        f"{qtd} dias"
    )