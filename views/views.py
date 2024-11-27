import tkinter as tk
from tkinter import ttk
import threading
from models import SystemInfo, format_memory
from services import (
    buscaInformacoesCPU,
    buscaInfoMemoria,
    buscaProcessosAtivos,
    buscaInfoSO,
    buscaDetalhesProcesso,
)

class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dashboard Sistemas Operacionais CSO30-S71 2024.2 - Mateus e Murilo")
        self.geometry("900x768")  # Ajuste para um tamanho maior da janela
        self.dados = SystemInfo()
        self.cpu_usage_history = [0] * 50  # Histórico de uso da CPU (50 pontos)
        self.memory_used_history = [0] * 50  # Histórico de uso da memória (50 pontos)
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # Canvas para rolagem
        self.canvas = tk.Canvas(self, width=1024, height=768)  # Define dimensões iniciais maiores
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Barra de rolagem
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Frame que conterá todo o conteúdo
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Adicionar o frame ao canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Adicionar eventos para rolagem com o mouse
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)  # Suporte adicional para sistemas Unix
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)  # Suporte adicional para sistemas Unix

        # Adicionar widgets ao frame rolável
        self.create_scrollable_content()

    def _on_mousewheel(self, event):
        """Handler para rolagem com o mouse."""
        if event.num == 4:  # Sistemas Unix (Scroll para cima)
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Sistemas Unix (Scroll para baixo)
            self.canvas.yview_scroll(1, "units")
        else:  # Sistemas Windows/Mac (MouseWheel)
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def create_scrollable_content(self):
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # CPU Information
        cpu_frame = ttk.LabelFrame(main_frame, text="CPU Information", padding="10")
        cpu_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.cpu_info = ttk.Label(cpu_frame, text="", anchor="w", justify="left", padding="5")
        self.cpu_info.grid(row=0, column=0, sticky="w")

        # Canvas para gráfico de CPU
        self.cpu_canvas = tk.Canvas(cpu_frame, width=800, height=150, bg="white")  # Gráfico maior
        self.cpu_canvas.grid(row=1, column=0, pady=5)

        # Adicionando legendas ao gráfico de CPU
        self.cpu_label_top = tk.Label(cpu_frame, text="100", anchor="e")
        self.cpu_label_top.grid(row=1, column=1, padx=5, sticky="n")

        self.cpu_label_bottom = tk.Label(cpu_frame, text="0", anchor="e")
        self.cpu_label_bottom.grid(row=1, column=1, padx=5, sticky="s")

        # Memory Information
        memory_frame = ttk.LabelFrame(main_frame, text="Memory Information", padding="10")
        memory_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.memory_info = ttk.Label(memory_frame, text="", anchor="w", justify="left", padding="5")
        self.memory_info.grid(row=0, column=0, sticky="w")

        # Canvas para gráfico de memória
        self.memory_canvas = tk.Canvas(memory_frame, width=800, height=150, bg="white")  # Gráfico maior
        self.memory_canvas.grid(row=1, column=0, pady=5)

        # Adicionando legendas ao gráfico de memória
        self.memory_label_top = tk.Label(memory_frame, text="100", anchor="e")
        self.memory_label_top.grid(row=1, column=1, padx=5, sticky="n")

        self.memory_label_bottom = tk.Label(memory_frame, text="0", anchor="e")
        self.memory_label_bottom.grid(row=1, column=1, padx=5, sticky="s")

        # Outras seções
        os_frame = ttk.LabelFrame(main_frame, text="Operating System Information", padding="10")
        os_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.os_info = ttk.Label(os_frame, text="", anchor="w", justify="left", padding="5")
        self.os_info.grid(row=0, column=0, sticky="w")

        processes_frame = ttk.LabelFrame(main_frame, text="Active Processes", padding="10")
        processes_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        processes_frame.rowconfigure(0, weight=1)
        processes_frame.columnconfigure(0, weight=1)

        columns = ("user", "pid", "vsz", "rss", "command")
        self.process_info = ttk.Treeview(processes_frame, columns=columns, show="headings", height=15)
        self.process_info.grid(row=0, column=0, sticky="nsew")

        for col in columns:
            self.process_info.heading(col, text=col.capitalize(), anchor="center")
            self.process_info.column(col, width=150, anchor="center")

        scrollbar = ttk.Scrollbar(processes_frame, orient="vertical", command=self.process_info.yview)
        self.process_info.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.process_info.bind("<Double-1>", self.show_process_details)


    def update_display(self):
        # Atualização das informações de CPU
        self.cpu_info.config(text=(
            f"Name: {self.dados.cpu_name}\n"
            f"Cores: {self.dados.quantidadeCPU}\n"
            f"Frequency: {self.dados.cpu_ghz} GHz\n"
            f"Usage: {self.dados.cpu_usage}%\n"
            f"Idle: {self.dados.idle_percent}%\n"  # Novo: Percentual de tempo ocioso
            f"Processes: {self.dados.total_processos}\n"  # Novo: Total de processos
            f"Threads: {self.dados.total_threads}"  # Novo: Total de threads
        ))

        # Atualização das informações de memória
        mem_used_percent = (self.dados.mUsada / self.dados.mtotal) * 100 if self.dados.mtotal > 0 else 0
        self.memory_info.config(text=(
            f"Total: {self.dados.mtotal // 1024} MB\n"
            f"Used: {self.dados.mUsada // 1024} MB ({mem_used_percent:.2f}%)\n"
            f"Free: {self.dados.mLivre // 1024} MB"
        ))

        # Atualização do SO
        self.os_info.config(text=self.dados.infoSO)

        # Atualização do Treeview
        for row in self.process_info.get_children():
            self.process_info.delete(row)
        for process in self.dados.processosAtivos:
            self.process_info.insert("", "end", values=process)

        # Atualização dos gráficos
        self.update_cpu_graph()
        self.update_memory_graph()

    def update_cpu_graph(self):
        self.cpu_usage_history.pop(0)
        self.cpu_usage_history.append(self.dados.cpu_usage)
        self.cpu_canvas.delete("all")
        max_value = 100
        for i in range(1, len(self.cpu_usage_history)):
            x1 = (i - 1) * 16  # Ajuste para gráficos maiores
            y1 = 150 - (self.cpu_usage_history[i - 1] / max_value * 150)
            x2 = i * 16
            y2 = 150 - (self.cpu_usage_history[i] / max_value * 150)
            self.cpu_canvas.create_line(x1, y1, x2, y2, fill="blue", width=2)

    def update_memory_graph(self):
        self.memory_used_history.pop(0)
        self.memory_used_history.append(self.dados.mUsada / 1024)  # Convertendo para MB
        self.memory_canvas.delete("all")
        max_value = self.dados.mtotal / 1024 if self.dados.mtotal > 0 else 1
        for i in range(1, len(self.memory_used_history)):
            x1 = (i - 1) * 16  # Ajuste para gráficos maiores
            y1 = 150 - (self.memory_used_history[i - 1] / max_value * 150)
            x2 = i * 16
            y2 = 150 - (self.memory_used_history[i] / max_value * 150)
            self.memory_canvas.create_line(x1, y1, x2, y2, fill="green", width=2)

    def refresh_data(self):
        threading.Thread(target=self.fetch_data).start()

    def fetch_data(self):
        buscaInformacoesCPU(self.dados)
        buscaInfoMemoria(self.dados)
        buscaInfoSO(self.dados)
        buscaProcessosAtivos(self.dados)
        self.update_display()
        self.after(1000, self.refresh_data)

    def show_process_details(self, event):
        selection = self.process_info.selection()
        if selection:
            selected_item = self.process_info.item(selection[0])
            pid = selected_item['values'][1]
            ProcessDetailsWindow(self, pid)

class ProcessDetailsWindow(tk.Toplevel):
    def __init__(self, parent, pid):
        super().__init__(parent)
        self.title(f"Details for PID {pid}")
        self.geometry("600x400")
        self.pid = pid

        self.details_label = ttk.Label(self, text=f"Details for Process {pid}:", font=("Arial", 12, "bold"))
        self.details_label.pack(anchor="w", padx=10, pady=5)

        # Text widget for displaying process details, set to not editable
        self.details_text = tk.Text(self, wrap="word", state="disabled")  # Start with disabled state
        self.details_text.pack(fill="both", expand=True, padx=10, pady=5)

        self.fetch_details()

    def fetch_details(self):
        details = buscaDetalhesProcesso(self.pid)
        useful_keys = ["Name", "State", "Pid", "PPid", "Threads", "VmSize", "VmRSS", "User"]

        # Temporarily enable the text widget to update its content
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)  # Clear existing content

        for key in useful_keys:
            if key in details:
                value = details[key]
                if key in ["VmSize", "VmRSS"]:
                    value = format_memory(int(value.split()[0]))
                self.details_text.insert(tk.END, f"{key}: {value}\n")

        # Disable the text widget to prevent editing
        self.details_text.config(state="disabled")
