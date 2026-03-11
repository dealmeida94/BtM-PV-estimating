#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:11:09 2026

@author: matheus
"""

import re

arquivo_entrada = "Load.dss"
arquivo_saida = "Load_novo.dss"

with open(arquivo_entrada) as f:
    linhas = f.readlines()

with open(arquivo_saida, "w") as f_out:

    for linha in linhas:

        if linha.strip().lower().startswith("new load"):

            match = re.search(r'Load_(\d+)', linha)

            if match:
                numero = match.group(1)

                linha = linha.strip()
                linha += f" yearly=LS_Bus{numero}\n"

        f_out.write(linha)

print("Load_novo.dss criado.")