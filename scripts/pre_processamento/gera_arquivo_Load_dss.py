import pandas as pd
import re
import configs as cf

#########################################################
################# FUNÇÃO extrair_loadshapes #############

def extrair_loadshapes(loadshape_dss):
    loadshapes = {}

    with open(loadshape_dss, "r") as f:
        for linha in f:
            linha = linha.strip()

            if not linha.lower().startswith("new loadshape"):
                continue

            # Extrai nome do loadshape
            partes = linha.split()
            nome_completo = None

            for p in partes:
                if "loadshape." in p.lower():
                    nome_completo = p.split(".")[1]
                    break

            if not nome_completo:
                print(f"Não conseguiu extrair nome:\n{linha}")
                continue

            # Extrai número do bus
            padrao_bus = re.search(r"(\d+)", nome_completo)
            if not padrao_bus:
                print(f"Não encontrou número no nome:\n{nome_completo}")
                continue

            numero_bus = str(int(padrao_bus.group(1)))  # remove zeros à esquerda
            chave_bus = f"Bus {numero_bus}"

            loadshapes[chave_bus] = nome_completo

    return loadshapes


#########################################################
################# FUNÇÃO processa_dados #################

def processa_dados(feeder):
    df_config = pd.read_excel(cf.CFG_LOADS, sheet_name=f"Feeder_{feeder}")
    df_base = pd.read_csv(cf.LS_DIR / f"Bases_Feeder{feeder}.csv")
    loadshapes_dss = cf.LS_DIR / f"Loadshapes_Feeder{feeder}.dss"

    # Padroniza colunas
    df_config.columns = [c.lower() for c in df_config.columns]
    df_base.columns = [c.lower() for c in df_base.columns]

    # Padroniza BUS (remove zeros à esquerda)
    df_base["bus"] = (
        df_base["bus"]
        .astype(str)
        .str.extract(r"(\d+)")[0]
        .astype(int)
        .astype(str)
    )

    loadshapes = extrair_loadshapes(loadshapes_dss)

    if not loadshapes:
        print(f"Erro!!! Nenhum loadshape encontrado para o feeder {feeder}")

    return df_base, df_config, loadshapes


#########################################################
################# FUNÇÃO gera_loads #####################

def gera_loads(valores_bases, configuracoes, loadshapes, feeder):
    linhas_saida = {feeder: []}
    faltantes_ls = []
    faltantes_base = []

    for _, row in configuracoes.iterrows():

        load = str(row["load"])
        bus = str(row["bus1"])
        phases = int(row.get("phases", 3))
        conn = row.get("conn", "wye")

        # Extrai ID numérico do load
        padrao = re.search(r"(\d+)", load)
        if not padrao:
            continue

        load_id = str(int(padrao.group(1)))  # padroniza
        chave_bus = f"Bus {load_id}"

        # Verifica loadshape
        nome_ls = loadshapes.get(chave_bus)
        if nome_ls is None:
            faltantes_ls.append(load)
            continue

        # Verifica base
        base_row = valores_bases[valores_bases["bus"] == load_id]
        if base_row.empty:
            faltantes_base.append(load)
            continue

        kw = float(base_row["p_base"].values[0])

        linha = (
            f"New Load.{load} "
            f"phases={phases} conn={conn} "
            f"bus1={bus} "
            f"kV=0.208 "
            f"kW={kw:.3f} "
            f"yearly={nome_ls} model=1"
        )

        linhas_saida[feeder].append(linha)

    print(f"\nFeeder {feeder}: {len(linhas_saida[feeder])} loads gerados")
    print(f"Sem loadshape: {len(faltantes_ls)}")
    print(f"Sem base: {len(faltantes_base)}")

    return linhas_saida, faltantes_ls, faltantes_base


#########################################################
################# FUNÇÃO salva_relatorio ################

def salva_relatorio(faltantes_ls, faltantes_base, caminho_arquivo):

    df_ls = pd.DataFrame({"load_sem_loadshape": faltantes_ls})
    df_base = pd.DataFrame({"load_sem_base": faltantes_base})

    with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
        df_ls.to_excel(writer, sheet_name="Sem_Loadshape", index=False)
        df_base.to_excel(writer, sheet_name="Sem_Base", index=False)

    print(f"Relatório salvo em: {caminho_arquivo}")


#########################################################
######################## MAIN ###########################

def gerar_loaddss():

    feeders = ["A", "B", "C"]

    for feeder in feeders:

        bases, configs, ls = processa_dados(feeder)

        linhas_por_feeder, faltantes_ls, faltantes_base = gera_loads(
            bases, configs, ls, feeder
        )

        for fdr, linhas in linhas_por_feeder.items():

            arquivo_saida = cf.LOADS_DIR / f"Loads_Feeder{fdr}.dss"

            with open(arquivo_saida, "w") as f:
                f.write(f"! Arquivo Load - Feeder {fdr}\n")

                for linha in linhas:
                    f.write(linha + "\n")

        print(f"Arquivo Load.dss salvo em: {arquivo_saida}")

        salva_relatorio(
            faltantes_ls,
            faltantes_base,
            cf.LOGS_DIR / f"relatorio_gera_load_dss_{feeder}.xlsx",
        )