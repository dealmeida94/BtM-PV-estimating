import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random

# =========================================================
# 1. CARREGAR A PLANILHA
# =========================================================
arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados/externos/climaticos/estacao_INMET_A853_cruz_alta.csv"

df = pd.read_csv(arquivo, sep=";", decimal=",", encoding="utf-8")

# =========================================================
# 2. TRATAR DATA E HORA
# =========================================================

def ajusta_hora(h):
    h = str(h).zfill(4)
    return f"{h[:2]}:{h[2:]}"

df["Hora_formatada"] = df["Hora (UTC)"].apply(ajusta_hora)

df["datetime_utc"] = pd.to_datetime(
    df["Data"] + " " + df["Hora_formatada"],
    format="%d/%m/%Y %H:%M",
    errors="coerce"
)

# UTC → UTC-3 (Brasil)
df["datetime_local"] = df["datetime_utc"] - pd.Timedelta(hours=3)

# =========================================================
# 3. FILTRAR INTERVALO DE TEMPO
# =========================================================
inicio = pd.to_datetime("2017-01-01 01:00")
fim = pd.to_datetime("2018-01-01 00:00")

df = df[(df["datetime_local"] >= inicio) & (df["datetime_local"] <= fim)]
df = df.reset_index(drop=True)

# =========================================================
# 4. CONVERSÃO DE DADOS
# =========================================================

df["temperatura"] = pd.to_numeric(df["Temp. Ins. (C)"], errors="coerce").astype(float)
df["radiacao_kj_m2"] = pd.to_numeric(df["Radiacao (KJ/m²)"], errors="coerce").astype(float)

# =========================================================
# 5. IRRADIÂNCIA
# =========================================================

df["irradiancia_W_m2"] = (df["radiacao_kj_m2"] * 1000) / 3600

# Remover ruído noturno
df.loc[df["irradiancia_W_m2"] < 1, "irradiancia_W_m2"] = 0

# =========================================================
# 6. INTERPOLAÇÃO LOCAL
# =========================================================

nan_idx = df[df["irradiancia_W_m2"].isna()].index

for i in nan_idx:
    if i > 0 and i < len(df) - 1:
        val_ant = df.iloc[i - 1]["irradiancia_W_m2"]
        val_post = df.iloc[i + 1]["irradiancia_W_m2"]
        
        if not np.isnan(val_ant) and not np.isnan(val_post):
            df.loc[i, "irradiancia_W_m2"] = (val_ant + val_post) / 2
        else:
            df.loc[i, "irradiancia_W_m2"] = 0

# Temperatura → interpolação
df["temperatura"] = df["temperatura"].interpolate()

# =========================================================
# 7. VERIFICAÇÃO FINAL
# =========================================================

print("Número de linhas:", len(df))
print("\nNaN após tratamento:")
print(df[["temperatura", "irradiancia_W_m2"]].isna().sum())

# =========================================================
# 8. SALVAR
# =========================================================

df_saida = df[["datetime_local", "temperatura", "irradiancia_W_m2"]]
df_saida.to_csv("dados_tratados.csv", index=False)

# =========================================================
# 9. PLOT ANUAL (COM EIXO AJUSTADO)
# =========================================================

plt.figure()
plt.plot(df_saida["datetime_local"], df_saida["irradiancia_W_m2"])
plt.title("Irradiância (ano)")
plt.grid()

ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

plt.figure()
plt.plot(df_saida["datetime_local"], df_saida["temperatura"])
plt.title("Temperatura (ano)")
plt.grid()

ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# =========================================================
# 10. DIA ALEATÓRIO (EIXO LIMPO)
# =========================================================

df_saida["data"] = df_saida["datetime_local"].dt.date
dia = random.choice(df_saida["data"].unique())

df_dia = df_saida[df_saida["data"] == dia]

print(f"\nDia aleatório: {dia}")

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

# =========================================================
# 11. NASCER E PÔR DO SOL
# =========================================================

df_saida["hora"] = df_saida["datetime_local"].dt.hour + df_saida["datetime_local"].dt.minute/60

nascer = []
por = []

for d, g in df_saida.groupby(df_saida["datetime_local"].dt.date):
    g_sol = g[g["irradiancia_W_m2"] > 0]
    if len(g_sol) > 0:
        nascer.append(g_sol["hora"].iloc[0])
        por.append(g_sol["hora"].iloc[-1])

print("\n===== RESULTADO SOLAR MÉDIO =====")
print(f"Nascer do sol médio: {np.mean(nascer):.2f} h")
print(f"Pôr do sol médio: {np.mean(por):.2f} h")

plt.show()