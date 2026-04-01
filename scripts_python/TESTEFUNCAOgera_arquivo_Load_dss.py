'''
Importa as configurações salvas na planilha "configuracao_buses.xlsx" e os valores de base de cada Feeder
salvos nas planilhas "Bases_FeederA.csv", "Bases_FeederB.csv" e "Bases_FeederC.csv".

Verifica possíveis inconsistências e gera um arquivo Load.dss
'''

import pandas as pd
import re

# FUNÇÃO PARA EXTRAIR O LOADSHAPE DE UM ARQUIVO loadshapes.dss
def extrair_loadshapes(loadshape_dss):
    loadshapes = {}
    with open(loadshape_dss, "r") as f:
        for linha in f:
            linha = linha.strip()
            
            # Identifica as linhas que iniciam com "new loadshape"
            if linha.lower().startswith("new loadshape"):

                # Verifica nome da carga
                padrao_load = re.search(r"Loadshape\.(.*?)\s+npts", linha, re.IGNORECASE)
                if not padrao_load: # se padrão retornar nulo
                    print(f"Nao foi encontrado Loadshape na linha: \n{linha}")
                    continue
                nome_load = padrao_load.group(1)
                
                # identifica se loadshape é de potência tiva ou reativa
                if "_P" in nome_load:
                    tipo = "P"
                elif "_Q" in nome_load:
                    tipo = "Q"
                else:
                    tipo = "?"

                # Verifica numero do bus
                padrao_bus = re.search(r"Bus\s*(\d+)", nome_load, re.IGNORECASE)
                if not padrao_bus:
                    print(f"Não foi encontrado o bus na linha: \n{nome_load}")
                    continue
                numero_bus = padrao_bus.group(1)
                chave_bus = f"Bus {numero_bus}"
                
                if chave_bus not in loadshapes:
                    loadshapes[chave_bus] = {}

                loadshapes[chave_bus][tipo] = nome_load

    return loadshapes

# Carrega e processa os dados para um feeder
def processa_dados(feeder, caminho_configuracoes, local_dos_loadshapes):
    # Carrega arquivos
    configuracoes = caminho_configuracoes
    df_config = pd.read_excel(configuracoes, sheet_name=f"Feeder_{feeder}")
    
    arquivo_bases = local_dos_loadshapes + f"Bases_Feeder{feeder}.csv"
    df_base = pd.read_csv(arquivo_bases)
    
    loadshapes_dss = local_dos_loadshapes + f"Loadshapes_Feeder{feeder}.dss"
    
    # Padroniza nomes das colunas no arquivo das configurações
    df_config.columns = [c.lower() for c in df_config.columns]
    
    # Padroniza nomes dos buses no arquivo dos valores de base
    df_base.columns = [c.lower() for c in df_base.columns]
    df_base["bus"] = (
        df_base["bus"]
        .astype(str)
        .str.extract(r"(\d+)")[0]
        .str.lstrip("0")
    )

    # Extrai loadshapes do arquivo loadshape.dss
    loadshapes = extrair_loadshapes(loadshapes_dss)

    if not loadshapes: # se extrair_loadshape retornar nulo
        print(f"Erro!!! Nenhum loadshape encontrador para o {feeders}")

    return (df_base, df_config, loadshapes)


def gera_loads (valores_bases, configuracoes, loadshapes, feeder):
    linhas_saida = {}
    linhas_saida[feeder] = []
    faltantes_ls = []
    faltantes_base = []

    for _, row in configuracoes.iterrows():
        
        # verifica configurações
        load = str(row["load"])
        bus = str(row["bus1"])
        phases = int(row.get("phases", 3))
        conn = row.get("conn", "wye")

        # verifica nome do load
        padrao = re.search(r"(\d+)", load)
        if not padrao: # se nulo
            continue
        load_id = padrao.group(1)        
        chave_bus = f"Bus {load_id}"
        
        # verifica se existe loadshape para o load
        if chave_bus not in loadshapes:
            faltantes_ls.append(load)
            continue
        
        # copia nome dos loadshapes
        nome_ls_p = loadshapes[chave_bus].get("P")
        nome_ls_q = loadshapes[chave_bus].get("Q")

        if nome_ls_p is None:
            faltantes_ls.append(load)
            continue

        # Verifica em qual linha da planilha de valores base esta o load_id procurado
        base_row = valores_bases[valores_bases["bus"] == load_id]
        
        if base_row.empty:
            faltantes_base.append(load)
            continue
        
        # Copia valores de kW e kVAr de base
        kw = float(base_row["p_base"].values[0])
        kvar = float(base_row["q_base"].values[0])

        # Cria linha do arquivo Load.dss
        linha = (
            f"New Load.{load} "
            f"phases={phases} conn={conn} "
            f"bus1={bus} "
            "kV=0.208 "
            f"kW={kw:.3f} kvar={kvar:.3f} "
            f"daily={nome_ls_p} "
            + (f"qmult={nome_ls_q} " if nome_ls_q else "")
            + "model=1"
        )

        linhas_saida[feeder].append(linha)
        
    return [linhas_saida, faltantes_ls, faltantes_base]


def salva_relatorio(faltantes_ls, faltantes_base, caminho_arquivo):
   
    # Cria DataFrames
    df_ls = pd.DataFrame({"load_sem_loadshape": faltantes_ls})
    df_base = pd.DataFrame({"load_sem_base": faltantes_base})

    # Salva em .xlsx
    with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
        df_ls.to_excel(writer, sheet_name="Sem_Loadshape", index=False)
        df_base.to_excel(writer, sheet_name="Sem_Base", index=False)

    # Mensagem única
    print(f"Relatório salvo em: {caminho_arquivo}")
    
    


local_dos_loadshapes = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"
caminho_arquivo_configuracoes = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/configuracao_buses.xlsx"

feeders = ["A", "B", "C"]

for feeder in feeders:
    df_base, df_config, loadshapes = processa_dados(feeder, caminho_arquivo_configuracoes, local_dos_loadshapes)
    
    linhas_por_feeder, faltantes_ls, faltantes_base = gera_loads(df_base, df_config, loadshapes, feeder)
    
    for fdr, linhas in linhas_por_feeder.items():
        
        arquivo_saida = local_dos_loadshapes + f"Loads_Feeder{fdr}.dss"
        
        with open(arquivo_saida, "w") as f:
            f.write(f"! Arquivo Load - Feeder {fdr}\n")
                      
            for linha in linhas:
                f.write(linha + "\n")
                
    print(f"Arquivo Load.dss salvo em: {arquivo_saida}")
    
    salva_relatorio(faltantes_ls, faltantes_base, local_dos_loadshapes + f"logs_{feeder}.xlsx")