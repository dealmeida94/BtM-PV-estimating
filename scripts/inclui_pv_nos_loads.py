import pandas as pd
import random

# ==============================
# CONFIGURAÇÕES
# ==============================

PENETRACAO = 0.10
POT_MIN = 1
POT_MAX = 15

LOAD_FILES = [
    "/home/matheus/Documentos/BtM-PV-estimating/dss/loads/Loads_FeederA.dss",
    "/home/matheus/Documentos/BtM-PV-estimating/dss/loads/Loads_FeederB.dss",
    "/home/matheus/Documentos/BtM-PV-estimating/dss/loads/Loads_FeederC.dss"
]

OUTPUT_FILE = f"PVSystems_{int(PENETRACAO*100)}.dss"

PV_SHAPE = "PVShape"
TEMP_SHAPE = "TempShape"

MODEL = 1
KV_BASE = 0.208


# ==============================
# 1. POTÊNCIA TOTAL
# ==============================

def calcula_potencia_total(parquet_path):
    df = pd.read_parquet(parquet_path)

    if "P_kW" not in df.columns:
        raise ValueError("Coluna 'P_kW' não encontrada.")

    df["P_kW_abs"] = df["P_kW"].abs()
    curva_total = df.groupby("hora")["P_kW_abs"].sum()

    total = curva_total.max()

    print(f"Potência máxima do sistema: {total:.2f} kW")
    return total


# ==============================
# 2. META PV
# ==============================

def calcula_meta_pv(total):
    meta = total * PENETRACAO
    print(f"Meta de PV ({PENETRACAO*100:.0f}%): {meta:.2f} kW")
    return meta


# ==============================
# 3. GERAR PVs
# ==============================

def gera_lista_pvs(meta_kw):
    pvs = []
    soma = 0

    while soma < meta_kw:
        pot = random.randint(POT_MIN, POT_MAX)
        pvs.append(pot)
        soma += pot

    pvs.sort(reverse=True)

    print(f"Total gerado de PV: {soma:.2f} kW ({len(pvs)} sistemas)")
    return pvs


# ==============================
# 4. BARRAS + CARGA
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
                            "kw": kw,
                            "pv_alocado": 0
                        })

                    except:
                        continue

    print(f"Total de cargas encontradas: {len(dados)}")
    return dados


# ==============================
# 🔥 extrai número de fases
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
# 5. DISTRIBUIÇÃO
# ==============================

def distribui_pvs_com_limite(pvs, dados_barras):
    distribuicao = []
    nao_alocados = []

    for i, pot_pv in enumerate(pvs):

        for _ in range(100):
            barra = random.choice(dados_barras)

            if barra["pv_alocado"] + pot_pv <= barra["kw"]:
                barra["pv_alocado"] += pot_pv

                distribuicao.append({
                    "nome": f"PV_{i+1}",
                    "bus": barra["bus"],
                    "potencia": pot_pv
                })
                break
        else:
            nao_alocados.append(pot_pv)

    print(f"PVs alocados: {len(distribuicao)}")
    print(f"PVs não alocados: {len(nao_alocados)}")

    return distribuicao


# ==============================
# 🔥 GERAR DSS (CORRIGIDO MESMO)
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
            f"kVA={pv['potencia']} "
            f"Pmpp={pv['potencia']} "
            f"model={MODEL} "
            f"conn=wye "          # 🔥 ESSENCIAL
            f"pf=1 "              # 🔥 ESSENCIAL
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
    parquet_path = "/home/matheus/Documentos/BtM-PV-estimating/dss/potencias_barras.parquet"

    total = calcula_potencia_total(parquet_path)
    meta = calcula_meta_pv(total)

    pvs = gera_lista_pvs(meta)
    dados_barras = extrai_barras_com_potencia(LOAD_FILES)

    distribuicao = distribui_pvs_com_limite(pvs, dados_barras)

    gera_dss(distribuicao, OUTPUT_FILE)


if __name__ == "__main__":
    main()