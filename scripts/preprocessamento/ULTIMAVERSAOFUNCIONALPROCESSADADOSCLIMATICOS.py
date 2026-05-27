import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))
import configs as cfg

df = pd.read_csv(cfg.DADOS_CLIMA, sep=";", decimal=",", encoding="utf-8")

#=========================================================================
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
df["radiacao_kj_m2"] = pd.to_numeric(df["Radiacao (KJ/m²)"], errors="coerce").astype(float)

# =========================================================
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
# VERIFICA SE EXISTEM HORÁRIOS FALTANTES

print("\nVerificação de sequência temporal:")

df_sorted = df.sort_values("datetime_local").reset_index(drop=True)
delta = df_sorted["datetime_local"].diff()

faltantes_idx = np.where(delta != pd.Timedelta(hours=1))[0]

if len(faltantes_idx) > 1:
    print("\nHorários faltantes detectados:")
    for i in faltantes_idx[1:]:
        anterior = df_sorted.loc[i-1, "datetime_local"]
        atual = df_sorted.loc[i, "datetime_local"]
        print(f"Falta entre {anterior} e {atual}")
else:
    print("Nenhum horário faltante encontrado.")

# =========================================================
df_saida = df[["datetime_local", "temperatura", "irradiancia_W_m2"]]
df_saida.to_csv("dados_tratados.csv", index=False)

# =========================================================
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
# NASCER E PÔR DO SOL (VERSÃO SIMPLES PARA VALIDAÇÃO)

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

# =========================================================
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
# PLOTS

plt.figure()
plt.plot(datas, nascer)
plt.title("Horário de Nascer do Sol (diário)")
plt.ylabel("Hora (decimal)")
plt.grid()

plt.figure()
plt.plot(datas, por)
plt.title("Horário de Pôr do Sol (diário)")
plt.ylabel("Hora (decimal)")
plt.grid()

plt.figure()
plt.plot(df_saida["datetime_local"], df_saida["irradiancia_W_m2"])
plt.title("Irradiância (ano)")
plt.grid()
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

plt.show()
#%%
# =========================================================
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