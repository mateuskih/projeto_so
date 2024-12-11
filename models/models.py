import os
import traceback


WSL_PATH = r"\\wsl.localhost\Ubuntu-20.04"

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


class SystemInfo:
    """
    Classe que armazena informações sobre o sistema.

    Esta classe é usada para guardar informações relacionadas ao hardware e ao sistema operacional,
    incluindo informações sobre a CPU, memória e processos.

    Atributos:
        cpu_name (str): Nome do modelo da CPU.
        cpu_ghz (float): Frequência da CPU em GHz.
        cpu_usage (float): Uso da CPU em percentual.
        idle_percent (float): Percentual de tempo ocioso da CPU.
        quantidadeCPU (int): Quantidade total de núcleos/processadores.
        mtotal (int): Memória total disponível (em KB).
        mUsada (int): Memória usada (em KB).
        mLivre (int): Memória livre (em KB).
        mDisponivel (int): Memória disponível para uso (em KB).
        total_processos (int): Quantidade total de processos ativos.
        total_threads (int): Quantidade total de threads ativas.
        infoSO (str): Informações sobre o sistema operacional.
        processosAtivos (list): Lista de processos ativos no sistema.
    """
    def __init__(self):
        self.cpu_name = ""
        self.cpu_ghz = 0.0
        self.cpu_usage = 0.0
        self.idle_percent = 0.0
        self.quantidadeCPU = 0
        self.mtotal = 0
        self.mUsada = 0
        self.mLivre = 0
        self.mDisponivel = 0
        self.total_processos = 0
        self.total_threads = 0
        self.infoSO = ""
        self.processosAtivos = []


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
        print(f"Model - get_username_from_uid: Erro ao abrir arquivo {path}")
        traceback.print_exc()
    return "unknown"
