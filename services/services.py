import os
import time
import traceback
from models import adjust_path, format_memory, get_username_from_uid

def fetch_cpu_info(dados):
    """
    Coleta informações detalhadas do CPU.

    Parâmetros:
        dados (object): Objeto para armazenar as informações coletadas, incluindo:
            - quantidadeCPU (int): Número de núcleos.
            - cpu_name (str): Nome do modelo do CPU.
            - cpu_ghz (float): Frequência do CPU em GHz.
            - cpu_usage (float): Uso da CPU em porcentagem.
            - idle_percent (float): Tempo ocioso da CPU em porcentagem.
            - total_processos (int): Número total de processos ativos.
            - total_threads (int): Número total de threads ativas.
    """
    try:
        _collect_basic_cpu_info(dados)
        idle_time, total_time = _read_initial_cpu_times()
        time.sleep(0.1)
        _calculate_cpu_usage(dados, idle_time, total_time)
        _count_active_processes_and_threads(dados)
    except Exception:
        dados.cpu_name = "Unknown"
        dados.cpu_ghz = 0.0
        dados.cpu_usage = 0.0
        dados.idle_percent = 0.0
        dados.total_processos = 0
        dados.total_threads = 0
        print(f"Service - fetch_cpu_info: Erro ao abrir arquivo /proc/cpuinfo")
        traceback.print_exc()

def fetch_memory_info(dados):
    """
    Coleta informações sobre a memória do sistema.

    Parâmetros:
        dados (object): Objeto para armazenar as informações coletadas, incluindo:
            - mtotal (int): Total de memória disponível no sistema (em KB).
            - mLivre (int): Quantidade de memória livre (em KB).
            - mDisponivel (int): Memória disponível para uso (em KB).
            - buffers (int): Quantidade de memória utilizada como buffers (em KB).
            - swapTotal (int): Total de espaço de swap disponível (em KB).
            - swapFree (int): Quantidade de swap livre (em KB).
            - mUsada (int): Quantidade de memória em uso (em KB).
    """
    try:
        meminfo = _read_memory_info()
        _store_memory_info(dados, meminfo)
    except Exception:
        print(f"Service - fetch_memory_info: Erro ao abrir arquivo /proc/meminfo")
        traceback.print_exc()


def fetch_active_processes(dados):
    """
    Coleta informações sobre os processos ativos no sistema.

    Parâmetros:
        dados (object): Objeto para armazenar as informações coletadas, incluindo:
            - processosAtivos (list): Lista de tuplas com informações sobre os processos ativos:
                - usuário (str): Nome do usuário que iniciou o processo.
                - pid (str): ID do processo.
                - estado (str): Estado do processo (exemplo: R, S).
                - memória virtual (str): Tamanho da memória virtual (VSZ).
                - memória residente (str): Tamanho da memória residente (RSS).
                - comando (str): Nome do comando do processo.
    """
    try:
        processos = _collect_processes()
        dados.processosAtivos = processos
    except Exception:
        dados.processosAtivos = []
        print(f"Service - fetch_active_processes: Erro ao abrir arquivo /proc")
        traceback.print_exc()

def fetch_os_info(dados):
    """
    Coleta informações sobre o sistema operacional.

    Parâmetros:
        dados (object): Objeto para armazenar as informações coletadas, incluindo:
            - infoSO (str): Informações do sistema operacional, incluindo:
                - Versão do kernel.
                - Nome do host.
                - Arquitetura do sistema.
    """
    try:
        kernel_info = _read_file_content(adjust_path("/proc/version"))
        hostname = _read_file_content(adjust_path("/proc/sys/kernel/hostname"))
        architecture = _read_file_content(adjust_path("/proc/sys/kernel/osrelease"))
        dados.infoSO = f"Kernel: {kernel_info.strip()}\nHostname: {hostname.strip()}\nArchitecture: {architecture.strip()}"
    except Exception:
        dados.infoSO = "Unknown OS"
        print(f"Service - fetch_os_info: Erro ao abrir arquivos /proc/version /proc/sys/kernel/hostname /proc/sys/kernel/osrelease")
        traceback.print_exc()

def fetch_process_details(pid):
    """
    Coleta detalhes sobre um processo específico com base no seu PID.

    Parâmetros:
        pid (str): ID do processo para o qual os detalhes serão coletados.

    Retorno:
        dict: Dicionário contendo os detalhes do processo, incluindo:
            - User (str): Usuário que iniciou o processo.
            - Chaves adicionais: Informações obtidas a partir do arquivo `/proc/[pid]/status`.
            - Error (str): Mensagem de erro, caso o processo não seja encontrado.
    """
    try:
        status = _read_process_status(pid)
        user = _get_user_from_status(status)
        return _parse_process_details(status, user)
    except Exception:
        return {"Error": f"Process {pid} not found."}

def _collect_basic_cpu_info(dados):
    """
    Lê informações básicas do CPU a partir do arquivo `/proc/cpuinfo`.

    Parâmetros:
        dados (object): Objeto para armazenar as informações do CPU.
    """
    path = adjust_path("/proc/cpuinfo")
    total_cores, cpu_name, cpu_mhz = 0, "", 0.0
    with open(path, "r") as f:
        for line in f:
            if line.startswith("processor"):
                total_cores += 1
            elif line.startswith("model name"):
                cpu_name = line.split(":")[1].strip()
            elif line.startswith("cpu MHz"):
                cpu_mhz = float(line.split(":")[1].strip())
    dados.quantidadeCPU = total_cores
    dados.cpu_name = cpu_name
    dados.cpu_ghz = round(cpu_mhz / 1000, 2)

def _read_initial_cpu_times():
    """
    Lê os tempos iniciais da CPU a partir do arquivo `/proc/stat`.

    Retorno:
        tuple: (idle_time, total_time)
            - idle_time (int): Tempo ocioso inicial.
            - total_time (int): Tempo total inicial.
    """
    stat_path = adjust_path("/proc/stat")
    with open(stat_path, "r") as f:
        for line in f:
            if line.startswith("cpu "):
                values = list(map(int, line.split()[1:]))
                return values[3], sum(values)

def _calculate_cpu_usage(dados, idle_time, total_time):
    """
    Calcula o uso da CPU e o tempo ocioso após um intervalo.

    Parâmetros:
        dados (object): Objeto para armazenar as informações calculadas.
        idle_time (int): Tempo ocioso inicial.
        total_time (int): Tempo total inicial.
    """
    stat_path = adjust_path("/proc/stat")
    with open(stat_path, "r") as f:
        for line in f:
            if line.startswith("cpu "):
                values = list(map(int, line.split()[1:]))
                new_idle_time = values[3]
                new_total_time = sum(values)
                delta_idle = new_idle_time - idle_time
                delta_total = new_total_time - total_time
                cpu_usage = (1 - delta_idle / delta_total) * 100
                idle_percent = (delta_idle / delta_total) * 100
                dados.cpu_usage = round(cpu_usage, 2)
                dados.idle_percent = round(idle_percent, 2)
                break

def _count_active_processes_and_threads(dados):
    """
    Conta o número total de processos e threads ativos no sistema.

    Parâmetros:
        dados (object): Objeto para armazenar os contadores:
            - total_processos (int): Número total de processos.
            - total_threads (int): Número total de threads.
    """
    total_processos, total_threads = 0, 0
    proc_path = adjust_path("/proc")
    for pid in os.listdir(proc_path):
        if pid.isdigit():
            total_processos += 1
            total_threads += _count_threads_in_process(pid)
    dados.total_processos = total_processos
    dados.total_threads = total_threads

def _count_threads_in_process(pid):
    """
    Conta o número de threads em um processo específico.

    Parâmetros:
        pid (str): ID do processo.

    Retorno:
        int: Número de threads do processo.
    """
    try:
        status_path = os.path.join(adjust_path("/proc"), pid, "status")
        with open(status_path, "r") as f:
            for line in f:
                if line.startswith("Threads:"):
                    return int(line.split()[1])
    except (FileNotFoundError, KeyError):
        return 0

def _read_memory_info():
    """
    Lê informações de memória do sistema a partir de `/proc/meminfo`.

    Retorno:
        dict: Dicionário contendo as informações de memória.
    """
    path = adjust_path("/proc/meminfo")
    meminfo = {}
    with open(path, "r") as f:
        for line in f:
            key, value = line.split(":")
            meminfo[key.strip()] = int(value.split()[0])
    return meminfo

def _store_memory_info(dados, meminfo):
    """
    Armazena informações de memória no objeto de dados.

    Parâmetros:
        dados (object): Objeto para armazenar as informações.
        meminfo (dict): Dicionário contendo as informações de memória.
    """
    dados.mtotal = meminfo.get("MemTotal", 0)
    dados.mLivre = meminfo.get("MemFree", 0)
    dados.mDisponivel = meminfo.get("MemAvailable", 0)
    dados.buffers = meminfo.get("Buffers", 0)
    dados.swapTotal = meminfo.get("SwapTotal", 0)
    dados.swapFree = meminfo.get("SwapFree", 0)
    dados.mUsada = dados.mtotal - dados.mLivre - dados.buffers

def _collect_processes():
    """
    Coleta informações de todos os processos ativos.

    Retorno:
        list: Lista de tuplas com informações sobre os processos ativos.
    """
    path = adjust_path("/proc")
    processos = []
    for pid in os.listdir(path):
        if pid.isdigit():
            process_data = _parse_process_status(pid)
            if process_data:
                processos.append(process_data)
    return processos

def _parse_process_status(pid):
    """
    Analisa o arquivo de status de um processo específico.

    Parâmetros:
        pid (str): ID do processo.

    Retorno:
        tuple: Informações do processo (usuário, pid, estado, memória virtual, memória residente, comando).
    """
    try:
        status_path = os.path.join(adjust_path("/proc"), pid, "status")
        user, command, state, vsz, rss = "unknown", "unknown", "S", 0, 0
        with open(status_path, "r") as f:
            for line in f:
                if line.startswith("Name:"):
                    command = line.split()[1]
                elif line.startswith("Uid:"):
                    uid = line.split()[1]
                    user = get_username_from_uid(uid)
                elif line.startswith("State"):
                    state = line.split()[1]
                elif line.startswith("VmSize:"):
                    vsz = int(line.split()[1])
                elif line.startswith("VmRSS:"):
                    rss = int(line.split()[1])
        return (user, pid, state, format_memory(vsz), format_memory(rss), command)
    except (FileNotFoundError, KeyError):
        return None

def _read_file_content(path):
    """
    Lê o conteúdo de um arquivo e retorna como string.

    Parâmetros:
        path (str): Caminho do arquivo a ser lido.

    Retorno:
        str: Conteúdo do arquivo.
    """
    with open(path, "r") as f:
        return f.read()


def _read_process_status(pid):
    """
    Lê o status de um processo específico.

    Parâmetros:
        pid (str): ID do processo.

    Retorno:
        str: Conteúdo do arquivo de status do processo.
    """
    status_path = adjust_path(f"/proc/{pid}/status")
    with open(status_path, "r") as f:
        return f.read()

def _get_user_from_status(status):
    """
    Obtém o usuário a partir do status do processo.

    Parâmetros:
        status (str): Conteúdo do arquivo de status do processo.

    Retorno:
        str: Nome do usuário que iniciou o processo.
    """
    for line in status.splitlines():
        if line.startswith("Uid:"):
            uid = line.split()[1]
            return get_username_from_uid(uid)
    return "unknown"

def _parse_process_details(status, user):
    """
    Analisa os detalhes do processo a partir do status e do usuário.

    Parâmetros:
        status (str): Conteúdo do arquivo de status do processo.
        user (str): Nome do usuário que iniciou o processo.

    Retorno:
        dict: Dicionário contendo os detalhes do processo.
    """
    details = {"User": user}
    for line in status.splitlines():
        key, *value = line.split(":")
        details[key.strip()] = ":".join(value).strip()
    return details
