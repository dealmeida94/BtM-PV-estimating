import pandas as pd
import re
from pathlib import Path

# -------------------------------
# CONFIG
# -------------------------------
pasta_dados = "C:/Users/User/Documents/GitHub/BtM-PV-estimating/loadshapes/"
feeders = ["A", "B", "C"]

pasta_saida = "C:/Users/User/Documents/GitHub/BtM-PV-estimating/dados_processados/"


# -------------------------------
# FUNÇÃO: extrair loadshapes do DSS
# -------------------------------
def extrair_loadshapes(caminho_dss):
    loadshapes = {}

    with open(caminho_dss, "r") as f:
        for linha in f:
            linha = linha.strip()
    
            if linha.lower().startswith("new loadshape"):
    
                # 🔥 pega nome completo (mesmo com espaço)
                match = re.search(r"Loadshape\.(.*?)\s+npts", linha, re.IGNORECASE)
                
                if not match:
                    print(f"⚠️ erro ao ler linha: {linha}")
                    continue
    
                nome = match.group(1)
                print(nome)
                # extrai número do bus
                bus_match = re.search(r"Bus\s*(\d+)", nome, re.IGNORECASE)
                print(bus_match)
    
                if not bus_match:
                    print(f"⚠️ sem bus: {nome}")
                    continue
    
                numero_bus = bus_match.group(1)
                bus_formatado = f"Bus {numero_bus}"
    
                # 🔥 separa P e Q
                if "_P" in nome:
                    tipo = "P"
                elif "_Q" in nome:
                    tipo = "Q"
                else:
                    tipo = "?"
    
                # cria estrutura organizada
                if bus_formatado not in loadshapes:
                    loadshapes[bus_formatado] = {}
    
                loadshapes[bus_formatado][tipo] = nome
    
               
    
        return loadshapes


# -------------------------------
# PROCESSAMENTO
# -------------------------------
for feeder in feeders:
    print(f"\n🔄 Processando Feeder {feeder}")

    arquivo_dss = pasta_dados + f"Loadshapes_Feeder{feeder}.dss"
    arquivo_csv = pasta_dados + f"Bases_Feeder{feeder}.csv"

    # 1. Ler dados
    df = pd.read_csv(arquivo_csv)

    # padroniza nomes
    df.columns = [c.lower() for c in df.columns]

    # 2. Extrair loadshapes
    loadshapes = extrair_loadshapes(arquivo_dss)

    if not loadshapes:
        raise ValueError(f"❌ Nenhum loadshape encontrado no feeder {feeder}")

    linhas_saida = []
    faltantes = []

    # 3. Percorrer bases
    for _, row in df.iterrows():
        load = str(row["load"])
        bus = row["bus"]
        kv = row["kv"]
        kw = row["kw"]
        kvar = row["kvar"]
        phases = int(row.get("phases", 3))

        # extrai ID numérico do load
        match = re.search(r"(\d+)", load)
        if not match:
            continue

        load_id = match.group(1)

        # 4. Verificar se existe loadshape correspondente
        if load_id not in loadshapes:
            faltantes.append(load)
            continue

        nome_ls = loadshapes[load_id]

        # 5. Montar linha DSS
        linha = (
            f"New Load.{load} "
            f"phases={phases} conn=wye "
            f"bus1={bus} "
            f"kV={kv} "
            f"kW={kw:.3f} kvar={kvar:.3f} "
            f"daily={nome_ls} model=1"
        )

        linhas_saida.append(linha)

    # 6. Aviso de inconsistências
    if faltantes:
        print(f"⚠️ Loads sem loadshape ({len(faltantes)}):")
        for f in faltantes[:10]:
            print("   ", f)

    # 7. Salvar arquivo
    arquivo_saida = pasta_saida / f"Loads_Feeder{feeder}.dss"

    with open(arquivo_saida, "w") as f:
        f.write("\n".join(linhas_saida))

    print(f"✅ Arquivo salvo: {arquivo_saida}")
