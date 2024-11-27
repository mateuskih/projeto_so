import os
import time

WSL_PATH = r"\\wsl.localhost\Ubuntu-20.04"

def adjust_path(path):
    """Adjust the path to redirect to WSL if necessary."""
    if os.name == 'nt':  # Running on Windows
        return os.path.join(WSL_PATH, path.lstrip('/').replace('/', '\\'))
    return path  # Default for non-Windows systems

class SystemInfo:
    def __init__(self):
        self.cpu_name = ""
        self.cpu_ghz = 0.0
        self.cpu_usage = 0.0
        self.idle_percent = 0.0  # Novo: Percentual de tempo ocioso
        self.quantidadeCPU = 0
        self.mtotal = 0
        self.mUsada = 0
        self.mLivre = 0
        self.mDisponivel = 0
        self.total_processos = 0  # Novo: Total de processos
        self.total_threads = 0    # Novo: Total de threads
        self.infoSO = ""
        self.processosAtivos = []

def format_memory(size_kb):
    """Format memory size as MB or KB with two decimal places."""
    return f"{size_kb / 1024:.2f} MB" if size_kb >= 1024 else f"{size_kb:.2f} KB"

def get_username_from_uid(uid):
    """Get the username corresponding to a UID by reading /etc/passwd."""
    try:
        with open(adjust_path("/etc/passwd"), "r") as f:
            for line in f:
                parts = line.split(":")
                if parts[2] == str(uid):
                    return parts[0]  # Username is the first field
    except FileNotFoundError:
        pass
    return "unknown"
