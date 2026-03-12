#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

# Dicionário que associa cada alimentador ao caminho de sua respectiva planilha.
feeders = {
    "FeederA": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv",
    "FeederB": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederB_clean.csv",
    "FeederC": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederC_clean.csv"
}

# Caminho onde serão salvos os arquivos de saída.
caminho_dos_loadshapes = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"
caminho_dos_multiplicadores = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"

# Parâmetros do Loadshape
numero_de_pontos = 8760
intervalo = 1  # horas


for feeder, arquivo in feeders.items():

    # Carrega planilha
    df = pd.read_csv(arquivo, parse_dates=["Time"])

    # Lista de comandos DSS
    dss_lines = []

    # Lista de buses com carga zero
    carga_zero = []

    # Lista para salvar Pbase
    bases = []

    # Número de colunas de carga
    n_colunas_carga = len(df.columns) - 1

    # Contador
    loadshapes_criados = 0

    # Loop pelas cargas
    for col in df.columns[1:]:

        serie = df[col]

        # Potência base
        P_base = serie.max()

        if P_base == 0:
            carga_zero.append(col)
            continue

        # Salva Pbase
        bases.append({
            "bus": col.replace(' ', ''),
            "Pbase_kW": P_base
        })

        # Conversão para PU
        PU = serie / P_base

        # Nome do loadshape
        nome_loadshape = f"Loadshape_{col.replace(' ', '')}"

        # Arquivo txt
        arquivo_txt = caminho_dos_multiplicadores + f"{feeder}/" + f"{nome_loadshape}.txt"

        # Salva multiplicadores
        PU.to_csv(arquivo_txt, index=False, header=False)

        # Linha DSS
        linha_dss = (
            f"New Loadshape.{nome_loadshape} "
            f"npts={numero_de_pontos} interval={intervalo} "
            f"mult=(file={arquivo_txt})"
        )

        dss_lines.append(linha_dss)

        loadshapes_criados += 1

    ########################################################################

    # Salva arquivo DSS
    arquivo_dss = caminho_dos_multiplicadores + f"{feeder}/" + f"Loadshape_{feeder}.dss"

    with open(arquivo_dss, "w") as f:
        for linha in dss_lines:
            f.write(linha + "\n")

    ########################################################################
    # Salva arquivo de potências base

    df_bases = pd.DataFrame(bases)

    arquivo_bases = caminho_dos_multiplicadores + f"{feeder}/" + f"Pbase_{feeder}.csv"

    df_bases.to_csv(arquivo_bases, index=False)

    ########################################################################

    print("\n###############################################")
    print(f"\nAlimentador: {feeder}")
    print(f"\nColunas na planilha original: {n_colunas_carga}")
    print(f"\nLoadshapes criados: {loadshapes_criados}")

    if carga_zero:
        print("\nNós com carga nula:")
        print(f"\t{carga_zero}")

    print(f"\nArquivo DSS salvo como: {arquivo_dss}")
    print(f"\nArquivo de potências base salvo como: {arquivo_bases}")
