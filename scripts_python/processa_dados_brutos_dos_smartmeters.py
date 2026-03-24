#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

"""
    Este script verifica e padroniza os dados de medições reais do sistema de testes disponibilizado em:
    <https://wzy.ece.iastate.edu/Testsystem.html>

    O sistema inclui componentes típicos de redes de distribuição, como linhas aéreas, cabos subterrâneos,
    transformadores de subestação com comutador sob carga (LTC), chaves de linha, bancos de capacitores e
    transformadores de distribuição. Também são fornecidas a topologia real da rede e os parâmetros dos equipamentos.
    
    Os dados correspondem a um modelo real de uma rede de distribuição composta por 3 alimentadores,
    aos quais estão conectados 1120 consumidores. Todos os consumidores são equipados com smart meters
    que registram o consumo horário de energia (kWh). O conjunto de dados disponibilizado corresponde a
    1 ano de medições.

    Os alimentadores operam em 13,8 kV, enquanto as cargas estão conectadas no nível secundário de 120/240 V.
    Os três alimentadores derivam de um mesmo barramento da subestação distribuidora. Para preservar a
    privacidade dos consumidores, as medições dos smart meters são agregadas no nível secundário
    dos transformadores de distribuição, formando um nó (bus). Ao todo, o sistema possui 240 nós (buses).

    A potência reativa da rede foi determinada atribuindo-se aos nós (buses) fatores de potência aleatórios,
    no intervalo de 0,9 a 0,95. A metodologia de cálculo utilizada está presente na própria planilha de dados
    disponibilizada pelos autores. 

Referência:
F. Bu, Y. Yuan, Z. Wang, K. Dehghanpour, and A. Kimber, "A Time-series Distribution Test System based on Real
Utility Data." 2019 North American Power Symposium (NAPS), Wichita, KS, USA, 2019, pp. 1-6.

=====================================================================================================

DADOS DE ENTRADA:
    + "Calculated Nodal P&Q.xlsx" --> Planilha contendo os valores originais de potência ativa medidos e 
                                    potência reativa calculada, fornecida pelos autores.
    
DADOS DE SAÍDA:
    + "dados_processados.xlsx" --> Planilha gerada após tratamento dos dados da planilha de entrada.
    + breve relatório dos dados
    + gráficos
          
"""

###############################################################################################################
###############################################################################################################
# 1. INICIO - DEFINIÇÕES DOS DADOS DE ENTRADA E SAÍDA:
# 
# Determina caminho para planilha com dados dos smart meters
# Obs.: A planilha contém 6 abas, sendo 2 abas para cada alimentador (uma com as medições de potência ativa,
# e outra com as potências reativas), nomeadas conforme abaixo:
#                        --> FeederA_P
#                        --> FeederA_Q
#                        --> FeederB_P
#                        --> FeederB_Q
#                        --> FeederC_P
#                        --> FeederC_Q

# Caminho para planilha dos dados de entrada
planilha_dados_brutos = "/home/matheus/Documentos/BtM-PV-estimating/dados_brutos/Calculated Nodal P&Q.xlsx"

# Caminho para salvar os dados de saída:
caminho_salvar_planilha = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/"
caminho_salvar_figuras = "/home/matheus/Documentos/BtM-PV-estimating/resultados/processamento_dos_dados_brutos/"

###############################################################################################################
# 3. ETAPA DE PROCESSAMENTO

feeders = ["FeederA", "FeederB", "FeederC"]

relatorio = []
dataframes_processados = {}

for feeder in feeders:

    aba_P = f"{feeder}_P"
    aba_Q = f"{feeder}_Q"
    
    # Carrega tabelas de potência ativa
    df_P = pd.read_excel(planilha_dados_brutos, sheet_name=aba_P)
    # Carrega tabelas de potência reativa
    df_Q = pd.read_excel(planilha_dados_brutos, sheet_name=aba_Q)

    # Renomeia primeira coluna que contém data e hora para "Time"
    df_P.rename(columns={df_P.columns[0]: "Time"}, inplace=True)
    df_Q.rename(columns={df_Q.columns[0]: "Time"}, inplace=True)

    # Converte os valores da coluna "Time" para formato datetime
    df_P["Time"] = pd.to_datetime(df_P["Time"], errors="coerce")
    df_Q["Time"] = pd.to_datetime(df_Q["Time"], errors="coerce")
    
    # Cópia todos os dados exceto os da coluna "Time"
    colunas_P = [c for c in df_P.columns if c != "Time"]
    colunas_Q = [c for c in df_Q.columns if c != "Time"]
    
    # Converte os dados para o tipo numérico
    df_P[colunas_P] = df_P[colunas_P].apply(pd.to_numeric, errors="coerce")
    df_Q[colunas_Q] = df_Q[colunas_Q].apply(pd.to_numeric, errors="coerce")
    
    # Converte os valores em arrays numpy
    P = df_P[colunas_P].to_numpy()
    Q = df_Q[colunas_Q].to_numpy()
    
    # Calcula potência aparente
    S = np.sqrt(P**2 + Q**2)
    
    # Calcula fator de potência (FP)
    FP = np.divide(P, S, out=np.zeros_like(P), where=S!=0)
    
    # Cria dataframe com (FP) calculado, utiliza os mesmos cabeçarios do
    # df_P
    df_FP = pd.DataFrame(FP, columns=colunas_P)
    
    # Adiciona ao df_FP a coluna de tempo
    df_FP.insert(0, "Time", df_P["Time"].values)
    
    
    #**************************************************************************
    # Realiza uma série de verificações
    
    # Copia todos os dados exceto os da coluna "Time"
    colunas_FP = [c for c in df_FP.columns if c != "Time"]
    
    # Inicializa variáveis auxiliares
    igual_colunas = True
    igual_cabecalhos = True
    igual_datas = True
    igual_linhas = True
    
    # Verifica se os dataframes possuem o mesmo número de colunas
    if not (len(colunas_P) == len(colunas_Q) == len(colunas_FP)):
        print (f"\nAS PLANILHAS P, Q E FP DO {feeder} NÃO POSSUEM O MESMO Nº DE COLUNAS")
        print ("\nNECESSÁRIO VERIFICAR")
        igual_colunas = False
    
    # Verifica se os dataframes possuem os mesmos cabeçalhos
    if not (set(colunas_P) == set(colunas_Q) == set(colunas_FP)):
        print (f"\nAS PLANILHAS P, Q E FP DO {feeder} NÃO POSSUEM OS MESMOS CABEÇALHOS")
        print ("\nNECESSÁRIO VERIFICAR")
        igual_cabecalhos = False
    
    # Verifica se os dataframes possuem o mesmo número de linhas
    if not (len(df_P) == len(df_Q) == len(df_FP)):
        print (f"\nAS PLANILHAS P, Q E FP DO {feeder} POSSUEM DIFERENTES NÚMEROS DE LINHAS")
        print ("\nNECESSÁRIO VERIFICAR")
        igual_linhas = False
    
    # Verifica se os dataframes possuem as mesmas datas
    if not df_P["Time"].equals(df_Q["Time"]) and df_P["Time"].equals(df_FP["Time"]):
        print (f"\nAS DATAS DAS PLANILHAS P, Q E FP DO {feeder} NÃO POSSUEM AS MESMAS DATAS")
        print ("\nNECESSÁRIO VERIFICAR")
        igual_datas = False

    # Verifica se os dataframes possuem valores que são NaN (Not-a-Number)
    resultado_NaN_P = df_P.isna().any().any()
    resultado_NaN_Q = df_Q.isna().any().any()
    resultado_NaN_FP = df_FP.isna().any().any()

    # Agrupa dataframes
    dataframes_processados[f"{feeder}_P"] = df_P
    dataframes_processados[f"{feeder}_Q"] = df_Q
    dataframes_processados[f"{feeder}_FP"] = df_FP

    # -------------------------
    # RELATÓRIO
    # -------------------------
    relatorio.append({
        "|Feeder|": feeder,
        "|nº de linhas|": len(df_P),
        "|DFs com mesmo nº de linhas?|": "sim   " if igual_linhas == True else "não",
        "|DFs com mesmo nº de colunas?|": "sim   " if igual_colunas == True else "não",
        "|Mesmos cabeçalhos?|": "sim   " if igual_cabecalhos == True else "não",
        "|Mesmas datas|": "sim  " if igual_datas == True else "não",
        "|df_P possui NaN?|": "Sim   " if resultado_NaN_P else "Não",
        "|df_Q possui NaN?|": "Sim   " if resultado_NaN_Q else "Não",
        "|df_FP possui NaN?|": "Sim   " if resultado_NaN_FP else "Não",
    })

# Transforma dicionário relatório em dataframe    
df_relatorio = pd.DataFrame(relatorio)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(df_relatorio)  

#**************************************************************************
# Salva os dataframes gerados
with pd.ExcelWriter(caminho_salvar_planilha + "dados_processados.xlsx") as writer:
   
    for nome_aba, df in dataframes_processados.items():
        df.to_excel(writer, sheet_name=nome_aba, index=False)

    df_relatorio.to_excel(writer, sheet_name="Relatorio", index=False)


###############################################################################################################
# 4. CALCULA POTÊNCIA POR ALIMENTADOR E TOTAL

# Calcula da potência por alimentador
P_feeders = {}
Q_feeders = {}

for feeder in feeders:

    df_P = dataframes_processados[f"{feeder}_P"]
    df_Q = dataframes_processados[f"{feeder}_Q"]

    colunas_P = [c for c in df_P.columns if c != "Time"]
    colunas_Q = [c for c in df_Q.columns if c != "Time"]
    
    # Soma os dados horizontalmente
    P_total = df_P[colunas_P].sum(axis=1)
    Q_total = df_Q[colunas_Q].sum(axis=1)

    P_feeders[feeder] = P_total
    Q_feeders[feeder] = Q_total

# Potência total = absorvido da subestação
P_total_rede = sum(P_feeders.values())
Q_total_rede = sum(Q_feeders.values())
S_total_rede = np.sqrt(P_total_rede**2 + Q_total_rede**2)
FP_total_rede = P_total_rede.divide(S_total_rede).replace([np.inf, -np.inf], 0).fillna(0)


###############################################################################################################
# 4. CALCULA POTÊNCIA POR ALIMENTADOR E TOTAL

# Determina o intervalo da plotagem
FP_min, FP_max = 0.85, 1.0
# Copia apenas as datas
tempo = df_P["Time"].values

# Plota potências na subestação
plt.figure(figsize=(10,5))
plt.plot(tempo, P_total_rede, label="P")
plt.plot(tempo,Q_total_rede, label="Q")
plt.title("Subestação - P(kW) & Q(kVAr) ")
plt.legend()
plt.grid()
plt.savefig(caminho_salvar_figuras + f"{feeder}_P_Q.png")
plt.show()
plt.close()

# Plota FP na subestação
plt.figure(figsize=(10,4))
plt.plot(tempo, FP_total_rede, label="FP")
plt.ylim(FP_min, FP_max)
plt.title("Subestação - FP")
plt.grid()
plt.savefig(caminho_salvar_figuras + f"{feeder}_FP.png")
plt.show()
plt.close()

# Plota potências e FP por alimentador 
for feeder in feeders:

    P = P_feeders[feeder]
    Q = Q_feeders[feeder]
    S = np.sqrt(P**2 + Q**2)
    FP = P.divide(S).replace([np.inf, -np.inf], 0).fillna(0)

    # Plota potências
    plt.figure(figsize=(10,5))
    plt.plot(tempo, P, label="P")
    plt.plot(tempo, Q, label="Q")
    plt.title(f"{feeder} - P(kW) & Q(kVAr)")
    plt.legend()
    plt.grid()
    plt.savefig(caminho_salvar_figuras + f"{feeder}_P_Q.png")
    plt.show()
    plt.close()

    plt.figure(figsize=(10,4))
    plt.plot(tempo,FP)
    plt.ylim(FP_min, FP_max)
    plt.title(f"{feeder} - FP")
    plt.grid()
    plt.savefig(caminho_salvar_figuras + f"{feeder}_FP.png")
    plt.show()
    plt.close()

# Plota um ou mais dias específicos
# Pode-se optar por escolher dias especícos ou determinar os dias aleatoriamente
# No caso de dias especificos, a variavel dia deve ser uma lista:
    # dias = [2, 150, 220]

# Número de dias aleatórios que deve ser plotado    
num_de_dias = 1
# Gera dias aleatoriamente
dias = np.random.randint(0, 365, num_de_dias)

for dia in dias:
    for feeder in feeders:
    
        P = P_feeders[feeder]
        Q = Q_feeders[feeder]
        S = np.sqrt(P**2 + Q**2)
        FP = P.divide(S).replace([np.inf, -np.inf], 0).fillna(0)
    
        inicio = dia * 24
        fim = inicio + 24
    
        horas = range(24)
        
        data = pd.to_datetime(tempo[dia])
    
        plt.figure(figsize=(10,5))
        plt.plot(horas, P.iloc[inicio:fim])
        plt.plot(horas, Q.iloc[inicio:fim])
        plt.title(f"{feeder} - P&Q Dia {data.strftime('%d/%m/%Y')} ({dia}º dia)")
        plt.grid()
        plt.savefig(caminho_salvar_figuras + f"{feeder}_P_Q_dia_{dia}.png")
        plt.show()
        plt.close()
    
        plt.figure(figsize=(10,5))
        plt.plot(horas, FP.iloc[inicio:fim])
        plt.title(f"{feeder} - FP Dia {data.strftime('%d/%m/%Y')} ({dia}º dia)")
        plt.grid()
        plt.savefig(caminho_salvar_figuras + f"{feeder}_FP_dia_{dia}.png")
        plt.show()
        plt.close()
        
    # Plota potências na subestação
    plt.figure(figsize=(10,5))
    plt.plot(horas, P_total_rede.iloc[inicio:fim], label="P")
    plt.plot(horas,Q_total_rede.iloc[inicio:fim], label="Q")
    plt.title(f"Subestação - P&Q Dia {data.strftime('%d/%m/%Y')} ({dia}º dia)")
    plt.legend()
    plt.grid()
    plt.savefig(caminho_salvar_figuras + f"Subestacao_P_Q_dia_{dia}.png")
    plt.show()
    plt.close()
        
    # Plota FP na subestação
    plt.figure(figsize=(10,4))
    plt.plot(horas, FP_total_rede.iloc[inicio:fim], label="FP")
    plt.ylim(FP_min, FP_max)
    plt.title(f"Subestação - FP Dia {data.strftime('%d/%m/%Y')} ({dia}º dia)")
    plt.grid()
    plt.savefig(caminho_salvar_figuras + f"Subestacao_FP_dia_{dia}.png")
    plt.show()
    plt.close()


###############################################################################################################
# FIM
print(f"\nPlanilha salva em: {caminho_salvar_planilha}")
print(f"\nGráficos salvos em: {caminho_salvar_figuras}")
print("\nProcessamento concluído")

