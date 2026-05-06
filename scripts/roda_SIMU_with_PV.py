#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import configs as cf

# =========================
# CONFIGURAÇÕES
# =========================
MASTER_DSS = "/home/matheus/Documentos/BtM-PV-estimating/dss/Master_withPV.dss"

SIMULACAO = 3
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

print("PVs encontrados:")
print([e for e in dss.Circuit.AllElementNames() if "pvsystem" in e.lower()])

dss.Text.Command("set maxcontroliter=100")

# 🔥 configuração temporal
dss.Text.Command("set mode=yearly")
dss.Text.Command("set stepsize=1h")
dss.Text.Command("set number=1")

print("Loadshapes:", dss.LoadShape.AllNames())
dss.LoadShape.Name("PVShape")
print(dss.LoadShape.PMult()[:24])

# =========================
# LISTAS
# =========================
dados_potencia = []
dados_tensao = []
dados_corrente = []
dados_fp = []
dados_pv = []
dados_subestacao = []

bus_names = dss.Circuit.AllBusNames()
element_names = dss.Circuit.AllElementNames()
load_names = dss.Loads.AllNames()

# =========================
# MODELO DE FP
# =========================
fp_parametros = {}

for load in load_names:
    fp_base = np.random.normal(0.92, 0.02)

    fp_parametros[load] = {
        "min": max(0.85, fp_base - 0.05),
        "max": min(0.99, fp_base + 0.05)
    }

# =========================
# MAPA BUS
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

    dss.Solution.Hour(hora)

    # -------------------------
    # ATUALIZA FP DAS CARGAS
    # -------------------------
    for load in load_names:
        dss.Loads.Name(load)

        params = fp_parametros[load]
        fp = np.random.uniform(params["min"], params["max"])

        dss.Loads.PF(fp)

        dados_fp.append({
            "hora": hora,
            "load": load,
            "fp": fp
        })

    dss.Solution.Solve()

    # =========================
    # POTÊNCIA PV
    # =========================
    p_pv_total = 0
    q_pv_total = 0

    for pv in dss.PVsystems.AllNames():
        dss.PVsystems.Name(pv)

        p_pv_total += dss.PVsystems.kW()
        q_pv_total += dss.PVsystems.kvar()

    dados_pv.append({
        "hora": hora,
        "P_pv_kW": abs(p_pv_total),
        "Q_pv_kvar": q_pv_total
    })

    # -------------------------
    # POTÊNCIA TOTAL POR BUS
    # -------------------------
    for bus in bus_names:
        p_total = 0
        q_total = 0

        for elem in bus_element_map[bus]:
            dss.Circuit.SetActiveElement(elem)
            powers = dss.CktElement.Powers()

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
    # 🔥 POTÊNCIA NA SUBESTAÇÃO (CORRIGIDO)
    # =========================

    P_sub, Q_sub = dss.Circuit.TotalPower()

    S_sub = (P_sub**2 + Q_sub**2) ** 0.5
    fp_sub = P_sub / S_sub if S_sub != 0 else 0

    dados_subestacao.append({
        "hora": hora,
        "P_sub": P_sub,
        "Q_sub": Q_sub,
        "FP_sub": fp_sub
    })

# =========================
# DATAFRAMES
# =========================
df_pot = pd.DataFrame(dados_potencia)
df_tensao = pd.DataFrame(dados_tensao)
df_corrente = pd.DataFrame(dados_corrente)
df_fp = pd.DataFrame(dados_fp)
df_pv = pd.DataFrame(dados_pv)
df_sub = pd.DataFrame(dados_subestacao)

# =========================
# PLOT PV
# =========================
plt.figure(figsize=(10,5))
plt.plot(df_pv["hora"], df_pv["P_pv_kW"], label="PV (kW)")
plt.xlabel("Hora")
plt.ylabel("Potência PV (kW)")
plt.title("Geração Fotovoltaica Total")
plt.legend()
plt.grid()
plt.show()

# =========================
# PLOT SUBESTAÇÃO (AGORA CORRETO)
# =========================
plt.figure(figsize=(10,5))
plt.plot(df_sub["hora"], df_sub["P_sub"], label="P_sub (kW)")
plt.plot(df_sub["hora"], df_sub["Q_sub"], label="Q_sub (kvar)")

plt.xlabel("Hora")
plt.ylabel("Potência")
plt.title("Potência na Subestação")
plt.legend()
plt.grid()

plt.savefig(cf.FIG_SIMU_DIR / "subestacao.png")
plt.show()
plt.close()

# =========================
# FP SUBESTAÇÃO
# =========================
plt.figure(figsize=(10,5))
plt.plot(df_sub["hora"], df_sub["FP_sub"], label="FP Subestação")

plt.xlabel("Hora")
plt.ylabel("Fator de Potência")
plt.title("FP na Subestação")
plt.legend()
plt.grid()

plt.show()

#%%
# =========================
# PLOT COM DUAS ESCALAS
# =========================

fig, ax1 = plt.subplots(figsize=(10,5))

# eixo 1 → subestação
ax1.plot(df_sub["hora"], -df_sub["P_sub"], label="Subestação (kW)")
ax1.set_xlabel("Hora")
ax1.set_ylabel("Potência Subestação (kW)")
ax1.grid()

# eixo 2 → PV
ax2 = ax1.twinx()
ax2.plot(df_pv["hora"], df_pv["P_pv_kW"], linestyle="--", label="PV (kW)")
ax2.set_ylabel("Geração PV (kW)")

# legenda combinada
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()

ax1.legend(lines_1 + lines_2, labels_1 + labels_2)

plt.title("Comparação: Subestação vs Geração PV (Escalas Separadas)")

plt.show()