#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 15:58:36 2026

@author: matheus
"""

import re

# Caminhos dos arquivos
arquivo_entrada = "Load.dss"
arquivo_saida = "Load_corrigido.dss"

def definir_feeder(numero_barra):
    if 3000 <= numero_barra <= 3099:
        return "FeederA"
    elif 3100 <= numero_barra <= 3199:
        return "FeederB"
    elif numero_barra >= 3200:
        return "FeederC"
    else:
        return None

with open(arquivo_entrada, "r") as f:
    linhas = f.readlines()

linhas_corrigidas = []

for linha in linhas:
    
    if linha.strip().lower().startswith("new load"):
        
        # Extrai número da barra
        match = re.search(r'bus1=(\d+)', linha, re.IGNORECASE)
        
        if match:
            numero_barra = int(match.group(1))
            feeder = definir_feeder(numero_barra)
            
            if feeder:
                # Remove yearly antigo se existir
                linha = re.sub(r'yearly=\w+', '', linha, flags=re.IGNORECASE)
                
                # Adiciona yearly no final
                linha = linha.strip() + f" yearly={feeder}\n"
    
    linhas_corrigidas.append(linha)

with open(arquivo_saida, "w") as f:
    f.writelines(linhas_corrigidas)

print("Arquivo Load_corrigido.dss criado com sucesso.")