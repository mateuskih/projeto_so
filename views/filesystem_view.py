import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os
import traceback
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
    na árvore de diretórios a partir da raiz.
    """
    def __init__(self, parent, start_path="/"):
        super().__init__(parent)
        self.current_path = start_path

        # Rótulo que mostra o caminho atual
        self.path_label = ttk.Label(self, text=f"Caminho: {self.current_path}")
        self.path_label.pack(fill="x", padx=10, pady=5)

        # Botão para voltar um nível
        self.back_button = ttk.Button(self, text="Voltar", command=self.go_back)
        self.back_button.pack(padx=10, pady=5)

        # Treeview para listar os arquivos e diretórios do caminho atual
        self.tree = ttk.Treeview(self, 
                                 columns=("Name", "Type", "Size", "Permissions", "Last Modified", "Owner"), 
                                 show="headings")
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
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Separador para exibir as partições do sistema de arquivos
        self.partition_label = ttk.Label(self, text="Partições:")
        self.partition_label.pack(fill="x", padx=10, pady=5)

        self.partition_tree = ttk.Treeview(self, 
                                           columns=("Device", "Mountpoint", "Fstype", "Total", "Used", "Free", "Percent"), 
                                           show="headings")
        for col in self.partition_tree["columns"]:
            self.partition_tree.heading(col, text=col)
            self.partition_tree.column(col, anchor="center", width=100)
        self.partition_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Atualiza os dados iniciais
        self.update_directory()
        self.update_partitions()

    def update_directory(self):
        """Atualiza a listagem dos arquivos/diretórios do caminho atual."""
        self.tree.delete(*self.tree.get_children())
        try:
            entries = fetch_directory_info(self.current_path)
            for entry in entries:
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
        except Exception as e:
            print(f"Erro ao atualizar diretório: {e}")
            traceback.print_exc()

    def update_partitions(self):
        """Atualiza a listagem das partições do sistema de arquivos."""
        self.partition_tree.delete(*self.partition_tree.get_children())
        try:
            partitions = fetch_filesystem_info()
            for part in partitions:
                self.partition_tree.insert("", "end", values=(
                    part["device"],
                    part["mountpoint"],
                    part["fstype"],
                    f"{part['total']} KB",
                    f"{part['used']} KB",
                    f"{part['free']} KB",
                    f"{part['percent']}%"
                ))
        except Exception as e:
            print(f"Erro ao atualizar partições: {e}")
            traceback.print_exc()

    def on_double_click(self, event):
        """
        Ao dar duplo clique em um item da listagem,
        se for um diretório, navega para dentro dele.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            return
        values = self.tree.item(selected_item, "values")
        name = values[0]
        new_path = os.path.join(self.current_path, name)
        if os.path.isdir(new_path):
            self.current_path = new_path
            self.update_directory()

    def go_back(self):
        """
        Navega para o diretório pai.
        """
        parent_path = os.path.dirname(self.current_path.rstrip("/"))
        if parent_path and parent_path != self.current_path:
            self.current_path = parent_path
            self.update_directory()
