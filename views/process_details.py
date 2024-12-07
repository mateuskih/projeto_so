import tkinter as tk
from tkinter import ttk
import threading
from models import SystemInfo, format_memory
from services import (
    buscaDetalhesProcesso,
)

class ProcessDetailsWindow(tk.Toplevel):
    def __init__(self, parent, pid):
        super().__init__(parent)
        self.title(f"Details for PID {pid}")
        self.geometry("600x400")
        self.pid = pid
        self.data_ready = False

        self.details_label = ttk.Label(self, text=f"Details for Process {pid}:", font=("Arial", 12, "bold"))
        self.details_label.pack(anchor="w", padx=10, pady=5)

        # Text widget for displaying process details, set to not editable
        self.details_text = tk.Text(self, wrap="word", state="disabled")  # Start with disabled state
        self.details_text.pack(fill="both", expand=True, padx=10, pady=5)

        self.fetch_details()
        self.refresh_data()
        
    def update_display(self):
        """Atualiza as informações detalhadas do processo na interface."""
        if not hasattr(self, 'details') or not self.details:
            return  # Garante que self.details existe antes de atualizar

        useful_keys = ["Name", "State", "Pid", "PPid", "Threads", "VmRSS", "VmSize", "User"]

        # Temporariamente habilita o widget para edição e limpa o conteúdo anterior
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)

        # Atualiza o conteúdo com as informações processadas
        for key in useful_keys:
            if key in self.details:
                value = self.details[key]
                if key in ["VmSize", "VmRSS"] and value.split()[0].isdigit():
                    value = format_memory(int(value.split()[0]))
                self.details_text.insert(tk.END, f"{key}: {value}\n")

        # Desabilita o widget para evitar edições
        self.details_text.config(state="disabled")
        
    def fetch_details(self):
        """Busca os detalhes do processo em uma thread separada."""
        try:
            self.details = buscaDetalhesProcesso(self.pid)
            self.data_ready = True  # Sinaliza que os dados foram buscados
        except Exception as e:
            print(f"Erro ao buscar detalhes do processo {self.pid}: {e}")
            self.details = {}
            self.data_ready = True  # Mesmo com erro, sinaliza que a thread terminou

    def refresh_data(self):
        """Inicia uma thread para buscar os dados e verifica o estado."""
        # Inicia a thread para buscar os detalhes do processo
        thread = threading.Thread(target=self.fetch_details, daemon=True)
        thread.start()

        # Programa verificações regulares do estado da thread
        self.after(100, self.check_data_ready)

    def check_data_ready(self):
        """Verifica se os dados foram buscados e atualiza a interface."""
        if hasattr(self, 'data_ready') and self.data_ready:
            self.update_display()
            self.data_ready = False  # Reseta a flag para a próxima atualização
            self.after(1000, self.refresh_data)  # Programa a próxima atualização
        else:
            # Continua verificando se os dados estão prontos
            self.after(100, self.check_data_ready)

    

