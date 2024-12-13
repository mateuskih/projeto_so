"""
Módulo de inicialização para o pacote views.

Este módulo fornece a interface gráfica principal e funcionalidades auxiliares para o monitoramento do sistema operacional.

Funcionalidades:
- **DashboardApp**: Classe principal para a interface gráfica com gráficos em tempo real para CPU, memória e processos.
- **ProcessDetailsWindow**: Classe que exibe detalhes de um processo específico e suas threads (tasks).

Classes:
- **DashboardApp**: Implementa a interface gráfica principal do dashboard, permitindo a visualização em tempo real de informações de CPU, memória, e processos.
- **ProcessDetailsWindow**: Exibe informações detalhadas sobre um processo específico, incluindo threads/tasks associadas.
"""
from .dashboard_view import DashboardApp
from .process_details_view import ProcessDetailsWindow
