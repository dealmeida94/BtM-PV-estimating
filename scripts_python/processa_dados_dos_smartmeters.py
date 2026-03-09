#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Realiza o processa


"""

import pandas as pd

# Abre o arquivo .xlsx que contém os dados medidos pelos smart meters.
arquivo = "/home/matheus/Documentos/Projeto/dados_brutos/smart_meter_data.xlsx"

# O arquivo possui 
# As medições individuais de cada consumidor estão 

# O arquivo possui 4 abas:
#   - README
#   - FeederA_Smart Meter Data 
#   - FeederB_Smart Meter Data
#   - FeederC_Smart Meter Data

# Cria um dicionário que associa cada planilha (Aba) ao respectivo arquivo
# de saída. 
abas = {
    "FeederA_Smart Meter Data": "FeederA_clean.csv",
    "FeederB_Smart Meter Data": "FeederB_clean.csv",
    "FeederC_Smart Meter Data": "FeederC_clean.csv"
}


for aba, nome_do_arquivo in abas.items():

    # Copia as medições contidas na aba que esta sendo processada
    df = pd.read_excel(
        arquivo,
        sheet_name=aba,
        header=0   # Indica que primeira linha contém os cabeçalhos
    )

    # Renomeia primeira coluna para "Time"
    df.rename(columns={df.columns[0]: "Time"}, inplace=True)
    #df.rename(columns={df.columns[0]: "Time"})


    # Converter dados da coluna Time para datetime
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

    # Remover linhas com datas inválidas
    #df = df.dropna(subset=["Time"])

    # Corrigir possíveis milissegundos estranhos
    #df["Time"] = df["Time"].dt.round("h")

    # Ordenar
    #df = df.sort_values("Time").reset_index(drop=True)

    # Troca a virgula "," por ponto "." nos valores medidos
    for col in df.columns[1:]:
        df[col] = (df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

    # ==========================
    # Verificações
    # ==========================

    print(f"\n{aba}\n")
    print("Valores NaN: \n")
    if df.isna().any().any():
        print("\t A planilha gerada contém células NaN.")
    else:
        print("\t Nenhuma célula NaN foi encontrado.")
    
    print("\nQuantidade de linhas: ")
    if len(df) == 8760:
        print(f"\tOk, a planilha possui {len(df)} linhas (1 ano hora a hora)")
    else:
        print(f"\tIncorreto, a planilha está com {len(df)} linhas. Verificar")

    print("\nDatas duplicadas:")    
    duplicados = df["Time"].duplicated().sum()
    if duplicados == 0:
        print("\tNão existem datas duplicadas")
    else:
        print("\tExistem datas duplicadas na planilha")

    print("\nValores nulos:\n")
    nulos = df.isna().sum().sum()
    if nulos == 0:
        print("\tNão existem valores nulos na planilha")
    else:
        print("\tExistem valores nulos na planilha")

    # Salvar CSV
    caminho_do_arquivo = "/home/matheus/Documentos/Projeto/loadshapes" + nome_do_arquivo
    df.to_csv(caminho_do_arquivo, index=False)
    print("Planilha salva em: /home/matheus/Documentos/Projeto/loadshapes")


print("\nProcessamento finalizado.")

# ==========================
# Teste de leitura final
# ==========================

#for arquivo_csv in ["FeederA_clean.csv", "FeederB_clean.csv", "FeederC_clean.csv"]:
#    print(f"\nTestando {arquivo_csv}")
#    df_test = pd.read_csv(arquivo_csv, parse_dates=["Time"])
#    print(df_test.head())
#    print(df_test.info())