import re

arquivo_entrada = "Load.dss"
arquivo_saida = "Load_corrigido.dss"

with open(arquivo_entrada) as f:
    linhas = f.readlines()

linhas_corrigidas = []

for linha in linhas:

    if linha.strip().lower().startswith("new load"):

        match = re.search(r'Load_(\d+)', linha)

        if match:
            numero = match.group(1)

            linha = linha.strip() + f" yearly=LS_Bus{numero}\n"

    linhas_corrigidas.append(linha)

with open(arquivo_saida, "w") as f:
    f.writelines(linhas_corrigidas)

print("Load_corrigido.dss criado.")