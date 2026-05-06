#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Realiza uma leitura da planilha "Nodal_P&Q_processados.xlsx", e gera
arquivos loadshapes de P com valores em p.u (normalizado por unidade).

Etapas do processo:
    1. Leitura dos dados
    2. Eliminação de cargas nulas
    3. Para cada bus, adota o valor máximo de potência como valor de base
    4. Realiza a normalização dos valores em cada bus
    5. Salva loadshapes em arquivos .txt
    6. Gera arquivos loadshapes.dss
    7. Salva os valores bases em uma planilha .xlsx
    
'''

import pandas as pd
import configs as cf

# Função que realiza o processamento por feeder
def processar_feeder(feeder):

    # 1. Leitura dos dados
    df = pd.read_excel(cf.NODAL_PeQ, sheet_name=f"{feeder}_P")

    # Remove coluna "Time"
    for col in df.columns:
        if str(col) == "Time":
            df = df.drop(columns=[col])

    # Todos os dados convertidos para tipo numérico
    df = df.apply(pd.to_numeric, errors="coerce")
    
    # 2. Elimina cargas nulas
    df = df.loc[:, (df != 0).any(axis=0)]
    
    # Cria dataframe para salvar valores de base
    df_base = pd.DataFrame(columns=["Bus", "P_base"])

    linhas_dss = []

    for bus in df.columns:

        serie = df[bus]
        
        # 3. Determina o valor máximo da serie como valor de base
        P_base = serie.max()
        
        # 4. Converte valores da serie para p.u
        pu = serie / P_base

        # 5. Salva os loadshapes em arquivos .txt
        bus = bus.replace(" ", "_")
        caminho = cf.LS_DIR / f"{feeder}" / f"{feeder}_{bus}.txt"
        pu.to_csv(caminho, index=False, header=False)

        # 6. Gera arquivo Load.dss
        nome = f"Load_{bus}"
        
        linha = (
            f"New Loadshape.{nome} "
            f"npts=8760 interval=1 "
            f"mult=(file={caminho})"
        )
        
        linhas_dss.append(linha)
        df_base.loc[len(df_base)] = [bus, P_base]
    
        
    # Salva arquivo       
    loadshape_dss = cf.LS_DIR / f"Loadshapes_{feeder}.dss"
    with open(loadshape_dss, "w") as f:
        f.write(f"// Loadshapes do {feeder}\n")
        f.write("// Dados normalizados em PU\n")
        f.write("// Valores de base salvos em: \n")
        f.write(f"// cf.LS_DIR/{feeder}_bases.csv \n\n")

        for linha in linhas_dss:
            f.write(linha + "\n")

    # 7. Salva valores de base
    caminho_base = cf.LS_DIR / f"Bases_{feeder}.csv"
    df_base.to_csv(caminho_base, index=False)

    # FIM DA FUNÇÃO
    
###################################################################################    

# EXECUTA O PROCESSAMENTO
def gera_loadshapes():
    feeders = ["FeederA", "FeederB", "FeederC"]
    
    for feeder in feeders:
        processar_feeder(feeder)
    
    print("\nProcesso finalizado!")