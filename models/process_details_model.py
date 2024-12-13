class ProcessDetails:
    """
    Classe que armazena informações detalhadas de um processo.

    Esta classe é usada para representar os atributos de um processo no sistema
    incluindo informações sobre memória estado permissões e outros detalhes.

    Atributos:
        name (str): Nome do processo.
        state (str): Estado do processo.
        tgid (int): Thread Group ID do processo.
        pid (int): ID do processo.
        ppid (int): ID do processo pai.
        tracer_pid (int): ID do processo rastreador.
        uid (list): Lista de IDs de usuário.
        gid (list): Lista de IDs de grupo.
        fd_size (int): Tamanho do descritor de arquivo.
        groups (str): Grupos aos quais o processo pertence.
        vm_peak (str): Pico de uso de memória virtual.
        vm_size (str): Tamanho atual de memória virtual.
        vm_lck (str): Memória virtual bloqueada.
        vm_hwm (str): High Water Mark da memória.
        vm_rss (str): Tamanho da memória residente.
        vm_data (str): Tamanho da memória de dados.
        vm_stk (str): Tamanho da memória de pilha.
        vm_exe (str): Tamanho da memória de execução.
        vm_lib (str): Tamanho da memória de bibliotecas.
        vm_pte (str): Tamanho das tabelas de página.
        threads (int): Número de threads do processo.
        sig_q (str): Fila de sinais.
        sig_pnd (str): Sinais pendentes.
        shd_pnd (str): Sinais compartilhados pendentes.
        sig_blk (str): Sinais bloqueados.
        sig_ign (str): Sinais ignorados.
        sig_cgt (str): Sinais capturados.
        cap_inh (str): Capacidades herdadas.
        cap_prm (str): Capacidades permitidas.
        cap_eff (str): Capacidades efetivas.
        cap_bnd (str): Capacidades limitadas.
        cpus_allowed (str): CPUs permitidas para execução.
        cpus_allowed_list (str): Lista de CPUs permitidas.
        mems_allowed (str): Memórias permitidas.
        mems_allowed_list (str): Lista de memórias permitidas.
        voluntary_ctxt_switches (int): Número de trocas de contexto voluntárias.
        nonvoluntary_ctxt_switches (int): Número de trocas de contexto não voluntárias.
    """

    def __init__(self):
        self.name=""
        self.state=""
        self.pid=0
        self.ppid=0
        self.vm_size="0 kB"
        self.vm_rss="0 kB"
        self.vm_exe="0 kB"
        self.threads=0