'''
Gera um arquivo Master.dss baseado no arquivo Master.dss original
'''

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import configs as cfg


# Elementos do sistema que constam no Master.dss original
elementos_sistema = {
    "Vsource.dss": "Source definition",
    "SubTransformer.dss": "Substation transformer definition",
    "RegControl.dss": "Tap changer control definition",
    "DistriTransformer.dss": "Secondary distribution transformer definition",
    "Linecode.dss": "Line configuration",
    "Line.dss": "Line segment definition",
    "CircuitBreaker.dss": "Circuit breaker definition",
    "Capacitor.dss": "Shunt capacitor bank definition"
}

################################################################################
######  FUNÇÃO PARA LISTAR OS ARQUIVOS .dss CONTIDOS EM UMA PASTA  #############
#
# local: diretório onde será feita a busca
# filtrar_nome: verifica se a string informada existe no nome do arquivo
# se não for informado, assume None e não aplica filtro
#
# retorna uma lista com os caminhos completos de cada arquivo encontrado
def listar_arquivos(local, filtrar_nome = None):
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
# Recebe uma lista de arquivos como argumento e retorna um dicionário associando
# nome do arquivo ao caminho completo do arquivo
def criadic_nome_local(lista_arquivos):
    dic = {}
    for caminho in lista_arquivos:
        nome = os.path.basename(caminho)
        dic[nome] = caminho
    return dic

################################################################################
#################  FUNÇÕES GERA REDIRECTS PARA OS ARQUIVOS  ####################
# Recebe uma lista de arquivos e retorna uma lista de strings no formato
# Redirect "caminho do arquivo"
def gerar_redirects_simples(lista_arquivos):
    return [f'Redirect "{arq}"\n' for arq in lista_arquivos]

# Recebe uma lista de arquivos e um conjunto de arquivos prioritários, que
#precisam ser declarados primeiro no Master.dss
# Retorna as strings no formato Redirect "caminho do arquivo" com comentários
def gerar_redirects_compostos(lista_arquivos, arquivos_prioritarios):
    elemento_nome = criadic_nome_local(lista_arquivos)
    redirects = []
    
    for nome, comentario in elementos_sistema.items():
        if nome in elemento_nome:
            caminho = elemento_nome[nome]
            raiz = f'Redirect "{caminho}"'
            raiz_ajustada = raiz.ljust(100) # Ajusta tamanho da string
            redirects.append(f'{raiz_ajustada}! {comentario}\n')
        else:
            print("\nERRO!!!\n")
            print(f"Arquivo {nome} não encontrado.\n")
    return redirects

################################################################################
################################################################################


################################################################################
######################## GERA O ARQUIVO MASTER.dss #############################

# Produz as listas com os caminhos para os arquivos
elementos = listar_arquivos(cfg.ELEM_DIR)
loadshapes = listar_arquivos(cfg.BASE_LOAD, filtrar_nome="Loadshapes")
loads = listar_arquivos(cfg.BASE_LOAD, filtrar_nome='Loads')

# Gera o arquivo Master.dss
novo_conteudo = []

novo_conteudo.append("// This is the OpenDSS Master file to solve the test system time-series power flow using loadshapes.\n\n")
novo_conteudo.append("Clear\n")
novo_conteudo.append("New Circuit.240_bus_test_system   ! Initiate a new circuit called '240_bus_test_system' \n\n\n")

# ELEMENTOS DO SISTEMA
novo_conteudo.append("! ELEMENTOS DO SISTEMA\n")
novo_conteudo.append("!--------------------------------------------------------!\n")
novo_conteudo.extend(gerar_redirects_compostos(elementos, elementos_sistema))

# LOADSHAPES
novo_conteudo.append("\n\n\n! ==============================\n")
novo_conteudo.append("! LOADSHAPES\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects_simples(loadshapes))

# LOADS
novo_conteudo.append("\n\n\n! ==============================\n")
novo_conteudo.append("! LOADS\n")
novo_conteudo.append("! ==============================\n")
novo_conteudo.extend(gerar_redirects_simples(loads))

novo_conteudo.append("\n\n\n!--------------------------Calculate---------------------!\n")
novo_conteudo.append('Set VoltageBases = "69.0, 13.8, 0.208"	! Set base voltage as 69 kV, 13.8 kV, 0.208 kV\n')
novo_conteudo.append("CalcVoltageBases			! Estimate the voltage base for each bus\n") 
novo_conteudo.append("solve					! Solve the circuit\n")

novo_conteudo.append("BusCoords       Buscoords.dss\n\n")

novo_conteudo.append("\n\n\n!-------------Show Snapshot Power Flow Result------------!\n")
novo_conteudo.append("!Show Voltage LN Nodes\n")
novo_conteudo.append("!Show currents\n")
novo_conteudo.append("!Show power kva element\n")
novo_conteudo.append("!Show convergence\n")
novo_conteudo.append("!Show isolated\n")
novo_conteudo.append("!Show kvbasemismatch\n")
novo_conteudo.append("!Show losses\n")
novo_conteudo.append("!Show overloads\n")
novo_conteudo.append("!Show topology\n")

novo_conteudo.append("\n\n\n!----------------- Plotting -----------------------!\n\n")

novo_conteudo.append("!Set markCapacitors=yes  CapMarkersize=3\n")
novo_conteudo.append("!Set markRegulators=yes  RegMarkersize=5\n")
novo_conteudo.append("!Interpolate\n")
novo_conteudo.append("!Plot Circuit Power Max=500 dots=n labels=n  C1=Blue  1ph=3   ! $00FF0000\n")
novo_conteudo.append("!Plot Circuit voltage Max=0 dots=n n  C1=Blue C2=$FF00FF  1ph=3\n")
novo_conteudo.append("!plot circuit Losses Max=1 dots=n labels=n subs=y C1=Blue\n")


# Salva arquivo
with open(cfg.BASE_LOAD / "Master.dss", "w") as f:
    f.writelines(novo_conteudo)

print(f"Arquivo 'Master.dss' salvo em: {cfg.BASE_LOAD}")