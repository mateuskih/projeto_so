"""
Módulo de inicialização para o pacote models.

Este módulo serve como um ponto de entrada para o pacote `models`, expondo 
as principais classes necessárias para manipulação e armazenamento de 
informações relacionadas ao sistema e processos.

Exporta:
    - SystemInfo: Classe que encapsula informações detalhadas sobre o sistema, 
      como CPU, memória, e processos ativos.
    - ProcessDetails: Classe que armazena informações detalhadas de um processo 
      específico, incluindo atributos como PID, estado, e uso de memória.
"""

from .system_info_model import SystemInfo
from .process_details_model import ProcessDetails