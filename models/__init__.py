"""
Módulo de inicialização para o pacote models.

Este módulo expõe as principais classes e funções do pacote models, 
permitindo que sejam facilmente importadas e utilizadas em outros 
módulos do projeto.

Exporta:
    - SystemInfo: Classe que armazena informações sobre o sistema, 
      incluindo CPU, memória e processos.
    - adjust_path: Função para ajustar caminhos, especialmente ao 
      trabalhar com o Windows Subsystem for Linux (WSL).
    - format_memory: Função para formatar tamanhos de memória em MB 
      ou KB, com duas casas decimais.
    - get_username_from_uid: Função para buscar o nome do usuário 
      associado a um UID, lendo o arquivo /etc/passwd.
"""

from .models import SystemInfo, adjust_path, format_memory, get_username_from_uid
