"""
Diálogo para exibir histórico de alterações
"""
import customtkinter as ctk
from tkinter import ttk, Toplevel
import sys
import os

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class HistoryDialog:
    """Diálogo de histórico"""
    
    def __init__(self, parent, db, record_id):
        self.parent = parent
        self.db = db
        self.record_id = record_id
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Histórico - Registro #{record_id}")
        self.window.geometry("800x500")
        self.window.grab_set()
        self.window.transient(parent)
        
        # Centralizar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 400
        y = (self.window.winfo_screenheight() // 2) - 250
        self.window.geometry(f"800x500+{x}+{y}")

        # Definir ícone da janela
        self.set_window_icon()
        
        # Tooltip
        self.tooltip = None
        
        self.create_widgets()
        self.load_history()

    def set_window_icon(self):
        """Define o ícone para a janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")
    
    def create_widgets(self):
        """Criar interface"""
        main = ctk.CTkFrame(self.window, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main, text=f"📋 Histórico de Alterações",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))
        
        # Tabela
        table_frame = ctk.CTkFrame(main)
        table_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        cols = ("Tipo", "Campo", "Anterior", "Novo", "Data/Hora")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.tree.yview)
        
        # Configurar colunas
        widths = [100, 120, 150, 200, 150]
        for col, width in zip(cols, widths):
            self.tree.column(col, width=width, anchor="center")
            self.tree.heading(col, text=col, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind para tooltip
        self.tree.bind('<Motion>', self.on_tree_motion)
        self.tree.bind('<Leave>', self.hide_tooltip)
        
        # Botão fechar
        ctk.CTkButton(main, text="FECHAR", command=self.window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563",
                     height=40, width=150).pack()
    
    def on_tree_motion(self, event):
        """Mostrar tooltip ao passar o mouse sobre células"""
        # Identificar item e coluna
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            self.hide_tooltip()
            return
        
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            self.hide_tooltip()
            return
        
        # Pegar valores
        values = self.tree.item(item)['values']
        if not values:
            self.hide_tooltip()
            return
        
        # Índice da coluna (começa em #1)
        col_idx = int(column.replace('#', '')) - 1
        
        # Só mostrar tooltip para colunas "Anterior" (2) e "Novo" (3)
        if col_idx not in [2, 3]:
            self.hide_tooltip()
            return
        
        cell_value = str(values[col_idx]) if col_idx < len(values) else ""
        
        if not cell_value or cell_value == '-':
            self.hide_tooltip()
            return
        
        # Formatar texto para exibição organizada
        formatted_text = self.format_tooltip_text(cell_value)
        
        # Criar chave única para evitar recriação desnecessária
        tooltip_key = f"{item}_{column}"
        if hasattr(self, '_last_tooltip_key') and self._last_tooltip_key == tooltip_key:
            return
        
        self._last_tooltip_key = tooltip_key
        
        # Mostrar tooltip
        self.show_tooltip(event, formatted_text)
    
    def format_tooltip_text(self, text):
        """Formata o texto do tooltip para exibição organizada"""
        # Se contém vírgulas e dois pontos, provavelmente é um registro de criação
        if ', ' in text and ': ' in text:
            # Separar por vírgula e organizar
            parts = text.split(', ')
            formatted_parts = []
            for part in parts:
                part = part.strip()
                if ': ' in part:
                    formatted_parts.append(part)
                else:
                    # Se não tem ":", adiciona ao último
                    if formatted_parts:
                        formatted_parts[-1] += f", {part}"
                    else:
                        formatted_parts.append(part)
            return '\n'.join(formatted_parts)
        
        return text
    
    def show_tooltip(self, event, text):
        """Mostra tooltip com o texto formatado"""
        self.hide_tooltip()
        
        # Criar janela do tooltip
        self.tooltip = Toplevel(self.window)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes('-topmost', True)
        
        # Frame do tooltip
        frame = ctk.CTkFrame(self.tooltip, fg_color="#f3f4f6", corner_radius=6)
        frame.pack(fill="both", expand=True)
        
        # Label com o texto
        label = ctk.CTkLabel(frame, text=text,
                            font=ctk.CTkFont(size=11),
                            text_color="#374151",
                            justify="left",
                            anchor="w")
        label.pack(padx=10, pady=8)
        
        # Posicionar tooltip
        x = event.x_root + 15
        y = event.y_root + 10
        
        # Ajustar se sair da tela
        self.tooltip.update_idletasks()
        tooltip_width = self.tooltip.winfo_reqwidth()
        tooltip_height = self.tooltip.winfo_reqheight()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        if x + tooltip_width > screen_width:
            x = event.x_root - tooltip_width - 5
        if y + tooltip_height > screen_height:
            y = event.y_root - tooltip_height - 5
        
        self.tooltip.geometry(f"+{x}+{y}")
    
    def hide_tooltip(self, event=None):
        """Esconde o tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        if hasattr(self, '_last_tooltip_key'):
            self._last_tooltip_key = None
    
    def load_history(self):
        """Carregar histórico"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        history = self.db.get_history(self.record_id)
        
        if not history:
            self.tree.insert('', 'end', 
                           values=('', '', 'Nenhuma alteração', '', ''))
            return
        
        for campo, anterior, novo, data, tipo in history:
            tipo_icon = {'CRIAÇÃO': '✨', 'EDIÇÃO': '✏️', 'EXCLUSÃO': '🗑️'}.get(tipo, '•')
            self.tree.insert('', 'end',
                           values=(f"{tipo_icon} {tipo}", campo, 
                                  anterior or '-', novo or '-', data))