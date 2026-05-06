import pandas as pd

# ==============================
# CONFIGURAÇÕES
# ==============================

PENETRACAO = 0.05

LOAD_FILES = [
    "/home/matheus/Documentos/BtM-PV-estimating/dss/loads/Loads_FeederA.dss",
    "/home/matheus/Documentos/BtM-PV-estimating/dss/loads/Loads_FeederB.dss",
    "/home/matheus/Documentos/BtM-PV-estimating/dss/loads/Loads_FeederC.dss"
]

PARQUET_PATH = "/home/matheus/Documentos/BtM-PV-estimating/dss/potencias_barras.parquet"

OUTPUT_FILE = f"PVSystems_{int(PENETRACAO*100)}.dss"

PV_SHAPE = "PVShape"
TEMP_SHAPE = "TempShape"

MODEL = 1
KV_BASE = 0.208


# ==============================
# 1. MÉDIA DIURNA
# ==============================

def calcula_media_diurna(parquet_path):
    df = pd.read_parquet(parquet_path)

    if "P_kW" not in df.columns:
        raise ValueError("Coluna 'P_kW' não encontrada.")

    df["P_kW_abs"] = df["P_kW"].abs()

    curva_total = df.groupby("hora")["P_kW_abs"].sum()

    # filtra período diurno (6h–18h)
    curva_dia = curva_total[(curva_total.index % 24 >= 6) & (curva_total.index % 24 <= 18)]

    media_dia = curva_dia.mean()

    print(f"Carga média diurna: {media_dia:.2f} kW")

    return media_dia


# ==============================
# 2. META PV
# ==============================

def calcula_meta_pv(media_dia):
    meta = media_dia * PENETRACAO
    print(f"Meta PV (base diurna): {meta:.2f} kW")
    return meta


# ==============================
# 3. BARRAS + CARGA
# ==============================

def extrai_barras_com_potencia(load_files):
    dados = []

    for file in load_files:
        with open(file, "r") as f:
            for linha in f:
                linha_lower = linha.lower()

                if "bus1=" in linha_lower and "kw=" in linha_lower:
                    try:
                        bus = linha_lower.split("bus1=")[1].split()[0]
                        kw = float(linha_lower.split("kw=")[1].split()[0])
                        kw = abs(kw)

                        dados.append({
                            "bus": bus,
                            "kw": kw
                        })

                    except:
                        continue

    print(f"Total de cargas encontradas: {len(dados)}")
    return dados


# ==============================
# FASES
# ==============================

def extrai_fases(bus):
    partes = bus.split(".")

    if len(partes) == 1:
        return 3

    fases = [p for p in partes[1:] if p in ["1", "2", "3"]]

    if len(fases) == 0:
        return 3

    return len(fases)


# ==============================
# 4. DISTRIBUIÇÃO PROPORCIONAL
# ==============================

def distribui_pv_realista(dados_barras, meta_pv):
    distribuicao = []

    total_carga = sum(b["kw"] for b in dados_barras)
    contador = 1

    for barra in dados_barras:

        proporcao = barra["kw"] / total_carga
        pot_barra = proporcao * meta_pv

        # 🔥 limitador
        pot_barra = min(pot_barra, 0.9 * barra["kw"])

        restante = pot_barra

        # 🔥 divide em sistemas menores
        while restante > 0.5:

            pot = min(restante, 5.0)  # tamanho típico (ajustável)

            distribuicao.append({
                "nome": f"PV_{contador}",
                "bus": barra["bus"],
                "potencia": pot
            })

            restante -= pot
            contador += 1

    total_pv = sum(p["potencia"] for p in distribuicao)
    print(f"Total PV alocado: {total_pv:.2f} kW")
    print(f"Número de sistemas PV: {len(distribuicao)}")

    return distribuicao

# ==============================
# 5. GERAR DSS
# ==============================

def gera_dss(distribuicao, output_file):
    linhas = []

    for pv in distribuicao:

        fases = extrai_fases(pv["bus"])

        linha = (
            f"New PVSystem.{pv['nome']} "
            f"bus1={pv['bus']} "
            f"phases={fases} "
            f"kV={KV_BASE} "
            f"kVA={pv['potencia']:.3f} "
            f"Pmpp={pv['potencia']:.3f} "
            f"model={MODEL} "
            f"conn=wye "
            f"pf=1 "  # 🔥 mantido conforme pedido
            f"irradiance=1 "
            f"temperature=25 "
            f"daily={PV_SHAPE} "
            f"Tdaily={TEMP_SHAPE}"
        )

        linhas.append(linha)

    with open(output_file, "w") as f:
        f.write("\n".join(linhas))

    print(f"Arquivo DSS gerado: {output_file}")


# ==============================
# MAIN
# ==============================

def main():

    media_dia = calcula_media_diurna(PARQUET_PATH)

    meta_pv = calcula_meta_pv(media_dia)

    dados_barras = extrai_barras_com_potencia(LOAD_FILES)

    distribuicao = distribui_pv_realista(dados_barras, meta_pv)

    gera_dss(distribuicao, OUTPUT_FILE)


if __name__ == "__main__":
    main()