import pandas as pd
import re


pasta_dados = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes/"
feeders = ["A", "B", "C"]
pasta_saida = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/"


# -------------------------------
# FUNÇÃO: extrair loadshapes do DSS
# -------------------------------
def extrair_loadshapes(caminho_dss):
    loadshapes = {}

    with open(caminho_dss, "r") as f:
        for linha in f:
            linha = linha.strip()

            if linha.lower().startswith("new loadshape"):

                match = re.search(r"Loadshape\.(.*?)\s+npts", linha, re.IGNORECASE)

                if not match:
                    print(f"⚠️ erro ao ler linha: {linha}")
                    continue

                nome = match.group(1)

                # extrai número do bus
                bus_match = re.search(r"Bus\s*(\d+)", nome, re.IGNORECASE)

                if not bus_match:
                    print(f"⚠️ sem bus: {nome}")
                    continue

                numero_bus = bus_match.group(1)
                chave_bus = f"Bus {numero_bus}"

                # identifica P ou Q
                if "_P" in nome:
                    tipo = "P"
                elif "_Q" in nome:
                    tipo = "Q"
                else:
                    tipo = "?"

                if chave_bus not in loadshapes:
                    loadshapes[chave_bus] = {}

                loadshapes[chave_bus][tipo] = nome

    return loadshapes


# -------------------------------
# PROCESSAMENTO
# -------------------------------
  # ========================================================
  # CAMINHOS
  # ========================================================
#arquivo_dss = pasta_dados + f"Loadshapes_Feeder{feeder}.dss"
#arquivo_config = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/configuracao_buses.xlsx"
#arquivo_bases = pasta_dados + f"Bases_Feeder{feeder}.csv"
#df_config = pd.read_excel(arquivo_config)
for feeder in feeders:

    #print(f"\n🔄 Processando Feeder {feeder}")
    arquivo_config = "/home/matheus/Documentos/BtM-PV-estimating/dados_processados/configuracao_buses.xlsx"
    arquivo_bases = pasta_dados + f"Bases_Feeder{feeder}.csv"
    arquivo_dss = pasta_dados + f"Loadshapes_Feeder{feeder}.dss"
    df_config = pd.read_excel(arquivo_config, sheet_name=f"Feeder_{feeder}")
    # ========================================================
    # 1. LEITURA DOS DADOS
    # ========================================================
    
    df_config.columns = [c.lower() for c in df_config.columns]

    df_base = pd.read_csv(arquivo_bases)
    df_base.columns = [c.lower() for c in df_base.columns]

    # padroniza BUS → só número
    df_base = pd.read_csv(arquivo_bases)
    df_base.columns = [c.lower() for c in df_base.columns]
    
    df_base["bus"] = (
        df_base["bus"]
        .astype(str)
        .str.extract(r"(\d+)")[0]
        .str.lstrip("0")
    )
#%%
    # ========================================================
    # 2. LOADSHAPES
    # ========================================================
    loadshapes = extrair_loadshapes(arquivo_dss)

    if not loadshapes:
        raise ValueError(f"❌ Nenhum loadshape encontrado no feeder {feeder}")

    linhas_saida = []
    faltantes_ls = []
    faltantes_base = []

    kv = 0.208

    # ========================================================
    # 3. LOOP NOS LOADS
    # ========================================================
    for _, row in df_config.iterrows():

        load = str(row["load"])
        bus = str(row["bus1"])
        phases = int(row.get("phases", 3))
        conn = row.get("conn", "wye")

        # extrai número do load
        match = re.search(r"(\d+)", load)
        if not match:
            continue

        load_id = match.group(1)
        chave_bus = f"Bus {load_id}"
#%%
        # ====================================================
        # 4. LOADSHAPE
        # ====================================================
        if chave_bus not in loadshapes:
            faltantes_ls.append(load)
            continue

        # usa P (ou pode adaptar para Q depois)
        nome_ls = loadshapes[chave_bus].get("P")

        if nome_ls is None:
            faltantes_ls.append(load)
            continue

        # ====================================================
        # 5. BASE
        # ====================================================
        base_row = df_base[df_base["bus"] == load_id]
        print (f"df_base : {df_base["bus"]}")
        print (load_id)

        if base_row.empty:
            faltantes_base.append(load)
            print(base_row)
            continue

        kw = float(base_row["p_base"].values[0])
        kvar = float(base_row["q_base"].values[0])

        # ====================================================
        # 6. LINHA DSS
        # ====================================================
        linha = (
            f"New Load.{load} "
            f"phases={phases} conn={conn} "
            f"bus1={bus} "
            f"kV={kv} "
            f"kW={kw:.3f} kvar={kvar:.3f} "
            f"daily={nome_ls} model=1"
        )

        linhas_saida.append(linha)

        # ========================================================
        # 7. LOGS
        # ========================================================
        if faltantes_ls:
            print(f"⚠️ Sem loadshape ({len(faltantes_ls)}):")
            for f in faltantes_ls[:10]:
                print("   ", f)
    
        if faltantes_base:
            print(f"⚠️ Sem base ({len(faltantes_base)}):")
            for f in faltantes_base[:10]:
                print("   ", f)
    
        print(f"DEBUG -> load: {load} | id: {load_id} | chave: {chave_bus}")
        print(f"Total loadshapes: {len(loadshapes)}")
        print(f"Exemplo keys: {list(loadshapes.keys())[:5]}")
    # ========================================================
    # 8. SALVAR
    # ========================================================
    arquivo_saida = pasta_saida + f"Loads_Feeder{feeder}.dss"

    with open(arquivo_saida, "w") as f:
        f.write("\n".join(linhas_saida))

    print(f"✅ Arquivo salvo: {arquivo_saida}")