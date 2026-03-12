#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 18:17:49 2026

@author: matheus
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

arquivo = "/home/matheus/Documentos/BtM-PV-estimating/dados_brutos/smart_meter_data.xlsx"

abas = {
    "FeederA_Smart Meter Data": "FeederA_clean.csv",
    "FeederB_Smart Meter Data": "FeederB_clean.csv",
    "FeederC_Smart Meter Data": "FeederC_clean.csv"
}

relatorio = []
dataframes_processados = {}

df = pd.read_excel(
    arquivo,
    sheet_name='FeederA_Smart Meter Data',
    header=0
)

df.rename(columns={df.columns[0]: "Time"}, inplace=True)
df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
print(df.iloc[:,3])

'''
for aba, nome_do_arquivo in abas.items():

    df = pd.read_excel(
        arquivo,
        sheet_name=aba,
        header=0
    )

    df.rename(columns={df.columns[0]: "Time"}, inplace=True)
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

    
    for col in df.columns[1:3]:
        print(df[col])
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        print(df[col])    '''