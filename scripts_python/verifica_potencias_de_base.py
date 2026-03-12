#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pandas as pd

arquivo_loads = "/home/matheus/Documentos/BtM-PV-estimating/elementos/Load.dss"
arquivo_saida = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/potencias_base.csv"


def extrair_potencias_base(caminho):

    dados = []

    with open(caminho, "r") as f:

        for linha in f:

            linha = linha.strip()

            # detecta linhas de carga
            if re.search(r"new\s+load\.", linha, re.IGNORECASE):

                bus_match = re.search(r"bus1=([^\s]+)", linha, re.IGNORECASE)
                kw_match = re.search(r"kw=([\d\.]+)", linha, re.IGNORECASE)

                if bus_match and kw_match:

                    bus = bus_match.group(1)
                    kw = float(kw_match.group(1))

                    dados.append({
                        "bus": bus,
                        "base_kw": kw
                    })

    return pd.DataFrame(dados)


def main():

    df = extrair_potencias_base(arquivo_loads)

    df.to_csv(arquivo_saida, index=False)

    print("\n###################################")
    print("Leitura do Load.dss concluída")
    print(f"\nCargas encontradas: {len(df)}")
    print(f"\nArquivo salvo em:\n{arquivo_saida}")
    print("###################################\n")


if __name__ == "__main__":
    main()