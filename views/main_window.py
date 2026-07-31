"""
Janela principal do sistema - COMPLETA com TODAS as funcionalidades
Inclui: Janela Principal, Gerenciar, Registros Antigos, ESTATÍSTICAS COMPLETA
Atualizado: Filtro de Matrícula + Aba Gerenciar Clientes
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import os
import json
import re
import sys
from tkcalendar import Calendar, DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from collections import Counter
import numpy as np
import plotly.graph_objects as go
import tempfile
import webbrowser
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment  
from PIL import Image, ImageGrab
from plotly.subplots import make_subplots
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from views.widgets.scrollable_combobox import ScrollableComboBox
from views.widgets.tooltip import Tooltip
from views.widgets.history_dialog import HistoryDialog
from views.record_window import RecordWindow
from models.database import Database as HistoryDB

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        # Executando como .exe (PyInstaller)
        return os.path.join(sys._MEIPASS, relative_path)
    # Executando como script Python
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class EquipControlApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Sistema de Controle de Equipamentos")
        self.root.geometry("1500x900")
        
        # Maximizar após a janela ser criada
        self.root.after(10, lambda: self.root.state('zoomed'))

        # Definir ícone da janela principal
        self.set_window_icon(self.root)
        
        # Tema atual
        self.current_theme = "light"
        
        # Inicializar banco de dados
        self.init_database()
        self.history_db = HistoryDB()
        
        # Variáveis de filtro - COM MATRÍCULA COL e CLI separadas
        self.filter_vars = {
            'data': ctk.StringVar(),
            'colaborador': ctk.StringVar(value="Todos"),
            'matricula_col': ctk.StringVar(value="Todos"),  # Matrícula do colaborador
            'equipamento': ctk.StringVar(value="Todos"),
            'cliente': ctk.StringVar(value="Todos"),
            'matricula_cli': ctk.StringVar(value="Todos"),  # Matrícula do cliente
            'local': ctk.StringVar(value="Todos"),
            'tipo': ctk.StringVar(value="Todos")
        }
        
        # Variáveis para registros antigos (ARQUIVOS) - COM MATRÍCULA COL e CLI separadas
        self.archive_filter_vars = {
            'mes': ctk.StringVar(value=str(datetime.now().month).zfill(2)),
            'ano': ctk.StringVar(value=str(datetime.now().year)),
            'colaborador': ctk.StringVar(value="Todos"),
            'matricula_col': ctk.StringVar(value="Todos"),  # Matrícula do colaborador
            'equipamento': ctk.StringVar(value="Todos"),
            'cliente': ctk.StringVar(value="Todos"),
            'matricula_cli': ctk.StringVar(value="Todos"),  # Matrícula do cliente
            'local': ctk.StringVar(value="Todos"),
            'tipo': ctk.StringVar(value="Todos"),
            'data': ctk.StringVar()
        }

        # Variáveis para filtros de estatísticas
        self.stats_filter_vars = {
            'mes': ctk.StringVar(value=str(datetime.now().month).zfill(2)),
            'ano': ctk.StringVar(value=str(datetime.now().year)),
            'data': ctk.StringVar()
        }
        
        # Tooltip para tabelas - COM DEBOUNCE
        self.tree_tooltip = None
        self._tooltip_timer = None
        self._last_tooltip_key = None

        # Controle de encerramento (graceful shutdown)
        self._closing = False
        # Garante que o clique no X sempre finalize o processo
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Criar interface
        self.create_widgets()
        
        # Carregar dados
        self.load_main_data()
        
        # Verificar arquivamento mensal
        self.check_monthly_archive()
        
        # Vincular eventos de filtro automático
        self.bind_filter_events()
        
        # Vincular eventos de filtro automático para registros antigos
        self.bind_archive_filter_events()
        # bind_stats_filter_events() será chamado pelo StatsManager

    def set_window_icon(self, window):
        """Define o ícone para uma janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
                # Para Windows - também define na barra de tarefas
                window.after(200, lambda: window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")

    def init_database(self):
        """Inicializa conexão com banco (tabelas criadas por Database)"""
        from models.database import Database
        db = Database('equip_control.db')  # Isso cria as tabelas se não existirem
        self.conn = db.conn
        self.cursor = db.cursor
        
    def create_widgets(self):
        """Cria a interface principal"""
        # Container principal
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Cabeçalho com botão de tema
        header = ctk.CTkFrame(main_container, corner_radius=10)
        header.pack(fill="x", pady=(0, 20))
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(header_content, text="CONTROLE DE EQUIPAMENTOS", 
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        # Botão de tema
        self.theme_btn = ctk.CTkButton(header_content, text="TEMA ESCURO", 
                                       command=self.toggle_theme,
                                       fg_color="#6b7280", hover_color="#4b5563",
                                       width=130, height=35)
        self.theme_btn.pack(side="right")
        
        # Sistema de Abas
        self.tabview = ctk.CTkTabview(main_container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True)
        
        # Criar abas - ADICIONANDO "Gerenciar Clientes"
        self.tabview.add("Janela Principal")
        self.tabview.add("Gerenciar Colaboradores")
        self.tabview.add("Gerenciar Locais")
        self.tabview.add("Gerenciar Equipamentos")
        self.tabview.add("Gerenciar Clientes")
        self.tabview.add("Registros Antigos")
        self.tabview.add("Estatísticas")
        self.tabview.add("Ranking")
        
        # Configurar cada aba
        self.create_main_tab()
        self.create_manage_tab("colaboradores")
        self.create_manage_tab("locais")
        self.create_manage_tab("equipamentos")
        self.create_clientes_tab()
        self.create_archive_tab()
        self.create_stats_tab()
        self.create_ranking_tab()
        
        # Vincular evento de mudança de aba
        self.tabview.configure(command=self.on_tab_changed)
        
    def on_tab_changed(self):
        """Executado quando a aba é alterada"""
        # Esconder tooltip ao trocar de aba
        self.hide_tree_tooltip()
        
        current_tab = self.tabview.get()
        if current_tab == "Janela Principal":
            # Recarregar dados quando voltar para a aba principal
            self.load_main_data()
        elif current_tab == "Registros Antigos":
            # Recarregar dados E ordenar por Data ao entrar na aba
            self.load_archive_data()
        elif current_tab == "Estatísticas":
            if hasattr(self, 'stats_manager'):
                self.stats_manager.update_statistics()
        elif current_tab == "Gerenciar Clientes":
            self.load_clientes_data()
        
    def bind_filter_events(self):
        """Vincula eventos para filtro automático"""
        self.filter_vars['data'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['colaborador'].trace_add('write', lambda *args: self.on_colaborador_filter_changed())
        self.filter_vars['matricula_col'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['equipamento'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['cliente'].trace_add('write', lambda *args: self.on_cliente_filter_changed())
        self.filter_vars['matricula_cli'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['local'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['tipo'].trace_add('write', lambda *args: self.apply_filters())
    
    def on_colaborador_filter_changed(self):
        """Quando colaborador muda, atualiza matrículas disponíveis"""
        colaborador = self.filter_vars['colaborador'].get()
        
        if colaborador == "Todos":
            # Mostrar todas as matrículas de colaboradores
            matriculas = ["Todos"] + self.get_todas_matriculas_colaboradores()
        else:
            # Buscar matrículas deste colaborador
            matriculas = ["Todos"] + self.get_matriculas_by_colaborador(colaborador)
        
        # Atualizar combobox de matrícula COL
        self.matricula_col_filter.configure(values=matriculas)
        self.filter_vars['matricula_col'].set("Todos")
        
        self.apply_filters()
    
    def on_cliente_filter_changed(self):
        """Quando cliente muda, atualiza matrículas disponíveis"""
        cliente = self.filter_vars['cliente'].get()
        
        if cliente == "Todos":
            # Mostrar todas as matrículas de clientes
            matriculas = ["Todos"] + self.get_todas_matriculas_clientes()
        else:
            # Buscar matrículas deste cliente
            matriculas = ["Todos"] + self.get_matriculas_by_cliente(cliente)
        
        # Atualizar combobox de matrícula CLI
        self.matricula_cli_filter.configure(values=matriculas)
        self.filter_vars['matricula_cli'].set("Todos")
        
        self.apply_filters()
        
    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        if self.current_theme == "dark":
            ctk.set_appearance_mode("light")
            self.current_theme = "light"
            self.theme_btn.configure(text="TEMA ESCURO")
        else:
            ctk.set_appearance_mode("dark")
            self.current_theme = "dark"
            self.theme_btn.configure(text="TEMA CLARO")
        
        # Atualizar cores de todas as tabelas
        self.update_all_table_styles()
    
    def update_all_table_styles(self):
        """Atualiza o estilo de todas as tabelas"""
        self.update_table_style()
        self.update_manage_table_styles()
    
    def update_table_style(self):
        """Atualiza o estilo da tabela principal conforme o tema"""
        style = ttk.Style()
        
        if self.current_theme == "dark":
            style.theme_use('default')
            style.configure("Treeview", 
                           background="#2b2b2b",
                           foreground="white",
                           fieldbackground="#2b2b2b",
                           rowheight=30,
                           borderwidth=0)
            style.configure("Treeview.Heading",
                           background="#1a1a1a",
                           foreground="white",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#3b3b3b")
            style.map("Treeview", 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
        else:
            style.theme_use('default')
            style.configure("Treeview", 
                           background="white",
                           foreground="black",
                           fieldbackground="white",
                           rowheight=30,
                           borderwidth=0)
            style.configure("Treeview.Heading",
                           background="#e5e5e5",
                           foreground="black",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#d4d4d4")
            style.map("Treeview", 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
    
    def update_manage_table_styles(self):
        """Atualiza o estilo das tabelas de gerenciamento"""
        for tipo in ["colaboradores", "locais", "equipamentos", "clientes"]:
            if hasattr(self, f'{tipo}_listbox'):
                listbox = getattr(self, f'{tipo}_listbox')
                style = ttk.Style()
                if self.current_theme == "dark":
                    style.theme_use('default')
                    style.configure(f"{tipo}.Treeview", 
                                   background="#2b2b2b",
                                   foreground="white",
                                   fieldbackground="#2b2b2b",
                                   rowheight=30,
                                   borderwidth=0)
                    style.configure(f"{tipo}.Treeview.Heading",
                                   background="#1a1a1a",
                                   foreground="white",
                                   relief="flat",
                                   borderwidth=1,
                                   bordercolor="#3b3b3b")
                    style.map(f"{tipo}.Treeview", 
                             background=[('selected', '#3b82f6')],
                             foreground=[('selected', 'white')])
                else:
                    style.theme_use('default')
                    style.configure(f"{tipo}.Treeview", 
                                   background="white",
                                   foreground="black",
                                   fieldbackground="white",
                                   rowheight=30,
                                   borderwidth=0)
                    style.configure(f"{tipo}.Treeview.Heading",
                                   background="#e5e5e5",
                                   foreground="black",
                                   relief="flat",
                                   borderwidth=1,
                                   bordercolor="#d4d4d4")
                    style.map(f"{tipo}.Treeview", 
                             background=[('selected', '#3b82f6')],
                             foreground=[('selected', 'white')])
                listbox.configure(style=f"{tipo}.Treeview")
    
    def create_main_tab(self):
        """Cria aba principal com filtros de matrícula COL e CLI"""
        tab = self.tabview.tab("Janela Principal")
        
        # Frame de filtros
        filter_frame = ctk.CTkFrame(tab, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15))
        
        filter_title = ctk.CTkLabel(filter_frame, text="FILTROS", 
                                    font=ctk.CTkFont(size=16, weight="bold"))
        filter_title.grid(row=0, column=0, columnspan=8, pady=(15, 10), padx=20, sticky="w")
        
        # === LINHA 1: Data, Colaborador, Mat. COL, Equipamento ===
        
        # Filtro Data
        ctk.CTkLabel(filter_frame, text="Data:").grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")
        
        # Frame para campo de data e botão do calendário
        date_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_frame.grid(row=1, column=0, padx=(60, 5), pady=10)
        
        date_entry = ctk.CTkEntry(date_frame, textvariable=self.filter_vars['data'], 
                                 placeholder_text="DD/MM/AAAA", width=110)
        date_entry.pack(side="left")
        date_entry.bind('<KeyRelease>', self.format_date_input)
        
        # Botão do calendário
        calendar_btn = ctk.CTkButton(date_frame, text="📅", 
                                    width=30, height=30,
                                    command=lambda: self.open_calendar(date_entry))
        calendar_btn.pack(side="left", padx=(5, 0))
        
        # Filtro Colaborador (nomes únicos)
        ctk.CTkLabel(filter_frame, text="Colaborador:").grid(row=1, column=1, padx=(15, 5), pady=10, sticky="w")
        self.colaborador_filter = ScrollableComboBox(filter_frame, 
                                                variable=self.filter_vars['colaborador'],
                                                values=["Todos"] + self.get_colaboradores_nomes_unicos(), 
                                                width=200,
                                                max_visible_items=6,
                                                app=self)
        self.colaborador_filter.grid(row=1, column=1, padx=(95, 5), pady=10)
        
        # Filtro Matrícula COL (atualiza baseado no colaborador selecionado)
        ctk.CTkLabel(filter_frame, text="Mat. COL:").grid(row=1, column=2, padx=(12, 5), pady=10, sticky="w")
        self.matricula_col_filter = ScrollableComboBox(filter_frame,
                                              variable=self.filter_vars['matricula_col'],
                                              values=["Todos"] + self.get_todas_matriculas_colaboradores(), 
                                              width=130,
                                              max_visible_items=6,
                                              app=self)
        self.matricula_col_filter.grid(row=1, column=2, padx=(75, 5), pady=10)
        
        # Filtro Equipamento
        ctk.CTkLabel(filter_frame, text="Equipamento:").grid(row=1, column=3, padx=(15, 5), pady=10, sticky="w")
        self.equipamento_filter = ScrollableComboBox(filter_frame,
                                            variable=self.filter_vars['equipamento'],
                                            values=["Todos"] + self.get_items("equipamentos"), 
                                            width=200,
                                            max_visible_items=6,
                                            app=self)
        self.equipamento_filter.grid(row=1, column=3, padx=(100, 5), pady=10)
        
        # === LINHA 2: Cliente, Mat. CLI, Local, Tipo, Limpar Filtros ===
        
        # Filtro Cliente (nomes únicos)
        ctk.CTkLabel(filter_frame, text="Cliente:").grid(row=2, column=1, padx=(45, 5), pady=10, sticky="w")
        self.cliente_filter = ScrollableComboBox(filter_frame,
                                              variable=self.filter_vars['cliente'],
                                              values=["Todos"] + self.get_clientes_nomes_unicos(), 
                                              width=200,
                                              max_visible_items=6,
                                              app=self)
        self.cliente_filter.grid(row=2, column=1, padx=(95, 5), pady=10)
        
        # Filtro Matrícula CLI (atualiza baseado no cliente selecionado)
        ctk.CTkLabel(filter_frame, text="Mat. CLI:").grid(row=2, column=2, padx=(15, 5), pady=10, sticky="w")
        self.matricula_cli_filter = ScrollableComboBox(filter_frame,
                                              variable=self.filter_vars['matricula_cli'],
                                              values=["Todos"] + self.get_todas_matriculas_clientes(), 
                                              width=130,
                                              max_visible_items=6,
                                              app=self)
        self.matricula_cli_filter.grid(row=2, column=2, padx=(75, 5), pady=10)
        
        # Filtro Local
        ctk.CTkLabel(filter_frame, text="Local:").grid(row=2, column=3, padx=(60, 5), pady=10, sticky="w")
        self.local_filter = ScrollableComboBox(filter_frame,
                                              variable=self.filter_vars['local'],
                                              values=["Todos"] + self.get_items("locais"), 
                                              width=200,
                                              max_visible_items=6,
                                              app=self)
        self.local_filter.grid(row=2, column=3, padx=(100, 5), pady=10)
        
        # Filtro Tipo
        ctk.CTkLabel(filter_frame, text="Tipo:").grid(row=2, column=0, padx=(22, 5), pady=10, sticky="w")
        self.tipo_filter = ScrollableComboBox(filter_frame,
                                              variable=self.filter_vars['tipo'],
                                              values=["Todos", "ENTREGA", "RETIRADA"], 
                                              width=130,
                                              max_visible_items=3,
                                              app=self)
        self.tipo_filter.grid(row=2, column=0, padx=(40, 5), pady=10)
        
        # Botão de limpar filtros
        clear_btn = ctk.CTkButton(filter_frame, text="LIMPAR FILTROS", 
                                 command=self.clear_filters,
                                 fg_color="#475569", hover_color="#334155",
                                 width=130, height=35)
        clear_btn.grid(row=2, column=4, pady=(15, 15), padx=30, sticky="e")
        
        # Frame de botões
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 10))
        
        btn_novo = ctk.CTkButton(action_frame, text="NOVO REGISTRO", 
                                command=self.new_record,
                                fg_color="#10b981", hover_color="#059669",
                                width=150, height=40)
        btn_novo.pack(side="left", padx=5)
        
        btn_editar = ctk.CTkButton(action_frame, text="EDITAR", 
                                  command=self.edit_record,
                                  fg_color="#f59e0b", hover_color="#d97706",
                                  width=150, height=40)
        btn_editar.pack(side="left", padx=5)
        
        btn_info = ctk.CTkButton(action_frame, text="ℹ️ INFO", 
                     command=self.show_record_history,
                     fg_color="#3b82f6", hover_color="#2563eb",
                     width=120, height=40)
        btn_info.pack(side="left", padx=5)
        
        # Label informativo sobre o limite de 20 registros
        info_label = ctk.CTkLabel(action_frame, 
                                 text="📌 Exibindo os últimos 20 registros mais recentes",
                                 font=ctk.CTkFont(size=12),
                                 text_color="#60a5fa")
        info_label.pack(side="right", padx=20)
        
        # Frame da tabela
        table_frame = ctk.CTkFrame(tab, corner_radius=10)
        table_frame.pack(fill="both", expand=True)
        
        # Configurar estilo da tabela
        self.update_table_style()
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # Tabela - COM COLUNA MATRÍCULA
        columns = ("ID", "Data", "Colaborador", "Equipamento", "Matrícula", "Cliente", "Local", 
                  "Horário", "Tipo")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                yscrollcommand=lambda *args: self.on_tree_scroll_main(*args, scrollbar=scrollbar), 
                                height=15)
        scrollbar.config(command=lambda *args: self.on_scrollbar_main(*args))
        
        # Configurar colunas
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Data", width=90, anchor="center")
        self.tree.column("Colaborador", width=140, anchor="center")
        self.tree.column("Equipamento", width=110, anchor="center")
        self.tree.column("Matrícula", width=90, anchor="center")
        self.tree.column("Cliente", width=140, anchor="center")
        self.tree.column("Local", width=150, anchor="center")
        self.tree.column("Horário", width=70, anchor="center")
        self.tree.column("Tipo", width=90, anchor="center")
        
        # Configurar cabeçalhos com função de ordenação
        for col in columns:
            self.tree.heading(col, text=col, anchor="center", 
                            command=lambda c=col: self.sort_treeview(self.tree, c, False))
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar tags de cores para tipo (cores vibrantes)
        self.tree.tag_configure('entrega', background='#fca5a5')  # Vermelho coral vibrante
        self.tree.tag_configure('retirada', background='#fde047')  # Amarelo vibrante
        
        # === TOOLTIP PARA COLABORADOR E CLIENTE ===
        self.tree.bind('<Motion>', lambda e: self.show_tree_tooltip(e, self.tree, "Janela Principal"))
        self.tree.bind('<Leave>', lambda e: self.on_tree_leave(e))
        self.tree.bind('<Leave>', lambda e: self.hide_tree_tooltip())
        self.tree.bind('<MouseWheel>', lambda e: self.hide_tree_tooltip())  # Scroll Windows
        self.tree.bind('<Button-4>', lambda e: self.hide_tree_tooltip())    # Scroll Linux up
        self.tree.bind('<Button-5>', lambda e: self.hide_tree_tooltip())    # Scroll Linux down
    
    def create_archive_tab(self):
        """Cria aba de registros antigos com filtros Mat. COL e Mat. CLI"""
        tab = self.tabview.tab("Registros Antigos")
        
        # Frame de filtros
        filter_frame = ctk.CTkFrame(tab, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), padx=20)
        
        # Título
        filter_title = ctk.CTkLabel(filter_frame, text="FILTROS - REGISTROS ANTIGOS", 
                                    font=ctk.CTkFont(size=16, weight="bold"))
        filter_title.grid(row=0, column=0, columnspan=10, pady=(15, 10), padx=20, sticky="w")
        
        # === LINHA 1: Mês, Ano, Colaborador, Mat. COL, Equipamento ===
        
        # Filtro Mês
        ctk.CTkLabel(filter_frame, text="Mês:").grid(row=1, column=4, padx=(15, 5), pady=10, sticky="w")
        self.archive_mes_filter = ScrollableComboBox(filter_frame, 
                                                    variable=self.archive_filter_vars['mes'],
                                                    values=[f"{i:02d}" for i in range(1, 13)], 
                                                    width=100,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_mes_filter.grid(row=1, column=4, padx=(50, 5), pady=10)
        
        # Filtro Ano
        ctk.CTkLabel(filter_frame, text="Ano:").grid(row=2, column=4, padx=(20, 5), pady=10, sticky="w")
        self.archive_ano_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['ano'],
                                                    values=self.get_available_years(), 
                                                    width=100,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_ano_filter.grid(row=2, column=4, padx=(50, 5), pady=10)
        
        # Filtro Colaborador (nomes únicos)
        ctk.CTkLabel(filter_frame, text="Colaborador:").grid(row=1, column=1, padx=(15, 5), pady=10, sticky="w")
        self.archive_colaborador_filter = ScrollableComboBox(filter_frame, 
                                                        variable=self.archive_filter_vars['colaborador'],
                                                        values=["Todos"] + self.get_colaboradores_nomes_unicos(), 
                                                        width=200,
                                                        max_visible_items=6,
                                                        app=self)
        self.archive_colaborador_filter.grid(row=1, column=1, padx=(95, 5), pady=10)
        
        # Filtro Matrícula COL
        ctk.CTkLabel(filter_frame, text="Mat. COL:").grid(row=1, column=2, padx=(12, 5), pady=10, sticky="w")
        self.archive_matricula_col_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['matricula_col'],
                                                    values=["Todos"] + self.get_todas_matriculas_colaboradores(), 
                                                    width=130,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_matricula_col_filter.grid(row=1, column=2, padx=(75, 5), pady=10)
        
        # Filtro Equipamento
        ctk.CTkLabel(filter_frame, text="Equipamento:").grid(row=1, column=3, padx=(15, 5), pady=10, sticky="w")
        self.archive_equipamento_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['equipamento'],
                                                    values=["Todos"] + self.get_items("equipamentos"), 
                                                    width=200,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_equipamento_filter.grid(row=1, column=3, padx=(100, 5), pady=10)
        
        # === LINHA 2: Cliente, Mat. CLI, Local, Tipo, Data, Limpar ===
        
        # Filtro Cliente (nomes únicos)
        ctk.CTkLabel(filter_frame, text="Cliente:").grid(row=2, column=1, padx=(45, 5), pady=10, sticky="w")
        self.archive_cliente_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['cliente'],
                                                    values=["Todos"] + self.get_clientes_nomes_unicos(), 
                                                    width=200,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_cliente_filter.grid(row=2, column=1, padx=(95, 5), pady=10)
        
        # Filtro Matrícula CLI
        ctk.CTkLabel(filter_frame, text="Mat. CLI:").grid(row=2, column=2, padx=(15, 5), pady=10, sticky="w")
        self.archive_matricula_cli_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['matricula_cli'],
                                                    values=["Todos"] + self.get_todas_matriculas_clientes(), 
                                                    width=130,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_matricula_cli_filter.grid(row=2, column=2, padx=(75, 5), pady=10)
        
        # Filtro Local
        ctk.CTkLabel(filter_frame, text="Local:").grid(row=2, column=3, padx=(60, 5), pady=10, sticky="w")
        self.archive_local_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['local'],
                                                    values=["Todos"] + self.get_items("locais"), 
                                                    width=200,
                                                    max_visible_items=6,
                                                    app=self)
        self.archive_local_filter.grid(row=2, column=3, padx=(100, 5), pady=10)
        
        # Filtro Tipo
        ctk.CTkLabel(filter_frame, text="Tipo:").grid(row=2, column=0, padx=(22, 5), pady=10, sticky="w")
        self.archive_tipo_filter = ScrollableComboBox(filter_frame,
                                                    variable=self.archive_filter_vars['tipo'],
                                                    values=["Todos", "ENTREGA", "RETIRADA"], 
                                                    width=130,
                                                    max_visible_items=3,
                                                    app=self)
        self.archive_tipo_filter.grid(row=2, column=0, padx=(40, 5), pady=10)
        
        # Frame para Data + Calendário
        date_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_frame.grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")
        
        ctk.CTkLabel(date_frame, text="Data:").pack(side="left", padx=(0, 5))
        archive_date_entry = ctk.CTkEntry(date_frame, 
                                        textvariable=self.archive_filter_vars['data'], 
                                        placeholder_text="DD/MM/AAAA",
                                        width=110)
        archive_date_entry.pack(side="left")
        archive_date_entry.bind('<KeyRelease>', self.format_date_input)
        
        archive_calendar_btn = ctk.CTkButton(date_frame, text="📅", 
                                            width=30, height=30,
                                            command=lambda: self.open_calendar(archive_date_entry))
        archive_calendar_btn.pack(side="left", padx=(5, 0))
        
        # === LINHA 3: INFO e Limpar ===
        
        # Botão INFO
        btn_archive_info = ctk.CTkButton(filter_frame, text="ℹ️ INFO", 
                                        command=self.show_archive_history,
                                        fg_color="#3b82f6", hover_color="#2563eb",
                                        width=80, height=30)
        btn_archive_info.grid(row=3, column=0, padx=(20, 5), pady=(5, 15), sticky="w")
        
        # Botão Limpar Filtros
        clear_btn = ctk.CTkButton(filter_frame, text="LIMPAR FILTROS", 
                                command=self.clear_archive_filters,
                                fg_color="#475569", hover_color="#334155",
                                width=130, height=35)
        clear_btn.grid(row=3, column=1, pady=(5, 15), padx=(0, 150), sticky="e")
        
        # === TABELA - COM COLUNA MATRÍCULA ===
        
        table_frame = ctk.CTkFrame(tab, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Scrollbar
        archive_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        archive_scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        # Tabela
        columns = ("ID", "Data", "Colaborador", "Equipamento", "Matrícula", "Cliente", "Local", 
                "Horário", "Tipo")
        self.archive_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                        yscrollcommand=lambda *args: self.on_tree_scroll_archive(*args, scrollbar=archive_scrollbar), 
                                        height=15)
        archive_scrollbar.config(command=lambda *args: self.on_scrollbar_archive(*args))
        
        # Configurar colunas
        self.archive_tree.column("ID", width=50, anchor="center")
        self.archive_tree.column("Data", width=90, anchor="center")
        self.archive_tree.column("Colaborador", width=140, anchor="center")
        self.archive_tree.column("Equipamento", width=110, anchor="center")
        self.archive_tree.column("Matrícula", width=90, anchor="center")
        self.archive_tree.column("Cliente", width=140, anchor="center")
        self.archive_tree.column("Local", width=150, anchor="center")
        self.archive_tree.column("Horário", width=70, anchor="center")
        self.archive_tree.column("Tipo", width=90, anchor="center")
        
        # Configurar cabeçalhos
        for col in columns:
            self.archive_tree.heading(col, text=col, anchor="center", 
                                    command=lambda c=col: self.sort_treeview(self.archive_tree, c, False))
        
        self.archive_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar tags de cores para tipo (cores vibrantes)
        self.archive_tree.tag_configure('entrega', background='#fca5a5')
        self.archive_tree.tag_configure('retirada', background='#fde047')
        
        # === TOOLTIP PARA COLABORADOR E CLIENTE ===
        self.archive_tree.bind('<Motion>', lambda e: self.show_tree_tooltip(e, self.archive_tree, "Registros Antigos"))
        self.archive_tree.bind('<Leave>', lambda e: self.on_tree_leave(e))
        self.archive_tree.bind('<Leave>', lambda e: self.hide_tree_tooltip())
        
        # Carregar dados iniciais
        self.load_archive_data()
    
    def create_clientes_tab(self):
        """Cria aba de gerenciamento de clientes - apenas visualização e edição"""
        tab = self.tabview.tab("Gerenciar Clientes")
        
        # Container
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        title = ctk.CTkLabel(container, text="GERENCIAR CLIENTES",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(0, 30))
        
        # Frame de ação (botão EDITAR + info + buscador)
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 20))

        btn_editar = ctk.CTkButton(input_frame, text="EDITAR", 
                                  command=self.edit_cliente,
                                  fg_color="#f59e0b", hover_color="#d97706",
                                  width=150, height=40)
        btn_editar.pack(side="left")
        
        # Info
        info_label = ctk.CTkLabel(input_frame, 
                                 text="💡 Clientes são cadastrados automaticamente ao criar registros",
                                 font=ctk.CTkFont(size=12),
                                 text_color="#6b7280")
        info_label.pack(side="left", padx=(20, 0))
        
        # === BUSCADOR (lado direito) ===
        search_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        search_frame.pack(side="right")
        
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        
        self.clientes_search_var = ctk.StringVar()
        self.clientes_search_var.trace_add('write', lambda *args: self.filter_clientes_list())
        
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.clientes_search_var,
                                   placeholder_text="Buscar cliente ou matrícula...",
                                   width=200, height=35)
        search_entry.pack(side="left")
        
        # Frame da lista
        list_frame = ctk.CTkFrame(container, corner_radius=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        # Treeview para lista
        columns = ("ID", "Cliente", "Matrícula")
        self.clientes_listbox = ttk.Treeview(list_frame, columns=columns, show="headings",
                              yscrollcommand=scrollbar.set, height=12)
        scrollbar.config(command=self.clientes_listbox.yview)
        
        self.clientes_listbox.column("ID", width=80, anchor="center")
        self.clientes_listbox.column("Cliente", width=350, anchor="center")
        self.clientes_listbox.column("Matrícula", width=150, anchor="center")
        
        # Configurar cabeçalhos com função de ordenação
        self.clientes_listbox.heading("ID", text="ID", anchor="center", 
                       command=lambda: self.sort_clientes_treeview("ID", False))
        self.clientes_listbox.heading("Cliente", text="Cliente", anchor="center",
                       command=lambda: self.sort_clientes_treeview("Cliente", False))
        self.clientes_listbox.heading("Matrícula", text="Matrícula", anchor="center",
                       command=lambda: self.sort_clientes_treeview("Matrícula", False))
        
        self.clientes_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar estilo da lista
        style_name = "clientes.Treeview"
        style = ttk.Style()
        if self.current_theme == "dark":
            style.theme_use('default')
            style.configure(style_name, 
                           background="#2b2b2b",
                           foreground="white",
                           fieldbackground="#2b2b2b",
                           rowheight=30,
                           borderwidth=0)
            style.configure(style_name + ".Heading",
                           background="#1a1a1a",
                           foreground="white",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#3b3b3b")
            style.map(style_name, 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
        else:
            style.theme_use('default')
            style.configure(style_name, 
                           background="white",
                           foreground="black",
                           fieldbackground="white",
                           rowheight=30,
                           borderwidth=0)
            style.configure(style_name + ".Heading",
                           background="#e5e5e5",
                           foreground="black",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#d4d4d4")
            style.map(style_name, 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
        
        self.clientes_listbox.configure(style=style_name)
        
        # Botões de ação
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # Carregar dados
        self.load_clientes_data()
    
    def load_clientes_data(self):
        """Carrega lista de clientes únicos com suas matrículas"""
        # Limpar lista
        for item in self.clientes_listbox.get_children():
            self.clientes_listbox.delete(item)
        
        # Buscar clientes únicos
        self.cursor.execute('''
            SELECT ROW_NUMBER() OVER (ORDER BY cliente) as id, cliente, matricula
            FROM (
                SELECT DISTINCT cliente, matricula
                FROM registros 
                WHERE cliente IS NOT NULL AND cliente != ''
            )
            ORDER BY cliente
        ''')
        
        clientes = self.cursor.fetchall()
        
        for cliente in clientes:
            # id, cliente, matricula
            self.clientes_listbox.insert("", "end", values=(cliente[0], cliente[1], cliente[2] or ""))
    
    def sort_clientes_treeview(self, col, reverse):
        """Ordena a lista de clientes"""
        data = [(self.clientes_listbox.set(item, col), item) for item in self.clientes_listbox.get_children('')]
        
        if col == "ID":
            try:
                data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'), reverse=reverse)
            except:
                data.sort(reverse=reverse)
        else:
            data.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(data):
            self.clientes_listbox.move(item, '', index)
        
        self.clientes_listbox.heading(col, command=lambda: self.sort_clientes_treeview(col, not reverse))
    
    def filter_clientes_list(self):
        """Filtra lista de clientes por busca (cliente ou matrícula)"""
        search = self.clientes_search_var.get().upper()
        
        # Limpar lista
        for item in self.clientes_listbox.get_children():
            self.clientes_listbox.delete(item)
        
        # Buscar clientes que correspondam
        self.cursor.execute('''
            SELECT ROW_NUMBER() OVER (ORDER BY cliente) as id, cliente, matricula
            FROM (
                SELECT DISTINCT cliente, matricula
                FROM registros 
                WHERE cliente IS NOT NULL AND cliente != ''
                AND (UPPER(cliente) LIKE ? OR UPPER(COALESCE(matricula, '')) LIKE ?)
            )
            ORDER BY cliente
        ''', (f'%{search}%', f'%{search}%'))
        
        clientes = self.cursor.fetchall()
        
        for cliente in clientes:
            self.clientes_listbox.insert("", "end", values=(cliente[0], cliente[1], cliente[2] or ""))
    
    def filter_manage_list(self, tipo):
        """Filtra lista de gerenciamento por busca - COM MATRÍCULA PARA COLABORADORES"""
        search_var = getattr(self, f'{tipo}_search_var', None)
        if not search_var:
            return
        
        search = search_var.get().upper()
        listbox = getattr(self, f'{tipo}_listbox')
        
        # Limpar lista
        for item in listbox.get_children():
            listbox.delete(item)
        
        if tipo == "colaboradores":
            # Buscar por matrícula OU nome
            if search:
                self.cursor.execute('''
                    SELECT id, matricula, nome FROM colaboradores 
                    WHERE UPPER(matricula) LIKE ? OR UPPER(nome) LIKE ?
                    ORDER BY nome
                ''', (f'%{search}%', f'%{search}%'))
            else:
                self.cursor.execute("SELECT id, matricula, nome FROM colaboradores ORDER BY nome")
        else:
            # Buscar apenas por nome
            if search:
                self.cursor.execute(f'''
                    SELECT id, nome FROM {tipo} 
                    WHERE UPPER(nome) LIKE ?
                    ORDER BY nome
                ''', (f'%{search}%',))
            else:
                self.cursor.execute(f"SELECT id, nome FROM {tipo} ORDER BY nome")
        
        for row in self.cursor.fetchall():
            listbox.insert("", "end", values=row)
    
    def edit_cliente(self):
        """Edita cliente selecionado"""
        selected = self.clientes_listbox.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um cliente para editar")
            return
        
        item = self.clientes_listbox.item(selected[0])
        values = item['values']
        old_cliente = values[1]
        old_matricula = values[2] if values[2] else ""
        
        # Janela de edição
        edit_window = ctk.CTkToplevel(self.root)
        edit_window.title("Editar Cliente")
        edit_window.geometry("500x380")
        edit_window.grab_set()
        edit_window.transient(self.root)
        
        # Centralizar
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - 250
        y = (edit_window.winfo_screenheight() // 2) - 190
        edit_window.geometry(f"500x380+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        title = ctk.CTkLabel(main_frame, text="✏️ EDITAR CLIENTE",
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(0, 20))
        
        # Campo Cliente
        ctk.CTkLabel(main_frame, text="Nome do Cliente:",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        cliente_var = ctk.StringVar(value=old_cliente)
        cliente_entry = ctk.CTkEntry(main_frame, textvariable=cliente_var, 
                                    height=40, width=400)
        cliente_entry.pack(fill="x", pady=(0, 15))
        cliente_entry.bind('<KeyRelease>', self.make_uppercase)
        
        # Campo Matrícula
        ctk.CTkLabel(main_frame, text="Matrícula:",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        matricula_var = ctk.StringVar(value=old_matricula)
        matricula_entry = ctk.CTkEntry(main_frame, textvariable=matricula_var, 
                                      height=40, width=400)
        matricula_entry.pack(fill="x", pady=(0, 15))
        matricula_entry.bind('<KeyRelease>', self.make_uppercase)
        
        def confirm_edit():
            new_cliente = cliente_var.get().strip().upper()
            new_matricula = matricula_var.get().strip().upper()
            
            if not new_cliente:
                messagebox.showerror("Erro", "O nome do cliente não pode estar vazio!")
                return
            
            # Verificar se a matrícula mudou e se já está sendo usada por outro cliente
            if new_matricula and new_matricula != old_matricula:
                self.cursor.execute('''
                    SELECT DISTINCT cliente FROM registros 
                    WHERE matricula = ? 
                    AND NOT (cliente = ? AND (matricula = ? OR (matricula IS NULL AND ? = '')))
                    LIMIT 1
                ''', (new_matricula, old_cliente, old_matricula, old_matricula))
                
                conflito = self.cursor.fetchone()
                if conflito:
                    messagebox.showerror("Erro", 
                        f"⚠️ A matrícula '{new_matricula}' já está sendo usada pelo cliente:\n\n"
                        f"'{conflito[0]}'\n\n"
                        f"Escolha outra matrícula!")
                    return
            
            try:
                # Contar registros que serão atualizados
                self.cursor.execute('''
                    SELECT COUNT(*) FROM registros 
                    WHERE cliente = ? AND (matricula = ? OR (matricula IS NULL AND ? = ''))
                ''', (old_cliente, old_matricula, old_matricula))
                count = self.cursor.fetchone()[0]
                
                # Confirmar alteração
                if not messagebox.askyesno("Confirmar", 
                    f"Deseja alterar:\n\n"
                    f"Cliente: {old_cliente} → {new_cliente}\n"
                    f"Matrícula: {old_matricula or '(vazio)'} → {new_matricula or '(vazio)'}\n\n"
                    f"Isso afetará {count} registro(s)"):
                    return
                
                # Atualizar registros
                self.cursor.execute('''
                    UPDATE registros 
                    SET cliente = ?, matricula = ?
                    WHERE cliente = ? AND (matricula = ? OR (matricula IS NULL AND ? = ''))
                ''', (new_cliente, new_matricula or None, old_cliente, old_matricula, old_matricula))
                
                # Atualizar arquivos JSON
                count_json = self.update_json_files_cliente(old_cliente, old_matricula, new_cliente, new_matricula)
                
                self.conn.commit()
                
                # Recarregar dados
                self.load_clientes_data()
                self.update_filters()
                
                messagebox.showinfo("Sucesso", 
                    f"✅ Cliente atualizado com sucesso!\n\n"
                    f"Registros no banco: {count}\n"
                    f"Registros em JSON: {count_json}")
                
                edit_window.destroy()
                
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Erro", f"Erro ao atualizar:\n{str(e)}")
        
        # Botões
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(20, 0))
        
        ctk.CTkButton(btn_frame, text="✓ Confirmar", 
                     command=confirm_edit,
                     fg_color="#10b981", hover_color="#059669",
                     width=170, height=45,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="✕ Cancelar", 
                     command=edit_window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563",
                     width=170, height=45,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
    
    def update_json_files_cliente(self, old_cliente, old_matricula, new_cliente, new_matricula):
        """Atualiza cliente/matrícula nos arquivos JSON"""
        arquivos_dir = 'arquivos_mensais'
        total_updated = 0
        
        if not os.path.exists(arquivos_dir):
            return 0
        
        json_files = [f for f in os.listdir(arquivos_dir) if f.endswith('.json')]
        
        for filename in json_files:
            filepath = os.path.join(arquivos_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
                
                count_file = 0
                for registro in registros:
                    reg_cliente = registro.get('cliente', '')
                    reg_matricula = registro.get('matricula', '') or ''
                    
                    if reg_cliente == old_cliente and reg_matricula == old_matricula:
                        registro['cliente'] = new_cliente
                        registro['matricula'] = new_matricula or None
                        count_file += 1
                
                if count_file > 0:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(registros, f, indent=2, ensure_ascii=False)
                    total_updated += count_file
                    
            except Exception as e:
                print(f"Erro ao processar {filename}: {e}")
                continue
        
        return total_updated
    
    # Estatísticas gerenciadas por StatsManager
    def create_stats_tab(self):
        """Cria aba de estatísticas"""
        from views.stats_manager import StatsManager
        tab = self.tabview.tab("Estatísticas")
        self.stats_manager = StatsManager(self)
        self.stats_manager.create_stats_tab(tab)

    # Estatísticas gerenciadas por RankingManager
    def create_ranking_tab(self):
        """Cria aba de ranking"""
        from views.ranking_manager import RankingManager
        tab = self.tabview.tab("Ranking")
        self.ranking_manager = RankingManager(self)
        self.ranking_manager.create_ranking_tab(tab)

    def bind_archive_filter_events(self):
        """Vincula eventos para filtro automático da aba de arquivos"""
        self.archive_filter_vars['mes'].trace_add('write', self.on_archive_mes_ano_changed)
        self.archive_filter_vars['ano'].trace_add('write', self.on_archive_mes_ano_changed)
        self.archive_filter_vars['colaborador'].trace_add('write', lambda *args: self.on_archive_colaborador_filter_changed())
        self.archive_filter_vars['matricula_col'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['equipamento'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['cliente'].trace_add('write', lambda *args: self.on_archive_cliente_filter_changed())
        self.archive_filter_vars['matricula_cli'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['local'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['tipo'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['data'].trace_add('write', self.on_archive_data_changed)
    
    def on_archive_colaborador_filter_changed(self):
        """Quando colaborador muda nos arquivos, atualiza matrículas disponíveis"""
        colaborador = self.archive_filter_vars['colaborador'].get()
        
        if colaborador == "Todos":
            # Mostrar todas as matrículas de colaboradores
            matriculas = ["Todos"] + self.get_todas_matriculas_colaboradores()
        else:
            # Buscar matrículas deste colaborador
            matriculas = ["Todos"] + self.get_matriculas_by_colaborador(colaborador)
        
        # Atualizar combobox de matrícula COL
        self.archive_matricula_col_filter.configure(values=matriculas)
        self.archive_filter_vars['matricula_col'].set("Todos")
        
        self.load_archive_data()
    
    def on_archive_cliente_filter_changed(self):
        """Quando cliente muda nos arquivos, atualiza matrículas disponíveis"""
        cliente = self.archive_filter_vars['cliente'].get()
        
        if cliente == "Todos":
            # Mostrar todas as matrículas de clientes
            matriculas = ["Todos"] + self.get_todas_matriculas_clientes()
        else:
            # Buscar matrículas deste cliente
            matriculas = ["Todos"] + self.get_matriculas_by_cliente(cliente)
        
        # Atualizar combobox de matrícula CLI
        self.archive_matricula_cli_filter.configure(values=matriculas)
        self.archive_filter_vars['matricula_cli'].set("Todos")
        
        self.load_archive_data()
    
    def on_archive_mes_ano_changed(self, *args):
        """Callback quando mês ou ano mudam em Registros Antigos"""
        if self.archive_filter_vars['data'].get():
            self.archive_filter_vars['data'].set("")
        self.load_archive_data()
    
    def on_archive_data_changed(self, *args):
        """Callback quando data específica muda em Registros Antigos"""
        data = self.archive_filter_vars['data'].get()
        if data:
            self.load_archive_data()
    
    def get_available_years(self):
        """Retorna lista de anos que possuem registros"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT substr(data, 7, 4) as ano
                FROM registros 
                ORDER BY ano DESC
            ''')
            years = [row[0] for row in self.cursor.fetchall() if row[0]]
            
            if not years:
                years = [str(datetime.now().year)]
            
            return years
        except:
            return [str(datetime.now().year)]
    
    def get_clientes(self):
        """Retorna lista de clientes únicos dos registros"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT cliente FROM registros 
                WHERE cliente IS NOT NULL AND cliente != ''
                ORDER BY cliente
            ''')
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_matriculas(self):
        """Retorna lista de matrículas únicas dos registros"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT matricula FROM registros 
                WHERE matricula IS NOT NULL AND matricula != ''
                ORDER BY matricula
            ''')
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_colaboradores_nomes_unicos(self):
        """Retorna lista de nomes únicos de colaboradores (sem duplicatas)"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT nome FROM colaboradores 
                WHERE nome IS NOT NULL AND nome != ''
                ORDER BY nome
            ''')
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_clientes_nomes_unicos(self):
        """Retorna lista de nomes únicos de clientes dos registros (sem duplicatas)"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT cliente FROM registros 
                WHERE cliente IS NOT NULL AND cliente != ''
                ORDER BY cliente
            ''')
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_matriculas_by_colaborador(self, nome):
        """Retorna lista de matrículas de colaboradores com o nome especificado"""
        try:
            self.cursor.execute('''
                SELECT matricula FROM colaboradores 
                WHERE nome = ?
                ORDER BY matricula
            ''', (nome,))
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_matriculas_by_cliente(self, nome_cliente):
        """Retorna lista de matrículas de clientes com o nome especificado"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT matricula FROM registros 
                WHERE cliente = ? AND matricula IS NOT NULL AND matricula != ''
                ORDER BY matricula
            ''', (nome_cliente,))
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_todas_matriculas_colaboradores(self):
        """Retorna todas as matrículas de colaboradores cadastrados"""
        try:
            self.cursor.execute('''
                SELECT matricula FROM colaboradores 
                WHERE matricula IS NOT NULL AND matricula != ''
                ORDER BY matricula
            ''')
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def get_todas_matriculas_clientes(self):
        """Retorna todas as matrículas de clientes dos registros"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT matricula FROM registros 
                WHERE matricula IS NOT NULL AND matricula != ''
                ORDER BY matricula
            ''')
            return [row[0] for row in self.cursor.fetchall()]
        except:
            return []
    
    def clear_archive_filters(self):
        """Limpa todos os filtros da aba de arquivos"""
        self.archive_filter_vars['mes'].set(str(datetime.now().month).zfill(2))
        self.archive_filter_vars['ano'].set(str(datetime.now().year))
        self.archive_filter_vars['data'].set("")
        self.archive_filter_vars['colaborador'].set("Todos")
        self.archive_filter_vars['matricula_col'].set("Todos")
        self.archive_filter_vars['equipamento'].set("Todos")
        self.archive_filter_vars['cliente'].set("Todos")
        self.archive_filter_vars['matricula_cli'].set("Todos")
        self.archive_filter_vars['local'].set("Todos")
        self.archive_filter_vars['tipo'].set("Todos")
        
        # Resetar comboboxes de matrícula com todas as opções
        if hasattr(self, 'archive_matricula_col_filter'):
            self.archive_matricula_col_filter.configure(values=["Todos"] + self.get_todas_matriculas_colaboradores())
        if hasattr(self, 'archive_matricula_cli_filter'):
            self.archive_matricula_cli_filter.configure(values=["Todos"] + self.get_todas_matriculas_clientes())
    
    def update_archive_filters(self):
        """Atualiza os valores dos filtros da aba de arquivos"""
        colaboradores = ["Todos"] + self.get_colaboradores_nomes_unicos()
        equipamentos = ["Todos"] + self.get_items("equipamentos")
        clientes = ["Todos"] + self.get_clientes_nomes_unicos()
        locais = ["Todos"] + self.get_items("locais")
        years = self.get_available_years()
        
        if hasattr(self, 'archive_colaborador_filter'):
            self.archive_colaborador_filter.configure(values=colaboradores)
        if hasattr(self, 'archive_equipamento_filter'):
            self.archive_equipamento_filter.configure(values=equipamentos)
        if hasattr(self, 'archive_cliente_filter'):
            self.archive_cliente_filter.configure(values=clientes)
        if hasattr(self, 'archive_local_filter'):
            self.archive_local_filter.configure(values=locais)
        if hasattr(self, 'archive_ano_filter'):
            self.archive_ano_filter.configure(values=years)
    
    def load_archive_data(self):
        """Carrega dados de registros com filtros aplicados - INCLUI MATRÍCULA COL e CLI"""
        for item in self.archive_tree.get_children():
            self.archive_tree.delete(item)
        
        mes = self.archive_filter_vars['mes'].get()
        ano = self.archive_filter_vars['ano'].get()
        data_especifica = self.archive_filter_vars['data'].get()
        colaborador = self.archive_filter_vars['colaborador'].get()
        matricula_col = self.archive_filter_vars['matricula_col'].get()
        equipamento = self.archive_filter_vars['equipamento'].get()
        cliente = self.archive_filter_vars['cliente'].get()
        matricula_cli = self.archive_filter_vars['matricula_cli'].get()
        local = self.archive_filter_vars['local'].get()
        tipo = self.archive_filter_vars['tipo'].get()
        
        query = '''
            SELECT id, data, colaborador, equipamento, matricula, cliente, local, 
                horario, tipo, colaborador_matricula
            FROM registros 
            WHERE 1=1
        '''
        params = []
        
        if data_especifica and self.validate_date(data_especifica):
            query += " AND data = ?"
            params.append(data_especifica)
        elif mes and ano:
            query += " AND substr(data, 4, 2) = ? AND substr(data, 7, 4) = ?"
            params.extend([mes, ano])
        
        if colaborador != "Todos":
            query += " AND colaborador = ?"
            params.append(colaborador)
        
        if matricula_col != "Todos":
            query += " AND colaborador_matricula = ?"
            params.append(matricula_col)
        
        if equipamento != "Todos":
            query += " AND equipamento = ?"
            params.append(equipamento)
        
        if cliente != "Todos":
            query += " AND cliente = ?"
            params.append(cliente)
        
        if matricula_cli != "Todos":
            query += " AND matricula = ?"
            params.append(matricula_cli)
        
        if local != "Todos":
            query += " AND local = ?"
            params.append(local)
        
        if tipo != "Todos":
            query += " AND tipo = ?"
            params.append(tipo)
        
        query += '''
            ORDER BY 
                substr(data, 7, 4) || '-' || 
                substr(data, 4, 2) || '-' || 
                substr(data, 1, 2) DESC,
                horario DESC
        '''
        
        try:
            self.cursor.execute(query, params)
            records = self.cursor.fetchall()
            
            for record in records:
                # Estrutura: id, data, colaborador, equipamento, matricula, cliente, local, horario, tipo
                tipo_registro = record[8] if len(record) > 8 else ""
                if tipo_registro == "ENTREGA":
                    self.archive_tree.insert('', 'end', values=record, tags=('entrega',))
                elif tipo_registro == "RETIRADA":
                    self.archive_tree.insert('', 'end', values=record, tags=('retirada',))
                else:
                    self.archive_tree.insert('', 'end', values=record)
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar registros: {str(e)}")

    def sort_archive_by_date(self):
        """Ordena a tabela de registros antigos por Data (decrescente)"""
        if not hasattr(self, 'archive_tree'):
            return
        
        items = [(self.archive_tree.set(item, 'Data'), item) 
                 for item in self.archive_tree.get_children('')]
        
        def date_key(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return datetime.min
        
        items.sort(key=lambda x: date_key(x[0]), reverse=True)
        
        for index, (_, item) in enumerate(items):
            self.archive_tree.move(item, '', index)
    
    def open_calendar(self, date_entry):
        """Abre o calendário para seleção de data"""
        calendar_window = ctk.CTkToplevel(self.root)
        calendar_window.title("Selecionar Data")
        calendar_window.geometry("300x300")
        calendar_window.grab_set()
        calendar_window.transient(self.root)
        
        cal = Calendar(calendar_window, selectmode='day', 
                      year=datetime.now().year, 
                      month=datetime.now().month, 
                      day=datetime.now().day,
                      date_pattern='dd/mm/yyyy')
        cal.pack(padx=20, pady=20, fill="both", expand=True)
        
        def set_date():
            selected_date = cal.get_date()
            date_entry.delete(0, 'end')
            date_entry.insert(0, selected_date)
            calendar_window.destroy()
        
        btn_confirm = ctk.CTkButton(calendar_window, text="SELECIONAR DATA", 
                                   command=set_date,
                                   fg_color="#10b981", hover_color="#059669")
        btn_confirm.pack(pady=10)
    
    def sort_treeview(self, tree, col, reverse):
        """Ordena a treeview pela coluna clicada"""
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        if "Data" in col:
            try:
                data.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y") if x[0] else datetime.min, reverse=reverse)
            except:
                data.sort(reverse=reverse)
        elif col in ["ID", "Equipamento"]:
            try:
                data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'), reverse=reverse)
            except:
                data.sort(reverse=reverse)
        else:
            data.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(data):
            tree.move(item, '', index)
        
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))
    
    def sort_manage_treeview(self, tree, col, reverse, tipo):
        """Ordena a treeview de gerenciamento pela coluna clicada"""
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        if col == "ID":
            try:
                data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'), reverse=reverse)
            except:
                data.sort(reverse=reverse)
        else:
            data.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(data):
            tree.move(item, '', index)
        
        tree.heading(col, command=lambda: self.sort_manage_treeview(tree, col, not reverse, tipo))
    
    def format_date_input(self, event):
        """Formata automaticamente a data enquanto o usuário digita"""
        widget = event.widget
        content = widget.get()
        
        numbers = re.sub(r'[^\d]', '', content)
        
        if len(numbers) > 8:
            numbers = numbers[:8]
        
        formatted = ""
        if len(numbers) > 0:
            formatted = numbers[0:2]
        if len(numbers) >= 3:
            formatted += "/" + numbers[2:4]
        if len(numbers) >= 5:
            formatted += "/" + numbers[4:8]
        
        if content != formatted:
            widget.delete(0, 'end')
            widget.insert(0, formatted)
    
    def format_time_input(self, event):
        """Formata automaticamente o horário enquanto o usuário digita"""
        widget = event.widget
        content = widget.get()
        
        numbers = re.sub(r'[^\d]', '', content)
        
        if len(numbers) > 4:
            numbers = numbers[:4]
        
        formatted = ""
        if len(numbers) > 0:
            formatted = numbers[0:2]
        if len(numbers) >= 3:
            formatted += ":" + numbers[2:4]
        
        if content != formatted:
            widget.delete(0, 'end')
            widget.insert(0, formatted)
    
    def validate_date(self, date_string):
        """Valida se a data é válida"""
        try:
            datetime.strptime(date_string, "%d/%m/%Y")
            return True
        except ValueError:
            return False
    
    def validate_time(self, time_string):
        """Valida se o horário é válido"""
        try:
            datetime.strptime(time_string, "%H:%M")
            return True
        except ValueError:
            return False
    
    def make_uppercase(self, event):
        """Converte o texto para maiúsculas automaticamente"""
        widget = event.widget
        content = widget.get()
        if content != content.upper():
            widget.delete(0, 'end')
            widget.insert(0, content.upper())
    
    def create_manage_tab(self, tipo):
        """Cria aba de gerenciamento - COM SUPORTE A MATRÍCULA PARA COLABORADORES"""
        if tipo == "colaboradores":
            tab_name = "Gerenciar Colaboradores"
            label = "COLABORADORES"
        elif tipo == "locais":
            tab_name = "Gerenciar Locais"
            label = "LOCAIS"
        else:
            tab_name = "Gerenciar Equipamentos"
            label = "EQUIPAMENTOS"
            
        tab = self.tabview.tab(tab_name)
        
        # Container
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        title = ctk.CTkLabel(container, text=f"GERENCIAR {label}",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(0, 30))
        
        # Frame de entrada
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 20))
        
        # ===== LAYOUT ESPECIAL PARA COLABORADORES (com matrícula) =====
        if tipo == "colaboradores":
            # Frame para campos de entrada
            fields_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
            fields_frame.pack(side="left")
            
            # Campo Matrícula
            mat_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            mat_frame.pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(mat_frame, text="Matrícula:", 
                        font=ctk.CTkFont(size=12)).pack(anchor="w")
            
            if not hasattr(self, 'colaboradores_matricula_var'):
                setattr(self, 'colaboradores_matricula_var', ctk.StringVar())
            
            matricula_entry = ctk.CTkEntry(mat_frame, 
                                        textvariable=self.colaboradores_matricula_var,
                                        placeholder_text="Ex: COL-001", 
                                        height=40, width=120)
            matricula_entry.pack()
            matricula_entry.bind('<KeyRelease>', self.make_uppercase)
            
            # Campo Nome
            nome_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
            nome_frame.pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(nome_frame, text="Nome:", 
                        font=ctk.CTkFont(size=12)).pack(anchor="w")
            
            if not hasattr(self, 'colaboradores_entry_var'):
                setattr(self, 'colaboradores_entry_var', ctk.StringVar())
            
            nome_entry = ctk.CTkEntry(nome_frame, 
                                    textvariable=self.colaboradores_entry_var,
                                    placeholder_text="Nome do Colaborador", 
                                    height=40, width=280)
            nome_entry.pack()
            nome_entry.bind('<KeyRelease>', self.make_uppercase)
            
            # Botões
            btn_add = ctk.CTkButton(input_frame, text="ADICIONAR", 
                                command=lambda: self.add_item(tipo),
                                fg_color="#10b981", hover_color="#059669",
                                width=120, height=40)
            btn_add.pack(side="left", padx=(10, 5))

            btn_editar = ctk.CTkButton(input_frame, text="EDITAR", 
                                    command=lambda: self.edit_item(tipo),
                                    fg_color="#f59e0b", hover_color="#d97706",
                                    width=150, height=40)
            btn_editar.pack(side="left", padx=(10, 5))
            
        else:
            # ===== LAYOUT PADRÃO (locais e equipamentos) =====
            if not hasattr(self, f'{tipo}_entry_var'):
                setattr(self, f'{tipo}_entry_var', ctk.StringVar())
            
            entry_var = getattr(self, f'{tipo}_entry_var')
            
            placeholder = f"Nome do Equipamento" if tipo == "equipamentos" else f"Nome do {tipo[:-1]}"
            entry = ctk.CTkEntry(input_frame, textvariable=entry_var, 
                                placeholder_text=placeholder, 
                                height=40, width=400)
            entry.pack(side="left", padx=(0, 10))
            entry.bind('<KeyRelease>', self.make_uppercase)
            
            btn_add = ctk.CTkButton(input_frame, text="ADICIONAR", 
                                command=lambda: self.add_item(tipo),
                                fg_color="#10b981", hover_color="#059669",
                                width=150, height=40)
            btn_add.pack(side="left")

            btn_editar = ctk.CTkButton(input_frame, text="EDITAR", 
                                    command=lambda: self.edit_item(tipo),
                                    fg_color="#f59e0b", hover_color="#d97706",
                                    width=150, height=40)
            btn_editar.pack(side="left", padx=(10, 5))
        
        # ===== BUSCADOR (lado direito) =====
        search_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        search_frame.pack(side="right")
        
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        
        if not hasattr(self, f'{tipo}_search_var'):
            setattr(self, f'{tipo}_search_var', ctk.StringVar())
        
        search_var = getattr(self, f'{tipo}_search_var')
        search_var.trace_add('write', lambda *args, t=tipo: self.filter_manage_list(t))
        
        search_placeholder = "Buscar por matrícula ou nome..." if tipo == "colaboradores" else "Buscar..."
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var,
                                placeholder_text=search_placeholder,
                                width=180 if tipo == "colaboradores" else 150, 
                                height=35)
        search_entry.pack(side="left")
        
        # Frame da lista
        list_frame = ctk.CTkFrame(container, corner_radius=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        # ===== TREEVIEW - COM MATRÍCULA PARA COLABORADORES =====
        if tipo == "colaboradores":
            columns = ("ID", "Matrícula", "Nome")
            listbox = ttk.Treeview(list_frame, columns=columns, show="headings",
                                yscrollcommand=scrollbar.set, height=12)
            scrollbar.config(command=listbox.yview)
            
            listbox.column("ID", width=60, anchor="center")
            listbox.column("Matrícula", width=120, anchor="center")
            listbox.column("Nome", width=350, anchor="center")
            
            listbox.heading("ID", text="ID", anchor="center", 
                        command=lambda: self.sort_manage_treeview(listbox, "ID", False, tipo))
            listbox.heading("Matrícula", text="Matrícula", anchor="center",
                        command=lambda: self.sort_manage_treeview(listbox, "Matrícula", False, tipo))
            listbox.heading("Nome", text="Nome", anchor="center",
                        command=lambda: self.sort_manage_treeview(listbox, "Nome", False, tipo))
        else:
            columns = ("ID", "Nome")
            listbox = ttk.Treeview(list_frame, columns=columns, show="headings",
                                yscrollcommand=scrollbar.set, height=12)
            scrollbar.config(command=listbox.yview)
            
            listbox.column("ID", width=80, anchor="center")
            listbox.column("Nome", width=400, anchor="center")
            
            listbox.heading("ID", text="ID", anchor="center", 
                        command=lambda: self.sort_manage_treeview(listbox, "ID", False, tipo))
            listbox.heading("Nome", text="Nome", anchor="center",
                        command=lambda: self.sort_manage_treeview(listbox, "Nome", False, tipo))
        
        listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar estilo da lista
        style_name = f"{tipo}.Treeview"
        style = ttk.Style()
        if self.current_theme == "dark":
            style.theme_use('default')
            style.configure(style_name, 
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        rowheight=30,
                        borderwidth=0)
            style.configure(style_name + ".Heading",
                        background="#1a1a1a",
                        foreground="white",
                        relief="flat",
                        borderwidth=1,
                        bordercolor="#3b3b3b")
            style.map(style_name, 
                    background=[('selected', '#3b82f6')],
                    foreground=[('selected', 'white')])
        else:
            style.theme_use('default')
            style.configure(style_name, 
                        background="white",
                        foreground="black",
                        fieldbackground="white",
                        rowheight=30,
                        borderwidth=0)
            style.configure(style_name + ".Heading",
                        background="#e5e5e5",
                        foreground="black",
                        relief="flat",
                        borderwidth=1,
                        bordercolor="#d4d4d4")
            style.map(style_name, 
                    background=[('selected', '#3b82f6')],
                    foreground=[('selected', 'white')])
        
        listbox.configure(style=style_name)
        
        # Guardar referência
        setattr(self, f'{tipo}_listbox', listbox)
        
        # Botões de ação
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # Carregar dados
        self.load_manage_data(tipo)
    
    def get_items(self, tipo, campo="nome"):
        """Retorna lista de itens cadastrados"""
        if tipo == "colaboradores":
            # Para colaboradores, retornar apenas os nomes (para filtros)
            self.cursor.execute("SELECT nome FROM colaboradores ORDER BY nome")
        else:
            self.cursor.execute(f"SELECT {campo} FROM {tipo} ORDER BY {campo}")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_colaboradores_for_combobox(self):
        """Retorna lista de colaboradores formatados para ComboBox (Matrícula - Nome)"""
        self.cursor.execute("SELECT matricula, nome FROM colaboradores ORDER BY nome")
        return [f"{row[0]} - {row[1]}" for row in self.cursor.fetchall()]
    
    def load_main_data(self):
        """Carrega dados na tabela principal - INCLUI MATRÍCULA"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.cursor.execute('''
            SELECT id, data, colaborador, equipamento, matricula, cliente, local, 
                horario, tipo 
            FROM registros 
            ORDER BY 
                substr(data, 7, 4) || '-' || 
                substr(data, 4, 2) || '-' || 
                substr(data, 1, 2) DESC,
                horario DESC
            LIMIT 20
        ''')

        for row in self.cursor.fetchall():
            # Estrutura: id, data, colaborador, equipamento, matricula, cliente, local, horario, tipo
            tipo_registro = row[8] if len(row) > 8 else ""
            if tipo_registro == "ENTREGA":
                self.tree.insert("", "end", values=row, tags=('entrega',))
            elif tipo_registro == "RETIRADA":
                self.tree.insert("", "end", values=row, tags=('retirada',))
            else:
                self.tree.insert("", "end", values=row)

    def apply_filters(self, *args):
        """Aplica filtros na tabela - COM MATRÍCULA COL e CLI"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = "SELECT id, data, colaborador, equipamento, matricula, cliente, local, horario, tipo, colaborador_matricula FROM registros WHERE 1=1"
        params = []
        
        if self.filter_vars['data'].get():
            query += " AND data = ?"
            params.append(self.filter_vars['data'].get())
        
        if self.filter_vars['colaborador'].get() != "Todos":
            query += " AND colaborador = ?"
            params.append(self.filter_vars['colaborador'].get())
        
        if self.filter_vars['matricula_col'].get() != "Todos":
            query += " AND colaborador_matricula = ?"
            params.append(self.filter_vars['matricula_col'].get())
        
        if self.filter_vars['equipamento'].get() != "Todos":
            query += " AND equipamento = ?"
            params.append(self.filter_vars['equipamento'].get())
        
        if self.filter_vars['cliente'].get() != "Todos":
            query += " AND cliente = ?"
            params.append(self.filter_vars['cliente'].get())
        
        if self.filter_vars['matricula_cli'].get() != "Todos":
            query += " AND matricula = ?"
            params.append(self.filter_vars['matricula_cli'].get())
        
        if self.filter_vars['local'].get() != "Todos":
            query += " AND local = ?"
            params.append(self.filter_vars['local'].get())
        
        if self.filter_vars['tipo'].get() != "Todos":
            query += " AND tipo = ?"
            params.append(self.filter_vars['tipo'].get())
        
        query += '''
            ORDER BY 
                substr(data, 7, 4) || '-' || 
                substr(data, 4, 2) || '-' || 
                substr(data, 1, 2) DESC,
                horario DESC
            LIMIT 20
        '''
        
        self.cursor.execute(query, params)
        
        for row in self.cursor.fetchall():
            # Exibir apenas as 9 primeiras colunas (sem colaborador_matricula)
            display_row = row[:9]
            tipo_registro = row[8] if len(row) > 8 else ""
            if tipo_registro == "ENTREGA":
                self.tree.insert("", "end", values=display_row, tags=('entrega',))
            elif tipo_registro == "RETIRADA":
                self.tree.insert("", "end", values=display_row, tags=('retirada',))
            else:
                self.tree.insert("", "end", values=display_row)
    
    def load_manage_data(self, tipo):
        """Carrega dados na lista de gerenciamento - COM MATRÍCULA PARA COLABORADORES"""
        listbox = getattr(self, f'{tipo}_listbox')
        
        for item in listbox.get_children():
            listbox.delete(item)
        
        if tipo == "colaboradores":
            # Colaboradores têm matrícula
            self.cursor.execute("SELECT id, matricula, nome FROM colaboradores ORDER BY nome")
            for row in self.cursor.fetchall():
                listbox.insert("", "end", values=row)
        else:
            # Locais e equipamentos - apenas nome
            self.cursor.execute(f"SELECT id, nome FROM {tipo} ORDER BY nome")
            for row in self.cursor.fetchall():
                listbox.insert("", "end", values=row)
    
    def clear_filters(self):
        """Limpa os filtros"""
        self.filter_vars['data'].set("")
        self.filter_vars['colaborador'].set("Todos")
        self.filter_vars['matricula_col'].set("Todos")
        self.filter_vars['equipamento'].set("Todos")
        self.filter_vars['cliente'].set("Todos")
        self.filter_vars['matricula_cli'].set("Todos")
        self.filter_vars['local'].set("Todos")
        self.filter_vars['tipo'].set("Todos")
        
        # Resetar comboboxes de matrícula com todas as opções
        if hasattr(self, 'matricula_col_filter'):
            self.matricula_col_filter.configure(values=["Todos"] + self.get_todas_matriculas_colaboradores())
        if hasattr(self, 'matricula_cli_filter'):
            self.matricula_cli_filter.configure(values=["Todos"] + self.get_todas_matriculas_clientes())
        
        self.load_main_data()
    
    def new_record(self):
        """Abre janela para novo registro"""
        RecordWindow(self, mode="new")
    
    def edit_record(self):
        """Abre janela para editar registro"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para editar")
            return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        RecordWindow(self, mode="edit", record_id=record_id)
    
    def delete_record(self):
        """Exclui registro selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para excluir")
            return
        
        if messagebox.askyesno("Confirmar", "Deseja excluir este registro?"):
            item = self.tree.item(selected[0])
            record_id = item['values'][0]
            
            self.cursor.execute("DELETE FROM registros WHERE id = ?", (record_id,))
            self.conn.commit()
            
            self.load_main_data()
            messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")
    
    def add_item(self, tipo):
        """Adiciona novo item - COM MATRÍCULA PARA COLABORADORES"""
        if tipo == "colaboradores":
            # Colaboradores precisam de matrícula e nome
            matricula_var = getattr(self, 'colaboradores_matricula_var', None)
            nome_var = getattr(self, 'colaboradores_entry_var', None)
            
            if not matricula_var or not nome_var:
                messagebox.showerror("Erro", "Erro interno: variáveis não inicializadas")
                return
            
            matricula = matricula_var.get().strip().upper()
            nome = nome_var.get().strip().upper()
            
            if not matricula:
                messagebox.showerror("Erro", "Digite a matrícula do colaborador")
                return
            
            if not nome:
                messagebox.showerror("Erro", "Digite o nome do colaborador")
                return
            
            try:
                self.cursor.execute(
                    "INSERT INTO colaboradores (matricula, nome) VALUES (?, ?)", 
                    (matricula, nome)
                )
                self.conn.commit()
                
                matricula_var.set("")  # Limpar campo
                nome_var.set("")  # Limpar campo
                self.load_manage_data(tipo)
                self.update_filters()
                
                messagebox.showinfo("Sucesso", f"Colaborador adicionado com sucesso!\n\nMatrícula: {matricula}\nNome: {nome}")
            except sqlite3.IntegrityError:
                # Buscar qual colaborador já usa essa matrícula
                self.cursor.execute("SELECT nome FROM colaboradores WHERE matricula = ?", (matricula,))
                conflito = self.cursor.fetchone()
                nome_conflito = conflito[0] if conflito else "Desconhecido"
                
                messagebox.showerror("Erro", 
                    f"⚠️ A matrícula '{matricula}' já está sendo usada pelo colaborador:\n\n"
                    f"'{nome_conflito}'\n\n"
                    f"Escolha outra matrícula!")
        else:
            # Locais e equipamentos - apenas nome
            entry_var = getattr(self, f'{tipo}_entry_var')
            nome = entry_var.get().strip().upper()
            
            if not nome:
                messagebox.showerror("Erro", "Digite um nome")
                return
            
            try:
                self.cursor.execute(f"INSERT INTO {tipo} (nome) VALUES (?)", (nome,))
                self.conn.commit()
                
                entry_var.set("")  # Limpar campo
                self.load_manage_data(tipo)
                self.update_filters()
                
                messagebox.showinfo("Sucesso", f"Item adicionado com sucesso!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", f"Este nome já existe!")
    
    def delete_item(self, tipo):
        """Exclui item selecionado"""
        listbox = getattr(self, f'{tipo}_listbox')
        selected = listbox.selection()
        
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um item para excluir")
            return
        
        if messagebox.askyesno("Confirmar", "Deseja excluir este item?"):
            item = listbox.item(selected[0])
            item_id = item['values'][0]
            
            self.cursor.execute(f"DELETE FROM {tipo} WHERE id = ?", (item_id,))
            self.conn.commit()
            
            self.load_manage_data(tipo)
            self.update_filters()
            
            messagebox.showinfo("Sucesso", "Item excluído com sucesso!")
    
    def edit_item(self, tipo):
        """Edita item selecionado - COM MATRÍCULA PARA COLABORADORES"""
        listbox = getattr(self, f'{tipo}_listbox')
        selected = listbox.selection()
        
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um item para editar")
            return
        
        item = listbox.item(selected[0])
        values = item['values']
        item_id = values[0]
        
        if tipo == "colaboradores":
            # Colaboradores têm matrícula e nome
            old_matricula = values[1]
            old_nome = values[2]
            
            edit_window = ctk.CTkToplevel(self.root)
            edit_window.title("Editar Colaborador")
            edit_window.geometry("500x400")
            edit_window.grab_set()
            edit_window.transient(self.root)
            
            edit_window.update_idletasks()
            x = (edit_window.winfo_screenwidth() // 2) - 250
            y = (edit_window.winfo_screenheight() // 2) - 200
            edit_window.geometry(f"500x400+{x}+{y}")
            
            main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=30, pady=30)
            
            title = ctk.CTkLabel(main_frame, text="✏️ EDITAR COLABORADOR",
                                font=ctk.CTkFont(size=18, weight="bold"))
            title.pack(pady=(0, 20))
            
            # Campo Matrícula
            ctk.CTkLabel(main_frame, text="Matrícula:",
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
            
            matricula_var = ctk.StringVar(value=old_matricula)
            matricula_entry = ctk.CTkEntry(main_frame, textvariable=matricula_var, 
                                        height=40, width=400)
            matricula_entry.pack(fill="x", pady=(0, 10))
            matricula_entry.bind('<KeyRelease>', self.make_uppercase)
            
            # Campo Nome
            ctk.CTkLabel(main_frame, text="Nome do Colaborador:",
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
            
            nome_var = ctk.StringVar(value=old_nome)
            nome_entry = ctk.CTkEntry(main_frame, textvariable=nome_var, 
                                    height=40, width=400)
            nome_entry.pack(fill="x", pady=(0, 10))
            nome_entry.bind('<KeyRelease>', self.make_uppercase)
            nome_entry.focus()
            
            info_label = ctk.CTkLabel(main_frame, 
                                    text="⚠️ A alteração do nome será aplicada em todos os registros",
                                    text_color="#f59e0b",
                                    font=ctk.CTkFont(size=11))
            info_label.pack(pady=(5, 15))
            
            def confirm_edit():
                new_matricula = matricula_var.get().strip().upper()
                new_nome = nome_var.get().strip().upper()
                
                if not new_matricula:
                    messagebox.showerror("Erro", "A matrícula não pode estar vazia!")
                    return
                
                if not new_nome:
                    messagebox.showerror("Erro", "O nome não pode estar vazio!")
                    return
                
                if new_matricula == old_matricula and new_nome == old_nome:
                    edit_window.destroy()
                    return
                
                try:
                    # Atualizar tabela colaboradores
                    self.cursor.execute(
                        "UPDATE colaboradores SET matricula = ?, nome = ? WHERE id = ?", 
                        (new_matricula, new_nome, item_id)
                    )
                    
                    # Se a matrícula mudou, atualizar o campo colaborador_matricula nos registros
                    if new_matricula != old_matricula:
                        self.cursor.execute(
                            "UPDATE registros SET colaborador_matricula = ? WHERE colaborador_matricula = ?",
                            (new_matricula, old_matricula)
                        )
                    
                    # Contar e atualizar registros se o nome mudou
                    count_banco = 0
                    count_json = 0
                    if new_nome != old_nome:
                        # Contar registros que serão atualizados (pela matrícula do colaborador)
                        self.cursor.execute(
                            "SELECT COUNT(*) FROM registros WHERE colaborador_matricula = ?",
                            (old_matricula,)
                        )
                        count_banco = self.cursor.fetchone()[0]
                        
                        # Atualizar APENAS os registros desse colaborador específico (pela matrícula)
                        self.cursor.execute(
                            "UPDATE registros SET colaborador = ? WHERE colaborador_matricula = ?",
                            (new_nome, old_matricula)
                        )
                        
                        count_json = self.update_json_files_by_matricula('colaborador', old_nome, new_nome, old_matricula)
                    
                    self.conn.commit()
                    
                    self.load_manage_data(tipo)
                    self.update_filters()
                    
                    # Montar mensagem de sucesso
                    msg_parts = ["✅ Colaborador atualizado com sucesso!\n"]
                    
                    if new_matricula != old_matricula:
                        msg_parts.append(f"\n📋 Matrícula: {old_matricula} → {new_matricula}")
                    
                    if new_nome != old_nome:
                        msg_parts.append(f"\n👤 Nome: {old_nome} → {new_nome}")
                        msg_parts.append(f"\n📝 Registros no banco: {count_banco} atualizado(s)")
                        msg_parts.append(f"\n📁 Arquivos JSON: {count_json} registro(s) atualizado(s)")
                    
                    messagebox.showinfo("Sucesso", "".join(msg_parts))
                    edit_window.destroy()
                    
                except sqlite3.IntegrityError:
                    # Buscar qual colaborador já usa essa matrícula
                    self.cursor.execute("SELECT nome FROM colaboradores WHERE matricula = ?", (new_matricula,))
                    conflito = self.cursor.fetchone()
                    nome_conflito = conflito[0] if conflito else "Desconhecido"
                    
                    messagebox.showerror("Erro", 
                        f"⚠️ A matrícula '{new_matricula}' já está sendo usada pelo colaborador:\n\n"
                        f"'{nome_conflito}'\n\n"
                        f"Escolha outra matrícula!")
                except Exception as e:
                    self.conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao atualizar:\n{str(e)}")
            
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            ctk.CTkButton(btn_frame, 
                        text="✓ Confirmar", 
                        command=confirm_edit,
                        fg_color="#10b981", 
                        hover_color="#059669",
                        width=170, 
                        height=45,
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=8)
            
            ctk.CTkButton(btn_frame, 
                        text="✕ Cancelar", 
                        command=edit_window.destroy,
                        fg_color="#6b7280", 
                        hover_color="#4b5563",
                        width=170, 
                        height=45,
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=8)
        
        else:
            # ===== CÓDIGO ORIGINAL PARA LOCAIS E EQUIPAMENTOS =====
            old_value = values[1]
            
            tipo_nome = {
                'colaboradores': 'Colaborador',
                'locais': 'Local',
                'equipamentos': 'Equipamento'
            }.get(tipo, tipo.title())
            
            campo_registro = {
                'colaboradores': 'colaborador',
                'locais': 'local',
                'equipamentos': 'equipamento'
            }.get(tipo, tipo[:-1])
            
            edit_window = ctk.CTkToplevel(self.root)
            edit_window.title(f"Editar {tipo_nome}")
            edit_window.geometry("500x360")
            edit_window.grab_set()
            edit_window.transient(self.root)
            
            edit_window.update_idletasks()
            x = (edit_window.winfo_screenwidth() // 2) - 250
            y = (edit_window.winfo_screenheight() // 2) - 180
            edit_window.geometry(f"500x360+{x}+{y}")
            
            main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=30, pady=30)
            
            title = ctk.CTkLabel(main_frame, text=f"✏️ EDITAR {tipo_nome.upper()}",
                                font=ctk.CTkFont(size=18, weight="bold"))
            title.pack(pady=(0, 20))
            
            ctk.CTkLabel(main_frame, text=f"Nome do {tipo_nome}:",
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
            
            edit_var = ctk.StringVar(value=old_value)
            edit_entry = ctk.CTkEntry(main_frame, textvariable=edit_var, height=45, width=400)
            edit_entry.pack(fill="x", pady=(0, 10))
            edit_entry.bind('<KeyRelease>', self.make_uppercase)
            edit_entry.focus()
            
            info_label = ctk.CTkLabel(main_frame, 
                                    text="⚠️ A alteração será aplicada em todos os registros e arquivos JSON",
                                    text_color="#f59e0b",
                                    font=ctk.CTkFont(size=11))
            info_label.pack(pady=(5, 15))
            
            def confirm_edit():
                new_value = edit_var.get().strip().upper()
                
                if not new_value:
                    messagebox.showerror("Erro", "O nome não pode estar vazio!")
                    return
                
                if new_value == old_value:
                    edit_window.destroy()
                    return
                
                try:
                    self.cursor.execute(f"UPDATE {tipo} SET nome = ? WHERE id = ?", (new_value, item_id))
                    
                    self.cursor.execute(f'''
                        SELECT COUNT(*) FROM registros WHERE {campo_registro} = ?
                    ''', (old_value,))
                    count_banco = self.cursor.fetchone()[0]
                    
                    self.cursor.execute(f'''
                        UPDATE registros SET {campo_registro} = ? WHERE {campo_registro} = ?
                    ''', (new_value, old_value))
                    
                    count_json = self.update_json_files(campo_registro, old_value, new_value)
                    
                    self.conn.commit()
                    
                    self.load_manage_data(tipo)
                    self.update_filters()
                    
                    success_msg = (
                        f"✅ Alteração concluída com sucesso!\n\n"
                        f"📝 Resumo:\n"
                        f"• Cadastro atualizado: {tipo_nome}\n"
                        f"• Registros no banco: {count_banco} atualizado(s)\n"
                        f"• Arquivos JSON: {count_json} registro(s) atualizado(s)\n\n"
                        f"DE:  {old_value}\n"
                        f"PARA: {new_value}"
                    )
                    
                    messagebox.showinfo("Sucesso", success_msg)
                    edit_window.destroy()
                    
                except sqlite3.IntegrityError:
                    messagebox.showerror("Erro", f"Já existe um {tipo_nome.lower()} com este nome:\n{new_value}")
                except Exception as e:
                    self.conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao atualizar:\n{str(e)}")
            
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            ctk.CTkButton(btn_frame, 
                        text="✓ Confirmar", 
                        command=confirm_edit,
                        fg_color="#10b981", 
                        hover_color="#059669",
                        width=170, 
                        height=45,
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=8)
            
            ctk.CTkButton(btn_frame, 
                        text="✕ Cancelar", 
                        command=edit_window.destroy,
                        fg_color="#6b7280", 
                        hover_color="#4b5563",
                        width=170, 
                        height=45,
                        font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=8)


    def update_json_files(self, campo, old_value, new_value):
        """Atualiza todos os arquivos JSON mensais com o novo valor"""
        arquivos_dir = 'arquivos_mensais'
        total_updated = 0
        
        if not os.path.exists(arquivos_dir):
            return 0
        
        json_files = [f for f in os.listdir(arquivos_dir) if f.endswith('.json')]
        
        if not json_files:
            return 0
        
        for filename in json_files:
            filepath = os.path.join(arquivos_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
                
                count_file = 0
                for registro in registros:
                    if registro.get(campo) == old_value:
                        registro[campo] = new_value
                        count_file += 1
                
                if count_file > 0:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(registros, f, indent=2, ensure_ascii=False)
                    
                    total_updated += count_file
            
            except Exception as e:
                print(f"Erro ao processar {filename}: {e}")
                continue
        
        return total_updated
    
    def update_json_files_by_matricula(self, campo, old_value, new_value, matricula):
        """Atualiza arquivos JSON filtrando também pela matrícula do colaborador"""
        arquivos_dir = 'arquivos_mensais'
        total_updated = 0
        
        if not os.path.exists(arquivos_dir):
            return 0
        
        json_files = [f for f in os.listdir(arquivos_dir) if f.endswith('.json')]
        
        if not json_files:
            return 0
        
        for filename in json_files:
            filepath = os.path.join(arquivos_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
                
                count_file = 0
                for registro in registros:
                    # Atualizar apenas se o valor antigo coincide E a matrícula coincide
                    # (para evitar atualizar homônimos)
                    if (registro.get(campo) == old_value and 
                        registro.get('colaborador_matricula') == matricula):
                        registro[campo] = new_value
                        count_file += 1
                
                if count_file > 0:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(registros, f, indent=2, ensure_ascii=False)
                    
                    total_updated += count_file
            
            except Exception as e:
                print(f"Erro ao processar {filename}: {e}")
                continue
        
        return total_updated
    
    def update_filters(self):
        """Atualiza os filtros com novos dados"""
        self.colaborador_filter.configure(values=["Todos"] + self.get_colaboradores_nomes_unicos())
        self.local_filter.configure(values=["Todos"] + self.get_items("locais"))
        self.equipamento_filter.configure(values=["Todos"] + self.get_items("equipamentos"))
        self.cliente_filter.configure(values=["Todos"] + self.get_clientes_nomes_unicos())
        self.update_archive_filters()
    
    
    def check_monthly_archive(self):
        """Verifica se precisa arquivar dados do mês anterior"""
        self.cursor.execute("SELECT valor FROM config WHERE chave = 'ultimo_mes_arquivado'")
        result = self.cursor.fetchone()
        
        mes_atual = datetime.now().strftime("%Y-%m")
        
        if not result or result[0] != mes_atual:
            mes_anterior = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            self.archive_month(mes_anterior)
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO config (chave, valor) 
                VALUES ('ultimo_mes_arquivado', ?)
            ''', (mes_atual,))
            self.conn.commit()
    
    def archive_month(self, mes):
        """Arquiva dados de um mês específico em JSON (backup).
        Os dados permanecem no SQLite como fonte principal de consulta."""
        if not os.path.exists("arquivos_mensais"):
            os.makedirs("arquivos_mensais")
        
        self.cursor.execute('''
            SELECT * FROM registros 
            WHERE strftime('%Y-%m', substr(data, 7, 4) || '-' || 
                  substr(data, 4, 2)) = ?
        ''', (mes,))
        
        registros = self.cursor.fetchall()
        
        if registros:
            arquivo = f"arquivos_mensais/registros_{mes}.json"
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(registros, f, indent=4, ensure_ascii=False)
    
    def cancel_tooltip_timer(self):
        """Cancela timer pendente de tooltip"""
        if self._tooltip_timer:
            try:
                self.root.after_cancel(self._tooltip_timer)
            except:
                pass
            self._tooltip_timer = None
    
    def show_tree_tooltip(self, event, tree, tab_name):
        """Mostra tooltip ao passar o mouse sobre células de Colaborador ou Cliente
        Implementação com debounce para evitar múltiplos tooltips"""
        try:
            # Cancelar qualquer timer pendente
            self.cancel_tooltip_timer()
            
            # Verificar se estamos na aba correta
            current_tab = self.tabview.get()
            if current_tab != tab_name:
                self.hide_tree_tooltip()
                return
            
            # Identificar região e item
            region = tree.identify_region(event.x, event.y)
            if region != "cell":
                self.hide_tree_tooltip()
                return
            
            # Identificar coluna
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            
            if not item or not column:
                self.hide_tree_tooltip()
                return
            
            # Converter coluna para índice (ex: "#3" -> 2)
            col_index = int(column.replace('#', '')) - 1
            
            # Obter nome da coluna
            columns = tree['columns']
            if col_index >= len(columns):
                self.hide_tree_tooltip()
                return
            
            col_name = columns[col_index]
            
            # Mostrar tooltip apenas para Colaborador e Cliente
            if col_name not in ['Colaborador', 'Cliente']:
                self.hide_tree_tooltip()
                return
            
            # Obter valor da célula
            values = tree.item(item, 'values')
            if col_index >= len(values):
                self.hide_tree_tooltip()
                return
            
            cell_value = values[col_index]
            
            # Verificar se o valor é válido (não None, não "None", não vazio)
            if not cell_value or str(cell_value).strip() == "" or str(cell_value).lower() == "none":
                self.hide_tree_tooltip()
                return
            
            # Verificar se já está mostrando tooltip para o mesmo item/coluna
            tooltip_key = f"{item}_{col_index}"
            if self._last_tooltip_key == tooltip_key and self.tree_tooltip:
                return  # Não recriar se for o mesmo e tooltip ainda existe
            
            # Agendar criação do tooltip com debounce (200ms)
            self._tooltip_timer = self.root.after(
                200, 
                lambda: self._create_tooltip(event, tree, item, col_index, col_name, cell_value, tooltip_key)
            )
                
        except Exception as e:
            # Em caso de erro, apenas esconder o tooltip
            self.hide_tree_tooltip()
    
    def _create_tooltip(self, event, tree, item, col_index, col_name, cell_value, tooltip_key):
        """Cria o tooltip (chamado após debounce)"""
        try:
            # Verificar se ainda é válido mostrar o tooltip
            if not item or not tree.exists(item):
                return
            
            # Atualizar chave do tooltip
            self._last_tooltip_key = tooltip_key
            
            # Destruir tooltip anterior se existir
            if self.tree_tooltip:
                try:
                    self.tree_tooltip.destroy()
                except:
                    pass
                self.tree_tooltip = None
            
            # Buscar matrícula se for Colaborador ou Cliente
            matricula = None
            if col_name == 'Colaborador':
                # Buscar colaborador_matricula diretamente do registro pelo ID
                try:
                    values = tree.item(item, 'values')
                    record_id = values[0]  # ID está na primeira coluna
                    self.cursor.execute(
                        "SELECT colaborador_matricula FROM registros WHERE id = ?",
                        (record_id,)
                    )
                    result = self.cursor.fetchone()
                    if result and result[0]:
                        matricula = result[0]
                    else:
                        # Fallback: buscar pela tabela de colaboradores
                        self.cursor.execute(
                            "SELECT matricula FROM colaboradores WHERE nome = ?",
                            (str(cell_value).upper().strip(),)
                        )
                        result = self.cursor.fetchone()
                        if result and result[0]:
                            matricula = result[0]
                except:
                    pass
            elif col_name == 'Cliente':
                # Para cliente, a matrícula está na coluna "Matrícula" (índice 4)
                try:
                    columns = tree['columns']
                    values = tree.item(item, 'values')
                    mat_col_index = list(columns).index('Matrícula')
                    if mat_col_index < len(values):
                        mat_value = values[mat_col_index]
                        if mat_value and str(mat_value).strip() and str(mat_value).lower() != "none":
                            matricula = mat_value
                except:
                    pass
            
            # Posição do tooltip
            x = event.x_root + 10
            y = event.y_root + 5
            
            # Criar janela de tooltip usando tkinter puro (sem CustomTkinter).
            # Motivo: criar/destruir um ctk.CTkToplevel a cada passagem do mouse
            # acumulava loops 'after' internos do CustomTkinter que não eram
            # totalmente liberados no destroy(), degradando a responsividade da
            # interface ao longo do tempo. tk.Toplevel não tem esse loop interno.
            self.tree_tooltip = tk.Toplevel(self.root)
            self.tree_tooltip.wm_overrideredirect(True)
            self.tree_tooltip.wm_geometry(f"+{x}+{y}")
            self.tree_tooltip.attributes('-topmost', True)

            # Frame do tooltip
            tooltip_frame = tk.Frame(self.tree_tooltip,
                                     bg="#f3f4f6",
                                     highlightbackground="#d1d5db",
                                     highlightthickness=1)
            tooltip_frame.pack(fill="both", expand=True)

            # Nome
            label_nome = tk.Label(tooltip_frame,
                                text=str(cell_value),
                                font=("Segoe UI", 10, "bold"),
                                fg="#000103",
                                bg="#f3f4f6")
            label_nome.pack(padx=8, pady=(4, 0))

            # Matrícula (se existir)
            if matricula:
                label_matricula = tk.Label(tooltip_frame,
                                    text=f"📋 Matrícula: {matricula}",
                                    font=("Segoe UI", 10),
                                    fg="#333534",
                                    bg="#f3f4f6")
                label_matricula.pack(padx=8, pady=(0, 4))
            else:
                # Ajustar padding se não tiver matrícula
                label_nome.pack_configure(pady=4)
                
        except Exception as e:
            # Em caso de erro, apenas esconder o tooltip
            self.hide_tree_tooltip()
    
    def hide_tree_tooltip(self):
        """Esconde o tooltip da tabela e cancela timers pendentes"""
        # Cancelar timer pendente
        self.cancel_tooltip_timer()
        
        # Destruir tooltip
        try:
            if hasattr(self, 'tree_tooltip') and self.tree_tooltip:
                self.tree_tooltip.destroy()
                self.tree_tooltip = None
        except:
            self.tree_tooltip = None
        
        # Limpar chave
        if hasattr(self, '_last_tooltip_key'):
            self._last_tooltip_key = None
    
    def on_tree_leave(self, event):
        """Esconde tooltip quando o mouse sai da árvore"""
        self.hide_tree_tooltip()
    
    def on_tree_scroll_main(self, *args, scrollbar):
        """Wrapper para scroll da tabela principal - esconde tooltip"""
        self.hide_tree_tooltip()
        scrollbar.set(*args)
    
    def on_scrollbar_main(self, *args):
        """Wrapper para scrollbar da tabela principal - esconde tooltip"""
        self.hide_tree_tooltip()
        self.tree.yview(*args)
    
    def on_tree_scroll_archive(self, *args, scrollbar):
        """Wrapper para scroll da tabela de arquivos - esconde tooltip"""
        self.hide_tree_tooltip()
        scrollbar.set(*args)
    
    def on_scrollbar_archive(self, *args):
        """Wrapper para scrollbar da tabela de arquivos - esconde tooltip"""
        self.hide_tree_tooltip()
        self.archive_tree.yview(*args)
    
    def on_closing(self):
        """Encerramento controlado da aplicação (graceful shutdown).

        Garante que o clique no X SEMPRE finalize o processo, independentemente
        do tempo de execução. Cancela timers pendentes, destrói tooltips, fecha
        as figuras do matplotlib e as conexões de banco, e por fim encerra o
        processo. O os._exit final é a garantia de que nenhum recurso preso
        (loops 'after' do Tcl/CustomTkinter, backend do matplotlib, etc.)
        mantenha o processo vivo após o fechamento da janela.
        """
        # Evita reentrância (ex.: múltiplos cliques no X)
        if getattr(self, "_closing", False):
            return
        self._closing = True

        # 1. Cancelar timers agendados e destruir tooltip pendente
        try:
            self.cancel_tooltip_timer()
        except Exception:
            pass
        try:
            self.hide_tree_tooltip()
        except Exception:
            pass

        # 2. Fechar todas as figuras do matplotlib
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except Exception:
            pass

        # 3. Fechar conexões de banco de dados
        try:
            if getattr(self, "conn", None) is not None:
                self.conn.close()
        except Exception:
            pass
        try:
            hdb = getattr(self, "history_db", None)
            if hdb is not None and hasattr(hdb, "close"):
                hdb.close()
        except Exception:
            pass

        # 4. Encerrar o loop e destruir a janela
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

        # 5. Garantia final: encerra o processo imediatamente
        os._exit(0)

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()
        # Fallback caso o loop termine sem passar por on_closing
        try:
            self.conn.close()
        except Exception:
            pass

    def show_record_history(self):
        """Mostra histórico do registro selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para ver o histórico")
            return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        HistoryDialog(self.root, self.history_db, record_id)
    
    def show_archive_history(self):
        """Mostra histórico de registro arquivado"""
        selected = self.archive_tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para ver o histórico")
            return
        
        item = self.archive_tree.item(selected[0])
        record_id = item['values'][0]
        HistoryDialog(self.root, self.history_db, record_id)