#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Este script realiza a leitura linha a linha do arquivo "Load.dss" original, fornecido pelos
autores (ver referência), buscando padrões de texto, no intuito de extrair as informações:
        + nome da carga
        + quantidade de fases (mono, bi ou trífasico)
        + tipo de conexão (estrela ou triângulo)
        + nome do bus
        
    As informações extraídas são armazenadas em uma planilha (.xlsx).
    
    No arquivo Load.dss as cargas de cada alimentador estão identificadas pelo comentário padrão:
        
        //***************************************************************************************//
        //                                             Feeder A
        //***************************************************************************************//
        
    As cargas são declaras conforme:
        
        New  Load.Load_1003  phases=3  conn=wye  bus1=T_bus1003_L.1.2.3.0  kV=0.208  kW=15.29   Kvar=3.83
        
        sendo:
            Load name, number of phases, connection, bus, kV rating, active power, reactive power
            
    
Referência:
    F. Bu, Y. Yuan, Z. Wang, K. Dehghanpour, and A. Kimber, "A Time-series Distribution Test System based on Real
    Utility Data." 2019 North American Power Symposium (NAPS), Wichita, KS, USA, 2019, pp. 1-6.
    <https://wzy.ece.iastate.edu/Testsystem.html>


"""

import pandas as pd
import re
from collections import defaultdict
import configs as cf

# Cria um dicionário vazio
dados_por_feeder = defaultdict(list)

# Cria variável com conteúdo nulo
feeder_atual = None

def extrair_parametro(texto, parametro):
    # FUNÇÃO PARA LOCALIZAR UM PARÂMETRO E SEU VALOR
    # Busca no texto o padrão especificado usando regex.
    # Se o padrão especificado não for encontrado retorna nulo (None)
    #
    #   Parâmetros:
    #            texto : o texto onde deve ser feita a busca;
    #            parametro : o parametro a ser localizado. 
    #
    # Exemplo:
    #    texto = "phases=3 conn=wye bus1=T_bus1004_L.1.2.3.0"
    #
    #    se parametro ="phases" retorna  "3"
    #    se parametro = "conn"  retorna "wye"
    #    se parametro = "bus1"  retorna "T_bus1004_L.1.2.3.0"

    informacao = re.search(rf"{parametro}\s*=\s*([^\s]+)", texto, re.IGNORECASE)
    return informacao.group(1) if informacao else None

def le_load_dss():
    # REALIZA A LEITURA DO ARQUIVO
    with open(cf.LOAD_ORG / "Load.dss", "r") as arquivo:
        for linha in arquivo:
            
            # Elimina espaços e caracteres no inicio e fim da linha
            linha = linha.strip()
    
            # Verifica se existe a palavra "feeder" na linha
            if "feeder" in linha.lower():
                # Captura "feeder" + o caracteres que esta logo após
                nome_alimentador = re.search(r"feeder\s+([A-Za-z0-9_]+)", linha, re.IGNORECASE)
                if nome_alimentador:
                    # Atualiza o feeder_atual
                    feeder_atual = nome_alimentador.group(1).strip()
                continue
    
            # Se não existir "feeder" na linha, mas começa com "//" ou "!" é comentário
            # ignorar e pular para próxima linha
            if not linha or linha.startswith("//") or linha.startswith("!"):
                continue
    
            # Se a linha possui "New Load" é necessario extrair os parâmetros
            if re.match(r"new\s+load", linha, re.IGNORECASE):
    
                # Nome da carga
                nome = re.search(r"Load\.([^\s]+)", linha, re.IGNORECASE)
                nome_load = nome.group(1) if nome else None
    
                # Quantidade de fases
                fases = extrair_parametro(linha, "phases")
                # Tipo de conexão
                conexao   = extrair_parametro(linha, "conn")
                # Nome do bus
                bus = extrair_parametro(linha, "bus1")
    
                # Armazena
                dados_por_feeder[feeder_atual].append({
                    "Load": nome_load,
                    "phases": fases,
                    "conn": conexao,
                    "bus1": bus
                })
    
    # SALVA OS DADOS EM UMA PLANILHA .xlsx
    with pd.ExcelWriter(cf.PROCESSADOS_DIR / "configuracoes_dos_loads.xlsx", engine="openpyxl") as writer:
        for feeder, dados in dados_por_feeder.items():  
            # Gera um dataframe com os dados
            df = pd.DataFrame(dados)
            # Determina o nome da aba
            nome_aba = f"Feeder_{feeder}"
            # Cria a planilha
            df.to_excel(writer, sheet_name=nome_aba, index=False)
    
    print("\nLeitura do arquivo Load.dss concluida.")
    print(f"Dados salvos em: {cf.PROCESSADOS_DIR}")