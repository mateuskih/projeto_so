"""
Módulo de inicialização para o pacote services.


Este módulo fornece funções para monitoramento de informações do sistema operacional, incluindo:
- **CPU**: uso, frequência, número de núcleos, tempo ocioso, etc.
- **Memória**: total, livre, buffers, swap, etc.
- **Processos**: lista de processos ativos com detalhes e threads associadas a processos.
- **Informações Gerais**: dados sobre o sistema operacional, como versão do kernel, arquitetura e hostname.

Exporta:
    - fetch_cpu_info: Coleta informações detalhadas sobre o uso e características da CPU.
    - fetch_memory_info: Coleta dados sobre a memória do sistema, incluindo buffers e swap.
    - fetch_active_processes: Retorna uma lista de processos ativos com informações detalhadas.
    - fetch_os_info: Coleta informações gerais sobre o sistema operacional.
    - fetch_process_details: Obtém detalhes sobre um processo específico com base no PID.
    - fetch_process_tasks: Retorna as threads/tasks associadas a um processo.
    - adjust_path: Ajusta o caminho para compatibilidade com WSL, se necessário.
    - format_memory: Formata valores de memória para MB ou KB.
    - get_username_from_uid: Obtém o nome do usuário com base no UID.

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
