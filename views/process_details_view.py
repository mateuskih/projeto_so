import tkinter as tk
from tkinter import ttk
import threading
import traceback
from models import ProcessDetails
from services import (
    fetch_process_details,
    fetch_process_tasks,
)
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
        self.tasks = []

        try:
            # Configuração do layout principal com Canvas para suporte a rolagem
            self.canvas = tk.Canvas(self, highlightthickness=0)
            self.scroll_frame = ttk.Frame(self.canvas)

            # Scrollbars para a tela principal
            self.scrollbar_vertical = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.scrollbar_horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

            # Configuração do canvas
            self.canvas.configure(yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=self.scrollbar_horizontal.set)

            # Posiciona o canvas e as barras de rolagem
            self.scrollbar_vertical.pack(side="right", fill="y")
            self.scrollbar_horizontal.pack(side="bottom", fill="x")
            self.canvas.pack(side="left", fill="both", expand=True)

            # Adiciona o frame interno ao canvas
            self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

            # Configuração do frame interno
            self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

            # Layout interno no frame rolável
            self.main_frame = ttk.Frame(self.scroll_frame)
            self.main_frame.grid(row=0, column=0, sticky="nsew")
            self.main_frame.rowconfigure(0, weight=1)
            self.main_frame.columnconfigure(0, weight=1)

            # Primeira seção: Detalhes do processo
            process_details_frame = ttk.LabelFrame(self.main_frame, text="Process Details", padding="10")
            process_details_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

            self.details_text = tk.Text(process_details_frame, wrap="word", state="disabled", height=10)
            self.details_text.pack(fill="both", expand=True, padx=10, pady=5)

            # Segunda seção: Tabela com tasks
            tasks_frame = ttk.LabelFrame(self.main_frame, text="Tasks", padding="10")
            tasks_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

            # Configuração do Treeview para threads
            columns = ("Pid", "Name", "State", "VmSize", "VmRSS", "VmExe")
            self.tasks_table = ttk.Treeview(tasks_frame, columns=columns, show="headings", height=15)

            # Configurando as colunas do Treeview
            for col in columns:
                self.tasks_table.heading(col, text=col.capitalize(), anchor="center")
                self.tasks_table.column(col, width=150, anchor="center")

            # Scrollbars para o Treeview
            tree_scroll_vertical = ttk.Scrollbar(tasks_frame, orient="vertical", command=self.tasks_table.yview)
            tree_scroll_horizontal = ttk.Scrollbar(tasks_frame, orient="horizontal", command=self.tasks_table.xview)
            self.tasks_table.configure(yscrollcommand=tree_scroll_vertical.set, xscrollcommand=tree_scroll_horizontal.set)

            # Posicionando barras de rolagem e tabela
            tree_scroll_vertical.pack(side="right", fill="y")
            tree_scroll_horizontal.pack(side="bottom", fill="x")
            self.tasks_table.pack(fill="both", expand=True)

            # Ajusta a região rolável do canvas após inicializar todos os widgets
            self.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

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
            for task in self.tasks:
                self.tasks_table.insert(
                    "",
                    "end",
                    values=(
                        task.pid,
                        task.name,
                        task.state,
                        task.vm_size,
                        task.vm_rss,
                        task.vm_exe,
                    )
                )

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
