"""
Módulo Dashboard

Este módulo fornece a interface gráfica principal e funcionalidades auxiliares para o monitoramento do sistema operacional.

Funcionalidades:
- `DashboardApp`: Classe principal para a interface gráfica com gráficos em tempo real para CPU e memória.
- `ProcessDetailsWindow`: Classe que exibe detalhes de um processo específico.

Classes:
- `DashboardApp`: Classe principal que implementa a interface gráfica da aplicação.
- `ProcessDetailsWindow`: Classe para exibição de informações detalhadas sobre um processo.

Imports:
- Funções de serviços e utilitários adicionais para suporte às classes do módulo.
"""

from .dashboard_view import DashboardApp
from .process_details_view import ProcessDetailsWindow
