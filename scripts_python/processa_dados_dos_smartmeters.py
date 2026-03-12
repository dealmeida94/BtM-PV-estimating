#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 16:32:18 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Este script verifica e padroniza os dados de medições reais do sistema de testes disponibilizado em:
<https://wzy.ece.iastate.edu/Testsystem.html>

    Os dados correspondem a um modelo real de uma rede de distribuição composta por 3 alimentadores,
aos quais estão conectados 1120 consumidores. Todos os consumidores são equipados com smart meters
que registram o consumo horário de energia (kWh). O conjunto de dados disponibilizado corresponde a
1 ano de medições.

    Os alimentadores operam em 13,8 kV, enquanto as cargas estão conectadas no nível secundário de 120/240 V.
    Para preservar a privacidade dos consumidores, as medições dos smart meters são agregadas no nível secundário
dos transformadores de distribuição.

    A rede possui um total de 240 nós (transformador + carga). O sistema inclui componentes típicos de redes de
distribuição, como linhas aéreas, cabos subterrâneos, transformadores de subestação com comutador sob carga (LTC),
chaves de linha, bancos de capacitores e transformadores de distribuição. Também são fornecidas a topologia 
real da rede e os parâmetros dos equipamentos.

Referência:
F. Bu, Y. Yuan, Z. Wang, K. Dehghanpour, and A. Kimber, "A Time-series Distribution Test System based on Real
Utility Data." 2019 North American Power Symposium (NAPS), Wichita, KS, USA, 2019, pp. 1-6.

=====================================================================================================
=====================================================================================================

ENTRADA: smart_meter_data.xlsx
    Planilha com medições dos Smart Meters.
    
SAÍDA: "FeederA_clean.csv", "FeederB_clean.csv" e "FeederC_clean.csv"
    3 planilhas contendo as medições padronizadas e verificadas para cada um dos 3
    alimentadores que compoem a rede.
   
 
"""

import pandas as pd

# Abre o arquivo 'smart_meter_data.xlsx' que contém os dados dos smart meters.
# Este arquivo contém 3 abas, sendo uma para cada um dos três alimentadores
# que constituem a rede teste (Feeder A, Feeder B e Feeder C).
arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados_brutos/smart_meter_data.xlsx"

# Cria uma dicionário associando cada Aba ao nome do arquivo de saída correspondente.
abas = {
    "FeederA_Smart Meter Data": "FeederA_clean.csv",
    "FeederB_Smart Meter Data": "FeederB_clean.csv",
    "FeederC_Smart Meter Data": "FeederC_clean.csv"
}

# Implementa uma lista para armazenar o resultado das
# verificações.
relatorio = []

# Dicionário para armazenar os dataframes processados
dataframes_processados = {}

for aba, nome_do_arquivo in abas.items():

    # Copia planilha para o dataframe df
    df = pd.read_excel(
        arquivo,
        sheet_name=aba,
        header=0 
    )

    # Renomeia primeira coluna como "Time".
    df.rename(columns={df.columns[0]: "Time"}, inplace=True)

    # Converte os valores da coluna "Time" para datetime.
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

    # Nos valores das medições, substitui a virgula ',' por '.' ponto.
    for col in df.columns[1:]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )


    ##############################################
    ##############################################
    
    # Verifica o dataframe

    # Verifica a existencia de valores NaN.
    possui_nan = df.isna().any().any()
    # Verifica o número de linhas.
    linhas = len(df)
    # Verifica a existência de datas duplicadas.
    duplicados = df["Time"].duplicated().sum()
    # Verifica a existência de valores nulos.
    nulos = df.isna().sum().sum()

    # Anexa os resultados das verificações a lista 'relatorio'.
    relatorio.append({
        "Planilha": aba,
        "nº linhas": linhas,
        "nº linhas = 8760": "OK" if linhas == 8760 else "ERRO",
        "Datas duplicadas": duplicados,
        "Valores nulos": nulos,
        "Possui NaN": "Sim" if possui_nan else "Não"
    })

    # Salvar planilhas
    caminho_do_arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/" + nome_do_arquivo
    df.to_csv(caminho_do_arquivo, index=False)

    # Salvar dataframe
    dataframes_processados[aba] = df


print("\nProcessamento concluído.\n")

tabela = pd.DataFrame(relatorio)

print("Verificações:\n")
print(tabela.to_string(index=False))

#%%
import matplotlib.pyplot as plt

# caminhos dos arquivos
feeders = {
    "FeederA": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv",
    "FeederB": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederB_clean.csv",
    "FeederC": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederC_clean.csv"
}

pot_feeders = {}

# leitura e soma dos buses
for nome, caminho in feeders.items():
    
    df = pd.read_csv(caminho)

    # ignora a primeira coluna (data)
    potencia = df.iloc[:,1:]

    # soma todos os buses
    pot_total = potencia.sum(axis=1)

    pot_feeders[nome] = pot_total


# soma total dos feeders
pot_total_rede = sum(pot_feeders.values())


# criação dos gráficos
plt.figure(figsize=(10,12))

for i, (nome, pot) in enumerate(pot_feeders.items(), start=1):

    plt.subplot(4,1,i)
    plt.plot(pot)
    plt.title(f"Potência {nome}")
    plt.ylabel("kW")
    plt.grid(True)


# gráfico total
plt.subplot(4,1,4)
plt.plot(pot_total_rede)
plt.title("Potência Total da Rede")
plt.ylabel("kW")
plt.xlabel("Tempo")
plt.grid(True)

plt.tight_layout()
plt.show()