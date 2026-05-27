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

df = pd.read_csv(cfg.DADOS_CLIMA, sep=";", decimal=",", encoding="utf-8")

# =========================================================
# TRATAMENTO INICIAL DA RADIAÇÃO (ANTES DE QUALQUER COISA)

# força numérico
df["radiacao_kj_m2"] = pd.to_numeric(df["Radiacao (KJ/m²)"], errors="coerce")

# substitui NaN por 0
df["radiacao_kj_m2"] = df["radiacao_kj_m2"].fillna(0)

# =========================================================
# AJUSTE DOS HORÁRIOS

def ajusta_hora(h):
    h = str(h).zfill(4)
    return f"{h[:2]}:{h[2:]}"

df["Hora_formatada"] = df["Hora (UTC)"].apply(ajusta_hora)

df["datetime_utc"] = pd.to_datetime(
    df["Data"] + " " + df["Hora_formatada"],
    format="%d/%m/%Y %H:%M",
    errors="coerce"
)

df["datetime_local"] = df["datetime_utc"] - pd.Timedelta(hours=3)

# =========================================================
inicio = pd.to_datetime("2017-01-01 01:00")
fim = pd.to_datetime("2018-01-01 00:00")
df = df[(df["datetime_local"] >= inicio) & (df["datetime_local"] <= fim)]
df = df.reset_index(drop=True)

# =========================================================
df["temperatura"] = pd.to_numeric(df["Temp. Ins. (C)"], errors="coerce").astype(float)

# =========================================================
# PLOT DA RADIAÇÃO DIÁRIA (ANTES DA CONVERSÃO)

df["hora"] = (
    df["datetime_local"].dt.hour +
    df["datetime_local"].dt.minute / 60
)

df["data"] = df["datetime_local"].dt.date

plt.figure()

for d, g in df.groupby("data"):
    plt.plot(g["hora"], g["radiacao_kj_m2"], alpha=0.1)

plt.title("Radiação diária (curvas sobrepostas)")
plt.xlabel("Hora do dia")
plt.ylabel("Radiação (kJ/m²)")
plt.xlim(0, 24)
plt.grid()

plt.show()

# =========================================================
# CONVERSÃO PARA IRRADIÂNCIA

df["irradiancia_W_m2"] = (df["radiacao_kj_m2"] * 1000) / 3600
df.loc[df["irradiancia_W_m2"] < 1, "irradiancia_W_m2"] = 0

# =========================================================
nan_antes = df[["temperatura", "irradiancia_W_m2"]].isna().sum()

# =========================================================
df["irradiancia_W_m2"] = df["irradiancia_W_m2"].interpolate()

if pd.isna(df.loc[0, "irradiancia_W_m2"]):
    df.loc[0, "irradiancia_W_m2"] = df.loc[1, "irradiancia_W_m2"]

if pd.isna(df.loc[len(df)-1, "irradiancia_W_m2"]):
    df.loc[len(df)-1, "irradiancia_W_m2"] = df.loc[len(df)-2, "irradiancia_W_m2"]

df["temperatura"] = df["temperatura"].interpolate()

if pd.isna(df.loc[0, "temperatura"]):
    df.loc[0, "temperatura"] = df.loc[1, "temperatura"]

if pd.isna(df.loc[len(df)-1, "temperatura"]):
    df.loc[len(df)-1, "temperatura"] = df.loc[len(df)-2, "temperatura"]

nan_depois = df[["temperatura", "irradiancia_W_m2"]].isna().sum()

# =========================================================
# RESTANTE DO SCRIPT (INALTERADO)

print("Número de linhas:", len(df))

print("\nNaN antes do tratamento:")
print(nan_antes)

print("\nNaN após tratamento:")
print(nan_depois)

irr_max = df["irradiancia_W_m2"].max()
irr_min = df["irradiancia_W_m2"].min()

temp_max = df["temperatura"].max()
temp_min = df["temperatura"].min()

# =========================================================
# NASCER E PÔR DO SOL

df_saida = df[["datetime_local", "temperatura", "irradiancia_W_m2"]]

df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

nascer = []
por = []
datas = []

for d, g in df_saida.groupby(df_saida["datetime_local"].dt.date):

    g = g.sort_values("datetime_local")

    irr = g["irradiancia_W_m2"].values
    horas = g["hora"].values

    nascer_h = None
    por_h = None

    # NASCER → primeiro > 10
    for i in range(len(irr)):
        if irr[i] > 10:
            nascer_h = horas[i]
            break

    # PÔR → último > 10
    for i in range(len(irr)-1, -1, -1):
        if irr[i] > 10:
            por_h = horas[i]
            break

    if nascer_h is not None and por_h is not None:
        nascer.append(nascer_h)
        por.append(por_h)
        datas.append(d)

media_nascer = np.mean(nascer)
media_por = np.mean(por)

def hora_decimal_para_hhmm(h):
    horas = int(h)
    minutos = int((h - horas) * 60)
    return f"{horas:02d}:{minutos:02d}"

nascer_str = hora_decimal_para_hhmm(media_nascer)
por_str = hora_decimal_para_hhmm(media_por)

print("\nHorário médio:")
print(f"\n\tNascer do sol: {nascer_str}")
print(f"\n\tPôr do sol: {por_str}")

# =========================================================
plt.show()

# PLOT DE TODOS OS DIAS SOBREPOSTOS (IRRADIÂNCIA)

plt.figure()

# cria coluna com data (sem hora)
df_saida["data"] = df_saida["datetime_local"].dt.date

# hora em formato decimal (0–24)
df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

# plota cada dia como uma curva
for d, g in df_saida.groupby("data"):
    plt.plot(g["hora"], g["irradiancia_W_m2"], alpha=0.1)

plt.title("Irradiância diária (curvas sobrepostas)")
plt.xlabel("Hora do dia")
plt.ylabel("Irradiância (W/m²)")
plt.xlim(0, 24)
plt.grid()

plt.show()

#%%
# =========================================================
# PLOT IRRADIÂNCIA NOTURNA (20h → 05h)

plt.figure()

# garante colunas auxiliares
df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

df_saida["hora_int"] = df_saida["datetime_local"].dt.hour
df_saida["data"] = df_saida["datetime_local"].dt.date

# filtra período noturno
df_noite = df_saida[
    (df_saida["hora_int"] >= 20) | (df_saida["hora_int"] <= 5)
]

# plot por dia
for d, g in df_noite.groupby("data"):
    plt.plot(g["hora"], g["irradiancia_W_m2"], alpha=0.1)

plt.title("Irradiância noturna (20h–05h)")
plt.xlabel("Hora do dia")
plt.ylabel("Irradiância (W/m²)")
plt.xlim(0, 24)
plt.grid()

plt.show()