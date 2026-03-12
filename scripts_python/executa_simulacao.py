#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opendssdirect as dss
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import os

# Define diretório base do projeto
base_path = "/home/matheus/Documentos/BtM-PV-estimating"

# Muda o diretório de execução
os.chdir(base_path)

print("Diretório atual:", os.getcwd())

dss.Text.Command("Clear")
dss.Text.Command("Compile /home/matheus/Documentos/BtM-PV-estimating/scripts_python/Master_Base.dss")

# ============================================================
# 1) COMPILA O SISTEMA
# ============================================================

dss.Text.Command("Clear")
dss.Text.Command("Compile /home/matheus/Documentos/BtM-PV-estimating/scripts_python/Master_Base.dss")

print("Sistema compilado com sucesso!")

#%%
# ============================================================
# CONECTA LOADSHAPES ÀS CARGAS
# ============================================================

dss.Loads.First()

for _ in range(dss.Loads.Count()):
    
    nome_carga = dss.Loads.Name()      # ex: load_1003
    
    numero = nome_carga.split("_")[1]  # pega 1003
    
    nome_ls = f"LS_Bus{numero}"        # monta nome do loadshape
    
    dss.Loads.Yearly(nome_ls)          # associa
    
    dss.Loads.Next()

print("Loadshapes conectados com sucesso!")

# ============================================================
# 2) DIAGNÓSTICO RÁPIDO DO MODELO
# ============================================================

print("\n--- DIAGNÓSTICO DO MODELO ---")
print("Número de cargas:", dss.Loads.Count())
print("Número de loadshapes:", dss.LoadShape.Count())

if dss.LoadShape.Count() > 0:
    dss.LoadShape.First()
    print("Primeiro Loadshape:", dss.LoadShape.Name())
    print("Número de pontos:", dss.LoadShape.Npts())

print("-----------------------------\n")

# ============================================================
# 3) CONFIGURA SIMULAÇÃO TIME-SERIES (CONTROLADO PELO PYTHON)
# ============================================================

dss.Text.Command("Set mode=yearly")
dss.Text.Command("Set stepsize=1h")
dss.Text.Command("Set number=1")

n_horas = 8760

# ============================================================
# 4) ARRAYS PARA RESULTADOS
# ============================================================

potencia_kw = np.zeros(n_horas)
potencia_kvar = np.zeros(n_horas)
tensao_min = np.zeros(n_horas)
tensao_max = np.zeros(n_horas)

# ============================================================
# 5) LOOP ANUAL (QSTS)
# ============================================================

inicio = time.time()

for h in range(n_horas):

    dss.Text.Command(f"Set hour={h}")
    dss.Solution.Solve()

    if not dss.Solution.Converged():
        print(f"Não convergiu na hora {h}")
        continue

    # Potência total do sistema (subestação equivalente)
    p_total, q_total = dss.Circuit.TotalPower()

    # Corrige sinal (OpenDSS retorna negativo para carga)
    potencia_kw[h] = -p_total
    potencia_kvar[h] = -q_total

    # Tensões pu
    tensoes = np.array(dss.Circuit.AllBusMagPu())
    tensao_min[h] = np.min(tensoes)
    tensao_max[h] = np.max(tensoes)

fim = time.time()

print(f"\nSimulação concluída em {fim - inicio:.2f} segundos")

# ============================================================
# 6) SALVA RESULTADOS
# ============================================================

df = pd.DataFrame({
    "Hora": np.arange(n_horas),
    "P_kW": potencia_kw,
    "Q_kvar": potencia_kvar,
    "Vmin_pu": tensao_min,
    "Vmax_pu": tensao_max
})

df.to_csv("resultado_time_series.csv", index=False)

print("Resultados salvos em resultado_time_series.csv")

# ============================================================
# 7) PLOTS
# ============================================================

plt.figure()
plt.plot(potencia_kw)
plt.title("Potência Total do Alimentador (kW)")
plt.xlabel("Hora")
plt.ylabel("kW")
plt.grid()
plt.show()

plt.figure()
plt.plot(tensao_min, label="Vmin")
plt.plot(tensao_max, label="Vmax")
plt.legend()
plt.title("Faixa de Tensão (pu)")
plt.xlabel("Hora")
plt.ylabel("pu")
plt.grid()
plt.show()