#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 21 15:28:23 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opendssdirect as dss
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

import configs as cfg

# ============================================================
# CONFIGURAÇÕES
# ============================================================

MASTER_DSS = cfg.BASE_LOAD / "Master_sem_PV.dss"

SIMULACAO = "full"   # "full" ou número de dias (ex: 3)

HORAS_TOTAL = 8760

if SIMULACAO == "full":
    HORAS = HORAS_TOTAL
else:
    HORAS = int(SIMULACAO) * 24

# Ativar variação de FP das cargas?
VARIAR_FP = False   # 🔥 coloque True se quiser usar o modelo aleatório

# ============================================================
# INICIALIZAÇÃO
# ============================================================

dss.Basic.ClearAll()
dss.Text.Command(f"compile {MASTER_DSS}")

print("Sistema compilado com sucesso!")

# ============================================================
# ASSOCIA LOADSHAPES CORRETAMENTE
# ============================================================

nomes_loadshapes = set(dss.LoadShape.AllNames())

dss.Loads.First()

for _ in range(dss.Loads.Count()):
    
    nome_carga = dss.Loads.Name()
    
    try:
        numero = nome_carga.split("_")[1]
        nome_ls = f"load_bus_{numero}"
        
        if nome_ls in nomes_loadshapes:
            dss.Loads.Yearly(nome_ls)
        else:
            print(f"❌ Loadshape não encontrado: {nome_ls}")

    except Exception as e:
        print(f"⚠️ Problema com carga: {nome_carga} | {e}")

    dss.Loads.Next()

print("Loadshapes conectados!")

# ============================================================
# CONFIGURA SIMULAÇÃO
# ============================================================

dss.Text.Command("set mode=yearly")
dss.Text.Command("set stepsize=1h")
dss.Text.Command("set number=1")

# ============================================================
# MODELO DE FP (OPCIONAL)
# ============================================================

load_names = dss.Loads.AllNames()
fp_parametros = {}

if VARIAR_FP:
    for load in load_names:
        fp_base = np.random.normal(0.92, 0.02)
        fp_parametros[load] = {
            "min": max(0.85, fp_base - 0.05),
            "max": min(0.99, fp_base + 0.05)
        }

# ============================================================
# ARRAYS
# ============================================================

potencia_kw = np.zeros(HORAS)
potencia_kvar = np.zeros(HORAS)
tensao_min = np.zeros(HORAS)
tensao_max = np.zeros(HORAS)
fp_subestacao = np.zeros(HORAS)

# ============================================================
# LOOP TEMPORAL
# ============================================================

inicio = time.time()

for h in range(HORAS):

    # Atualiza FP das cargas (se ativado)
    if VARIAR_FP:
        for load in load_names:
            dss.Loads.Name(load)
            params = fp_parametros[load]
            fp = np.random.uniform(params["min"], params["max"])
            dss.Loads.PF(fp)

    # Avança tempo
    dss.Text.Command(f"set hour={h}")
    dss.Text.Command("solve")

    if not dss.Solution.Converged():
        print(f"⚠️ Não convergiu na hora {h}")
        continue

    # =========================
    # POTÊNCIA TOTAL (CORRETO)
    # =========================
    p_total, q_total = dss.Circuit.TotalPower()

    # Corrige sinal do OpenDSS
    P = -p_total
    Q = -q_total

    potencia_kw[h] = P
    potencia_kvar[h] = Q

    # =========================
    # FATOR DE POTÊNCIA
    # =========================
    S = np.sqrt(P**2 + Q**2)
    fp_subestacao[h] = P / S if S != 0 else 0

    # =========================
    # TENSÃO
    # =========================
    tensoes = np.array(dss.Circuit.AllBusMagPu())
    tensao_min[h] = np.min(tensoes)
    tensao_max[h] = np.max(tensoes)

    # Debug leve
    if h % 1000 == 0:
        print(f"Hora {h} | P = {P:.2f} kW | FP = {fp_subestacao[h]:.3f}")

fim = time.time()

print(f"\nSimulação concluída em {fim - inicio:.2f} s")

# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame({
    "hora": np.arange(HORAS),
    "P_kW": potencia_kw,
    "Q_kvar": potencia_kvar,
    "FP": fp_subestacao,
    "Vmin_pu": tensao_min,
    "Vmax_pu": tensao_max
})

# Salvar se quiser
# df.to_parquet(cfg.RESULTADOS, index=False)

# ============================================================
# PLOTS
# ============================================================

# Potência
plt.figure(figsize=(10,5))
plt.plot(df["hora"], df["P_kW"], label="P (kW)")
plt.plot(df["hora"], df["Q_kvar"], label="Q (kvar)")
plt.legend()
plt.title("Potência Total do Sistema")
plt.xlabel("Hora")
plt.grid()
plt.show()

# Fator de potência
plt.figure(figsize=(10,4))
plt.plot(df["hora"], df["FP"])
plt.title("Fator de Potência da Subestação")
plt.xlabel("Hora")
plt.ylabel("FP")
plt.grid()
plt.show()

# Tensões
plt.figure(figsize=(10,4))
plt.plot(df["hora"], df["Vmin_pu"], label="Vmin")
plt.plot(df["hora"], df["Vmax_pu"], label="Vmax")
plt.legend()
plt.title("Faixa de Tensão")
plt.xlabel("Hora")
plt.ylabel("pu")
plt.grid()
plt.show()