import os

'''
Gera um arquivo Master.dss

'''

# Definição dos caminhos para os arquivos que contém os elementos da rede,
# os loads e os loadshapes
loc_elementos = "/home/matheus/Documentos/BtM-PV-estimating/elementos_da_rede"
loc_loadshapes = "/home/matheus/Documentos/BtM-PV-estimating/loadshapes"
loc_loads = "/home/matheus/Documentos/BtM-PV-estimating/loads"

# Nome do arquivo de saída
master_novo = "Master_2.dss"

# Elementos do sistema que constam no Master.dss original
elementos_sistema = {
    "Vsource.dss": "Source definition",
    "SubTransformer.dss": "Substation transformer definition",
    "RegControl.dss": "Tap changer control definition",
    "DistriTransformer.dss": "Secondary distribution transformer definition",
    "Linecode.dss": "Line configuration",
    "Line.dss": "Line segment definition",
    "CircuitBreaker.dss": "Circuit breaker definition",
    "Load.dss": "Load definition",
    "Capacitor.dss": "Shunt capacitor bank definition"
}

################################################################################
######  FUNÇÃO PARA LISTAR OS ARQUIVOS .dss CONTIDOS EM UMA PASTA  #############
def listar_arquivos(local):
    arquivos = []
    for f in sorted(os.listdir(local)):
        if f.endswith(".dss"):
            if filtrar_nome:
                if filtrar_nome.lower() not in f.lower():
                    continue
            caminho = os.path.join(local, f)
            arquivos.append(caminho)
    return arquivos

################################################################################
########  FUNÇÃO PARA CRIAR UM DICIONARIO ASSOCIANDO NOME:LOCAL  ###############
def criadic_nome_local(lista_arquivos):
    dic = {}
    for caminho in lista_arquivos:
        nome = os.path.basename(caminho)
        dic[nome] = caminho
    return dic

################################################################################
#################  FUNÇÕES GERA REDIRECTS PARA OS ARQUIVOS  ####################
def gerar_redirects_simples(lista_arquivos):
    return [f'Redirect "{arq}"\n' for arq in lista_arquivos]

def gerar_redirects_compostos(lista_arquivos, arquivos_prioritarios):
    # inclui os comentários descrevendo cada elemento da rede
    elemento_nome = criadic_nome_local(lista_arquivos)
    redirects = []

    for nome, comentario in elementos_sistema.items():
        if nome in elemento_nome:
            caminho = elemento_nome[nome]
            redirects.append(f'Redirect "{caminho}"   ! {comentario}\n')
        else:
            print(f"Arquivo {nome} não encontrado!")

    return redirects


################################################################################
#  EXECUÇÃO:

# Gera listas com os caminhos para os arquivos
elementos = listar_arquivos(loc_elementos)
loadshapes = listar_arquivos(loc_loadshapes, filtrar_nome="loadshape")
loads = listar_arquivos(loc_loads)

# Gera o arquivo Master.dss
novo_conteudo = []

novo_conteudo.append("// This is the OpenDSS Master file to solve the test system time-series power flow using loadshapes.\n")
novo_conteudo.append("Clear\n")
novo_conteudo.append("New Circuit.240_bus_test_system   ! Initiate a new circuit called '240_bus_test_system' \n")

# ELEMENTOS DO SISTEMA
novo_conteudo.append("! ELEMENTOS DO SISTEMA\n")
novo_conteudo.append("!--------------------------------------------------------!\n")
novo_conteudo.extend(gerar_redirects_completos(elementos, elementos_sistema))

# LOADSHAPES
novo_conteudo.append("\n! ==============================\n")
novo_conteudo.append("! LOADSHAPES\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects(loadshapes))

# LOADS
novo_conteudo.append("\n! ==============================\n")
novo_conteudo.append("! LOADS\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects(loads))

novo_conteudo.append("\n!--------------------------Calculate---------------------!\n")
novo_conteudo.append('Set VoltageBases = "69.0, 13.8, 0.208"	! Set base voltage as 69 kV, 13.8 kV, 0.208 kV\n')
novo_conteudo.append("CalcVoltageBases			! Estimate the voltage base for each bus\n") 
novo_conteudo.append("solve					! Solve the circuit\n")

novo_conteudo.append("BusCoords       Buscoords.dss\n\n")

novo_conteudo.append("\n!-------------Show Snapshot Power Flow Result------------!\n")
novo_conteudo.append("!Show Voltage LN Nodes\n")
novo_conteudo.append("!Show currents\n")
novo_conteudo.append("!Show power kva element\n")
novo_conteudo.append("!Show convergence\n")
novo_conteudo.append("!Show isolated\n")
novo_conteudo.append("!Show kvbasemismatch\n")
novo_conteudo.append("!Show losses\n")
novo_conteudo.append("!Show overloads\n")
novo_conteudo.append("!Show topology\n")

novo_conteudo.append("\n!----------------- Plotting -----------------------!\n\n")

novo_conteudo.append("!Set markCapacitors=yes  CapMarkersize=3\n")
novo_conteudo.append("!Set markRegulators=yes  RegMarkersize=5\n")
novo_conteudo.append("!Interpolate\n")
novo_conteudo.append("!Plot Circuit Power Max=500 dots=n labels=n  C1=Blue  1ph=3   ! $00FF0000\n")
novo_conteudo.append("!Plot Circuit voltage Max=0 dots=n n  C1=Blue C2=$FF00FF  1ph=3\n")
novo_conteudo.append("!plot circuit Losses Max=1 dots=n labels=n subs=y C1=Blue\n")


# Salva arquivo
with open(master_novo, "w") as f:
    f.writelines(novo_conteudo)

print(f"Arquivo gerado com sucesso: {master_novo}")