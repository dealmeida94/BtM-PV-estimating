import random
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))
import configs as cfg

# Carrega planilha com os dados climáticos
df = pd.read_csv(cfg.DADOS_CLIMA, sep=";", decimal=",", encoding="utf-8")

#=========================================================================
# AJUSTE DOS HORÁRIOS
# Na planilha do INMET a hora é em UTC escrita sem separação entre hora e
# minuto: 0100 (01:00), 0200 (02:00), etc.
#
# Para utilização, é necessário converter esse formato para "HH:MM"
# e posteriormente unir a hora com a data para formar um datetime.

def ajusta_hora(h):
    h = str(h).zfill(4)  # Garante o padrão de 4 dígitos (ex: 100 -> 0100)
    return f"{h[:2]}:{h[2:]}"  # Reescreve como hh:mm

# Aplica a função na coluna horas
df["Hora_formatada"] = df["Hora (UTC)"].apply(ajusta_hora)

# Cria datetimes com data e hora
df["datetime_utc"] = pd.to_datetime(
    df["Data"] + " " + df["Hora_formatada"],
    format="%d/%m/%Y %H:%M",
    errors="coerce"  # Valores inválidos viram NaT
)

# Converte para horário local (Horário de brasília = UTC-3)
df["datetime_local"] = df["datetime_utc"] - pd.Timedelta(hours=3)

# =========================================================
# EXTRAI DO DATAFRAME APENAS O PERÍODO DE TEMPO QUE SERÁ
# UTILIZADO
inicio = pd.to_datetime("2017-01-01 01:00")
fim = pd.to_datetime("2018-01-01 00:00")
df = df[(df["datetime_local"] >= inicio) & (df["datetime_local"] <= fim)]
df = df.reset_index(drop=True) # reinicia o índice do dataframe

# =========================================================
# GARANTE QUE OS DADOS ESTÃO NO FORMATO ADEQUADO
df["temperatura"] = pd.to_numeric(df["Temp. Ins. (C)"], errors="coerce").astype(float)
df["radiacao_kj_m2"] = pd.to_numeric(df["Radiacao (KJ/m²)"], errors="coerce").astype(float)

# =========================================================
# CONVERTE RADIAÇÃO PARA IRRADIÂNCIA
df["irradiancia_W_m2"] = (df["radiacao_kj_m2"] * 1000) / 3600

# Remove ruídos noturnos
# considera nulo qualquer valor de irradiância menor que 1
df.loc[df["irradiancia_W_m2"] < 1, "irradiancia_W_m2"] = 0

# =========================================================
# VERIFICA A EXISTÊNCIA DE VALORES NaN

# Aplica interpolação linear na coluna de irradiância
df["irradiancia_W_m2"] = df["irradiancia_W_m2"].interpolate()

# Verifica os extremos da série
# Se o 1º valor for NaN, assume o valor do 2º
if pd.isna(df.loc[0, "irradiancia_W_m2"]):
    df.loc[0, "irradiancia_W_m2"] = df.loc[1, "irradiancia_W_m2"]

# Verifica fim da série
# Se o último valor for NaN, assume o valor do penúltimo
if pd.isna(df.loc[len(df)-1, "irradiancia_W_m2"]):
    df.loc[len(df)-1, "irradiancia_W_m2"] = df.loc[len(df)-2, "irradiancia_W_m2"]


# Aplica interpolação linear na coluna de temperatura
df["temperatura"] = df["temperatura"].interpolate()

# Verifica os extremos da série
# Se o 1º valor for NaN, assume o valor do 2º
if pd.isna(df.loc[0, "temperatura"]):
    df.loc[0, "temperatura"] = df.loc[1, "temperatura"]

# Verifica fim da série
# Se o último valor for NaN, assume o valor do penúltimo
if pd.isna(df.loc[len(df)-1, "temperatura"]):
    df.loc[len(df)-1, "temperatura"] = df.loc[len(df)-2, "temperatura"]

# =========================================================
# SALVA DATAFRAME
df_saida = df[["datetime_local", "temperatura", "irradiancia_W_m2"]]
df_saida.to_csv("dados_tratados.csv", index=False)

# =========================================================
# ANALISE DOS DADOS
print("Número de linhas:", len(df))
print("\nNaN após tratamento:")
print(df[["temperatura", "irradiancia_W_m2"]].isna().sum())

# Verifica horario do nascer e por do sol
# Converte a hora para decimal (hora + fração de minuto)
df_saida["hora"] = (
    df_saida["datetime_local"].dt.hour +
    df_saida["datetime_local"].dt.minute / 60
)

# Inicializa listas
nascer = []  # horários de nascer do sol
por = []     # horários de pôr do sol

# Agrupa os dados por dia
# d = dia, g = irradiância do dia d
for d, g in df_saida.groupby(df_saida["datetime_local"].dt.date):
    # Copia os valores de g que são maiores que 0
    g_sol = g[g["irradiancia_W_m2"] > 0]

    # Primeira hora com irradiância > 0
    nascer.append(g_sol["hora"].iloc[0])

    # Ultima hora com irradiância maior que zero
    por.append(g_sol["hora"].iloc[-1])

# Calcula o horário médio de nascer e por do sol
media_nascer = np.mean(nascer)
media_por = np.mean(por)    

print("Horário médio:")
print(f"\n\tNascer do sol: {media_nascer:.2f} h")
print(f"\n\tPôr do sol: {media_por:.2f} h")

# =================================================================
# PLOTA GRÁFICOS
# Irradiância anual
plt.figure()
plt.plot(df_saida["datetime_local"], df_saida["irradiancia_W_m2"])
plt.title("Irradiância (ano)")
plt.grid()
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# Temperatura anual
plt.figure()
plt.plot(df_saida["datetime_local"], df_saida["temperatura"])
plt.title("Temperatura (ano)")
plt.grid()
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# Dia aleátorio
df_saida["data"] = df_saida["datetime_local"].dt.date
dia = random.choice(df_saida["data"].unique())
df_dia = df_saida[df_saida["data"] == dia]

# Irradiância
plt.figure()
plt.plot(df_dia["datetime_local"], df_dia["irradiancia_W_m2"])
plt.title(f"Irradiância - {dia}")
plt.grid()
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))

# Temperatura
plt.figure()
plt.plot(df_dia["datetime_local"], df_dia["temperatura"])
plt.title(f"Temperatura - {dia}")
plt.grid()
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))

plt.show()