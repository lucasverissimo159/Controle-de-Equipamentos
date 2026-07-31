"""
Diálogo de progresso para operações demoradas
Salvar em: views/widgets/progress_dialog.py
"""
import customtkinter as ctk
import sys
import os

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # Subir 3 níveis: widgets -> views -> kit_control_final
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)

class ProgressDialog:
    """Diálogo de progresso com barra e mensagem de status"""
    
    def __init__(self, parent, title="Processando...", total_steps=100):
        self.parent = parent
        self.total_steps = total_steps
        self.current_step = 0
        self.cancelled = False
        
        # Criar janela
        self.window = ctk.CTkToplevel(parent)
        self.window.title(title)
        self.window.geometry("450x180")
        self.window.resizable(False, False)
        self.window.grab_set()
        self.window.transient(parent)
        
        # Centralizar na tela
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.window.winfo_screenheight() // 2) - (180 // 2)
        self.window.geometry(f"450x180+{x}+{y}")
        
        # Impedir fechamento pelo X
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Definir ícone da janela
        self.set_window_icon()
        
        # Container
        container = ctk.CTkFrame(self.window, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Ícone e título
        self.title_label = ctk.CTkLabel(
            container, 
            text="📊 Gerando PDF...",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=(0, 15))
        
        # Label de status
        self.status_label = ctk.CTkLabel(
            container, 
            text="Iniciando...",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(
            container, 
            width=380, 
            height=20,
            corner_radius=10,
            progress_color="#10b981"
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)
        
        # Label de porcentagem
        self.percent_label = ctk.CTkLabel(
            container, 
            text="0%",
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af"
        )
        self.percent_label.pack()
        
        # Forçar atualização visual
        self.window.update()

    def set_window_icon(self):
        """Define o ícone para a janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")
    
    def update_progress(self, step, status_text=None):
        """Atualiza o progresso"""
        if self.cancelled:
            return
            
        self.current_step = step
        progress = step / self.total_steps
        
        try:
            self.progress_bar.set(progress)
            self.percent_label.configure(text=f"{int(progress * 100)}%")
            
            if status_text:
                self.status_label.configure(text=status_text)
            
            # Forçar atualização visual
            self.window.update()
        except:
            pass  # Janela pode ter sido fechada
    
    def set_status(self, text):
        """Atualiza apenas o texto de status"""
        try:
            self.status_label.configure(text=text)
            self.window.update()
        except:
            pass
    
    def close(self):
        """Fecha o diálogo"""
        try:
            self.window.grab_release()
            self.window.destroy()
        except:
            pass