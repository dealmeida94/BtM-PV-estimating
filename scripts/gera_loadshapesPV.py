import pandas as pd
import os

# =========================================================
# 1. CARREGAR DADOS
# =========================================================
arquivo = "dados_tratados.csv"
df = pd.read_csv(arquivo)

df["datetime_local"] = pd.to_datetime(df["datetime_local"])

# =========================================================
# 2. NORMALIZAÇÃO
# =========================================================

df["irradiancia_norm"] = df["irradiancia_W_m2"] / df["irradiancia_W_m2"].max()

df["temp_norm"] = (
    (df["temperatura"] - df["temperatura"].min()) /
    (df["temperatura"].max() - df["temperatura"].min())
)

# =========================================================
# 3. CRIAR DIRETÓRIO
# =========================================================

output_dir = "loadshapes"
os.makedirs(output_dir, exist_ok=True)

# =========================================================
# 4. SALVAR MULTIPLICADORES (.txt)
# =========================================================

pv_path = os.path.join(output_dir, "pv_mult.txt")
temp_path = os.path.join(output_dir, "temp_mult.txt")

df["irradiancia_norm"].round(6).to_csv(pv_path, index=False, header=False)
df["temp_norm"].round(6).to_csv(temp_path, index=False, header=False)

# =========================================================
# 5. CRIAR ARQUIVO DSS (CORRIGIDO)
# =========================================================

npts = len(df)

loadshapes_dss = f"""
New Loadshape.PVShape
~ npts={npts}
~ interval=1
~ mult=(file={pv_path})

New Tshape.TempShape
~ npts={npts}
~ interval=1
~ temp=(file={temp_path})
"""

dss_path = os.path.join(output_dir, "loadshapes.dss")

with open(dss_path, "w") as f:
    f.write(loadshapes_dss)

# =========================================================
# 6. INFO
# =========================================================

print("Arquivos gerados com sucesso!\n")
print(f"PV:   {pv_path}")
print(f"Temp: {temp_path}")
print(f"DSS:  {dss_path}")
print(f"\nNúmero de pontos: {npts}")