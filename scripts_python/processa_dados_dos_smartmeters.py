#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 16:32:18 2026

@author: matheus
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Realiza o processamento
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

    # Salvar CSV
    caminho_do_arquivo = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes" + nome_do_arquivo
    df.to_csv(caminho_do_arquivo, index=False)

    # Guardar dataframe
    dataframes_processados[aba] = df


print("\nProcessamento concluído.\n")

tabela = pd.DataFrame(relatorio)

print("Verificações:\n")
print(tabela.to_string(index=False))