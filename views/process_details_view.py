import tkinter as tk
from tkinter import ttk
import threading
import traceback
from models import SystemInfo
from services import (
    fetch_process_details,
)
from services.system_info_service import format_memory


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

        try:
            self.details_label = ttk.Label(self, text=f"Details for Process {pid}:", font=("Arial", 12, "bold"))
            self.details_label.pack(anchor="w", padx=10, pady=5)

            # Text widget for displaying process details, set to not editable
            self.details_text = tk.Text(self, wrap="word", state="disabled")  # Start with disabled state
            self.details_text.pack(fill="both", expand=True, padx=10, pady=5)

            self.fetch_details()
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
        except Exception:
            print(f"ProcessDetailsWindow - update_display: Erro ao atualizar os detalhes do processo PID {self.pid}")
            traceback.print_exc()

    def fetch_details(self):
        """
        Busca os detalhes do processo em uma thread separada.

        Este método coleta informações detalhadas do processo identificado pelo PID e sinaliza quando os dados estão prontos.
        """
        try:
            self.details = fetch_process_details(self.pid)
            self.data_ready = True  # Sinaliza que os dados foram buscados
        except Exception:
            print(f"ProcessDetailsWindow - fetch_details: Erro ao buscar detalhes do processo PID {self.pid}")
            traceback.print_exc()
            self.details = {}
            self.data_ready = True  # Mesmo com erro, sinaliza que a thread terminou

    def refresh_data(self):
        """
        Inicia uma thread para buscar os dados e programa verificações regulares do estado da thread.

        Este método é responsável por garantir que a coleta de dados do processo seja executada de forma assíncrona.
        """
        try:
            # Inicia a thread para buscar os detalhes do processo
            thread = threading.Thread(target=self.fetch_details, daemon=True)
            thread.start()

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
            if hasattr(self, 'data_ready') and self.data_ready:
                self.update_display()
                self.data_ready = False  # Reseta a flag para a próxima atualização
                self.after(1000, self.refresh_data)  # Programa a próxima atualização
            else:
                # Continua verificando se os dados estão prontos
                self.after(1000, self.check_data_ready)
        except Exception:
            print(f"ProcessDetailsWindow - check_data_ready: Erro ao verificar se os dados estão prontos para PID {self.pid}")
            traceback.print_exc()
