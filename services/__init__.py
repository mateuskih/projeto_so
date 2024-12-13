"""
Módulo system_monitor

Este módulo fornece funções para monitoramento de informações do sistema operacional, incluindo:
- CPU: uso, frequência, número de núcleos, tempo ocioso, etc.
- Memória: total, livre, buffers, swap, etc.
- Processos: lista de processos ativos com detalhes.
- Informações gerais do sistema operacional.
"""

from .system_info_service import (
    fetch_cpu_info,
    fetch_memory_info,
    fetch_active_processes,
    fetch_os_info,
    fetch_process_details,
    fetch_process_tasks,
    adjust_path,
    format_memory,
    get_username_from_uid
)
