#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 24 16:50:56 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""


"""



import pandas as pd

# Dicionário que associa cada alimentador ao caminho de sua respectiva planilha.
feeders = {
    "FeederA": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv",
    "FeederB": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederB_clean.csv",
    "FeederC": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederC_clean.csv"
}

# Caminho onde serão salvos os arquivos de saída.
caminho_dos_loadshapes = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"
caminho_dos_multiplicadores = "/home/matheus/Documentos/BtM-PV-estimating/multiplicadores/"

# Parâmetros do Loadshape
numero_de_pontos = 8760
intervalo = 1  # horas


for feeder, arquivo in feeders.items():

    # Carrega planilha.
    df = pd.read_csv(arquivo, parse_dates=["Time"])

    # Cria uma lista vazia para armazenas comandos do openDSS.
    dss_lines = []

    # Cria uma lista vazia para armazenas possíveis nós (bus) com carga nula.
    carga_zero = []

    # Verifica a quantidade de nós (bus) existentes na planilha. 
    n_colunas_carga = len(df.columns) - 1

    # Contador de loadshapes criados
    loadshapes_criados = 0

    # Inicia processo de geração de loadshapes.
    for col in df.columns[1:]:  # ignora coluna Time

        serie = df[col]

        # Estabelece o maior valor de potência da serie histórica
        # como potência base.
        P_base = serie.max()

        # Verifica se o nó (bus) não possui carga nula.
        if P_base == 0:
            # Adiciona a lista de nós (buses) com carga nula
            carga_zero.append(col)
            continue

        # Conversão das potência para PU
        PU = serie / P_base

        # Nomeia o loadshape
        nome_loadshape = f"Loadshape_{col.replace(' ', '')}" # Elimina o espaço do nome
                                                     # da coluna

        # Arquivo txt dos multiplicadores
        arquivo_txt = caminho_dos_multiplicadores + f"{feeder}/" + f"{nome_loadshape}.txt"

        # Salva multiplicadores
        PU.to_csv(arquivo_txt, index=False, header=False)

        # Cria a linha DSS
        linha_dss = (
            f"New Loadshape.{nome_loadshape} "
            f"npts={numero_de_pontos} interval={intervalo} "
            f"mult=(file={arquivo_txt})"
        )

        # Adiciona a linha criada na lista de linhas
        dss_lines.append(linha_dss)

        # Incrementa contador
        loadshapes_criados += 1

        # FIM DO LOOP
        ########################################################################
        ########################################################################


    # Cria arquivo para salvar loadshape
    arquivo_dss = caminho_dos_multiplicadores + f"{feeder}/" + f"Loadshape_{feeder}.dss"

    # Escreve as linhas dss no arquivo
    with open(arquivo_dss, "w") as f:
        for linha in dss_lines:
            f.write(linha + "\n")


    # Mostra relatório do processo
    print ("\n###############################################")
    print (f"\nAlimentador: {feeder}")
    print(f"\nColunas na planilha original: {n_colunas_carga}")
    print(f"\nLoadshapes criados: {loadshapes_criados}")

    if carga_zero:
        nos=[]
        for b in carga_zero:
            nos.append(b)
        print("\nNós com carga nula:")
        print(f"\t{nos}")
        
    print(f"\nArquivo DSS salvo como: {arquivo_dss}")


