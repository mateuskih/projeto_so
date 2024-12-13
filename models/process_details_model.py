class ProcessDetails:
    """
    Classe que armazena informações detalhadas de um processo.

    Esta classe é usada para representar os atributos de um processo no sistema
    incluindo informações sobre memória estado permissões e outros detalhes.

    Atributos:
        name (str): Nome do processo.
        state (str): Estado do processo.
        pid (int): ID do processo.
        ppid (int): ID do processo pai.
        vm_size (str): Tamanho atual de memória virtual.
        vm_rss (str): Tamanho da memória residente.
        vm_exe (str): Tamanho da memória de execução.
        threads (int): Número de threads do processo.
    """

    def __init__(self):
        self.name = ""
        self.state = ""
        self.pid = 0
        self.ppid = 0
        self.vm_size = "0 kB"
        self.vm_rss = "0 kB"
        self.vm_exe = "0 kB"
        self.threads = 0

