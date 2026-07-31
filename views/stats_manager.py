"""
Gerenciador da aba de Estatísticas COMPLETA
Sistema de Controle de Equipamentos
Contém todos os gráficos, KPIs, exportações
OTIMIZADO: Fechamento correto de figuras matplotlib + Tela de progresso + Hover
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog, Toplevel
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import tempfile
import os
import shutil
from views.widgets.tooltip import Tooltip
from views.widgets.scrollable_combobox import ScrollableComboBox
from views.widgets.progress_dialog import ProgressDialog


class StatsManager:
    """Gerencia todas as funcionalidades de estatísticas"""
    
    # Cores padrão para ENTREGA e RETIRADA (vibrantes)
    COR_ENTREGA = '#dc2626'  # Vermelho intenso vibrante
    COR_RETIRADA = '#eab308'  # Amarelo dourado vibrante
    
    def __init__(self, app):
        self.app = app
        self.cursor = app.cursor
        self.conn = app.conn
        self.root = app.root
        self.stats_filter_vars = app.stats_filter_vars
        self.current_theme = app.current_theme
        self.stats_container = None
        self.active_figures = []
        self.last_filter_changed = 'mes_ano'
        self.current_registros = []
        self.current_registros_colab = []
        self.show_year_accumulated = False
    
    def get_export_filename_prefix(self):
        """Gera prefixo do nome do arquivo baseado no último filtro alterado"""
        mes = self.stats_filter_vars['mes'].get()
        ano = self.stats_filter_vars['ano'].get()
        data_especifica = self.stats_filter_vars['data'].get()
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        if self.last_filter_changed == 'data' and data_especifica and self.validate_date(data_especifica):
            parts = data_especifica.split('/')
            date_str = f"{parts[2]}{parts[1]}{parts[0]}"
            return f"estatisticas_{date_str}_{timestamp}"
        elif self.last_filter_changed == 'mes_ano' and mes and ano:
            return f"estatisticas_{ano}{mes}_{timestamp}"
        elif mes and ano:
            return f"estatisticas_{ano}{mes}_{timestamp}"
        else:
            return f"estatisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def validate_date(self, date_str):
        return self.app.validate_date(date_str)
    
    def format_date_input(self, event):
        return self.app.format_date_input(event)
    
    def open_calendar(self, entry):
        return self.app.open_calendar(entry)
    
    def cleanup_figures(self):
        """Fecha todas as figuras matplotlib ativas"""
        for fig in self.active_figures:
            try:
                plt.close(fig)
            except:
                pass
        self.active_figures.clear()
        plt.close('all')
    
    def create_stats_tab(self, tab):
        """Cria aba de estatísticas com design moderno"""
        main_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(header_frame, text="📊 ESTATÍSTICAS E RELATÓRIOS", 
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=("black"))
        title.pack(side="left")
        
        export_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        export_frame.pack(side="right")
        
        btn_export_png = ctk.CTkButton(export_frame, text="📄 EXPORTAR PDF",
                                       command=self.export_stats_pdf,
                                       fg_color="#8b5cf6", hover_color="#7c3aed",
                                       width=150, height=35)
        btn_export_png.pack(side="left", padx=5)
        
        btn_export_csv = ctk.CTkButton(export_frame, text="📊 EXPORTAR CSV",
                                       command=self.export_stats_csv,
                                       fg_color="#10b981", hover_color="#059669",
                                       width=150, height=35)
        btn_export_csv.pack(side="left", padx=5)
        
        filter_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        filter_title = ctk.CTkLabel(filter_frame, text="FILTROS", 
                                    font=ctk.CTkFont(size=16, weight="bold"))
        filter_title.grid(row=0, column=0, columnspan=4, pady=(15, 10), padx=20, sticky="w")
        
        ctk.CTkLabel(filter_frame, text="Mês:").grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")
        self.stats_mes_filter = ScrollableComboBox(filter_frame, 
                                                   variable=self.stats_filter_vars['mes'],
                                                   values=[f"{i:02d}" for i in range(1, 13)], 
                                                   width=120,
                                                   max_visible_items=6,
                                                   app=self)
        self.stats_mes_filter.grid(row=1, column=0, padx=(70, 20), pady=10)
        
        ctk.CTkLabel(filter_frame, text="Ano:").grid(row=1, column=1, padx=(20, 5), pady=10, sticky="w")
        self.stats_ano_filter = ScrollableComboBox(filter_frame,
                                                   variable=self.stats_filter_vars['ano'],
                                                   values=self.get_available_years_stats(), 
                                                   width=120,
                                                   max_visible_items=6,
                                                   app=self)
        self.stats_ano_filter.grid(row=1, column=1, padx=(65, 20), pady=10)
        
        ctk.CTkLabel(filter_frame, text="Data:").grid(row=1, column=2, padx=(20, 5), pady=10, sticky="w")
        
        date_stats_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_stats_frame.grid(row=1, column=2, padx=(70, 20), pady=10)
        
        stats_date_entry = ctk.CTkEntry(date_stats_frame, 
                                        textvariable=self.stats_filter_vars['data'], 
                                        placeholder_text="DD/MM/AAAA",
                                        width=110)
        stats_date_entry.pack(side="left")
        stats_date_entry.bind('<KeyRelease>', self.format_date_input)
        
        stats_calendar_btn = ctk.CTkButton(date_stats_frame, text="📅", 
                                          width=30, height=30,
                                          command=lambda: self.open_calendar(stats_date_entry))
        stats_calendar_btn.pack(side="left", padx=(5, 0))
        
        clear_btn = ctk.CTkButton(filter_frame, text="LIMPAR FILTROS", 
                                 command=self.clear_stats_filters,
                                 fg_color="#475569", hover_color="#334155",
                                 width=150, height=35)
        clear_btn.grid(row=1, column=3, pady=(15, 15), padx=20)

        self.acumulado_btn = ctk.CTkButton(filter_frame, text="📅 ACUMULADO DO ANO",
                                           command=self.toggle_year_accumulated,
                                           fg_color="#059669", hover_color="#047857",
                                           width=180, height=35)
        self.acumulado_btn.grid(row=1, column=4, pady=(15, 15), padx=(0, 20))

        info_label = ctk.CTkLabel(filter_frame, 
                                 text="💡 Estatísticas do mês vigente por padrão. Selecione mês/ano para comparar. Clique nos gráficos para ampliar.",
                                 text_color="#6b7280",
                                 font=ctk.CTkFont(size=11))
        info_label.grid(row=2, column=0, columnspan=4, pady=(0, 15), padx=20, sticky="w")
        
        self.stats_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.stats_container.pack(fill="both", expand=True)
        
        self.update_statistics()
        self.bind_stats_filter_events()

    def bind_stats_filter_events(self):
        self.stats_filter_vars['mes'].trace_add('write', self.on_mes_ano_changed)
        self.stats_filter_vars['ano'].trace_add('write', self.on_mes_ano_changed)
        self.stats_filter_vars['data'].trace_add('write', self.on_data_changed)

    def toggle_year_accumulated(self):
        self.show_year_accumulated = not self.show_year_accumulated
        if self.show_year_accumulated:
            self.acumulado_btn.configure(text="📊 VER FILTRADO", fg_color="#2563eb", hover_color="#1d4ed8")
        else:
            self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO", fg_color="#059669", hover_color="#047857")
        self.update_statistics()

    def on_mes_ano_changed(self, *args):
        self.last_filter_changed = 'mes_ano'
        if self.stats_filter_vars['data'].get():
            self.stats_filter_vars['data'].set("")
        if self.show_year_accumulated:
            self.show_year_accumulated = False
            self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO", fg_color="#059669", hover_color="#047857")
        self.update_statistics()

    def on_data_changed(self, *args):
        data = self.stats_filter_vars['data'].get()
        if data:
            self.last_filter_changed = 'data'
            if self.show_year_accumulated:
                self.show_year_accumulated = False
                self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO", fg_color="#059669", hover_color="#047857")
        self.update_statistics()

    def get_available_years_stats(self):
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
    
    def clear_stats_filters(self):
        self.stats_filter_vars['mes'].set(str(datetime.now().month).zfill(2))
        self.stats_filter_vars['ano'].set(str(datetime.now().year))
        self.stats_filter_vars['data'].set("")
        if self.show_year_accumulated:
            self.show_year_accumulated = False
            self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO", fg_color="#059669", hover_color="#047857")

    # ==================== FUNÇÕES AUXILIARES ====================

    def get_entregas_retiradas(self, registros):
        """Retorna listas separadas de entregas e retiradas"""
        entregas = [r for r in registros if r[7] == 'ENTREGA']
        retiradas = [r for r in registros if r[7] == 'RETIRADA']
        return entregas, retiradas

    def count_by_field(self, registros, field_index):
        """Conta registros por campo específico"""
        counter = {}
        for r in registros:
            if len(r) > field_index and r[field_index]:
                counter[r[field_index]] = counter.get(r[field_index], 0) + 1
        return counter

    def build_colaborador_registros(self, registros):
        """Retorna registros com r[2] substituído por 'NOME (MAT)' para homônimos.
        Usa colaborador_matricula (índice 9) para identificar pessoas distintas.
        Colaboradores sem homônimos mantêm apenas o nome original.
        """
        # Detectar nomes que possuem mais de uma matrícula distinta
        nomes_mats = {}
        for r in registros:
            if len(r) > 2 and r[2]:
                mat = r[9] if len(r) > 9 and r[9] else ''
                nomes_mats.setdefault(r[2], set()).add(mat)

        homonimos = {nome for nome, mats in nomes_mats.items() if len(mats) > 1}

        if not homonimos:
            return registros  # nada a fazer

        novos = []
        for r in registros:
            if len(r) > 2 and r[2] and r[2] in homonimos:
                mat   = r[9] if len(r) > 9 and r[9] else ''
                label = f"{r[2]} ({mat})" if mat else r[2]
                r = tuple(label if i == 2 else v for i, v in enumerate(r))
            novos.append(r)
        return novos

    def add_hover_to_grouped_bars(self, fig, ax, bars1, bars2, nomes, valores1, valores2, label1="Entregas", label2="Retiradas"):
        """Adiciona hover interativo às barras agrupadas"""
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.95, edgecolor='gray'),
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                            fontsize=10, fontweight='bold')
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars1):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height() * 0.5)
                        total = sum(valores1) + sum(valores2)
                        pct = (valores1[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\n{label1}: {valores1[i]}\n({pct:.1f}% do total)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor('#fecaca')
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
                
                for i, bar in enumerate(bars2):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height() * 0.5)
                        total = sum(valores1) + sum(valores2)
                        pct = (valores2[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\n{label2}: {valores2[i]}\n({pct:.1f}% do total)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor('#fef08a')
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)

    def add_hover_to_bars(self, fig, ax, bars, nomes, valores, label="Qtd"):
        """Adiciona hover interativo às barras"""
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.95, edgecolor='gray'),
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                            fontsize=10, fontweight='bold')
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        if bar.get_height() < bar.get_width():
                            # Barras horizontais - posicionar no meio, ligeiramente à esquerda
                            annot.xy = (bar.get_width() * 0.5, bar.get_y() + bar.get_height()/2)
                        else:
                            # Barras verticais - posicionar no meio horizontal, 50% da altura
                            annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height() * 0.5)
                        
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\n{label}: {valores[i]}\n({pct:.1f}%)"
                        annot.set_text(text)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)

    def add_hover_to_pie(self, fig, ax, wedges, labels, valores):
        """Adiciona hover interativo ao gráfico de pizza"""
        annot = ax.annotate("", xy=(0,0), xytext=(0,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.95, edgecolor='gray'),
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                            fontsize=10, fontweight='bold')
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    cont, _ = wedge.contains(event)
                    if cont:
                        ang = (wedge.theta2 + wedge.theta1) / 2
                        r = wedge.r * 0.5  # Centralizar no raio médio
                        x = r * np.cos(np.deg2rad(ang))
                        y = r * np.sin(np.deg2rad(ang))
                        annot.xy = (x, y)
                        
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{labels[i]}\nQtd: {valores[i]}\n({pct:.1f}%)"
                        annot.set_text(text)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)

    def add_hover_to_line(self, fig, ax, line, datas, valores, value_label="Total"):
        """Adiciona hover interativo ao gráfico de linha"""
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.5", fc="#fedbdb", alpha=0.95, edgecolor="#fe0401"),
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                            fontsize=10, fontweight='bold')
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                cont, ind = line.contains(event)
                if cont:
                    idx = ind["ind"][0]
                    annot.xy = (idx, valores[idx])
                    text = f"{datas[idx]}\n{value_label}: {valores[idx]}"
                    annot.set_text(text)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)

    # ==================== POPUP DE DESTAQUE ====================
    
    def open_chart_popup(self, chart_type, registros, title):
        """Abre uma janela popup com o gráfico em destaque"""
        popup = Toplevel(self.root)
        popup.title(f"📊 {title}")
        popup.geometry("1280x700")
        popup.configure(bg="#2b2b2b")
        
        # Herdar ícone da janela principal
        try:
            icon_path = self.root.iconbitmap()
            if icon_path:
                popup.iconbitmap(icon_path)
        except Exception:
            try:
                popup.tk.call("wm", "iconphoto", popup._w,
                              *self.root.tk.call("wm", "iconphoto", self.root._w))
            except Exception:
                pass
        
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (1280 // 2)
        y = (popup.winfo_screenheight() // 2) - (700 // 2)
        popup.geometry(f"1280x700+{x}+{y}")
        
        main_frame = ctk.CTkFrame(popup, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(main_frame, text=title, 
                                   font=ctk.CTkFont(size=20, weight="bold"),
                                   text_color="white")
        title_label.pack(pady=(10, 20))
        
        chart_frame = ctk.CTkFrame(main_frame, fg_color="#cfcfcf", corner_radius=15)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._render_popup_chart(chart_type, registros, chart_frame)
        
        close_btn = ctk.CTkButton(main_frame, text="✕ Fechar", 
                                  command=popup.destroy,
                                  fg_color="#ef4444", hover_color="#dc2626",
                                  width=120, height=35)
        close_btn.pack(pady=(15, 5))
        
        popup.transient(self.root)
        popup.grab_set()
    
    def _render_popup_chart(self, chart_type, registros, parent):
        """Renderiza o gráfico no popup com tamanho maior"""
        registros_colab = self.build_colaborador_registros(registros)

        if chart_type == "temporal_barras":
            self._popup_temporal_barras(registros, parent)
        elif chart_type == "temporal_linha":
            self._popup_temporal_linha(registros, parent)
        elif chart_type == "colaborador_barras":
            self._popup_entrega_retirada_barras(registros_colab, parent, 2, "Colaborador")
        elif chart_type == "local_barras":
            self._popup_entrega_retirada_barras(registros, parent, 5, "Local")
        elif chart_type == "equipamento_barras":
            self._popup_entrega_retirada_barras(registros, parent, 3, "Equipamento")
        elif chart_type == "entregas_vs_retiradas":
            self._popup_entregas_vs_retiradas(registros, parent)
        elif chart_type == "entregas_colaborador":
            self._popup_pie_tipo(registros_colab, parent, 2, "ENTREGA", "Entregas por Colaborador")
        elif chart_type == "retiradas_colaborador":
            self._popup_pie_tipo(registros_colab, parent, 2, "RETIRADA", "Retiradas por Colaborador")
        elif chart_type == "entregas_local":
            self._popup_pie_tipo(registros, parent, 5, "ENTREGA", "Entregas por Local")
        elif chart_type == "retiradas_local":
            self._popup_pie_tipo(registros, parent, 5, "RETIRADA", "Retiradas por Local")
        elif chart_type == "entregas_equipamento":
            self._popup_pie_tipo(registros, parent, 3, "ENTREGA", "Entregas por Equipamento")
        elif chart_type == "retiradas_equipamento":
            self._popup_pie_tipo(registros, parent, 3, "RETIRADA", "Retiradas por Equipamento")
        elif chart_type == "top5_colaboradores":
            self._popup_top5(registros_colab, parent, 2, "Top 5 Colaboradores")
        elif chart_type == "top5_locais":
            self._popup_top5(registros, parent, 5, "Top 5 Locais")
        elif chart_type == "top5_equipamentos":
            self._popup_top5(registros, parent, 3, "Top 5 Equipamentos")

    def _popup_temporal_barras(self, registros, parent):
        """Popup - Evolução Temporal de Retiradas e Entregas (barras)"""
        entregas, retiradas = self.get_entregas_retiradas(registros)
        entregas_por_data = self.count_by_field(entregas, 1)
        retiradas_por_data = self.count_by_field(retiradas, 1)
        todas_datas = sorted(set(entregas_por_data.keys()) | set(retiradas_por_data.keys()),
                            key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        if not todas_datas:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        if self.show_year_accumulated:
            ent_mes, ret_mes = {}, {}
            for d in todas_datas:
                m = d[3:]
                ent_mes[m] = ent_mes.get(m, 0) + entregas_por_data.get(d, 0)
                ret_mes[m] = ret_mes.get(m, 0) + retiradas_por_data.get(d, 0)
            eixo_x = sorted(set(ent_mes) | set(ret_mes), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores_entregas  = [ent_mes.get(m, 0) for m in eixo_x]
            valores_retiradas = [ret_mes.get(m, 0) for m in eixo_x]
        else:
            eixo_x = todas_datas
            valores_entregas  = [entregas_por_data.get(d, 0)  for d in eixo_x]
            valores_retiradas = [retiradas_por_data.get(d, 0) for d in eixo_x]
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        x = np.arange(len(eixo_x))
        width = 0.35
        bars1 = ax.bar(x - width/2, valores_entregas,  width, label='Entregas',  color=self.COR_ENTREGA,  edgecolor='white', linewidth=1.5)
        bars2 = ax.bar(x + width/2, valores_retiradas, width, label='Retiradas', color=self.COR_RETIRADA, edgecolor='white', linewidth=1.5)
        max_val = max(max(valores_entregas) if valores_entregas else 0, max(valores_retiradas) if valores_retiradas else 0)
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 1)
        for bar, val in zip(bars1, valores_entregas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02, str(val), ha='center', va='bottom', fontsize=10, fontweight='bold')
        for bar, val in zip(bars2, valores_retiradas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02, str(val), ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Quantidade', fontsize=12)
        ax.legend(loc='upper right')
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self.add_hover_to_grouped_bars(fig, ax, bars1, bars2, eixo_x, valores_entregas, valores_retiradas)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_temporal_linha(self, registros, parent):
        """Popup - Evolução Temporal de Movimentações (linha)"""
        datas_dict = self.count_by_field(registros, 1)
        if not datas_dict:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        datas_ordenadas = sorted(datas_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        if self.show_year_accumulated:
            meses_dict = {}
            for d in datas_ordenadas:
                m = d[3:]
                meses_dict[m] = meses_dict.get(m, 0) + datas_dict[d]
            eixo_x = sorted(meses_dict.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores = [meses_dict[m] for m in eixo_x]
            ylabel, hover_label = 'Visitas por Mês', "Visitas do Mês"
        else:
            eixo_x = datas_ordenadas
            valores = [datas_dict[d] for d in datas_ordenadas]
            ylabel, hover_label = 'Movimentações', "Total"
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        max_y = max(valores) if valores else 1
        line, = ax.plot(range(len(eixo_x)), valores, color="#fe0401", linewidth=3,
                marker='o', markersize=10, markerfacecolor="#fe0401")
        ax.fill_between(range(len(eixo_x)), valores, alpha=0.3, color="#fe0401")
        for i, (x_pos, y) in enumerate(zip(range(len(eixo_x)), valores)):
            ax.text(x_pos, y + max_y*0.03, str(y), ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax.set_ylim(0, max_y * 1.15)
        ax.set_xticks(range(len(eixo_x)))
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self.add_hover_to_line(fig, ax, line, eixo_x, valores, value_label=hover_label)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_entrega_retirada_barras(self, registros, parent, field_index, field_name):
        """Popup - Barras agrupadas Entrega/Retirada por campo"""
        entregas, retiradas = self.get_entregas_retiradas(registros)
        
        entregas_dict = self.count_by_field(entregas, field_index)
        retiradas_dict = self.count_by_field(retiradas, field_index)
        
        todos_items = sorted(set(entregas_dict.keys()) | set(retiradas_dict.keys()))
        
        if not todos_items:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        valores_entregas = [entregas_dict.get(item, 0) for item in todos_items]
        valores_retiradas = [retiradas_dict.get(item, 0) for item in todos_items]
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        x = np.arange(len(todos_items))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, valores_entregas, width, label='Entregas', 
                      color=self.COR_ENTREGA, edgecolor='white', linewidth=1.5)
        bars2 = ax.bar(x + width/2, valores_retiradas, width, label='Retiradas', 
                      color=self.COR_RETIRADA, edgecolor='white', linewidth=1.5)
        
        max_val = max(max(valores_entregas) if valores_entregas else 0, 
                     max(valores_retiradas) if valores_retiradas else 0)
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 1)
        
        for bar, val in zip(bars1, valores_entregas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02,
                       str(val), ha='center', va='bottom', fontsize=10, fontweight='bold')
        for bar, val in zip(bars2, valores_retiradas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02,
                       str(val), ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(todos_items, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Quantidade', fontsize=12)
        ax.legend(loc='upper right')
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.add_hover_to_grouped_bars(fig, ax, bars1, bars2, todos_items, valores_entregas, valores_retiradas)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_entregas_vs_retiradas(self, registros, parent):
        """Popup - Pizza Entregas vs Retiradas"""
        entregas, retiradas = self.get_entregas_retiradas(registros)
        
        valores = [len(entregas), len(retiradas)]
        labels = ['Entregas', 'Retiradas']
        colors = [self.COR_ENTREGA, self.COR_RETIRADA]
        
        if sum(valores) == 0:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.75,
                                           wedgeprops=dict(edgecolor='white', linewidth=3))
        
        for text in texts:
            text.set_fontsize(14)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(14)
            autotext.set_fontweight('bold')
        
        self.add_hover_to_pie(fig, ax, wedges, labels, valores)
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_pie_tipo(self, registros, parent, field_index, tipo, titulo):
        """Popup - Pizza de um tipo específico por campo"""
        filtrados = [r for r in registros if r[7] == tipo]
        data_dict = self.count_by_field(filtrados, field_index)
        
        if not data_dict:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [d[0] for d in sorted_data]
        valores = [d[1] for d in sorted_data]
        
        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        if tipo == "ENTREGA":
            colors = []
            for i in range(n_colors):
                ratio = i / max(n_colors - 1, 1)
                r = (220 + (254 - 220) * ratio) / 255
                g = (38 + (202 - 38) * ratio) / 255
                b = (38 + (202 - 38) * ratio) / 255
                colors.append((r, g, b))
        else:
            colors = []
            for i in range(n_colors):
                ratio = i / max(n_colors - 1, 1)
                r = (234 + (254 - 234) * ratio) / 255
                g = (179 + (240 - 179) * ratio) / 255
                b = (8 + (128 - 8) * ratio) / 255
                colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.8,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        self.add_hover_to_pie(fig, ax, wedges, labels, valores)
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_top5(self, registros, parent, field_index, titulo):
        """Popup - Top 5 (barras horizontais)"""
        data_dict = self.count_by_field(registros, field_index)
        top5 = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top5:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        nomes = [t[0] for t in top5]
        valores = [t[1] for t in top5]
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (220 + (234 - 220) * ratio) / 255
            g = (38 + (179 - 38) * ratio) / 255
            b = (38 + (8 - 38) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(nomes)), valores, color=colors, height=0.6, 
                      edgecolor='white', linewidth=1.5)
        
        max_val = max(valores)
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val*0.02, bar.get_y() + bar.get_height()/2,
                    str(valor), ha='left', va='center', fontsize=12, fontweight='bold')
        
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes, fontsize=12)
        ax.set_xlim(0, max_val * 1.2)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        ax.invert_yaxis()
        
        self.add_hover_to_bars(fig, ax, bars, nomes, valores, "Total")
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    # ==================== UPDATE STATISTICS ====================

    def update_statistics(self):
        """Atualiza as estatísticas com design moderno"""
        self.cleanup_figures()
        
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        try:
            mes = self.stats_filter_vars['mes'].get()
            ano = self.stats_filter_vars['ano'].get()
            data_especifica = self.stats_filter_vars['data'].get()
            
            query = """
                SELECT id, data, colaborador, equipamento, cliente, local, horario, tipo, matricula, colaborador_matricula
                FROM registros WHERE 1=1
            """
            params = []
            
            if self.show_year_accumulated:
                query += " AND substr(data, 7, 4) = ?"
                params.append(ano if ano else str(datetime.now().year))
            elif data_especifica and self.validate_date(data_especifica):
                query += " AND data = ?"
                params.append(data_especifica)
            elif mes and ano:
                query += " AND substr(data, 4, 2) = ? AND substr(data, 7, 4) = ?"
                params.extend([mes, ano])
            
            self.cursor.execute(query, params)
            registros = self.cursor.fetchall()
            
            if not registros:
                ctk.CTkLabel(self.stats_container, 
                            text="🔭 Nenhum registro encontrado para o período selecionado",
                            font=ctk.CTkFont(size=16)).pack(pady=100)
                return
            
            self.current_registros = registros
            self.current_registros_colab = self.build_colaborador_registros(registros)
            registros_colab = self.current_registros_colab
            
            # KPIs MODERNOS NO TOPO
            kpis_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            kpis_frame.pack(fill="x", pady=(0, 25))
            self.create_modern_kpis(kpis_frame, registros)
            
            # LINHA 1: Evolução Temporal
            row1_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row1_frame.pack(fill="x", pady=10)
            
            temporal_barras_frame = ctk.CTkFrame(row1_frame, corner_radius=15)
            temporal_barras_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_temporal_barras_chart(registros, temporal_barras_frame)
            
            temporal_linha_frame = ctk.CTkFrame(row1_frame, corner_radius=15)
            temporal_linha_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_temporal_linha_chart(registros, temporal_linha_frame)
            
            # LINHA 2: Por Colaborador + Pizza
            row2_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row2_frame.pack(fill="x", pady=10)
            
            colaborador_frame = ctk.CTkFrame(row2_frame, corner_radius=15)
            colaborador_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_entrega_retirada_barras_chart(registros_colab, colaborador_frame, 2, "👷 Entregas/Retiradas por Colaborador", "colaborador_barras")
            
            pizza_frame = ctk.CTkFrame(row2_frame, corner_radius=15)
            pizza_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_entregas_vs_retiradas_chart(registros, pizza_frame)
            
            # LINHA 3: Por Local
            row3_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row3_frame.pack(fill="x", pady=10)
            
            local_frame = ctk.CTkFrame(row3_frame, corner_radius=15)
            local_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_entrega_retirada_barras_chart(registros, local_frame, 5, "📍 Entregas/Retiradas por Local", "local_barras")
            
            # LINHA 4: Por Equipamento
            row4_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row4_frame.pack(fill="x", pady=10)
            
            equipamento_frame = ctk.CTkFrame(row4_frame, corner_radius=15)
            equipamento_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_entrega_retirada_barras_chart(registros, equipamento_frame, 3, "📦 Entregas/Retiradas por Equipamento", "equipamento_barras")
            
            # LINHA 5: Pizzas Colaborador
            row5_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row5_frame.pack(fill="x", pady=10)
            
            entregas_colab_frame = ctk.CTkFrame(row5_frame, corner_radius=15)
            entregas_colab_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_pie_tipo_chart(registros_colab, entregas_colab_frame, 2, "ENTREGA", "👷 Entregas por Colaborador", "entregas_colaborador")
            
            retiradas_colab_frame = ctk.CTkFrame(row5_frame, corner_radius=15)
            retiradas_colab_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_pie_tipo_chart(registros_colab, retiradas_colab_frame, 2, "RETIRADA", "👷 Retiradas por Colaborador", "retiradas_colaborador")
            
            # LINHA 6: Pizzas Local
            row6_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row6_frame.pack(fill="x", pady=10)
            
            entregas_local_frame = ctk.CTkFrame(row6_frame, corner_radius=15)
            entregas_local_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_pie_tipo_chart(registros, entregas_local_frame, 5, "ENTREGA", "📍 Entregas por Local", "entregas_local")
            
            retiradas_local_frame = ctk.CTkFrame(row6_frame, corner_radius=15)
            retiradas_local_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_pie_tipo_chart(registros, retiradas_local_frame, 5, "RETIRADA", "📍 Retiradas por Local", "retiradas_local")
            
            # LINHA 7: Pizzas Equipamento
            row7_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row7_frame.pack(fill="x", pady=10)
            
            entregas_equip_frame = ctk.CTkFrame(row7_frame, corner_radius=15)
            entregas_equip_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_pie_tipo_chart(registros, entregas_equip_frame, 3, "ENTREGA", "📦 Entregas por Equipamento", "entregas_equipamento")
            
            retiradas_equip_frame = ctk.CTkFrame(row7_frame, corner_radius=15)
            retiradas_equip_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_pie_tipo_chart(registros, retiradas_equip_frame, 3, "RETIRADA", "📦 Retiradas por Equipamento", "retiradas_equipamento")
            
            # LINHA 8: Top 5
            row8_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row8_frame.pack(fill="x", pady=10)
            
            top5_colab_frame = ctk.CTkFrame(row8_frame, corner_radius=15)
            top5_colab_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_top5_chart(registros_colab, top5_colab_frame, 2, "🏆 Top 5 Colaboradores", "top5_colaboradores")
            
            top5_local_frame = ctk.CTkFrame(row8_frame, corner_radius=15)
            top5_local_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_top5_chart(registros, top5_local_frame, 5, "🏆 Top 5 Locais", "top5_locais")
            
            # LINHA 9: Top 5 Equipamentos + Métricas
            row9_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row9_frame.pack(fill="x", pady=10)
            
            top5_equip_frame = ctk.CTkFrame(row9_frame, corner_radius=15)
            top5_equip_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_top5_chart(registros, top5_equip_frame, 3, "🏆 Top 5 Equipamentos", "top5_equipamentos")

            # Métricas de Performance
            row10_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row10_frame.pack(fill="x", pady=10)
            self.create_progress_charts(registros_colab, row10_frame)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar estatísticas: {str(e)}")

    # ==================== GRÁFICOS EMBUTIDOS ====================

    def create_temporal_barras_chart(self, registros, parent):
        """Gráfico de barras - Evolução Temporal"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401", cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        chart_title = "📊 Entregas e Retiradas por Mês (Ano)" if self.show_year_accumulated else "📊 Evolução Temporal de Retiradas e Entregas"
        title = ctk.CTkLabel(frame, text=chart_title, font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        entregas, retiradas = self.get_entregas_retiradas(registros)
        entregas_por_data = self.count_by_field(entregas, 1)
        retiradas_por_data = self.count_by_field(retiradas, 1)
        todas_datas = sorted(set(entregas_por_data.keys()) | set(retiradas_por_data.keys()),
                            key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        if not todas_datas:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        if self.show_year_accumulated:
            ent_mes, ret_mes = {}, {}
            for d in todas_datas:
                m = d[3:]
                ent_mes[m] = ent_mes.get(m, 0) + entregas_por_data.get(d, 0)
                ret_mes[m] = ret_mes.get(m, 0) + retiradas_por_data.get(d, 0)
            eixo_x = sorted(set(ent_mes) | set(ret_mes), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores_entregas  = [ent_mes.get(m, 0) for m in eixo_x]
            valores_retiradas = [ret_mes.get(m, 0) for m in eixo_x]
        else:
            eixo_x = todas_datas
            valores_entregas  = [entregas_por_data.get(d, 0)  for d in eixo_x]
            valores_retiradas = [retiradas_por_data.get(d, 0) for d in eixo_x]
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        x = np.arange(len(eixo_x))
        width = 0.35
        bars1 = ax.bar(x - width/2, valores_entregas,  width, label='Entregas',  color=self.COR_ENTREGA,  edgecolor='white', linewidth=1)
        bars2 = ax.bar(x + width/2, valores_retiradas, width, label='Retiradas', color=self.COR_RETIRADA, edgecolor='white', linewidth=1)
        max_val = max(max(valores_entregas) if valores_entregas else 0, max(valores_retiradas) if valores_retiradas else 0)
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 1)
        ax.set_xticks(x)
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('Qtd', fontsize=9)
        ax.legend(loc='upper right', fontsize=8)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self.add_hover_to_grouped_bars(fig, ax, bars1, bars2, eixo_x, valores_entregas, valores_retiradas)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("temporal_barras", registros, chart_title))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("temporal_barras", registros, chart_title))

    def create_temporal_linha_chart(self, registros, parent):
        """Gráfico de linha - Evolução Temporal"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401", cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        chart_title = "📈 Evolução de Visitas por Mês (Ano)" if self.show_year_accumulated else "📈 Evolução Temporal de Movimentações"
        title = ctk.CTkLabel(frame, text=chart_title, font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        datas_dict = self.count_by_field(registros, 1)
        if not datas_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        datas_ordenadas = sorted(datas_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        if self.show_year_accumulated:
            meses_dict = {}
            for d in datas_ordenadas:
                m = d[3:]
                meses_dict[m] = meses_dict.get(m, 0) + datas_dict[d]
            eixo_x = sorted(meses_dict.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores = [meses_dict[m] for m in eixo_x]
            ylabel, hover_label = 'Visitas por Mês', "Visitas do Mês"
        else:
            eixo_x = datas_ordenadas
            valores = [datas_dict[d] for d in datas_ordenadas]
            ylabel, hover_label = 'Total', "Total"
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        max_y = max(valores) if valores else 1
        line, = ax.plot(range(len(eixo_x)), valores, color="#fe0401", linewidth=2,
                marker='o', markersize=6, markerfacecolor="#fe0401")
        ax.fill_between(range(len(eixo_x)), valores, alpha=0.3, color="#fe0401")
        for i, (x_pos, y) in enumerate(zip(range(len(eixo_x)), valores)):
            ax.text(x_pos, y + max_y*0.03, str(y), ha='center', va='bottom', fontsize=8, fontweight='bold')
        ax.set_ylim(0, max_y * 1.15)
        ax.set_xticks(range(len(eixo_x)))
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self.add_hover_to_line(fig, ax, line, eixo_x, valores, value_label=hover_label)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("temporal_linha", registros, chart_title))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("temporal_linha", registros, chart_title))

    def create_entrega_retirada_barras_chart(self, registros, parent, field_index, titulo, popup_type):
        """Gráfico de barras agrupadas"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401", cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        entregas, retiradas = self.get_entregas_retiradas(registros)
        entregas_dict = self.count_by_field(entregas, field_index)
        retiradas_dict = self.count_by_field(retiradas, field_index)
        
        todos_items = sorted(set(entregas_dict.keys()) | set(retiradas_dict.keys()))
        
        if not todos_items:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        valores_entregas = [entregas_dict.get(item, 0) for item in todos_items]
        valores_retiradas = [retiradas_dict.get(item, 0) for item in todos_items]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        x = np.arange(len(todos_items))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, valores_entregas, width, label='Entregas', 
                      color=self.COR_ENTREGA, edgecolor='white', linewidth=1)
        bars2 = ax.bar(x + width/2, valores_retiradas, width, label='Retiradas', 
                      color=self.COR_RETIRADA, edgecolor='white', linewidth=1)
        
        max_val = max(max(valores_entregas) if valores_entregas else 0, 
                     max(valores_retiradas) if valores_retiradas else 0)
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 1)
        
        ax.set_xticks(x)
        ax.set_xticklabels(todos_items, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('Qtd', fontsize=9)
        ax.legend(loc='upper right', fontsize=8)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.add_hover_to_grouped_bars(fig, ax, bars1, bars2, todos_items, valores_entregas, valores_retiradas)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        frame.bind("<Button-1>", lambda e: self.open_chart_popup(popup_type, registros, titulo))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup(popup_type, registros, titulo))

    def create_entregas_vs_retiradas_chart(self, registros, parent):
        """Gráfico de pizza - Entregas vs Retiradas"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401", cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="⚖️ Entregas vs Retiradas", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        entregas, retiradas = self.get_entregas_retiradas(registros)
        valores = [len(entregas), len(retiradas)]
        labels = ['Entregas', 'Retiradas']
        colors = [self.COR_ENTREGA, self.COR_RETIRADA]
        
        if sum(valores) == 0:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.75,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(9)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        self.add_hover_to_pie(fig, ax, wedges, labels, valores)
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("entregas_vs_retiradas", registros, "⚖️ Entregas vs Retiradas"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("entregas_vs_retiradas", registros, "⚖️ Entregas vs Retiradas"))

    def create_pie_tipo_chart(self, registros, parent, field_index, tipo, titulo, popup_type):
        """Gráfico de pizza por tipo"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, 
                            border_color=self.COR_ENTREGA if tipo == "ENTREGA" else self.COR_RETIRADA,
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        filtrados = [r for r in registros if r[7] == tipo]
        data_dict = self.count_by_field(filtrados, field_index)
        
        if not data_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        MAX_PIE = 8
        total_itens = len(data_dict)
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:MAX_PIE]
        labels = [d[0] for d in sorted_data]
        valores = [d[1] for d in sorted_data]
        
        if total_itens > MAX_PIE:
            ctk.CTkLabel(frame,
                         text=f"(top {MAX_PIE} de {total_itens} — clique para ver todos)",
                         font=ctk.CTkFont(size=9), text_color="#6b7280").pack()
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        if tipo == "ENTREGA":
            colors = []
            for i in range(n_colors):
                ratio = i / max(n_colors - 1, 1)
                r = (220 + (254 - 220) * ratio) / 255
                g = (38 + (202 - 38) * ratio) / 255
                b = (38 + (202 - 38) * ratio) / 255
                colors.append((r, g, b))
        else:
            colors = []
            for i in range(n_colors):
                ratio = i / max(n_colors - 1, 1)
                r = (234 + (254 - 234) * ratio) / 255
                g = (179 + (240 - 179) * ratio) / 255
                b = (8 + (128 - 8) * ratio) / 255
                colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.8,
                                           wedgeprops=dict(edgecolor='white', linewidth=1.5))
        
        for text in texts:
            text.set_fontsize(7)
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(8)
            autotext.set_fontweight('bold')
        
        self.add_hover_to_pie(fig, ax, wedges, labels, valores)
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        frame.bind("<Button-1>", lambda e: self.open_chart_popup(popup_type, registros, titulo))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup(popup_type, registros, titulo))

    def create_top5_chart(self, registros, parent, field_index, titulo, popup_type):
        """Gráfico de barras horizontais - Top 5"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401", cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        data_dict = self.count_by_field(registros, field_index)
        top5 = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top5:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        nomes = [t[0] for t in top5]
        valores = [t[1] for t in top5]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (220 + (234 - 220) * ratio) / 255
            g = (38 + (179 - 38) * ratio) / 255
            b = (38 + (8 - 38) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(nomes)), valores, color=colors, height=0.6, 
                      edgecolor='white', linewidth=1.5)
        
        max_val = max(valores) if valores else 1
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val*0.02, bar.get_y() + bar.get_height()/2,
                    str(valor), ha='left', va='center', fontsize=9, fontweight='bold')
        
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes, fontsize=8)
        ax.set_xlim(0, max_val * 1.2)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor("#cfcfcf")
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        ax.invert_yaxis()
        
        self.add_hover_to_bars(fig, ax, bars, nomes, valores, "Total")
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        frame.bind("<Button-1>", lambda e: self.open_chart_popup(popup_type, registros, titulo))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup(popup_type, registros, titulo))

    # ==================== KPIs E MÉTRICAS ====================

    def create_modern_kpis(self, parent, registros):
        """Cria KPIs modernos"""
        total_movimentacoes = len(registros)
        entregas, retiradas = self.get_entregas_retiradas(registros)
        total_entregas = len(entregas)
        total_retiradas = len(retiradas)
        colaboradores_unicos = len(set([r[2] for r in registros if r[2]]))
        locais_unicos = len(set([r[5] for r in registros if r[5]]))
        equipamentos_unicos = len(set([r[3] for r in registros if r[3]]))
        
        kpis_data = [
            ("📊", str(total_movimentacoes), "Total de Movimentações", "#3b82f6"),
            ("🔴", str(total_entregas), "Total de Entregas", self.COR_ENTREGA),
            ("🟡", str(total_retiradas), "Total de Retiradas", self.COR_RETIRADA),
            ("👷", str(colaboradores_unicos), "Colaboradores Ativos", "#10b981"),
            ("📍", str(locais_unicos), "Locais Diferentes", "#8b5cf6"),
            ("📦", str(equipamentos_unicos), "Equipamentos Movimentados", "#f59e0b")
        ]
        
        for icon, value, tooltip_text, color in kpis_data:
            kpi_card = ctk.CTkFrame(parent, fg_color=color, corner_radius=15, 
                                   width=150, height=100)
            kpi_card.pack(side="left", fill="both", expand=True, padx=5)
            kpi_card.pack_propagate(False)
            
            icon_label = ctk.CTkLabel(kpi_card, text=icon, font=ctk.CTkFont(size=28))
            icon_label.pack(pady=(12, 3))
            
            value_label = ctk.CTkLabel(kpi_card, text=value, 
                                      font=ctk.CTkFont(size=32, weight="bold"),
                                      text_color="white")
            value_label.pack(pady=2)
            
            Tooltip(kpi_card, tooltip_text)

    def create_progress_charts(self, registros, parent):
        """Cria gráficos de progresso"""
        frame = ctk.CTkFrame(parent, corner_radius=15)
        frame.pack(fill="x", padx=8)
        
        title = ctk.CTkLabel(frame, text="📊 Métricas de Performance",
                        font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(20, 15))
        
        progress_container = ctk.CTkFrame(frame, fg_color="transparent")
        progress_container.pack(fill="x", padx=30, pady=10)
        
        total = len(registros)
        entregas, retiradas = self.get_entregas_retiradas(registros)
        
        colaboradores_dict = self.count_by_field(registros, 2)
        todos_colaboradores = sorted(colaboradores_dict.items(), key=lambda x: x[1], reverse=True)
        
        def get_color_gradient(index, total_count):
            if total_count == 1:
                return "#dc2626"
            ratio = index / (total_count - 1)
            r1, g1, b1 = 0xdc, 0x26, 0x26
            r2, g2, b2 = 0xea, 0xb3, 0x08
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            return f"#{r:02x}{g:02x}{b:02x}"
        
        progress_data = [
            ("Taxa de Entregas", len(entregas), total, self.COR_ENTREGA),
            ("Taxa de Retiradas", len(retiradas), total, self.COR_RETIRADA),
        ]
        
        for idx, (nome, qtd) in enumerate(todos_colaboradores):
            cor = get_color_gradient(idx, len(todos_colaboradores))
            progress_data.append((f"Colaborador: {nome}", qtd, total, cor))
        
        for nome, qtd, total_val, cor in progress_data:
            bar_frame = ctk.CTkFrame(progress_container, fg_color="transparent")
            bar_frame.pack(fill="x", pady=10)
            
            info_frame = ctk.CTkFrame(bar_frame, fg_color="transparent")
            info_frame.pack(fill="x")
            
            ctk.CTkLabel(info_frame, text=nome, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            pct = int(qtd/total_val*100) if total_val > 0 else 0
            ctk.CTkLabel(info_frame, text=f"{qtd}/{total_val} ({pct}%)", 
                        font=ctk.CTkFont(size=11)).pack(side="right")
            
            progress_bg = ctk.CTkFrame(bar_frame, height=25, fg_color="#e5e5e5")
            progress_bg.pack(fill="x", pady=(5, 0))
            
            if total_val > 0:
                progress_fill = ctk.CTkFrame(progress_bg, height=25, fg_color=cor)
                progress_fill.place(relx=0, rely=0, relheight=1, relwidth=qtd/total_val)
        
        ctk.CTkLabel(frame, text="").pack(pady=10)

    # ==================== EXPORTAÇÕES ====================

    def export_stats_csv(self):
        """Exporta estatísticas para CSV com opção de escolher formato (Excel ou LibreOffice/WPS)"""
        try:
            if not self.current_registros:
                messagebox.showwarning("Aviso", "Não há dados para exportar!")
                return
            
            # Criar janela de escolha
            choice_window = ctk.CTkToplevel(self.root)
            choice_window.title("Escolher Formato")
            choice_window.geometry("400x200")
            choice_window.grab_set()
            choice_window.transient(self.root)
            
            # Centralizar
            choice_window.update_idletasks()
            x = (choice_window.winfo_screenwidth() // 2) - 200
            y = (choice_window.winfo_screenheight() // 2) - 100
            choice_window.geometry(f"400x200+{x}+{y}")
            
            # Variável para armazenar escolha
            self.csv_format_choice = None
            
            # Frame principal
            main_frame = ctk.CTkFrame(choice_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # Título
            title = ctk.CTkLabel(main_frame, text="📊 Escolha o formato do CSV",
                                font=ctk.CTkFont(size=16, weight="bold"))
            title.pack(pady=(0, 20))
            
            # Info
            info = ctk.CTkLabel(main_frame, 
                               text="Selecione o programa que você usa para abrir planilhas:",
                               font=ctk.CTkFont(size=12),
                               text_color="#6b7280")
            info.pack(pady=(0, 15))
            
            # Frame de botões
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=10)
            
            def choose_excel():
                self.csv_format_choice = 'excel'
                choice_window.destroy()
            
            def choose_libre():
                self.csv_format_choice = 'libre'
                choice_window.destroy()
            
            # Botão Excel / Libre
            excel_btn = ctk.CTkButton(btn_frame, text="📗 Excel / Libre",
                                     command=choose_excel,
                                     fg_color="#217346", hover_color="#1e5e3a",
                                     width=150, height=45,
                                     font=ctk.CTkFont(size=14, weight="bold"))
            excel_btn.pack(side="left", padx=10, expand=True)
            
            # Botão WPS
            libre_btn = ctk.CTkButton(btn_frame, text="📘 WPS",
                                     command=choose_libre,
                                     fg_color="#18a303", hover_color="#138a02",
                                     width=150, height=45,
                                     font=ctk.CTkFont(size=14, weight="bold"))
            libre_btn.pack(side="left", padx=10, expand=True)
            
            # Aguardar escolha
            self.root.wait_window(choice_window)
            
            # Verificar se usuário fez uma escolha
            if self.csv_format_choice is None:
                return
            
            # Mesmo formato para ambas as opções
            encoding = 'utf-8-sig'  # Com BOM
            delimiter = ';'
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"{self.get_export_filename_prefix()}.csv"
            )
            
            if not filename:
                return
            
            import csv
            
            with open(filename, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                # Título
                writer.writerow(['📊 Estatísticas - Sistema de Controle de Equipamentos'])
                
                # Período
                mes = self.stats_filter_vars['mes'].get()
                ano = self.stats_filter_vars['ano'].get()
                data = self.stats_filter_vars['data'].get()
                
                if self.show_year_accumulated:
                    periodo = f"Período: {ano if ano else str(datetime.now().year)}"
                elif data:
                    periodo = f"Data: {data}"
                elif mes and ano:
                    meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    periodo = f"Período: {meses[int(mes)]}/{ano}"
                else:
                    periodo = "Todos os registros"
                
                writer.writerow([periodo])
                writer.writerow([f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"])
                writer.writerow([])
                
                # Cabeçalho
                writer.writerow(['ID', 'Data', 'Colaborador', 'Equipamento', 'Cliente', 
                               'Local', 'Horário', 'Tipo'])
                
                # Registros - garantir que todos os campos sejam strings
                for r in self.current_registros:
                    row = [
                        str(r[0]) if r[0] is not None else '',  # ID
                        str(r[1]) if r[1] is not None else '',  # Data
                        str(r[2]) if r[2] is not None else '',  # Colaborador
                        str(r[3]) if r[3] is not None else '',  # Equipamento
                        str(r[4]) if len(r) > 4 and r[4] is not None else '',  # Cliente
                        str(r[5]) if len(r) > 5 and r[5] is not None else '',  # Local
                        str(r[6]) if len(r) > 6 and r[6] is not None else '',  # Horário
                        str(r[7]) if len(r) > 7 and r[7] is not None else ''   # Tipo
                    ]
                    writer.writerow(row)
                
                # Linha em branco
                writer.writerow([])
                
                # Resumo com emojis
                writer.writerow(['=== 📈 RESUMO ==='])
                
                entregas, retiradas = self.get_entregas_retiradas(self.current_registros)
                colaboradores_unicos = len(set([r[2] for r in self.current_registros if r[2]]))
                locais_unicos = len(set([r[5] for r in self.current_registros if len(r) > 5 and r[5]]))
                equipamentos_unicos = len(set([r[3] for r in self.current_registros if r[3]]))
                
                writer.writerow(['📊 Total de Movimentações', len(self.current_registros)])
                writer.writerow(['🔴 Total de Entregas', len(entregas)])
                writer.writerow(['🟡 Total de Retiradas', len(retiradas)])
                writer.writerow(['👷 Colaboradores Ativos', colaboradores_unicos])
                writer.writerow(['📍 Locais Diferentes', locais_unicos])
                writer.writerow(['📦 Equipamentos Movimentados', equipamentos_unicos])
            
            formato_nome = "Excel / Libre" if self.csv_format_choice == 'excel' else "WPS"
            messagebox.showinfo("Sucesso", f"Estatísticas exportadas para {formato_nome}!\n\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")

    def export_stats_pdf(self):
        """Exporta estatísticas para PDF com métricas estilizadas e gráficos"""
        try:
            if not self.current_registros:
                messagebox.showwarning("Aviso", "Não há dados para exportar!")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"{self.get_export_filename_prefix()}.pdf"
            )
            
            if not filename:
                return
            
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER
            
            progress = ProgressDialog(self.root, "Gerando PDF...", total_steps=10)
            
            try:
                progress.update_progress(1, "Preparando documento...")
                
                doc = SimpleDocTemplate(filename, pagesize=landscape(A4),
                                      leftMargin=1*cm, rightMargin=1*cm,
                                      topMargin=1*cm, bottomMargin=1*cm)
                
                elements = []
                styles = getSampleStyleSheet()
                
                # ==================== PÁGINA 1: MÉTRICAS ====================
                
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor=colors.HexColor("#1f2937"),
                    spaceAfter=10,
                    alignment=TA_CENTER
                )
                elements.append(Paragraph("📊 Estatísticas - Sistema de Controle de Equipamentos", title_style))
                
                mes = self.stats_filter_vars['mes'].get()
                ano = self.stats_filter_vars['ano'].get()
                data = self.stats_filter_vars['data'].get()
                
                if self.show_year_accumulated:
                    periodo = f"Período: {ano if ano else str(datetime.now().year)}"
                elif data:
                    periodo = f"Data: {data}"
                elif mes and ano:
                    meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    periodo = f"Período: {meses[int(mes)]}/{ano}"
                else:
                    periodo = "Todos os registros"
                
                info_style = ParagraphStyle('Info', parent=styles['Normal'],
                                           fontSize=12, alignment=TA_CENTER,
                                           textColor=colors.HexColor("#6b7280"))
                elements.append(Paragraph(periodo, info_style))
                elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", info_style))
                elements.append(Spacer(1, 1*cm))
                
                progress.update_progress(2, "Gerando métricas...")
                
                # Calcular métricas
                entregas, retiradas = self.get_entregas_retiradas(self.current_registros)
                total_movimentacoes = len(self.current_registros)
                total_entregas = len(entregas)
                total_retiradas = len(retiradas)
                colaboradores_unicos = len(set([r[2] for r in self.current_registros if r[2]]))
                locais_unicos = len(set([r[5] for r in self.current_registros if len(r) > 5 and r[5]]))
                equipamentos_unicos = len(set([r[3] for r in self.current_registros if r[3]]))
                
                # Cards de métricas estilizados
                kpis_data = [
                    ("📊", str(total_movimentacoes), "Total de Movimentações", "#3b82f6"),
                    ("🔴", str(total_entregas), "Total de Entregas", "#dc2626"),
                    ("🟡", str(total_retiradas), "Total de Retiradas", "#eab308"),
                    ("👷", str(colaboradores_unicos), "Colaboradores Ativos", "#10b981"),
                    ("📍", str(locais_unicos), "Locais Diferentes", "#8b5cf6"),
                    ("📦", str(equipamentos_unicos), "Equipamentos Movimentados", "#f59e0b")
                ]
                
                # Criar tabela de cards (2 linhas x 3 colunas)
                card_data = []
                row1 = []
                row2 = []
                
                for i, (icon, value, label, color) in enumerate(kpis_data):
                    # Criar mini-tabela para cada card
                    card_content = [
                        [Paragraph(f'<font size="24">{icon}</font>', ParagraphStyle('Icon', alignment=TA_CENTER))],
                        [Paragraph(f'<font size="28" color="white"><b>{value}</b></font>', ParagraphStyle('Value', alignment=TA_CENTER))],
                        [Paragraph(f'<font size="12" color="white">{label}</font>', ParagraphStyle('Label', alignment=TA_CENTER))]
                    ]
                    card_table = Table(card_content, colWidths=[8*cm], rowHeights=[1.2*cm, 1.5*cm, 0.8*cm])
                    card_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(color)),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                    ]))
                    
                    if i < 3:
                        row1.append(card_table)
                    else:
                        row2.append(card_table)
                
                # Tabela principal com os cards
                main_cards = Table([row1, row2], colWidths=[9*cm, 9*cm, 9*cm], rowHeights=[4*cm, 4*cm])
                main_cards.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                
                elements.append(main_cards)
                elements.append(PageBreak())
                
                # ==================== PÁGINAS DE GRÁFICOS ====================
                
                temp_dir = tempfile.mkdtemp()
                
                # Estilo para títulos de gráficos
                chart_title_style = ParagraphStyle(
                    'ChartTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=colors.HexColor("#1f2937"),
                    spaceAfter=20,
                    alignment=TA_CENTER
                )
                
                progress.update_progress(3, "Gerando gráficos de evolução temporal...")
                
                # Gráfico 1: Evolução Temporal (Barras)
                chart1_path = os.path.join(temp_dir, "chart1.png")
                self._save_temporal_barras_chart(chart1_path)
                if os.path.exists(chart1_path):
                    elements.append(Paragraph("📈 Evolução Temporal de Retiradas e Entregas", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart1_path, width=26*cm, height=12*cm))
                    elements.append(PageBreak())
                
                # Gráfico 2: Evolução Temporal (Linha)
                chart2_path = os.path.join(temp_dir, "chart2.png")
                self._save_temporal_linha_chart(chart2_path)
                if os.path.exists(chart2_path):
                    elements.append(Paragraph("📉 Evolução Temporal de Movimentações", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart2_path, width=26*cm, height=12*cm))
                    elements.append(PageBreak())
                
                progress.update_progress(4, "Gerando gráfico Entregas vs Retiradas...")
                
                # Gráfico 3: Pizza Entregas vs Retiradas
                chart3_path = os.path.join(temp_dir, "chart3.png")
                self._save_entregas_vs_retiradas_chart(chart3_path)
                if os.path.exists(chart3_path):
                    elements.append(Paragraph("🥧 Entregas vs Retiradas", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart3_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                progress.update_progress(5, "Gerando gráficos de pizza por colaborador...")
                
                # Gráfico 4: Entregas por Colaborador (Pizza)
                chart4_path = os.path.join(temp_dir, "chart4.png")
                self._save_pie_tipo_chart(chart4_path, 2, "ENTREGA", "Entregas por Colaborador")
                if os.path.exists(chart4_path):
                    elements.append(Paragraph("🔴 Entregas por Colaborador", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart4_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                # Gráfico 5: Retiradas por Colaborador (Pizza)
                chart5_path = os.path.join(temp_dir, "chart5.png")
                self._save_pie_tipo_chart(chart5_path, 2, "RETIRADA", "Retiradas por Colaborador")
                if os.path.exists(chart5_path):
                    elements.append(Paragraph("🟡 Retiradas por Colaborador", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart5_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                progress.update_progress(6, "Gerando gráficos de pizza por local...")
                
                # Gráfico 6: Entregas por Local (Pizza)
                chart6_path = os.path.join(temp_dir, "chart6.png")
                self._save_pie_tipo_chart(chart6_path, 5, "ENTREGA", "Entregas por Local")
                if os.path.exists(chart6_path):
                    elements.append(Paragraph("🔴 Entregas por Local", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart6_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                # Gráfico 7: Retiradas por Local (Pizza)
                chart7_path = os.path.join(temp_dir, "chart7.png")
                self._save_pie_tipo_chart(chart7_path, 5, "RETIRADA", "Retiradas por Local")
                if os.path.exists(chart7_path):
                    elements.append(Paragraph("🟡 Retiradas por Local", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart7_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                progress.update_progress(7, "Gerando gráficos de pizza por equipamento...")
                
                # Gráfico 8: Entregas por Equipamento (Pizza)
                chart8_path = os.path.join(temp_dir, "chart8.png")
                self._save_pie_tipo_chart(chart8_path, 3, "ENTREGA", "Entregas por Equipamento")
                if os.path.exists(chart8_path):
                    elements.append(Paragraph("🔴 Entregas por Equipamento", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart8_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                # Gráfico 9: Retiradas por Equipamento (Pizza)
                chart9_path = os.path.join(temp_dir, "chart9.png")
                self._save_pie_tipo_chart(chart9_path, 3, "RETIRADA", "Retiradas por Equipamento")
                if os.path.exists(chart9_path):
                    elements.append(Paragraph("🟡 Retiradas por Equipamento", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart9_path, width=18*cm, height=14*cm))
                    elements.append(PageBreak())
                
                progress.update_progress(8, "Gerando gráficos de barras agrupadas...")
                
                # Gráfico 10: Por Colaborador (Barras)
                chart10_path = os.path.join(temp_dir, "chart10.png")
                self._save_entrega_retirada_barras_chart(chart10_path, 2, "Entregas/Retiradas por Colaborador")
                if os.path.exists(chart10_path):
                    elements.append(Paragraph("👷 Entregas/Retiradas por Colaborador", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart10_path, width=26*cm, height=12*cm))
                    elements.append(PageBreak())
                
                # Gráfico 11: Por Local (Barras)
                chart11_path = os.path.join(temp_dir, "chart11.png")
                self._save_entrega_retirada_barras_chart(chart11_path, 5, "Entregas/Retiradas por Local")
                if os.path.exists(chart11_path):
                    elements.append(Paragraph("📍 Entregas/Retiradas por Local", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart11_path, width=26*cm, height=12*cm))
                    elements.append(PageBreak())
                
                # Gráfico 12: Por Equipamento (Barras)
                chart12_path = os.path.join(temp_dir, "chart12.png")
                self._save_entrega_retirada_barras_chart(chart12_path, 3, "Entregas/Retiradas por Equipamento")
                if os.path.exists(chart12_path):
                    elements.append(Paragraph("📦 Entregas/Retiradas por Equipamento", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart12_path, width=26*cm, height=12*cm))
                    elements.append(PageBreak())
                
                progress.update_progress(9, "Gerando Top 5...")

                # Gráfico 13: Top 5 Colaboradores
                chart13_path = os.path.join(temp_dir, "chart13.png")
                self._save_top5_chart(chart13_path, 2, "Top 5 Colaboradores")
                if os.path.exists(chart13_path):
                    elements.append(Paragraph("🏆 Top 5 Colaboradores", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart13_path, width=26*cm, height=13*cm))
                    elements.append(PageBreak())

                # Gráfico 14: Top 5 Locais
                chart14_path = os.path.join(temp_dir, "chart14.png")
                self._save_top5_chart(chart14_path, 5, "Top 5 Locais")
                if os.path.exists(chart14_path):
                    elements.append(Paragraph("🏆 Top 5 Locais", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart14_path, width=26*cm, height=13*cm))
                    elements.append(PageBreak())

                # Gráfico 15: Top 5 Equipamentos
                chart15_path = os.path.join(temp_dir, "chart15.png")
                self._save_top5_chart(chart15_path, 3, "Top 5 Equipamentos")
                if os.path.exists(chart15_path):
                    elements.append(Paragraph("🏆 Top 5 Equipamentos", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart15_path, width=26*cm, height=13*cm))
                    elements.append(PageBreak())

                # Gráfico 16: Métricas de Performance
                chart16_path = os.path.join(temp_dir, "chart16.png")
                self._save_progress_chart(chart16_path)
                if os.path.exists(chart16_path):
                    elements.append(Paragraph("📊 Métricas de Performance", chart_title_style))
                    elements.append(Spacer(1, 0.5*cm))
                    elements.append(Image(chart16_path, width=26*cm, height=14*cm))

                progress.update_progress(10, "Salvando PDF...")
                
                doc.build(elements)
                
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                progress.update_progress(10, "Concluído!")
                progress.close()
                
                messagebox.showinfo("Sucesso", f"PDF exportado com sucesso!\n\n{filename}")
                
            except Exception as e:
                progress.close()
                raise e
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {str(e)}")

    # ==================== FUNÇÕES PARA SALVAR GRÁFICOS ====================

    def _save_progress_chart(self, filepath):
        """Salva gráfico de Métricas de Performance (barras horizontais) para PDF"""
        registros = self.current_registros_colab
        total = len(registros)
        if total == 0:
            return

        entregas, retiradas = self.get_entregas_retiradas(registros)
        colaboradores_dict = self.count_by_field(registros, 2)
        todos_colaboradores = sorted(colaboradores_dict.items(), key=lambda x: x[1], reverse=True)

        def get_color_gradient(index, total_count):
            if total_count == 1:
                return "#dc2626"
            ratio = index / (total_count - 1)
            r = int(0xdc + (0xea - 0xdc) * ratio)
            g = int(0x26 + (0xb3 - 0x26) * ratio)
            b = int(0x26 + (0x08 - 0x26) * ratio)
            return f"#{r:02x}{g:02x}{b:02x}"

        items = [
            ("Taxa de Entregas",  len(entregas),  total, self.COR_ENTREGA),
            ("Taxa de Retiradas", len(retiradas), total, self.COR_RETIRADA),
        ]
        for idx, (nome, qtd) in enumerate(todos_colaboradores):
            items.append((f"Colaborador: {nome}", qtd, total, get_color_gradient(idx, len(todos_colaboradores))))

        n = len(items)
        # Altura fixa por item, mas limitada para caber numa página A4 landscape (max ~9 pol usável)
        row_h = 0.55
        fig_h = min(9.0, max(4.0, n * row_h + 1.5))

        fig, ax = plt.subplots(figsize=(22, fig_h), facecolor='white')

        nomes   = [it[0] for it in items]
        valores = [it[1] for it in items]
        totais  = [it[2] for it in items]
        cores   = [it[3] for it in items]
        pcts    = [(v / t) if t > 0 else 0 for v, t in zip(valores, totais)]
        y_pos   = list(range(n - 1, -1, -1))

        bar_h = min(0.55, (fig_h - 1.5) / max(n, 1) * 0.8)

        # Fundo cinza + barra colorida
        ax.barh(y_pos, [1.0] * n, bar_h, color='#e5e5e5', left=0, zorder=1)
        ax.barh(y_pos, pcts,       bar_h, color=cores,     left=0, zorder=2)

        fs = max(9, min(14, int(120 / max(n, 1))))

        for yp, nome, qtd, tot, pct in zip(y_pos, nomes, valores, totais, pcts):
            ax.text(-0.01, yp, nome,                          va='center', ha='right', fontsize=fs, fontweight='bold')
            ax.text(1.01,  yp, f"{qtd}/{tot}  ({int(pct*100)}%)", va='center', ha='left',  fontsize=fs-1, color='#374151')

        ax.set_xlim(-0.01, 1.40)
        ax.set_ylim(-0.8, n - 0.2)
        ax.axis('off')

        plt.tight_layout(rect=[0.25, 0, 0.82, 1])
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_top5_chart_slice(self, filepath, items_slice):
        """Salva gráfico de barras horizontais para uma fatia de dados (lista de (nome, valor))."""
        import textwrap
        if not items_slice:
            return

        nomes_orig = [t[0] for t in items_slice]
        valores    = [t[1] for t in items_slice]
        n_bars     = len(nomes_orig)

        nomes = ['\n'.join(textwrap.wrap(n, width=30)) for n in nomes_orig]

        fs_lbl = max(16, 24 - max(0, n_bars - 6))
        fig_h  = max(8, n_bars * 3.2)

        PALETTE = [
            '#4169E1', '#003087', '#00B4D8', '#DC2626', '#800020',
            '#7C3AED', '#16A34A', '#4ADE80', '#D946EF', '#EC4899',
            '#F9A8D4', '#C8A97E', '#6B7280', '#9CA3AF', '#EAB308',
            '#FDE047', '#92400E', '#F97316', '#F5F5F0', '#D4AF37',
        ]
        colors = [PALETTE[i % len(PALETTE)] for i in range(n_bars)]
        LIGHT = {'#F9A8D4', '#C8A97E', '#9CA3AF', '#FDE047', '#F5F5F0'}
        edge_colors = ['#333333' if c in LIGHT else 'white' for c in colors]

        fig, ax = plt.subplots(figsize=(20, fig_h), facecolor='white')
        bars = ax.barh(range(n_bars), valores, color=colors, height=0.65,
                       edgecolor=edge_colors, linewidth=1.5)

        max_val = max(valores) if valores else 1
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val * 0.015,
                    bar.get_y() + bar.get_height() / 2,
                    str(valor), ha='left', va='center',
                    fontsize=fs_lbl, fontweight='bold')

        ax.set_yticks(range(n_bars))
        ax.set_yticklabels(nomes, fontsize=fs_lbl)
        ax.set_xlim(0, max_val * 1.18)
        ax.tick_params(axis='y', pad=8)
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        ax.invert_yaxis()

        plt.tight_layout()
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_temporal_barras_chart(self, filepath):
        """Salva gráfico de evolução temporal como imagem"""
        entregas, retiradas = self.get_entregas_retiradas(self.current_registros)
        entregas_por_data = self.count_by_field(entregas, 1)
        retiradas_por_data = self.count_by_field(retiradas, 1)
        todas_datas = sorted(set(entregas_por_data.keys()) | set(retiradas_por_data.keys()),
                            key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        if not todas_datas:
            return
        if self.show_year_accumulated:
            ent_mes, ret_mes = {}, {}
            for d in todas_datas:
                m = d[3:]
                ent_mes[m] = ent_mes.get(m, 0) + entregas_por_data.get(d, 0)
                ret_mes[m] = ret_mes.get(m, 0) + retiradas_por_data.get(d, 0)
            eixo_x = sorted(set(ent_mes) | set(ret_mes), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores_entregas  = [ent_mes.get(m, 0) for m in eixo_x]
            valores_retiradas = [ret_mes.get(m, 0) for m in eixo_x]
        else:
            eixo_x = todas_datas
            valores_entregas  = [entregas_por_data.get(d, 0)  for d in eixo_x]
            valores_retiradas = [retiradas_por_data.get(d, 0) for d in eixo_x]
        n = len(eixo_x)
        fig_w   = max(20, n * 1.1)
        fs_tick = max(14, 22 - max(0, n - 12))
        fs_val  = max(14, 22 - max(0, n - 12))
        fig, ax = plt.subplots(figsize=(fig_w, 10), facecolor='white')
        x = np.arange(n)
        width = 0.35
        bars1 = ax.bar(x - width/2, valores_entregas,  width, label='Entregas',  color=self.COR_ENTREGA,  edgecolor='white', linewidth=1.5)
        bars2 = ax.bar(x + width/2, valores_retiradas, width, label='Retiradas', color=self.COR_RETIRADA, edgecolor='white', linewidth=1.5)
        max_val = max(max(valores_entregas) if valores_entregas else 0, max(valores_retiradas) if valores_retiradas else 0)
        ax.set_ylim(0, max_val * 1.25 if max_val > 0 else 1)
        for bar, val in zip(bars1, valores_entregas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02, str(val), ha='center', va='bottom', fontsize=fs_val, fontweight='bold')
        for bar, val in zip(bars2, valores_retiradas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02, str(val), ha='center', va='bottom', fontsize=fs_val, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=fs_tick)
        ax.set_ylabel('Quantidade', fontsize=22)
        ax.tick_params(axis='y', labelsize=20)
        ax.legend(loc='upper right', fontsize=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_entregas_vs_retiradas_chart(self, filepath):
        """Salva gráfico de pizza como imagem"""
        entregas, retiradas = self.get_entregas_retiradas(self.current_registros)
        
        valores = [len(entregas), len(retiradas)]
        labels = ['Entregas', 'Retiradas']
        colors = [self.COR_ENTREGA, self.COR_RETIRADA]
        
        if sum(valores) == 0:
            return
        
        fig, ax = plt.subplots(figsize=(14, 12), facecolor='white')
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.70,
                                           wedgeprops=dict(edgecolor='white', linewidth=3))
        
        for text in texts:
            text.set_fontsize(26)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(24)
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_entrega_retirada_barras_chart(self, filepath, field_index, titulo):
        """Salva gráfico de barras agrupadas como imagem"""
        source = self.current_registros_colab if field_index == 2 else self.current_registros
        entregas, retiradas = self.get_entregas_retiradas(source)
        
        entregas_dict = self.count_by_field(entregas, field_index)
        retiradas_dict = self.count_by_field(retiradas, field_index)
        
        todos_items = sorted(set(entregas_dict.keys()) | set(retiradas_dict.keys()))
        
        if not todos_items:
            return
        
        valores_entregas = [entregas_dict.get(item, 0) for item in todos_items]
        valores_retiradas = [retiradas_dict.get(item, 0) for item in todos_items]
        
        n = len(todos_items)
        fig_w = max(20, n * 1.2)
        fs_tick = max(14, 22 - max(0, n - 10))
        fs_val  = max(14, 22 - max(0, n - 10))
        
        fig, ax = plt.subplots(figsize=(fig_w, 10), facecolor='white')
        
        x = np.arange(n)
        width = 0.35
        
        bars1 = ax.bar(x - width/2, valores_entregas, width, label='Entregas',
                      color=self.COR_ENTREGA, edgecolor='white', linewidth=1.5)
        bars2 = ax.bar(x + width/2, valores_retiradas, width, label='Retiradas',
                      color=self.COR_RETIRADA, edgecolor='white', linewidth=1.5)
        
        max_val = max(max(valores_entregas) if valores_entregas else 0,
                     max(valores_retiradas) if valores_retiradas else 0)
        ax.set_ylim(0, max_val * 1.25 if max_val > 0 else 1)
        
        for bar, val in zip(bars1, valores_entregas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02,
                       str(val), ha='center', va='bottom', fontsize=fs_val, fontweight='bold')
        for bar, val in zip(bars2, valores_retiradas):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.02,
                       str(val), ha='center', va='bottom', fontsize=fs_val, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(todos_items, rotation=45, ha='right', fontsize=fs_tick)
        ax.set_ylabel('Quantidade', fontsize=22)
        ax.tick_params(axis='y', labelsize=20)
        ax.legend(loc='upper right', fontsize=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_temporal_linha_chart(self, filepath):
        """Salva gráfico de evolução temporal (linha) como imagem"""
        datas_dict = self.count_by_field(self.current_registros, 1)
        if not datas_dict:
            return
        datas_ordenadas = sorted(datas_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        if self.show_year_accumulated:
            meses_dict = {}
            for d in datas_ordenadas:
                m = d[3:]
                meses_dict[m] = meses_dict.get(m, 0) + datas_dict[d]
            eixo_x = sorted(meses_dict.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores = [meses_dict[m] for m in eixo_x]
            ylabel = 'Visitas por Mês'
        else:
            eixo_x = datas_ordenadas
            valores = [datas_dict[d] for d in datas_ordenadas]
            ylabel = 'Movimentações'
        n = len(eixo_x)
        fig_w   = max(20, n * 1.1)
        fs_tick = max(14, 22 - max(0, n - 12))
        fs_val  = max(14, 22 - max(0, n - 12))
        fig, ax = plt.subplots(figsize=(fig_w, 10), facecolor='white')
        max_y = max(valores) if valores else 1
        line, = ax.plot(range(n), valores, color="#fe0401", linewidth=4,
                marker='o', markersize=14, markerfacecolor="#fe0401")
        ax.fill_between(range(n), valores, alpha=0.3, color="#fe0401")
        for i, (x_pos, y) in enumerate(zip(range(n), valores)):
            ax.text(x_pos, y + max_y*0.03, str(y), ha='center', va='bottom', fontsize=fs_val, fontweight='bold')
        ax.set_ylim(0, max_y * 1.20)
        ax.set_xticks(range(n))
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=fs_tick)
        ax.set_ylabel(ylabel, fontsize=22)
        ax.tick_params(axis='y', labelsize=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.tight_layout()
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_pie_tipo_chart(self, filepath, field_index, tipo, titulo):
        """Salva gráfico de pizza - sem truncação, cores contrastantes, fontes grandes (PDF)"""
        source = self.current_registros_colab if field_index == 2 else self.current_registros
        entregas, retiradas = self.get_entregas_retiradas(source)
        registros_filtrados = entregas if tipo == "ENTREGA" else retiradas
        
        data_dict = self.count_by_field(registros_filtrados, field_index)
        if not data_dict:
            return
        
        # PDF: todos os itens sem truncação
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        nomes  = [item[0] for item in sorted_data]
        valores = [item[1] for item in sorted_data]
        n_items = len(nomes)
        
        PALETTE = [
            '#4169E1',  # Azul Royal
            '#003087',  # Azul Marinho
            '#00B4D8',  # Azul Turquesa
            '#DC2626',  # Vermelho
            '#800020',  # Vinho
            '#7C3AED',  # Roxo
            '#16A34A',  # Verde
            '#4ADE80',  # Verde Claro
            '#D946EF',  # Magenta
            '#EC4899',  # Rosa
            '#F9A8D4',  # Rosa Claro
            '#C8A97E',  # Bege
            '#6B7280',  # Cinza
            '#9CA3AF',  # Cinza Claro
            '#EAB308',  # Amarelo
            '#FDE047',  # Amarelo Claro
            '#92400E',  # Marrom
            '#F97316',  # Laranja
            '#F5F5F0',  # Branco (off-white)
            '#D4AF37',  # Dourado
        ]
        colors = [PALETTE[i % len(PALETTE)] for i in range(n_items)]
        
        if n_items <= 7:
            # Poucos itens: labels inline na pizza
            fig, ax = plt.subplots(figsize=(14, 12), facecolor='white')
            wedges, texts, autotexts = ax.pie(
                valores, labels=nomes, autopct='%1.1f%%',
                colors=colors, startangle=90, pctdistance=0.68,
                wedgeprops=dict(edgecolor='white', linewidth=3)
            )
            for text in texts:
                text.set_fontsize(20)
                text.set_fontweight('bold')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(18)
                autotext.set_fontweight('bold')
            plt.tight_layout()
        else:
            # Muitos itens: legenda lateral com fonte grande
            fig_h = max(12, 8 + n_items * 0.35)
            fig, ax = plt.subplots(figsize=(20, fig_h), facecolor='white')
            wedges, texts, autotexts = ax.pie(
                valores, autopct='%1.1f%%',
                colors=colors, startangle=90, pctdistance=0.75,
                wedgeprops=dict(edgecolor='white', linewidth=2.5)
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(16)
                autotext.set_fontweight('bold')
            legend_labels = [f"{n}  ({v})" for n, v in zip(nomes, valores)]
            ax.legend(wedges, legend_labels,
                      title="Itens", title_fontsize=18,
                      fontsize=16, loc="center left",
                      bbox_to_anchor=(1.02, 0.5),
                      frameon=True, framealpha=0.9)
            plt.tight_layout()
        
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def _save_top5_chart(self, filepath, field_index, titulo="Top 5"):
        """Salva gráfico Top 5 para PDF — mesma paleta gradiente da aplicação, apenas 5 itens."""
        source = self.current_registros_colab if field_index == 2 else self.current_registros
        data_dict = self.count_by_field(source, field_index)
        top5 = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:5]

        if not top5:
            return

        nomes  = [t[0] for t in top5]
        valores = [t[1] for t in top5]
        n_bars  = len(nomes)

        # Gradiente idêntico ao da aplicação: vermelho → amarelo-dourado
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (220 + (234 - 220) * ratio) / 255
            g = (38  + (179 - 38)  * ratio) / 255
            b = (38  + (8   - 38)  * ratio) / 255
            colors.append((r, g, b))

        fig, ax = plt.subplots(figsize=(20, 10), facecolor='white')

        bars = ax.barh(range(n_bars), valores, color=colors, height=0.55,
                       edgecolor='white', linewidth=1.5)

        max_val = max(valores) if valores else 1
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val * 0.015,
                    bar.get_y() + bar.get_height() / 2,
                    str(valor), ha='left', va='center',
                    fontsize=22, fontweight='bold')

        ax.set_yticks(range(n_bars))
        ax.set_yticklabels(nomes, fontsize=22)
        ax.set_xlim(0, max_val * 1.18)
        ax.tick_params(axis='y', pad=10)
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        ax.invert_yaxis()

        plt.tight_layout()
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)