from datetime import datetime
import tkinter as tk
from tkinter import ttk
import threading
import traceback
from models import ProcessDetails
from services.system_info_service import (
    fetch_process_details,
    fetch_process_tasks,
    fetch_io_info,
    fetch_process_resources
)
from concurrent.futures import ThreadPoolExecutor

from views.filesystem_view import format_size

class ProcessDetailsWindow(tk.Toplevel):
    """
    Janela que exibe detalhes de um processo específico, incluindo informações de I/O
    e recursos abertos (arquivos, sockets, etc.), organizados em abas.
    """
    def __init__(self, parent, pid):
        super().__init__(parent)
        self.title(f"Detalhes do Processo PID {pid}")
        self.geometry("800x600")
        self.pid = pid
        self.data_ready = False
        self.resources_ready = False
        self.data_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.details = ProcessDetails()
        self.tasks = []
        self.resources = []  # para armazenar os recursos abertos

        # Cria um Notebook com duas abas: "Detalhes" e "Recursos"
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Aba "Detalhes"
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="Detalhes")
        
        # Aba "Recursos"
        self.resources_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.resources_frame, text="Recursos")

        # Conteúdo da aba "Detalhes"
        # Frame para os detalhes do processo (texto)
        self.process_details_frame = ttk.LabelFrame(self.details_frame, text="Detalhes do Processo", padding="10")
        self.process_details_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.details_text = tk.Text(self.process_details_frame, wrap="word", state="disabled", height=10)
        self.details_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para as tasks (threads)
        self.tasks_frame = ttk.LabelFrame(self.details_frame, text="Tasks", padding="10")
        self.tasks_frame.pack(fill="both", expand=True, padx=10, pady=5)
        columns = ("Pid", "Name", "State", "VmSize", "VmRSS", "VmExe")
        self.tasks_table = ttk.Treeview(self.tasks_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tasks_table.heading(col, text=col.capitalize(), anchor="center")
            self.tasks_table.column(col, width=150, anchor="center")
        tasks_scroll_v = ttk.Scrollbar(self.tasks_frame, orient="vertical", command=self.tasks_table.yview)
        tasks_scroll_h = ttk.Scrollbar(self.tasks_frame, orient="horizontal", command=self.tasks_table.xview)
        self.tasks_table.configure(yscrollcommand=tasks_scroll_v.set, xscrollcommand=tasks_scroll_h.set)
        tasks_scroll_v.pack(side="right", fill="y")
        tasks_scroll_h.pack(side="bottom", fill="x")
        self.tasks_table.pack(fill="both", expand=True)

        # Conteúdo da aba "Recursos"
        # Treeview para exibir os recursos abertos pelo processo
        columns_res = ("FD", "Target", "Inode", "Size", "Last Modified")
        self.resources_table = ttk.Treeview(self.resources_frame, columns=columns_res, show="headings", height=15)

        # Configura os cabeçalhos de cada coluna
        self.resources_table.heading("FD", text="FD")
        self.resources_table.heading("Target", text="Target")
        self.resources_table.heading("Inode", text="Inode")
        self.resources_table.heading("Size", text="Size")
        self.resources_table.heading("Last Modified", text="Last Modified")

        # Define as larguras e alinhamentos de cada coluna
        self.resources_table.column("FD", width=50, anchor="center")
        self.resources_table.column("Target", width=300, anchor="w")
        self.resources_table.column("Inode", width=100, anchor="center")
        self.resources_table.column("Size", width=100, anchor="center")
        self.resources_table.column("Last Modified", width=150, anchor="center")

        # Cria as barras de rolagem e configura o Treeview
        res_scroll_v = ttk.Scrollbar(self.resources_frame, orient="vertical", command=self.resources_table.yview)
        res_scroll_h = ttk.Scrollbar(self.resources_frame, orient="horizontal", command=self.resources_table.xview)
        self.resources_table.configure(yscrollcommand=res_scroll_v.set, xscrollcommand=res_scroll_h.set)

        # Posiciona as barras de rolagem e o Treeview
        res_scroll_v.pack(side="right", fill="y")
        res_scroll_h.pack(side="bottom", fill="x")
        self.resources_table.pack(fill="both", expand=True, padx=10, pady=5)

        # Inicia a atualização dos dados
        self.refresh_data()

    def update_display(self):
        """
        Atualiza os detalhes do processo e a tabela de tasks na aba "Detalhes".
        """
        try:
            with self.data_lock:
                if not self.details:
                    return

            self.details_text.config(state="normal")
            self.details_text.delete("1.0", tk.END)

            # Exibe os detalhes básicos do processo
            details_str = ''.join([
                f"Name: {self.details.name}\n",
                f"State: {self.details.state}\n",
                f"Pid: {self.details.pid}\n",
                f"PPid: {self.details.ppid}\n",
                f"VmSize: {self.details.vm_size}\n",
                f"VmRSS: {self.details.vm_rss}\n",
                f"VmExe: {self.details.vm_exe}\n",
                f"Threads: {self.details.threads}\n",
            ])
            # Adiciona informações de I/O
            io_info = fetch_io_info(self.pid)
            if io_info:
                details_str += "\n--- I/O Info ---\n"
                for key, value in io_info.items():
                    details_str += f"{key}: {value}\n"

            self.details_text.insert(tk.END, details_str)
            self.details_text.config(state="disabled")

            # Atualiza a tabela de tasks (threads)
            self.tasks_table.delete(*self.tasks_table.get_children())
            for task in self.tasks:
                self.tasks_table.insert("", "end", values=(
                    task.pid,
                    task.name,
                    task.state,
                    task.vm_size,
                    task.vm_rss,
                    task.vm_exe,
                ))
        except Exception:
            print(f"ProcessDetailsWindow - update_display: Erro ao atualizar os detalhes do processo PID {self.pid}")
            traceback.print_exc()

    def update_resources(self):
        """
        Atualiza a tabela de recursos abertos na aba "Recursos".
        """
        try:
            self.resources_table.delete(*self.resources_table.get_children())
            for res in self.resources:
                self.resources_table.insert("", "end", values=(
                    res["fd"],
                    res["target"],
                    res["inode"],
                    format_size(res["size"]),
                    datetime.fromtimestamp(res["last_modified"]).strftime("%d/%m/%Y %H:%M:%S"),
                    res["target"]
                ))
        except Exception:
            print(f"ProcessDetailsWindow - update_resources: Erro ao atualizar recursos para PID {self.pid}")
            traceback.print_exc()

    def fetch_details(self):
        """
        Busca os detalhes do processo, tasks e recursos em threads separadas.
        """
        try:
            tasks_list = [
                self.executor.submit(fetch_process_details, self.pid, self.details),
                self.executor.submit(fetch_process_tasks, self.pid, self.tasks),
                self.executor.submit(fetch_process_resources, self.pid)
            ]
            # Aguarda os resultados; se a tarefa de recursos retornar um valor, atualiza self.resources
            for task in tasks_list:
                result = task.result()
                if result is not None and isinstance(result, list):
                    self.resources = result
            with self.data_lock:
                self.data_ready = True
                self.resources_ready = True
        except Exception:
            print(f"ProcessDetailsWindow - fetch_details: Erro ao buscar detalhes do processo PID {self.pid}")
            traceback.print_exc()
            with self.data_lock:
                self.data_ready = True
                self.resources_ready = True

    def refresh_data(self):
        """
        Inicia a busca dos dados e agenda a verificação periódica.
        """
        try:
            self.executor.submit(self.fetch_details)
            self.after(1000, self.check_data_ready)
        except Exception:
            print(f"ProcessDetailsWindow - refresh_data: Erro ao iniciar o refresh de dados para PID {self.pid}")
            traceback.print_exc()

    def check_data_ready(self):
        """
        Verifica se os dados foram atualizados e, se sim, atualiza a interface.
        """
        try:
            with self.data_lock:
                if self.data_ready:
                    self.data_ready = False
                    self.after_idle(self.update_display)
                if self.resources_ready:
                    self.resources_ready = False
                    self.after_idle(self.update_resources)
            self.after(1000, self.refresh_data)
        except Exception:
            print(f"ProcessDetailsWindow - check_data_ready: Erro na verificação dos dados para PID {self.pid}")
            traceback.print_exc()
