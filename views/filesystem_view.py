import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor
from services.system_info_service import fetch_filesystem_info, fetch_directory_info, adjust_path

def format_size(size_bytes):
    """
    Converte o tamanho em bytes para uma string formatada.
    Se for inferior a 1 MB, exibe em KB; caso contrário, exibe em MB.
    """
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

class FilesystemFrame(tk.Frame):
    """
    Frame para exibir as informações do sistema de arquivos e permitir a navegação
    na árvore de diretórios a partir da raiz, com atualização periódica.
    """
    def __init__(self, parent, start_path="/"):
        super().__init__(parent)
        self.current_path = start_path

        # Rótulo com o caminho atual
        self.path_label = ttk.Label(self, text=f"Caminho: {self.current_path}")
        self.path_label.pack(fill="x", padx=10, pady=5)

        # Botão para voltar um nível
        self.back_button = ttk.Button(self, text="Voltar", command=self.go_back)
        self.back_button.pack(padx=10, pady=5)

        # Cria um frame para a Treeview do diretório e suas barras de rolagem
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Barra de rolagem vertical para a Treeview de diretórios
        tree_vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_vsb.grid(row=0, column=1, sticky="ns")

        # Barra de rolagem horizontal para a Treeview de diretórios
        tree_hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_hsb.grid(row=1, column=0, sticky="ew")

        self.tree = ttk.Treeview(
            tree_frame, 
            columns=("Name", "Type", "Size", "Permissions", "Last Modified", "Owner"), 
            show="headings",
            yscrollcommand=tree_vsb.set,
            xscrollcommand=tree_hsb.set
        )
        self.tree.heading("Name", text="Nome")
        self.tree.heading("Type", text="Tipo")
        self.tree.heading("Size", text="Tamanho")
        self.tree.heading("Permissions", text="Permissões")
        self.tree.heading("Last Modified", text="Última Modificação")
        self.tree.heading("Owner", text="Dono")
        self.tree.column("Name", width=300)
        self.tree.column("Type", width=100, anchor="center")
        self.tree.column("Size", width=100, anchor="center")
        self.tree.column("Permissions", width=100, anchor="center")
        self.tree.column("Last Modified", width=150, anchor="center")
        self.tree.column("Owner", width=100, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.on_double_click)

        # Configura o grid do frame para expandir corretamente
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Separador para exibir as partições do sistema de arquivos
        self.partition_label = ttk.Label(self, text="Partições:")
        self.partition_label.pack(fill="x", padx=10, pady=5)

        # Cria um frame para a Treeview das partições e suas barras de rolagem
        partition_frame = ttk.Frame(self)
        partition_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Barra de rolagem vertical para a Treeview de partições
        partition_vsb = ttk.Scrollbar(partition_frame, orient="vertical")
        partition_vsb.grid(row=0, column=1, sticky="ns")

        # Barra de rolagem horizontal para a Treeview de partições
        partition_hsb = ttk.Scrollbar(partition_frame, orient="horizontal")
        partition_hsb.grid(row=1, column=0, sticky="ew")

        self.partition_tree = ttk.Treeview(
            partition_frame, 
            columns=("Device", "Mountpoint", "Fstype", "Total", "Used", "Free", "Percent"), 
            show="headings",
            yscrollcommand=partition_vsb.set,
            xscrollcommand=partition_hsb.set
        )
        for col in self.partition_tree["columns"]:
            self.partition_tree.heading(col, text=col)
            self.partition_tree.column(col, anchor="center", width=100)
        self.partition_tree.grid(row=0, column=0, sticky="nsew")

        # Configura os scrollbars para responderem à rolagem da Treeview
        tree_vsb.config(command=self.tree.yview)
        tree_hsb.config(command=self.tree.xview)
        partition_vsb.config(command=self.partition_tree.yview)
        partition_hsb.config(command=self.partition_tree.xview)

        # Configura o grid do frame das partições para expandir corretamente
        partition_frame.grid_rowconfigure(0, weight=1)
        partition_frame.grid_columnconfigure(0, weight=1)

        # Atributos para atualização em background
        self.data_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.dir_entries = []      # Dados do diretório
        self.partition_data = []   # Dados das partições
        self.directory_ready = False
        self.partition_ready = False

        # Inicia a atualização dos dados
        self.refresh_data()

    def update_directory_display(self):
        """
        Atualiza a listagem do diretório na Treeview.
        """
        try:
            self.tree.delete(*self.tree.get_children())
            for entry in self.dir_entries:
                tipo = "Diretório" if entry["is_dir"] else "Arquivo"
                tamanho = format_size(entry['size'])
                mod_time = datetime.fromtimestamp(entry['last_modified']).strftime("%d/%m/%Y %H:%M:%S")
                owner = entry.get('owner', 'N/A')
                self.tree.insert("", "end", values=(
                    entry["name"],
                    tipo,
                    tamanho,
                    entry["permissions"],
                    mod_time,
                    owner
                ))
            self.path_label.config(text=f"Caminho: {self.current_path}")
        except Exception:
            print("FilesystemFrame - update_directory_display: Erro ao atualizar o diretório")
            traceback.print_exc()

    def update_partition_display(self):
        """
        Atualiza a listagem das partições na Treeview, formatando os tamanhos com format_size.
        """
        try:
            self.partition_tree.delete(*self.partition_tree.get_children())
            for part in self.partition_data:
                # Converte os valores de KB para bytes e formata-os
                total_str = format_size(part['total'] * 1024)
                used_str = format_size(part['used'] * 1024)
                free_str = format_size(part['free'] * 1024)
                self.partition_tree.insert("", "end", values=(
                    part["device"],
                    part["mountpoint"],
                    part["fstype"],
                    total_str,
                    used_str,
                    free_str,
                    f"{part['percent']}%"
                ))
        except Exception:
            print("FilesystemFrame - update_partition_display: Erro ao atualizar as partições")
            traceback.print_exc()

    def fetch_directory_data(self):
        """
        Busca os dados do diretório atual em um worker separado.
        """
        try:
            directory_entries = fetch_directory_info(self.current_path)
            with self.data_lock:
                self.dir_entries = directory_entries
                self.directory_ready = True
        except Exception:
            print("FilesystemFrame - fetch_directory_data: Erro ao buscar dados do diretório")
            traceback.print_exc()
            with self.data_lock:
                self.directory_ready = True

    def fetch_partition_data(self):
        """
        Busca os dados das partições em um worker separado.
        """
        try:
            partitions = fetch_filesystem_info()
            with self.data_lock:
                self.partition_data = partitions
                self.partition_ready = True
        except Exception:
            print("FilesystemFrame - fetch_partition_data: Erro ao buscar dados das partições")
            traceback.print_exc()
            with self.data_lock:
                self.partition_ready = True

    def refresh_data(self):
        """
        Inicia a busca dos dados (diretório e partições) em workers separados e agenda
        a verificação periódica.
        """
        try:
            self.executor.submit(self.fetch_directory_data)
            self.executor.submit(self.fetch_partition_data)
            self.after(1000, self.check_data_ready)
        except Exception:
            print("FilesystemFrame - refresh_data: Erro ao iniciar o refresh de dados")
            traceback.print_exc()

    def check_data_ready(self):
        """
        Verifica se os dados foram atualizados e, se sim, agenda a atualização da interface.
        """
        try:
            with self.data_lock:
                if self.directory_ready:
                    self.directory_ready = False
                    self.after_idle(self.update_directory_display)
                if self.partition_ready:
                    self.partition_ready = False
                    self.after_idle(self.update_partition_display)
            self.after(1000, self.refresh_data)
        except Exception:
            print("FilesystemFrame - check_data_ready: Erro na verificação dos dados")
            traceback.print_exc()

    def on_double_click(self, event):
        """
        Ao dar duplo clique em um item da listagem, se for um diretório, navega para dentro dele.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            return
        values = self.tree.item(selected_item, "values")
        name = values[0]
        new_path = os.path.join(self.current_path, name)
        if os.path.isdir(new_path):
            self.current_path = new_path
            self.refresh_data()

    def go_back(self):
        """
        Navega para o diretório pai.
        """
        parent_path = os.path.dirname(self.current_path.rstrip("/"))
        if parent_path and parent_path != self.current_path:
            self.current_path = parent_path
            self.refresh_data()
