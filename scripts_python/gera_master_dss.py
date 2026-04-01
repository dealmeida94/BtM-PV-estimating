import os

# ==============================
# CONFIGURAÇÕES
# ==============================

master_novo = "Master_2.dss"

dir_elementos = "/home/matheus/Documentos/BtM-PV-estimating/elementos_da_rede"
dir_loadshapes = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes"
dir_loads = "/home/matheus/Documentos/BtM-PV-estimating/loads"


# ==============================
# LISTAR ARQUIVOS DSS
# ==============================

def listar_dss(diretorio, filtro_nome=None):
    arquivos = []
    for f in sorted(os.listdir(diretorio)):
        if f.endswith(".dss"):
            if filtro_nome:
                if filtro_nome.lower() not in f.lower():
                    continue
            caminho = os.path.join(diretorio, f)
            arquivos.append(caminho)
    return arquivos


# ==============================
# GERAR REDIRECTS
# ==============================

def gerar_redirects(lista_arquivos):
    return [f'Redirect "{arq}"\n' for arq in lista_arquivos]


# ==============================
# LISTAGEM DOS ARQUIVOS
# ==============================

elementos = listar_dss(dir_elementos)
loadshapes = listar_dss(dir_loadshapes, filtro_nome="loadshape")
loads = listar_dss(dir_loads)


# ==============================
# GERAR NOVO MASTER (DO ZERO)
# ==============================

novo_conteudo = []

novo_conteudo.append("! ==============================\n")
novo_conteudo.append("! MASTER GERADO AUTOMATICAMENTE\n")
novo_conteudo.append("! ==============================\n\n")

# ELEMENTOS
novo_conteudo.append("! ==============================\n")
novo_conteudo.append("! ELEMENTOS DA REDE\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects(elementos))

# LOADSHAPES (filtrados)
novo_conteudo.append("\n! ==============================\n")
novo_conteudo.append("! LOADSHAPES\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects(loadshapes))

# LOADS
novo_conteudo.append("\n! ==============================\n")
novo_conteudo.append("! LOADS\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects(loads))


# ==============================
# SALVAR
# ==============================

with open(master_novo, "w") as f:
    f.writelines(novo_conteudo)


print(f"Arquivo gerado com sucesso: {master_novo}")