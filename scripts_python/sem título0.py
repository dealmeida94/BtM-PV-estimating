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

arquivo = "/home/matheus/Documentos/Projeto/dados_brutos/smart_meter_data.xlsx"

abas = {
    "FeederA_Smart Meter Data": "FeederA_clean.csv",
    "FeederB_Smart Meter Data": "FeederB_clean.csv",
    "FeederC_Smart Meter Data": "FeederC_clean.csv"
}

# Lista para armazenar verificações
relatorio = []

# Dicionário para armazenar os dataframes processados
dataframes_processados = {}

for aba, nome_do_arquivo in abas.items():

    df = pd.read_excel(
        arquivo,
        sheet_name=aba,
        header=0
    )

    df.rename(columns={df.columns[0]: "Time"}, inplace=True)

    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

    for col in df.columns[1:]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

    # ==========================
    # Verificações
    # ==========================

    possui_nan = df.isna().any().any()
    linhas = len(df)
    duplicados = df["Time"].duplicated().sum()
    nulos = df.isna().sum().sum()

    # Salvar resultados
    relatorio.append({
        "Planilha": aba,
        "Linhas": linhas,
        "8760_linhas": "OK" if linhas == 8760 else "ERRO",
        "Datas_duplicadas": duplicados,
        "Valores_nulos": nulos,
        "Possui_NaN": "Sim" if possui_nan else "Não"
    })

    # Salvar CSV
    caminho_do_arquivo = "/home/matheus/Documentos/Projeto/loadshapes" + nome_do_arquivo
    df.to_csv(caminho_do_arquivo, index=False)

    # Guardar dataframe
    dataframes_processados[aba] = df


print("\nProcessamento finalizado.\n")

# ==========================
# Mostrar tabela de verificações
# ==========================

tabela = pd.DataFrame(relatorio)

print("Resumo das verificações:\n")
print(tabela.to_string(index=False))


# ==========================
# Perguntar se deseja ver cabeçalho
# ==========================

resposta = input("\nDeseja visualizar o cabeçalho das planilhas? (s/n): ").lower()

if resposta == "s":

    for aba, df in dataframes_processados.items():

        print(f"\nCabeçalho da planilha: {aba}\n")
        print(df.head())

else:
    print("\nPrograma encerrado.")