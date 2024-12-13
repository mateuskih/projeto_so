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
