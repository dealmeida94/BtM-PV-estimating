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

# Carrega planilhas com medições por alimentador.
feeders = {
    "FeederA": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederA_clean.csv",
    "FeederB": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederB_clean.csv",
    "FeederC": "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/FeederC_clean.csv"
}

# Caminho para salvar arquivos
caminho_do_arquivo = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"

# Parâmetros do Loadshape
npts = 8760
interval = 1  # horas


for feeder, arquivo in feeders.items():

    # Carregar dados
    df = pd.read_csv(arquivo, parse_dates=["Time"])

    # Lista para armazenar comandos DSS
    dss_lines = []

    # Lista para registrar buses com carga zero
    buses_zero = []

    # Número esperado de colunas de carga
    n_colunas_carga = len(df.columns) - 1

    # Contador de loadshapes criados
    loadshapes_criados = 0


    # =============================
    # LOOP DAS CARGAS
    # =============================

    for col in df.columns[1:]:  # ignora coluna Time

        serie = df[col]

        # potência base
        P_base = serie.max()

        # verificar se carga é zero
        if P_base == 0:
            buses_zero.append(col)
            continue

        # normalização
        mult = serie / P_base

        # nome do loadshape
        nome_ls = f"LS_{col.replace(' ', '')}"

        # arquivo txt dos multiplicadores
        arquivo_txt = caminho_do_arquivo + f"{nome_ls}.txt"

        # salvar multiplicadores
        mult.to_csv(arquivo_txt, index=False, header=False)

        # linha DSS
        linha_dss = (
            f"New Loadshape.{nome_ls} "
            f"npts={npts} interval={interval} "
            f"mult=(file={arquivo_txt})"
        )

        dss_lines.append(linha_dss)

        loadshapes_criados += 1


    # =============================
    # SALVAR ARQUIVO DSS
    # =============================

    arquivo_dss = caminho_do_arquivo + f"Loadshapes_{feeder}.dss"

    with open(arquivo_dss, "w") as f:
        for linha in dss_lines:
            f.write(linha + "\n")


    # =============================
    # RELATÓRIO FINAL
    # =============================

    print(f"\nTotal de colunas de carga: {n_colunas_carga}")
    print(f"Loadshapes criados: {loadshapes_criados}")

    if buses_zero:
        print("\n⚠ Buses com carga zero:")
        for b in buses_zero:
            print(f" - {b}")
    else:
        print("\n✔ Nenhum bus com carga zero encontrado")

    # conferência final
    if loadshapes_criados + len(buses_zero) == n_colunas_carga:
        print("\n✔ Conferência OK: todas as colunas foram processadas.")
    else:
        print("\n⚠ Inconsistência detectada no processamento.")

    print(f"\nArquivo DSS criado: {arquivo_dss}")


print("\n=================================")
print("Loadshapes gerados com sucesso.")
print("=================================")