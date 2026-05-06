import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import configs as cf


#def rodar_simulacao():

# =========================
# CONFIGURAÇÕES
# =========================
MASTER_DSS = cf.DSS_DIR / "Master.dss"

SIMULACAO = 3  # dias ou "full"

HORAS_TOTAL = 8760

if SIMULACAO == "full":
    HORAS = HORAS_TOTAL
else:
    HORAS = int(SIMULACAO) * 24

os.makedirs(cf.FIG_SIMU_DIR, exist_ok=True)

# =========================
# INICIALIZAÇÃO
# =========================
dss.Basic.ClearAll()
dss.Text.Command(f"compile {MASTER_DSS}")

dss.Text.Command("set mode=yearly")
dss.Text.Command(f"set number={HORAS}")
dss.Text.Command("set stepsize=1h")

# =========================
# LISTAS
# =========================
dados_potencia = []
dados_tensao = []
dados_corrente = []
dados_fp = []

bus_names = dss.Circuit.AllBusNames()
element_names = dss.Circuit.AllElementNames()
load_names = dss.Loads.AllNames()

# =========================
# MODELO DE FP POR CARGA
# =========================
fp_parametros = {}

for load in load_names:
    fp_base = np.random.normal(0.92, 0.02)

    fp_min = max(0.85, fp_base - 0.05)
    fp_max = min(0.99, fp_base + 0.05)

    fp_parametros[load] = {
        "base": fp_base,
        "min": fp_min,
        "max": fp_max
    }

# =========================
# PRÉ-PROCESSAMENTO
# =========================
bus_element_map = {}

for bus in bus_names:
    dss.Circuit.SetActiveBus(bus)
    bus_element_map[bus] = dss.Bus.AllPCEatBus()

# =========================
# LOOP TEMPORAL
# =========================
for hora in range(HORAS):

    if hora % 24 == 0:
        print(f"Dia {hora//24 + 1} / {HORAS//24}")

    # -------------------------
    # ATUALIZA FP
    # -------------------------
    for load in load_names:
        dss.Loads.Name(load)

        params = fp_parametros[load]

        fp = np.random.uniform(params["min"], params["max"])
        fp = max(params["min"], min(params["max"], fp))

        dss.Loads.PF(fp)

        dados_fp.append({
            "hora": hora,
            "load": load,
            "fp": fp
        })

    # resolve sistema
    dss.Text.Command("solve")

    # -------------------------
    # POTÊNCIA
    # -------------------------
    for bus in bus_names:
        p_total = 0
        q_total = 0

        for elem in bus_element_map[bus]:
            dss.Circuit.SetActiveElement(elem)
            powers = dss.CktElement.Powers()

            # 🔥 CORREÇÃO IMPORTANTE (sem abs)
            p_total += sum(powers[::2])
            q_total += sum(powers[1::2])

        dados_potencia.append({
            "hora": hora,
            "bus": bus,
            "P_kW": p_total,
            "Q_kvar": q_total
        })

    # -------------------------
    # TENSÃO
    # -------------------------
    for bus in bus_names:
        dss.Circuit.SetActiveBus(bus)
        v_pu = dss.Bus.puVmagAngle()[::2]

        for fase, v in enumerate(v_pu, start=1):
            dados_tensao.append({
                "hora": hora,
                "bus": bus,
                "fase": fase,
                "V_pu": v
            })

    # -------------------------
    # CORRENTE
    # -------------------------
    for elem in element_names:
        dss.Circuit.SetActiveElement(elem)
        correntes = dss.CktElement.CurrentsMagAng()[::2]

        for i, corrente in enumerate(correntes):
            dados_corrente.append({
                "hora": hora,
                "elemento": elem,
                "condutor": i + 1,
                "corrente_A": corrente
            })

# =========================
# DATAFRAMES
# =========================
df_pot = pd.DataFrame(dados_potencia)
df_tensao = pd.DataFrame(dados_tensao)
df_corrente = pd.DataFrame(dados_corrente)
df_fp = pd.DataFrame(dados_fp)

# =========================
# SALVAR
# =========================
df_pot.to_parquet("potencias_barras.parquet", index=False)
df_tensao.to_parquet("tensoes_barras.parquet", index=False)
df_corrente.to_parquet("correntes_elementos.parquet", index=False)
df_fp.to_parquet("fator_potencia.parquet", index=False)

# =========================
# PLOT P e Q (SUBESTAÇÃO)
# =========================
pot_total = df_pot.groupby("hora")[["P_kW", "Q_kvar"]].sum()

plt.figure(figsize=(10,5))
plt.plot(pot_total.index, pot_total["P_kW"], label="P (kW)")
plt.plot(pot_total.index, pot_total["Q_kvar"], label="Q (kvar)")
plt.xlabel("Hora")
plt.ylabel("Potência")
plt.title("Potência Total do Sistema")
plt.legend()
plt.grid()
plt.savefig(cf.FIG_SIMU_DIR / "P_Q_total.png")
plt.show()
plt.close()

# =========================
# FP SUBESTAÇÃO
# =========================
P_total = pot_total["P_kW"]
Q_total = pot_total["Q_kvar"]

S_total = np.sqrt(P_total**2 + Q_total**2)

FP_subestacao = P_total.divide(S_total).replace([np.inf, -np.inf], 0).fillna(0)

plt.figure(figsize=(10,4))
plt.plot(pot_total.index, FP_subestacao)
plt.xlabel("Hora")
plt.ylabel("Fator de Potência")
plt.title("Fator de Potência da Subestação")
plt.grid()
plt.savefig(cf.FIG_SIMU_DIR / "FP_subestacao.png")
plt.show()
plt.close()


#rodar_simulacao()