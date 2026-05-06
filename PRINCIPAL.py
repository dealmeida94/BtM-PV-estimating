# -*- coding: utf-8 -*-
"""
Editor Spyder

Este é um arquivo de script temporário.
"""
import os
import sys
import time

import scripts.pre_processamento.processa_medicoes as pm
import scripts.pre_processamento.gera_loadshapes as loadshapes
import scripts.pre_processamento.extrair_dados_do_Load_dss as leload 
import scripts.pre_processamento.gera_arquivo_Load_dss as gLoad
import scripts.pre_processamento.gera_master_dss as gMaster
import scripts.RODA_SIMULACAO as run_dss

sys.path.append('/home/matheus/Documentos/BtM-PV-estimating')
#%%
def print_tempo (start, end):
    tempo = end - start
    horas = int(tempo // 3600)
    minutos = int((tempo % 3600) // 60)
    segundos = tempo % 60
    print(f"Tempo de execução: {horas:02d}h:{minutos:02d}m:{segundos:.0f}s ")  
#%%

os.system('clear')

start_timer = time.perf_counter()
pm.processa_medicoes ()
end_timer = time.perf_counter()
print_tempo(start_timer, end_timer)


start_timer = time.perf_counter()
loadshapes.gera_loadshapes()
end_timer = time.perf_counter()
print_tempo(start_timer, end_timer)

#%%
start_timer = time.perf_counter()
leload.le_load_dss()
end_timer = time.perf_counter()
print_tempo(start_timer, end_timer)

#%%
start_timer = time.perf_counter()
gLoad.gerar_loaddss()
end_timer = time.perf_counter()
print_tempo(start_timer, end_timer)

#%%
start_timer = time.perf_counter()
gMaster.gerarMaster()
end_timer = time.perf_counter()
print_tempo(start_timer, end_timer)

#%%
start_timer = time.perf_counter()
run_dss.rodar_simulacao()
end_timer = time.perf_counter()
print_tempo(start_timer, end_timer)
