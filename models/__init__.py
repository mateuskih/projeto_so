"""
Módulo de inicialização para o pacote models.

Este módulo expõe as principais classes e funções do pacote models, 
permitindo que sejam facilmente importadas e utilizadas em outros 
módulos do projeto.

Exporta:
    - SystemInfo: Classe que armazena informações sobre o sistema, 
      incluindo CPU, memória e processos.
"""

from .system_info_model import SystemInfo
from .process_details_model import ProcessDetails