#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 11:32:44 2026

@author: matheus
"""

from pathlib import Path

# Pasta base (raiz)
BASE_DIR = Path(__file__).resolve().parent

# Dados
DADOS_DIR = BASE_DIR / "dados"
EXTERNOS_DIR = DADOS_DIR / "externos"
WANG_DIR = EXTERNOS_DIR / "zhaoyu_wang"
PROCESSADOS_DIR = DADOS_DIR / "processados"
NODAL_PeQ = PROCESSADOS_DIR / "Nodal_P&Q_processado.xlsx"
LOAD_ORG = WANG_DIR / "dss_originais"


# DSS
DSS_DIR = BASE_DIR / "dss"
LS_DIR = DSS_DIR / "loadshapes"
LOADS_DIR = DSS_DIR / "loads"


# Resultados
RESULTADOS_DIR = BASE_DIR / "resultados"
FIG_DIR = RESULTADOS_DIR / "figuras"
FIG_NPQ_DIR = FIG_DIR / "Nodal_P&Q_plots"
CFG_LOADS = DADOS_DIR / "processados" / "configuracoes_dos_loads.xlsx"
FIG_SIMU_DIR = RESULTADOS_DIR / "figuras_simulacao"

# Relatorios
LOGS_DIR = BASE_DIR / "relatorios"

#caminho para dados climáticos
CLIMATICOS_DIR = EXTERNOS_DIR / "climaticos"