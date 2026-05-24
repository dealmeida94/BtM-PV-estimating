#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 21 15:28:23 2026

@author: matheus
"""

import opendssdirect as dss
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import time
from pathlib import Path
from auxiliares import calc_tempo 

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

import configs as cfg

# Inicia o timer
begin_timer = time.perf_counter()

#=============================================================
# DETERMINAÇÃO DOS PARÂMETROS DE SIMULAÇÃO
# Local do arquivo Master.dss
MASTER_DSS = cfg.BASE_LOAD / "Master_sem_PV.dss"

# Numero de dias a ser simulado
# Se num_dias = "todos" roda os 365 dias do ano.
num_dias = "todos"

if num_dias == "todos":
    horas = 8760 # 24hrs x 365 dias
else:
    horas = int(num_dias)*24 


# ============================================================
# COMPILA ARQUIVO MASTER
dss.Basic.ClearAll()
dss.Text.Command(f"compile {MASTER_DSS}")

print("Sistema compilado.")

# ============================================================
# ASSOCIA LOADSHAPES AS CARGAS
# Verifica todos os loadshapes lidos no arquivo Master
nomes_loadshapes = set(dss.LoadShape.AllNames())
# Seleciona o primeiro load
dss.Loads.First()

for _ in range(dss.Loads.Count()):
    # Le nome do load
    nome_carga = dss.Loads.Name()
    # Verifica se todos os loads foram carregados corretamente
    #  e associados com o respectivo loadshape.
    try:
        numero = nome_carga.split("_")[1]
        nome_ls = f"load_bus_{numero}"
        
        if nome_ls in nomes_loadshapes:
            dss.Loads.Yearly(nome_ls)
        else:
            print(f"Erro!!! Loadshape '{nome_ls}' não encontrado.")

    except Exception as e:
        print(f"Verifique o load '{nome_carga}' | {e}")

    dss.Loads.Next()

print("Loadshapes associados as cargas.")

# ============================================================
# CONFIGURA PARÂMETROS SIMULAÇÃO
dss.Text.Command("set mode=yearly") # simulação usando loadshapes
dss.Text.Command("set stepsize=1h") # passo de simulação = 1 hora
dss.Text.Command("set number=1")    # roda 1 passo por vez

# ============================================================
# Cria arrays vazios para armazenar valores da simulação.
potencia_kw = np.zeros(horas)
potencia_kvar = np.zeros(horas)
tensao_min = np.zeros(horas)
tensao_max = np.zeros(horas)
fp_subestacao = np.zeros(horas)


# ============================================================
# Determina o intervalo de valores de FP
load_names = dss.Loads.AllNames()
fp_parametros = {}

# Gera, para cada carga, um intervalo de fator de potência aleatório baseado
# em uma distribuição normal (média 0.92, desvio 0.02), limitado entre 0.85 e 0.99,
for load in load_names:
    fp_base = np.random.normal(0.92, 0.02)
    fp_parametros[load] = {
        "min": max(0.85, fp_base - 0.05),
        "max": min(0.99, fp_base + 0.05)
    }


# ============================================================
# LOOP TEMPORAL
for h in range(horas):

    # Atribui a cada carga um valor de FP aleatório 
    # contido dentro do intervalo defindo anteriormente.
    for load in load_names:
        dss.Loads.Name(load)
        params = fp_parametros[load]
        fp = np.random.uniform(params["min"], params["max"])
        dss.Loads.PF(fp)

    # Avança tempo
    dss.Text.Command(f"set hour={h}")
    dss.Text.Command("solve")

    if not dss.Solution.Converged():
        print(f"Simulação não converge na hora {h}")
        continue

    # =========================
    # POTÊNCIA TOTAL 
    p_total, q_total = dss.Circuit.TotalPower()
    
    # O OpenDSS considera positivo (+) a injeção de potência na rede, e 
    # negativo (-) o consumo. Como esta sendo analisado o barramento da subestação,
    # desde que não haja fluxo reverso (das cargas para a subestação) as potências
    # serão sempre negativas.
    # Para facilitar a análise, optou-se por inverter o sinal.
    P = -p_total
    Q = -q_total

    potencia_kw[h] = P
    potencia_kvar[h] = Q

    # =========================
    # Calcula fator de potência na subestação
    S = np.sqrt(P**2 + Q**2)
    fp_subestacao[h] = P / S if S != 0 else 0

    # =========================
    # Verifica as tensões
    tensoes = np.array(dss.Circuit.AllBusMagPu())
    tensao_min[h] = np.min(tensoes)
    tensao_max[h] = np.max(tensoes)

    # A cada mil horas exibe uma amostra dos resultados.
    if h % 1000 == 0:
        print(f"Hora {h} | P = {P:.2f} kW | Q = {Q:.2f} kVA | FP = {fp_subestacao[h]:.3f}")

# ============================================================
# SALVA DATAFRAMES COM RESULTADOS
# Estrutura:
    # - hora: índice temporal (0 até HORAS-1)
    # - P_kW: potência ativa total na subestação (sinal conforme OpenDSS)
    # - Q_kvar: potência reativa total
    # - FP: fator de potência na subestação
    # - Vmin_pu: menor tensão do sistema (pu)
    # - Vmax_pu: maior tensão do sistema (pu)
df = pd.DataFrame({
    "hora": np.arange(horas),
    "P_kW": potencia_kw,
    "Q_kvar": potencia_kvar,
    "FP": fp_subestacao,
    "Vmin_pu": tensao_min,
    "Vmax_pu": tensao_max
})

# Salvar em um arquivo .parquet
df.to_parquet(cfg.RESULTADOS_BASE, index=False)

# ============================================================
# PLOTS
# ============================================================

# # Potência
# plt.figure(figsize=(10,5))
# plt.plot(df["hora"], df["P_kW"], label="P (kW)")
# plt.plot(df["hora"], df["Q_kvar"], label="Q (kvar)")
# plt.legend()
# plt.title("Potência Total do Sistema")
# plt.xlabel("Hora")
# plt.grid()
# plt.show()

# # Fator de potência
# plt.figure(figsize=(10,4))
# plt.plot(df["hora"], df["FP"])
# plt.title("Fator de Potência da Subestação")
# plt.xlabel("Hora")
# plt.ylabel("FP")
# plt.grid()
# plt.show()

# # Tensões
# plt.figure(figsize=(10,4))
# plt.plot(df["hora"], df["Vmin_pu"], label="Vmin")
# plt.plot(df["hora"], df["Vmax_pu"], label="Vmax")
# plt.legend()
# plt.title("Faixa de Tensão")
# plt.xlabel("Hora")
# plt.ylabel("pu")
# plt.grid()
# plt.show()

# End Timer
end_timer = time.perf_counter()
tempo_execucao = calc_tempo(begin_timer, end_timer)
print("\nSimulação concluída.")
print(f"\nTempo de execução: {tempo_execucao}")