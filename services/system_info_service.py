import os
import time
import traceback

from models.process_details_model import ProcessDetails

WSL_PATH = r"\\wsl.localhost\Ubuntu-20.04"


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
        collect_basic_cpu_info(dados)
        idle_time, total_time = read_initial_cpu_times()
        time.sleep(0.1)
        calculate_cpu_usage(dados, idle_time, total_time)
        count_active_processes_and_threads(dados)
    except Exception:
        dados.cpu_name = "Unknown"
        dados.cpu_ghz = 0.0
        dados.cpu_usage = 0.0
        dados.idle_percent = 0.0
        dados.total_processos = 0
        dados.total_threads = 0
        print(f"system_info_service - fetch_cpu_info: Erro ao abrir arquivo /proc/cpuinfo")
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
        meminfo = read_memory_info()
        store_memory_info(dados, meminfo)
    except Exception:
        print(f"system_info_service - fetch_memory_info: Erro ao abrir arquivo /proc/meminfo")
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
        processos = collect_processes()
        dados.processosAtivos = processos
    except Exception:
        dados.processosAtivos = []
        print(f"system_info_service - fetch_active_processes: Erro ao abrir arquivo /proc")
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
        kernel_info = read_file_content(adjust_path("/proc/version"))
        hostname = read_file_content(adjust_path("/proc/sys/kernel/hostname"))
        architecture = read_file_content(adjust_path("/proc/sys/kernel/osrelease"))
        dados.infoSO = f"Kernel: {kernel_info.strip()}\nHostname: {hostname.strip()}\nArchitecture: {architecture.strip()}"
    except Exception:
        dados.infoSO = "Unknown OS"
        print(f"system_info_service - fetch_os_info: Erro ao abrir arquivos /proc/version /proc/sys/kernel/hostname /proc/sys/kernel/osrelease")
        traceback.print_exc()


def fetch_process_details(pid, process_details):
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
        status = read_process_status(pid)
        parse_process_details(status, process_details)
    except Exception:
        return {"Error": f"Process {pid} not found."}
    

def fetch_process_tasks(pid, tasks):
    """
    Coleta detalhes sobre as threads de um processo específico com base no PID.

    Parâmetros:
        pid (str): ID do processo para o qual os detalhes serão coletados.
        tasks (list): Lista para armazenar os objetos `ProcessDetails` das threads.
    """
    try:
        process_tasks = read_process_tasks(pid)  # Lê os dados das threads no diretório `/proc/[pid]/task`
        tasks.clear()  # Limpa a lista de threads para garantir que está vazia antes de começar

        # Processa cada thread (task) e adiciona à lista
        for task_status in process_tasks:
            task_details = ProcessDetails()  # Cria um novo objeto para armazenar os detalhes da thread
            parse_process_details("\n".join(task_status), task_details)  # Analisa os detalhes da thread
            tasks.append(task_details)  # Adiciona o objeto processado à lista de tasks
    except Exception as e:
        print(f"Error fetching threads for PID {pid}: {e}")
        traceback.print_exc()


def collect_basic_cpu_info(dados):
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


def read_initial_cpu_times():
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


def calculate_cpu_usage(dados, idle_time, total_time):
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


def count_active_processes_and_threads(dados):
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
            total_threads += count_threads_in_process(pid)
    dados.total_processos = total_processos
    dados.total_threads = total_threads


def count_threads_in_process(pid):
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


def read_memory_info():
    """
    Lê informações de memória do sistema a partir de `/proc/meminfo`.

    Retorno:
        dict: Dicionário contendo as informações de memória.
    """
    try:
        path = adjust_path("/proc/meminfo")
        meminfo = {}
        with open(path, "r") as f:
            for line in f:
                key, value = line.split(":")
                meminfo[key.strip()] = int(value.split()[0])
        return meminfo
    except Exception:
        print(f"system_info_service - get_username_from_uid: Erro ao abrir arquivo {path}")
        traceback.print_exc()


def store_memory_info(dados, meminfo):
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


def collect_processes():
    """
    Coleta informações de todos os processos ativos.

    Retorno:
        list: Lista de tuplas com informações sobre os processos ativos.
    """
    path = adjust_path("/proc")
    processos = []
    for pid in os.listdir(path):
        if pid.isdigit():
            process_data = parse_process_status(pid)
            if process_data:
                processos.append(process_data)
    return processos


def parse_process_status(pid):
    """
    Analisa o arquivo de status de um processo específico.

    Parâmetros:
        pid (str): ID do processo.

    Retorno:
        tuple: Informações do processo (usuário, pid, estado, memória virtual, memória residente, comando).
    """
    try:
        status_path = os.path.join(adjust_path("/proc"), pid, "status")
        user, command, state, threads, vsz, rss = "unknown", "unknown", "S", 0, 0, 0
        with open(status_path, "r") as f:
            for line in f:
                if line.startswith("Name:"):
                    command = line.split()[1]
                elif line.startswith("Uid:"):
                    uid = line.split()[1]
                    user = get_username_from_uid(uid)
                elif line.startswith("State"):
                    state = line.split()[1]
                elif line.startswith("Threads:"):
                    threads = line.split()[1]
                elif line.startswith("VmSize:"): # (Virtual Memory Size)
                    vsz = int(line.split()[1])
                elif line.startswith("VmRSS:"): # (Resident Set Size)
                    rss = int(line.split()[1])
        return (user, pid, state, threads, format_memory(vsz), format_memory(rss), command)
    except (FileNotFoundError, KeyError):
        return None


def read_file_content(path):
    """
    Lê o conteúdo de um arquivo e retorna como string.

    Parâmetros:
        path (str): Caminho do arquivo a ser lido.

    Retorno:
        str: Conteúdo do arquivo.
    """
    with open(path, "r") as f:
        return f.read()


def read_process_status(pid):
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
    

def read_process_tasks(pid):
    """
    Lê os detalhes das threads (tasks) de um processo específico com base no PID.

    Esta função acessa o diretório `/proc/<pid>/task` para listar todas as threads associadas a um processo e retorna as informações do arquivo `status` de cada thread.

    Parâmetros:
        pid (int): ID do processo (PID) cujas threads serão lidas.

    Retorno:
        list: Lista de listas, onde cada sublista contém as linhas do arquivo `status` de uma task específica.

    """
    tasks_path = adjust_path(f"/proc/{pid}/task")

    # Verificar se o diretório existe
    if not os.path.exists(tasks_path):
        raise FileNotFoundError(f"Process with PID {pid} not found.")

    tasks_data = []

    # Iterar sobre cada thread (task) no diretório
    for tid in os.listdir(tasks_path):
        if tid.isdigit():
            task_path_info = os.path.join(tasks_path, tid)

            try:
                # Ler informações básicas da thread
                with open(os.path.join(task_path_info, "status"), "r") as f:
                    status_lines = f.readlines()
                    tasks_data.append(status_lines)

            except FileNotFoundError:
                continue

    return tasks_data


def get_user_from_status(status):
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


def parse_process_details(status, process_details):
    """
    Analisa os detalhes do processo a partir do conteúdo do arquivo de status.

    Parâmetros:
        status (str): Conteúdo do arquivo `status` do processo, contendo informações sobre o processo.
        process_details (ProcessDetails): Objeto onde os detalhes do processo serão armazenados.

    Retorno:
        dict: Dicionário contendo os detalhes do processo.
    """
    details = {}
    for line in status.splitlines():
        key, *value = line.split(":")
        details[key.strip()] = ":".join(value).strip()
    
    process_details.name = details.get("Name")
    process_details.state = details.get("State")
    process_details.pid = details.get("Pid")
    process_details.ppid = details.get("PPid")
    process_details.vm_size = format_memory(int(details.get("VmSize", 0).split()[0]))
    process_details.vm_rss = format_memory(int(details.get("VmRSS", 0).split()[0]))
    process_details.vm_exe = format_memory(int(details.get("VmExe", 0).split()[0]))
    process_details.threads = details.get("Threads")


def adjust_path(path):
    """
    Ajusta o caminho para redirecionar para o WSL, se necessário.

    Caso esteja rodando no Windows, modifica o caminho para seguir o formato usado pelo WSL.
    Caso contrário, retorna o caminho original para o Linux.

    Args:
        path (str): Caminho original a ser ajustado.

    Returns:
        str: Caminho ajustado para WSL (se no Windows) ou o caminho original se for Linux.
    """
    if os.name == 'nt':
        return os.path.join(WSL_PATH, path.lstrip('/').replace('/', '\\'))
    return path


def format_memory(size_kb):
    """
    Formata o tamanho da memória em MB ou KB, com duas casas decimais.

    Args:
        size_kb (int): Tamanho da memória em KB.

    Returns:
        str: Tamanho formatado como MB (se maior ou igual a 1024 KB) ou KB.
    """
    return f"{size_kb / 1024:.2f} MB" if size_kb >= 1024 else f"{size_kb:.2f} KB"


def get_username_from_uid(uid):
    """
    Obtém o nome do usuário correspondente a um UID lendo o arquivo /etc/passwd.

    No Linux e sistemas baseados em Unix, o arquivo /etc/passwd contém informações sobre usuários.
    Esta função busca o nome de usuário associado a um determinado UID.

    Args:
        uid (str): UID do usuário a ser buscado.

    Returns:
        str: Nome do usuário correspondente ao UID, ou "unknown" se não encontrado.
    """
    try:
        path = adjust_path("/etc/passwd")
        with open(path, "r") as f:
            for line in f:
                parts = line.split(":")
                if parts[2] == str(uid):
                    return parts[0]
    except Exception:
        print(f"system_info_service - get_username_from_uid: Erro ao abrir arquivo {path}")
        traceback.print_exc()
    return "unknown"

def fetch_filesystem_info():
    """
    Coleta informações sobre o sistema de arquivos lendo /proc/mounts e utilizando os dados de os.statvfs.
    
    Retorno:
        list: Lista de dicionários com informações de cada partição:
            - device: dispositivo (ex: /dev/sda1)
            - mountpoint: ponto de montagem (ex: /)
            - fstype: tipo do sistema de arquivos
            - total: tamanho total da partição (em KB)
            - used: espaço utilizado (em KB)
            - free: espaço livre (em KB)
            - percent: percentual de uso
    """
    partitions = []
    try:
        mounts_path = adjust_path("/proc/mounts")
        with open(mounts_path, "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                device, mountpoint, fstype = parts[0], parts[1], parts[2]
                try:
                    stats = os.statvfs(mountpoint)
                    total = (stats.f_blocks * stats.f_frsize) // 1024
                    free = (stats.f_bfree * stats.f_frsize) // 1024
                    used = total - free
                    percent = (used / total) * 100 if total > 0 else 0
                    partitions.append({
                        "device": device,
                        "mountpoint": mountpoint,
                        "fstype": fstype,
                        "total": total,
                        "used": used,
                        "free": free,
                        "percent": round(percent, 2)
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"Erro ao ler /proc/mounts: {e}")
        traceback.print_exc()
    return partitions


def fetch_directory_info(path):
    """
    Lista os arquivos e diretórios contidos no caminho especificado.
    
    Parâmetros:
        path (str): Caminho do diretório.
        
    Retorno:
        list: Lista de dicionários com informações de cada entrada:
            - name: nome do arquivo/diretório.
            - is_dir: True se for diretório, False caso contrário.
            - size: tamanho do arquivo (em bytes).
            - permissions: permissões do arquivo (ex: "755").
            - last_modified: timestamp da última modificação.
            - last_accessed: timestamp do último acesso.
            - metadata_change: timestamp da última alteração dos metadados.
            - owner: nome do usuário proprietário do arquivo.
            - inode: número do inode.
    """
    entries_info = []
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            try:
                stats = os.stat(full_path)
                entries_info.append({
                    "name": entry,
                    "is_dir": os.path.isdir(full_path),
                    "size": stats.st_size,
                    "permissions": oct(stats.st_mode)[-3:],
                    "last_modified": stats.st_mtime,
                    "last_accessed": stats.st_atime,
                    "metadata_change": stats.st_ctime,
                    "owner": get_username_from_uid(stats.st_uid),
                    "inode": stats.st_ino
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Erro ao listar o diretório {path}: {e}")
        traceback.print_exc()
    return entries_info

def fetch_io_info(pid):
    """
    Coleta informações de entrada/saída de um processo específico a partir do arquivo /proc/[pid]/io.
    
    Parâmetros:
        pid (str ou int): ID do processo.
        
    Retorno:
        dict: Dicionário com as informações de I/O (ex.: rchar, wchar, read_bytes, write_bytes).
    """
    io_info = {}
    try:
        io_path = adjust_path(f"/proc/{pid}/io")
        with open(io_path, "r") as f:
            for line in f:
                key, value = line.split(":")
                io_info[key.strip()] = value.strip()
    except Exception as e:
        print(f"Erro ao ler I/O do processo {pid}: {e}")
        traceback.print_exc()
    return io_info

import os
import stat
import traceback
from services.system_info_service import adjust_path  # Certifique-se de que adjust_path está disponível

def fetch_process_resources(pid):
    """
    Coleta informações detalhadas dos recursos abertos/alocados pelo processo.
    Lê o diretório /proc/<pid>/fd e retorna uma lista de dicionários com:
      - fd: número do file descriptor.
      - target: destino do link (arquivo, socket, pipe, etc.).
      - inode: número do inode do arquivo apontado.
      - size: tamanho do arquivo (em bytes).
      - last_modified: timestamp da última modificação (st_mtime).
    """
    resources = []
    try:
        fd_dir = adjust_path(f"/proc/{pid}/fd")
        for fd in os.listdir(fd_dir):
            fd_path = os.path.join(fd_dir, fd)
            try:
                target = os.readlink(fd_path)
            except Exception:
                target = "N/A"
            try:
                info = os.lstat(fd_path)
                inode = info.st_ino
                size = info.st_size
                last_modified = info.st_mtime
            except Exception:
                inode = size = last_modified = "N/A"
            resources.append({
                "fd": fd,
                "target": target,
                "inode": inode,
                "size": size,
                "last_modified": last_modified
            })
    except Exception as e:
        print(f"Erro ao coletar recursos abertos para PID {pid}: {e}")
        traceback.print_exc()
    return resources
