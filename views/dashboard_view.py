import tkinter as tk
from tkinter import ttk
import threading
import traceback
from models.system_info_model import SystemInfo
from services.system_info_service import fetch_active_processes, fetch_cpu_info, fetch_memory_info, fetch_os_info
from .process_details_view import ProcessDetailsWindow
from concurrent.futures import ThreadPoolExecutor

class DashboardApp(tk.Tk):
    """
    Classe principal para a aplicação de dashboard.

    Esta aplicação exibe informações sobre o sistema operacional, CPU, memória, e processos ativos.
    """
    def __init__(self):
        """
        Inicializa a aplicação de dashboard.
        """
        super().__init__()
        self.title("Dashboard Sistemas Operacionais CSO30-S71 2024.2 - Mateus e Murilo")
        self.geometry("600x600")  # Ajuste para um tamanho inicial
        self.dados = SystemInfo()
        self.cpu_usage_history = [0] * 27  # Histórico de uso da CPU (27 pontos)
        self.memory_used_history = [0] * 27  # Histórico de uso da memória (27 pontos)
        self.data_ready = False  # Inicializa a flag de dados prontos
        self.data_lock = threading.Lock()  # Lock para sincronização
        self.executor = ThreadPoolExecutor(max_workers=4) # Executor para gerenciar threads

        try:
            self.create_widgets()
            self.refresh_data()
        except Exception:
            print("Dashboard - __init__: Erro ao inicializar a aplicação")
            traceback.print_exc()

    def create_widgets(self):
        """
        Cria os widgets da interface gráfica.

        Este método configura a estrutura principal da interface, incluindo canvas, barras de rolagem, e frames para exibição de dados.
        """
        # Frame principal com grid para expandir a janela
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Canvas para rolagem
        self.canvas = tk.Canvas(main_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Barra de rolagem vertical
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar_y.set)

        # Barra de rolagem horizontal
        scrollbar_x = ttk.Scrollbar(main_frame, orient="horizontal", command=self.canvas.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=scrollbar_x.set)

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

        # Configure a expansão do grid para todo o tamanho
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Garantir que o Canvas preencha toda a janela
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_mousewheel(self, event):
        """Handler para rolagem com o mouse."""
        if event.num == 4:  # Sistemas Unix (Scroll para cima)
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Sistemas Unix (Scroll para baixo)
            self.canvas.yview_scroll(1, "units")
        else:  # Sistemas Windows/Mac (MouseWheel)
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def create_scrollable_content(self):
        """
        Adiciona o conteúdo ao frame rolável.

        Este método cria frames para exibir informações do sistema, CPU, memória e processos ativos.
        """

        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # OS Information
        os_frame = ttk.LabelFrame(main_frame, text="Operating System Information", padding="10")
        os_frame.grid(row=0, column=0, padx=10, pady=10, sticky="new")
        self.os_info = ttk.Label(os_frame, text="", anchor="w", justify="left", padding="5")
        self.os_info.grid(row=0, column=0, sticky="w")

        # CPU Information
        cpu_frame = ttk.LabelFrame(main_frame, text="CPU Information", padding="10")
        cpu_frame.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.cpu_info = ttk.Label(cpu_frame, text="", anchor="w", justify="left", padding="5")
        self.cpu_info.grid(row=0, column=0, sticky="w")

        # Canvas para gráfico de CPU
        self.cpu_canvas = tk.Canvas(cpu_frame, bg="white")  # Remova largura fixa
        self.cpu_canvas.grid(row=1, column=0, pady=5, sticky="nsew")  # Adicione sticky
        cpu_frame.rowconfigure(1, weight=1)  # Torna o gráfico responsivo
        cpu_frame.columnconfigure(0, weight=1)

        # Adicionando legendas ao gráfico de CPU
        self.cpu_label_top = tk.Label(cpu_frame, text="100%", anchor="e")
        self.cpu_label_top.grid(row=1, column=1, padx=5, sticky="n")

        self.cpu_label_bottom = tk.Label(cpu_frame, text="0", anchor="e")
        self.cpu_label_bottom.grid(row=1, column=1, padx=5, sticky="s")

        # Memory Information
        memory_frame = ttk.LabelFrame(main_frame, text="Memory Information", padding="10")
        memory_frame.grid(row=1, column=0, padx=5, pady=10, sticky="e")
        self.memory_info = ttk.Label(memory_frame, text="", anchor="w", justify="left", padding="5")
        self.memory_info.grid(row=0, column=0, sticky="w")

        # Canvas para gráfico de memória
        self.memory_canvas = tk.Canvas(memory_frame, bg="white")  # Remova largura fixa
        self.memory_canvas.grid(row=1, column=0, pady=5, sticky="nsew")  # Adicione sticky
        memory_frame.rowconfigure(1, weight=1)  # Torna o gráfico responsivo
        memory_frame.columnconfigure(0, weight=1)

        # Adicionando legendas ao gráfico de memória
        self.memory_label_top = tk.Label(memory_frame, text="100%", anchor="e")
        self.memory_label_top.grid(row=1, column=1, padx=5, sticky="n")

        self.memory_label_bottom = tk.Label(memory_frame, text="0", anchor="e")
        self.memory_label_bottom.grid(row=1, column=1, padx=5, sticky="s")

        # Canvas para os processos
        processes_frame = ttk.LabelFrame(main_frame, text="Active Processes", padding="10")
        processes_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        processes_frame.rowconfigure(0, weight=1)
        processes_frame.columnconfigure(0, weight=1)

        columns = ("user", "pid", "state", "Threads", "VmSize", "VmRSS", "command")
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
        """
        Atualiza as informações exibidas na interface.

        Este método atualiza as informações da CPU, memória, SO e os processos ativos exibidos na interface gráfica.
        """
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
        mem_swap_used_percent = ((self.dados.swapTotal - self.dados.swapFree) / self.dados.swapTotal) * 100 if self.dados.swapTotal > 0 else 0
        self.memory_info.config(text=(
            f"Total: {self.dados.mtotal // 1024} MB\n"
            f"Used: {self.dados.mUsada // 1024} MB ({mem_used_percent:.2f}%)\n"
            f"Free: {self.dados.mLivre // 1024} MB ({100 - mem_used_percent:.2f}%)\n\n"
            
            f"Swap Total: {self.dados.swapTotal // 1024} MB\n"
            f"Swap Used: {(self.dados.swapTotal - self.dados.swapFree) // 1024} MB ({mem_swap_used_percent:.2f}%)\n"
            f"Swap Free: {self.dados.swapFree // 1024} MB ({100 - mem_swap_used_percent:.2f}%)"
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
        """
        Atualiza o gráfico de uso da CPU.

        Este método desenha um gráfico que representa o uso da CPU ao longo do tempo.
        """
        self.cpu_usage_history.pop(0)
        self.cpu_usage_history.append(self.dados.cpu_usage)
        self.cpu_canvas.delete("all")
        width = self.cpu_canvas.winfo_width()
        height = self.cpu_canvas.winfo_height()
        max_value = 100

        if width == 1 or height == 1:  # Verifica se o Canvas foi renderizado
            return

        step_x = width / len(self.cpu_usage_history)
        points = [
            (i * step_x, height - (value / max_value) * height)
            for i, value in enumerate(self.cpu_usage_history)
        ]

        for i in range(len(points) - 1):
            self.cpu_canvas.create_line(points[i], points[i + 1], fill="blue", width=2)

    def update_memory_graph(self):
        """
        Atualiza o gráfico de uso da memória.

        Este método desenha um gráfico que representa o uso da memória ao longo do tempo.
        """
        self.memory_used_history.pop(0)
        self.memory_used_history.append(self.dados.mUsada / 1024)  # Convertendo para MB
        self.memory_canvas.delete("all")
        width = self.memory_canvas.winfo_width()
        height = self.memory_canvas.winfo_height()
        max_value = self.dados.mtotal / 1024 if self.dados.mtotal > 0 else 1

        if width == 1 or height == 1:  # Verifica se o Canvas foi renderizado
            return

        step_x = width / len(self.memory_used_history)
        points = [
            (i * step_x, height - (value / max_value) * height)
            for i, value in enumerate(self.memory_used_history)
        ]

        for i in range(len(points) - 1):
            self.memory_canvas.create_line(points[i], points[i + 1], fill="green", width=2)
        
    def fetch_data(self):
        """
        Busca as informações do sistema.

        Este método coleta informações da CPU, memória, sistema operacional e processos ativos.
        """
        try:
            tasks = [
                self.executor.submit(fetch_cpu_info, self.dados),
                self.executor.submit(fetch_memory_info, self.dados),
                self.executor.submit(fetch_os_info, self.dados),
                self.executor.submit(fetch_active_processes, self.dados),
            ]

            # Aguardar todas as threads finalizarem
            for task in tasks:
                task.result()
                        
            # Atualiza a flag dentro de um lock
            with self.data_lock:
                self.data_ready = True

        except Exception:
            print("Dashboard - fetch_data: Erro ao buscar dados do sistema")
            traceback.print_exc()

    def refresh_data(self):
        """
        Atualiza os dados periodicamente.

        Este método inicia uma thread para buscar os dados e verifica regularmente o estado da coleta.
        """
        try:
            # Inicia uma thread para buscar os dados
            thread = threading.Thread(target=self.fetch_data, daemon=True)
            thread.start()

            # Em vez de bloquear com join(), verificamos se a thread terminou
            self.after(1000, self.check_data_ready)
        except Exception:
            print("Dashboard - refresh_data: Erro ao iniciar o refresh de dados")
            traceback.print_exc()  

    def check_data_ready(self):
        """
        Verifica se os dados foram coletados.

        Este método verifica regularmente se os dados estão prontos e, se estiverem, atualiza a interface.
        """
        try:
            with self.data_lock:
                if self.data_ready:
                    self.update_display()  # Atualiza a interface
                    self.data_ready = False  # Reseta a flag
            self.after(1000, self.refresh_data)  # Agende a próxima atualização
        except Exception:
            print("Dashboard - check_data_ready: Erro ao verificar se os dados estão prontos")
            traceback.print_exc()
        
    def show_process_details(self, event):
        """
        Exibe os detalhes do processo selecionado.

        Este método abre uma nova janela com informações detalhadas do processo selecionado no TreeView.
        """
        try:
            selection = self.process_info.selection()
            if selection:
                selected_item = self.process_info.item(selection[0])
                pid = selected_item['values'][1]
                ProcessDetailsWindow(self, pid)
        except Exception:
            print("Dashboard - show_process_details: Erro ao exibir detalhes do processo")
            traceback.print_exc()
