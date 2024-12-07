import os
import time
from models import adjust_path, format_memory, get_username_from_uid

# Função para buscar informações sobre o CPU
def buscaInformacoesCPU(dados):
    """
    Coleta informações detalhadas do CPU, incluindo:
    - Quantidade de núcleos
    - Nome do modelo
    - Frequência (GHz)
    - Uso do CPU (%)
    - Percentual de tempo ocioso
    - Total de processos e threads ativas no sistema

    Parâmetros:
        dados: Objeto que armazena as informações coletadas
    """
    try:
        # Caminho para o arquivo de informações do CPU
        path = adjust_path("/proc/cpuinfo")
        total_cores = 0
        cpu_name = ""
        cpu_mhz = 0.0

        # Lê as informações básicas do CPU
        with open(path, "r") as f:
            for line in f:
                if line.startswith("processor"):
                    total_cores += 1
                elif line.startswith("model name"):
                    cpu_name = line.split(":")[1].strip()
                elif line.startswith("cpu MHz"):
                    cpu_mhz = float(line.split(":")[1].strip())

        # Salva as informações no objeto
        dados.quantidadeCPU = total_cores
        dados.cpu_name = cpu_name
        dados.cpu_ghz = round(cpu_mhz / 1000, 2)

        # Calcula o uso do CPU
        stat_path = adjust_path("/proc/stat")
        with open(stat_path, "r") as f:
            for line in f:
                if line.startswith("cpu "):
                    values = list(map(int, line.split()[1:]))
                    idle_time = values[3]
                    total_time = sum(values)
                    time.sleep(0.1)  # Aguarda para medir a diferença
                    break

        # Recalcula o uso do CPU após um intervalo
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

        # Contabiliza processos e threads ativos
        total_processos = 0
        total_threads = 0
        proc_path = adjust_path("/proc")
        for pid in os.listdir(proc_path):
            if pid.isdigit():
                total_processos += 1
                try:
                    status_path = os.path.join(proc_path, pid, "status")
                    with open(status_path, "r") as f:
                        for line in f:
                            if line.startswith("Threads:"):
                                total_threads += int(line.split()[1])
                except (FileNotFoundError, KeyError):
                    continue

        dados.total_processos = total_processos
        dados.total_threads = total_threads

    except FileNotFoundError:
        # Define valores padrão em caso de erro
        dados.cpu_name = "Unknown"
        dados.cpu_ghz = 0.0
        dados.cpu_usage = 0.0
        dados.idle_percent = 0.0
        dados.total_processos = 0
        dados.total_threads = 0

# Função para buscar informações de memória
def buscaInfoMemoria(dados):
    """
    Coleta informações sobre a memória do sistema, incluindo:
    - Total de memória
    - Memória livre
    - Memória disponível
    - Buffers
    - Swap total e livre
    - Memória usada

    Parâmetros:
        dados: Objeto que armazena as informações coletadas
    """
    try:
        path = adjust_path("/proc/meminfo")
        meminfo = {}
        with open(path, "r") as f:
            for line in f:
                key, value = line.split(":")
                meminfo[key.strip()] = int(value.split()[0])

        dados.mtotal = meminfo.get("MemTotal", 0)
        dados.mLivre = meminfo.get("MemFree", 0)
        dados.mDisponivel = meminfo.get("MemAvailable", 0)
        dados.buffers = meminfo.get("Buffers", 0)
        dados.swapTotal = meminfo.get("SwapTotal", 0)
        dados.swapFree = meminfo.get("SwapFree", 0)
        dados.mUsada = dados.mtotal - dados.mLivre - dados.buffers
    except FileNotFoundError:
        pass

# Função para buscar processos ativos
def buscaProcessosAtivos(dados):
    """
    Coleta informações sobre os processos ativos no sistema, incluindo:
    - Usuário que iniciou o processo
    - ID do processo (PID)
    - Estado do processo
    - Tamanho virtual (VSZ) e residente (RSS)
    - Nome do comando

    Parâmetros:
        dados: Objeto que armazena as informações coletadas
    """
    try:
        path = adjust_path("/proc")
        processos = []
        for pid in os.listdir(path):
            if pid.isdigit():
                try:
                    status_path = os.path.join(path, pid, "status")
                    with open(status_path, "r") as f:
                        status = f.read()
                        user = "unknown"
                        command = "unknown"
                        state = "S"
                        vsz = 0
                        rss = 0
                        uid = ""
                        for line in status.splitlines():
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
                        processos.append((user, pid, state, format_memory(vsz), format_memory(rss), command))
                except (FileNotFoundError, KeyError):
                    continue
        dados.processosAtivos = processos
    except FileNotFoundError:
        dados.processosAtivos = []

# Função para buscar informações do sistema operacional
def buscaInfoSO(dados):
    """
    Coleta informações sobre o sistema operacional, incluindo:
    - Versão do kernel
    - Nome do host
    - Arquitetura do sistema

    Parâmetros:
        dados: Objeto que armazena as informações coletadas
    """
    try:
        path = adjust_path("/proc/version")
        hostname_path = adjust_path("/proc/sys/kernel/hostname")
        architecture_path = adjust_path("/proc/sys/kernel/osrelease")

        with open(path, "r") as f:
            kernel_info = f.readline().strip()
        with open(hostname_path, "r") as f:
            hostname = f.readline().strip()
        with open(architecture_path, "r") as f:
            architecture = f.readline().strip()

        dados.infoSO = f"Kernel: {kernel_info}\nHostname: {hostname}\nArchitecture: {architecture}"
    except FileNotFoundError:
        dados.infoSO = "Unknown OS"

# Função para buscar detalhes de um processo específico
def buscaDetalhesProcesso(pid):
    """
    Coleta detalhes sobre um processo específico com base no seu PID.

    Parâmetros:
        pid: ID do processo
    Retorno:
        details: Dicionário com as informações do processo
    """
    details = {}
    try:
        status_path = adjust_path(f"/proc/{pid}/status")
        with open(status_path, "r") as f:
            for line in f:
                key, *value = line.split(":")
                details[key.strip()] = ":".join(value).strip()

        if "Uid" in details:
            uid = details["Uid"].split()[0]
            details["User"] = get_username_from_uid(uid)
    except (FileNotFoundError, KeyError):
        details["Error"] = f"Process {pid} not found."
    return details
