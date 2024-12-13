import tkinter as tk
from tkinter import ttk
import threading
import traceback
from models import ProcessDetails
from services import (
    fetch_process_details,
    fetch_process_tasks,
)
from services.system_info_service import format_memory
from concurrent.futures import ThreadPoolExecutor



class ProcessDetailsWindow(tk.Toplevel):
    """
    Classe que representa uma janela de detalhes de um processo específico.

    Esta janela exibe informações detalhadas de um processo identificado por seu PID.
    """

    def __init__(self, parent, pid):
        """
        Inicializa a janela de detalhes do processo.

        Args:
            parent (tk.Widget): Referência ao widget pai.
            pid (int): ID do processo a ser detalhado.
        """
        super().__init__(parent)
        self.title(f"Details for PID {pid}")
        self.geometry("600x400")
        self.pid = pid
        self.data_ready = False
        self.data_lock = threading.Lock()  # Lock para exclusão mútua
        self.executor = ThreadPoolExecutor(max_workers=2)  # Executor para gerenciar a concorrência
        self.details = ProcessDetails()
        self.tasks = ProcessDetails()

        try:
            # Configuração do layout principal
            self.main_frame = ttk.Frame(self)
            self.main_frame.grid(row=0, column=0, sticky="nsew")
            self.rowconfigure(0, weight=1)
            self.columnconfigure(0, weight=1)

            # Primeira seção: Detalhes do processo
            process_details_frame = ttk.LabelFrame(self.main_frame, text="Process Details", padding="10")
            process_details_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

            # Label para detalhes do processo
            self.details_text = tk.Text(process_details_frame, wrap="word", state="disabled", height=10)
            self.details_text.pack(fill="both", expand=True, padx=10, pady=5)

            # Segunda seção: Tabela com threads (tasks)
            tasks_frame = ttk.LabelFrame(self.main_frame, text="Threads (Tasks)", padding="10")
            tasks_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

            # Configuração do Treeview para threads
            columns = ("Pid", "Name", "State", "VmSize", "VmRSS", "VmExe")
            self.tasks_table = ttk.Treeview(tasks_frame, columns=columns, show="headings", height=15)
            self.tasks_table.pack(fill="both", expand=True)

            # Configurando as colunas do Treeview
            for col in columns:
                self.tasks_table.heading(col, text=col.capitalize(), anchor="center")
                self.tasks_table.column(col, width=150, anchor="center")

            # Scrollbar vertical para o Treeview
            scrollbar = ttk.Scrollbar(tasks_frame, orient="vertical", command=self.tasks_table.yview)
            self.tasks_table.config(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            # Ajustando o layout responsivo
            self.main_frame.rowconfigure(0, weight=1)  # Primeira seção
            self.main_frame.rowconfigure(1, weight=2)  # Segunda seção

            # Carregar dados iniciais
            self.refresh_data()
        except Exception:
            print(f"ProcessDetailsWindow - __init__: Erro ao inicializar a janela de detalhes para PID {pid}")
            traceback.print_exc()

    def update_display(self):
        """
        Atualiza as informações detalhadas do processo na interface.

        Este método processa e exibe os detalhes do processo, como nome, estado, memória usada, e outras informações relevantes.
        """
        try:
            with self.data_lock:
                if not self.details:
                    return
   
            # Temporariamente habilita o widget para edição e limpa o conteúdo anterior
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", tk.END)

            # Atualiza o conteúdo com as informações processadas

            self.details_text.insert(tk.END, ''.join([
                f"Name: {self.details.name}\n",
                f"State: {self.details.state}\n",
                f"Pid: {self.details.pid}\n",
                f"PPid: {self.details.ppid}\n",
                f"VmSize: {self.details.vm_size}\n",
                f"VmRSS: {self.details.vm_rss}\n",
                f"VmExe: {self.details.vm_exe}\n",
                f"Threads: {self.details.threads}\n",
            ]))
                    
            # Atualização do Treeview
            self.tasks_table.delete(*self.tasks_table.get_children())
            
            self.tasks_table.insert(
                "",  # Representa a linha sem um identificador específico
                "end",  # Inserir no final da tabela
                values=(
                    self.tasks.pid,  # Acessa o PID diretamente
                    self.tasks.name,  # Acessa o nome diretamente
                    self.tasks.state,  # Acessa o estado diretamente
                )
            )

            # Desabilita o widget para evitar edições
            self.details_text.config(state="disabled")
        except Exception:
            print(f"ProcessDetailsWindow - update_display: Erro ao atualizar os detalhes do processo PID {self.pid}")
            traceback.print_exc()

    def fetch_details(self):
        """
        Busca os detalhes do processo em uma thread separada.

        Este método coleta informações detalhadas do processo identificado pelo PID e sinaliza quando os dados estão prontos.
        """
        try:
            #details = fetch_process_details(self.pid)            
            tasks = [
                self.executor.submit(fetch_process_details, self.pid, self.details),
                self.executor.submit(fetch_process_tasks, self.pid, self.tasks)
            ]

            # Aguarda a conclusão da tarefa e obtém o resultado
            for task in tasks:
                task.result()   
            

            with self.data_lock:
                self.data_ready = True # Sinaliza que os dados foram buscados
        except Exception:
            print(f"ProcessDetailsWindow - fetch_details: Erro ao buscar detalhes do processo PID {self.pid}")
            traceback.print_exc()
            with self.data_lock:
                self.data_ready = True
    def refresh_data(self):
        """
        Inicia uma thread para buscar os dados e programa verificações regulares do estado da thread.

        Este método é responsável por garantir que a coleta de dados do processo seja executada de forma assíncrona.
        """
        try:
            # Submete a tarefa de buscar os detalhes do processo ao executor
            self.executor.submit(self.fetch_details)


            # Programa verificações regulares do estado da thread
            self.after(1000, self.check_data_ready)
        except Exception:
            print(f"ProcessDetailsWindow - refresh_data: Erro ao iniciar o refresh de dados para PID {self.pid}")
            traceback.print_exc()

    def check_data_ready(self):
        """
        Verifica se os dados foram buscados e atualiza a interface.

        Este método verifica regularmente se os dados do processo foram carregados e, caso positivo, atualiza a exibição.
        """
        try:
            with self.data_lock:
                if self.data_ready:
                    self.data_ready = False  # Reseta a flag
                    self.after_idle(self.update_display)  # Atualiza a interface de forma assíncrona
            self.after(1000, self.refresh_data)  # Programa a próxima verificação

        except Exception:
            print(f"ProcessDetailsWindow - check_data_ready: Erro ao verificar se os dados estão prontos para PID {self.pid}")
            traceback.print_exc()
