#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Este script realiza uma leitura da planilha "dados_processados.xlsx", e gera
arquivos com loadshapes de P e Q, com valores em p.u (normalizado por unidade).

Etapas do processo:
    1. Leitura dos dados
    2. Eliminação de cargas nulas
    3. Para cada bus, adota o valor máximo de potência como valor de base
    4. Realiza a normalização dos valores em cada bus
    5. Salva loadshapes em arquivos .txt
    6. Gera arquivo definindo os loadshapes para uso no openDSS
    7. Salva os valores bases em uma planilha .xlsx
    
ENTRADAS:
    + dados_processados.xlsx
              |- abas: FeederA_P, FeederA_Q, FeederA_FP,
                       FeederB_P, FeederB_Q, FeederB_FP,
                       FeederC_P, FeederC_Q, FeederC_FP,
                     
SAÍDAS:
    + Arquivo .txt com loadshape para cada bus
    + Arquivo Loadshape.dss para cada alimentador
    + Planilha com valores de base
    
'''

import pandas as pd

# CAMINHOS PARA ARQUIVOS DE ENTRADA E SAÍDA
# Caminho para planilha "dados_processados.xlsx"
dados = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/dados_processados.xlsx"

# Caminho para salvar arquivos de saída
local_saida = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"

# Função que realiza o processamento por feeder
def processar_feeder(feeder):

    # 1. Leitura dos dados
    df_P = pd.read_excel(dados, sheet_name=f"{feeder}_P")
    df_Q = pd.read_excel(dados, sheet_name=f"{feeder}_Q")

    # Remove coluna "Time"
    for col in df_P.columns:
        if str(col) == "Time":
            df_P = df_P.drop(columns=[col])

    for col in df_Q.columns:
        if str(col) == "Time":
            df_Q = df_Q.drop(columns=[col])

    # Todos os dados convertidos para tipo numérico
    df_P = df_P.apply(pd.to_numeric, errors="coerce")
    df_Q = df_Q.apply(pd.to_numeric, errors="coerce")

    # 2. Elimina cargas nulas
    df_P = df_P.loc[:, (df_P != 0).any(axis=0)]
    df_Q = df_Q.loc[:, (df_Q != 0).any(axis=0)]

    # Cria dataframe para salvar valores de base
    df_base = pd.DataFrame(columns=["Bus", "P_base", "Q_base"])

    linhas_dss = []

    for bus in df_P.columns:

        serie_P = df_P[bus]
        serie_Q = df_Q[bus]

        # 3. Determina o valor máximo da serie como valor de base
        P_base = serie_P.max()
        Q_base = serie_Q.max()

        #if P_base == 0 or Q_base == 0:
         #   continue

        # 4. Converte valores da serie para p.u
        pu_P = serie_P / P_base
        pu_Q = serie_Q / Q_base

        # 5. Salva os loadshapes em arquivos .txt
        caminho_P = local_saida + f"{feeder}/" + f"{feeder}_Bus_{bus}_P.txt"
        caminho_Q = local_saida + f"{feeder}/" + f"{feeder}_Bus_{bus}_Q.txt"
        pu_P.to_csv(caminho_P, index=False, header=False)
        pu_Q.to_csv(caminho_Q, index=False, header=False)


        # 6. Gera arquivo Load.dss
        nome_P = f"Load_{bus}_P"
        nome_Q = f"Load_{bus}_Q"

        linha_P = (
            f"New Loadshape.{nome_P} "
            f"npts=8760 interval=1 "
            f"mult=(file={caminho_P})"
        )

        linha_Q = (
            f"New Loadshape.{nome_Q} "
            f"npts=8760 interval=1 "
            f"mult=(file={caminho_Q})"
        )
        
        linhas_dss.append(linha_P)
        linhas_dss.append(linha_Q)
    
        
    # Salva arquivo       
    loadshape_dss = local_saida + f"Loadshapes_{feeder}.dss"
    with open(loadshape_dss, "w") as f:
        f.write(f"// Loadshapes do {feeder}\n")
        f.write("// Dados normalizados em PU\n")
        f.write("// Valores de base salvos em: \n")
        f.write(f"// {local_saida} + {feeder}_bases.csv \n\n")

        for linha in linhas_dss:
            f.write(linha + "\n")

    # 7. Salva valores de base
    df_base.loc[len(df_base)] = [bus, P_base, Q_base]
    caminho_base = local_saida + f"Bases_{feeder}.csv"
    df_base.to_csv(caminho_base, index=False)

    # FIM DA FUNÇÃO
    
###################################################################################    

# EXECUTA O PROCESSAMENTO
feeders = ["FeederA", "FeederB", "FeederC"]

for feeder in feeders:
    processar_feeder(feeder)

print("\nProcesso finalizado!")