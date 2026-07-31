"""ComboBox com scroll e busca por digitação - Sistema de Controle de Equipamentos"""
import customtkinter as ctk
import tkinter.font as tkfont

class ScrollableComboBox(ctk.CTkFrame):
    """ComboBox customizado com scrollbar e busca por digitação no campo"""
    
    def __init__(self, master, variable, values, width=200, height=40, max_visible_items=6, app=None, item_tooltip_callback=None, on_enter_callback=None, numeric_only=False, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=height)
        
        self.variable = variable
        self.values = values
        self.all_values = values.copy() if values else []
        self.max_visible_items = max_visible_items
        self.width = width
        self.dropdown_window = None
        self.app = app
        self.scroll_frame_widget = None
        self.buttons = []
        self.is_closing = False
        self.has_click_binding = False
        
        # Callback para tooltip dos itens (recebe valor, retorna texto do tooltip)
        self.item_tooltip_callback = item_tooltip_callback
        self.item_tooltip_window = None
        self._tooltip_after_id = None  # ID do after pendente
        
        # Callback para quando ENTER é pressionado (recebe o valor digitado)
        self.on_enter_callback = on_enter_callback
        
        # Se True, aceita apenas números e caracteres permitidos (-, /)
        self.numeric_only = numeric_only
        
        # Variável interna para o entry
        self.entry_var = ctk.StringVar()
        self.entry_var.set(variable.get())
        
        # Sincronizar variáveis
        self.variable.trace_add('write', self.on_variable_change)
        
        # Frame container
        self.container = ctk.CTkFrame(self, fg_color="transparent", width=width, height=height)
        self.container.pack(fill="both", expand=True)
        
        # Entry editável para digitar e buscar
        self.entry = ctk.CTkEntry(self.container, textvariable=self.entry_var, width=width-40, height=height)
        self.entry.pack(side="left", fill="x", expand=True)
        
        # Eventos do entry
        self.entry.bind("<Button-1>", self.on_entry_click)
        self.entry.bind("<KeyRelease>", self.on_entry_key)
        self.entry.bind("<FocusIn>", self.on_entry_focus)
        self.entry.bind("<Return>", self.on_entry_return)
        self.entry.bind("<Escape>", self.on_entry_escape)
        
        # Se numeric_only, adicionar validação para bloquear letras
        if self.numeric_only:
            self.entry.bind("<KeyPress>", self.on_key_press_validate)
        
        # Botão dropdown
        self.dropdown_btn = ctk.CTkButton(self.container, text="▼", width=30, height=height,
                                         command=self.on_dropdown_btn_click)
        self.dropdown_btn.pack(side="left", padx=(5, 0))
    
    def on_variable_change(self, *args):
        """Atualiza o entry quando a variável externa muda"""
        new_value = self.variable.get()
        if self.entry_var.get() != new_value:
            self.entry_var.set(new_value)
    
    def show_item_tooltip(self, event, value):
        """Agenda mostrar tooltip para um item do dropdown"""
        # Cancelar qualquer tooltip pendente
        if self._tooltip_after_id:
            try:
                self.after_cancel(self._tooltip_after_id)
            except:
                pass
            self._tooltip_after_id = None
        
        # Destruir tooltip atual imediatamente
        self._destroy_item_tooltip()
        
        if not self.item_tooltip_callback:
            return
        
        # Agendar criação do novo tooltip com delay (200ms - debounce)
        self._tooltip_after_id = self.after(200, lambda: self._create_tooltip(event, value))
    
    def _create_tooltip(self, event, value):
        """Cria o tooltip efetivamente"""
        self._tooltip_after_id = None
        
        if not self.item_tooltip_callback:
            return
        
        # Buscar texto do tooltip através do callback
        tooltip_text = self.item_tooltip_callback(value)
        
        if not tooltip_text:
            return
        
        # Verificar se dropdown ainda está aberto
        if not self.dropdown_window or not self.dropdown_window.winfo_exists():
            return
        
        # Criar novo tooltip
        try:
            self.item_tooltip_window = ctk.CTkToplevel(self)
            self.item_tooltip_window.wm_overrideredirect(True)
            self.item_tooltip_window.wm_attributes("-topmost", True)
            
            # Posicionar tooltip próximo ao cursor
            x = event.x_root + 15
            y = event.y_root - 10
            self.item_tooltip_window.wm_geometry(f"+{x}+{y}")
            
            # Estilo baseado no tema
            if self.app and hasattr(self.app, 'current_theme'):
                is_dark = self.app.current_theme == "dark"
            else:
                is_dark = ctk.get_appearance_mode() == "Dark"
            
            bg_color = "#1f2937" if is_dark else "#e5e7eb"
            text_color = "#242525"  # Verde para destacar
            
            # Frame do tooltip
            tooltip_frame = ctk.CTkFrame(self.item_tooltip_window, fg_color=bg_color, corner_radius=6)
            tooltip_frame.pack(fill="both", expand=True)
            
            ctk.CTkLabel(
                tooltip_frame,
                text=tooltip_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=text_color
            ).pack(padx=8, pady=4)
        except Exception as e:
            print(f"Erro ao criar tooltip: {e}")
            self.item_tooltip_window = None
    
    def _destroy_item_tooltip(self):
        """Método interno para destruir tooltip de forma segura"""
        # Cancelar tooltip pendente
        if self._tooltip_after_id:
            try:
                self.after_cancel(self._tooltip_after_id)
            except:
                pass
            self._tooltip_after_id = None
        
        # Destruir tooltip atual
        tooltip = self.item_tooltip_window
        self.item_tooltip_window = None  # Limpa referência ANTES de destruir
        
        if tooltip:
            try:
                tooltip.withdraw()  # Esconde imediatamente
                tooltip.destroy()   # Depois destrói
            except:
                pass
    
    def hide_item_tooltip(self, event=None):
        """Esconde o tooltip do item"""
        self._destroy_item_tooltip()
    
    def on_entry_click(self, event):
        """Ao clicar no entry, foca para digitação e abre o dropdown"""
        if self.is_closing:
            return
        
        # Focar no entry para permitir digitação imediata
        self.entry.focus_set()
        
        # Selecionar todo o texto para facilitar substituição
        self.after(10, lambda: self.entry.select_range(0, 'end'))
        
        # Abrir dropdown se não estiver aberto
        if not self.dropdown_window or not self.dropdown_window.winfo_exists():
            self.open_dropdown()
    
    def on_key_press_validate(self, event):
        """Valida teclas pressionadas - bloqueia letras se numeric_only"""
        # Permitir teclas de controle
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 
                           'Tab', 'Return', 'Escape', 'Up', 'Down'):
            return
        
        # Permitir Ctrl+C, Ctrl+V, Ctrl+A, etc
        if event.state & 0x4:  # Ctrl pressionado
            return
        
        # Permitir números
        if event.char.isdigit():
            return
        
        # Permitir caracteres especiais comuns em matrículas (-, /)
        if event.char in ('-', '/', '.'):
            return
        
        # Bloquear qualquer outra coisa (letras, etc)
        return "break"
    
    def on_dropdown_btn_click(self):
        """Ao clicar no botão dropdown"""
        if self.is_closing:
            return
        self.toggle_dropdown()
    
    def on_entry_focus(self, event):
        """Ao focar no entry, seleciona todo o texto"""
        self.entry.select_range(0, 'end')
    
    def on_entry_return(self, event):
        """Ao pressionar Enter, executa callback externo ou seleciona primeira opção"""
        # Se há um callback externo definido, chamar ele primeiro
        if self.on_enter_callback:
            # Fechar dropdown se estiver aberto
            self.close_dropdown()
            # Chamar callback com o valor atual
            valor_atual = self.entry_var.get()
            self.on_enter_callback(valor_atual)
            return "break"
        
        # Comportamento padrão: seleciona primeira opção ou fecha
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            if self.buttons:
                first_btn, first_value = self.buttons[0]
                self.select_value(first_value)
            else:
                self.close_dropdown()
        return "break"
    
    def on_entry_escape(self, event):
        """Ao pressionar Escape, restaura o valor original e fecha"""
        self.entry_var.set(self.variable.get())
        self.close_dropdown()
        self.entry.master.focus_set()
        return "break"
    
    def on_entry_key(self, event):
        """Ao digitar no entry, filtra as opções"""
        if event.keysym in ('Return', 'Escape', 'Tab', 'Shift_L', 'Shift_R', 
                           'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                           'Up', 'Down', 'Left', 'Right'):
            return
        
        if not self.dropdown_window or not self.dropdown_window.winfo_exists():
            self.open_dropdown()
        
        search_text = self.entry_var.get().upper()
        self.filter_options(search_text)
    
    def filter_options(self, search_text):
        """Filtra as opções baseado no texto digitado"""
        if not self.dropdown_window or not self.dropdown_window.winfo_exists():
            return
        
        # Esconder tooltip ao filtrar
        self.hide_item_tooltip()
        
        if search_text:
            filtered_values = [v for v in self.all_values if search_text in str(v).upper()]
        else:
            filtered_values = self.all_values
        
        self.recreate_buttons(filtered_values)
    
    def recreate_buttons(self, values_to_show):
        """Recria os botões com os valores filtrados"""
        if not self.dropdown_window or not self.dropdown_window.winfo_exists():
            return
        
        if not self.scroll_frame_widget:
            return
        
        # Esconder tooltip se existir
        self._destroy_item_tooltip()
        
        for btn, value in self.buttons:
            try:
                btn.destroy()
            except:
                pass
        self.buttons = []
        
        if self.app and hasattr(self.app, 'current_theme'):
            is_dark = self.app.current_theme == "dark"
        else:
            is_dark = ctk.get_appearance_mode() == "Dark"
        
        text_color = "white" if is_dark else "black"
        dropdown_width = self.calculate_dropdown_width()
        
        content_frame = self.scroll_frame_widget
        
        for widget in content_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        
        for value in values_to_show:
            btn = ctk.CTkButton(content_frame, text=str(value), 
                              command=lambda v=value: self.select_value(v),
                              height=28,
                              fg_color="transparent",
                              text_color=text_color,
                              hover_color=("#d1d5db", "#374151"),
                              anchor="w",
                              width=dropdown_width-30)
            btn.pack(fill="x", pady=1, padx=2)
            
            # Vincular eventos de tooltip se callback definido
            if self.item_tooltip_callback:
                btn.bind("<Enter>", lambda e, v=value: self.show_item_tooltip(e, v))
                btn.bind("<Leave>", self.hide_item_tooltip)
            
            self.buttons.append((btn, value))
        
        if not values_to_show:
            no_result = ctk.CTkLabel(content_frame, text="Nenhum resultado", 
                                    text_color="#6b7280")
            no_result.pack(pady=10)
    
    def calculate_dropdown_width(self):
        """Calcula a largura ideal do dropdown baseado na maior string"""
        if not self.all_values:
            return self.width
        
        try:
            font = tkfont.Font(family="Segoe UI", size=12)
        except:
            font = tkfont.Font(size=12)
        
        max_text_width = 0
        for value in self.all_values:
            text_width = font.measure(str(value))
            if text_width > max_text_width:
                max_text_width = text_width
        
        calculated_width = max_text_width + 60
        return max(self.width, min(calculated_width, 500))
    
    def is_click_inside_combobox(self, event):
        """Verifica se o clique foi dentro do combobox (entry + botão + dropdown)"""
        click_x = event.x_root
        click_y = event.y_root
        
        # Verificar entry
        try:
            entry_x1 = self.entry.winfo_rootx()
            entry_y1 = self.entry.winfo_rooty()
            entry_x2 = entry_x1 + self.entry.winfo_width()
            entry_y2 = entry_y1 + self.entry.winfo_height()
            
            if entry_x1 <= click_x <= entry_x2 and entry_y1 <= click_y <= entry_y2:
                return True
        except:
            pass
        
        # Verificar botão dropdown
        try:
            btn_x1 = self.dropdown_btn.winfo_rootx()
            btn_y1 = self.dropdown_btn.winfo_rooty()
            btn_x2 = btn_x1 + self.dropdown_btn.winfo_width()
            btn_y2 = btn_y1 + self.dropdown_btn.winfo_height()
            
            if btn_x1 <= click_x <= btn_x2 and btn_y1 <= click_y <= btn_y2:
                return True
        except:
            pass
        
        # Verificar dropdown window
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            try:
                dropdown_x1 = self.dropdown_window.winfo_rootx()
                dropdown_y1 = self.dropdown_window.winfo_rooty()
                dropdown_x2 = dropdown_x1 + self.dropdown_window.winfo_width()
                dropdown_y2 = dropdown_y1 + self.dropdown_window.winfo_height()
                
                if dropdown_x1 <= click_x <= dropdown_x2 and dropdown_y1 <= click_y <= dropdown_y2:
                    return True
            except:
                pass
        
        return False
    
    def on_click_outside(self, event):
        """Callback quando clica fora do combobox"""
        try:
            if not self.is_click_inside_combobox(event):
                self.close_dropdown()
                self.entry.master.focus_set()
        except:
            pass
    
    def bind_click_outside(self):
        """Vincula evento de clique global para detectar cliques fora"""
        if not self.has_click_binding:
            try:
                root = self.winfo_toplevel()
                root.bind("<Button-1>", self.on_click_outside, add="+")
                self.has_click_binding = True
            except:
                pass
    
    def unbind_click_outside(self):
        """Remove binding de clique global"""
        if self.has_click_binding:
            try:
                root = self.winfo_toplevel()
                root.unbind("<Button-1>")
                self.has_click_binding = False
            except:
                pass
        
    def toggle_dropdown(self):
        """Abre ou fecha o dropdown"""
        # Esconder tooltip ao alternar dropdown
        self.hide_item_tooltip()
        
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.close_dropdown()
        else:
            self.open_dropdown()
    
    def on_mousewheel(self, event):
        """Captura evento de scroll do mouse"""
        # Esconder tooltip ao fazer scroll
        self.hide_item_tooltip()
        
        if self.scroll_frame_widget and hasattr(self.scroll_frame_widget, '_parent_canvas'):
            if event.num == 4 or event.delta > 0:
                self.scroll_frame_widget._parent_canvas.yview_scroll(-69, "units")
            elif event.num == 5 or event.delta < 0:
                self.scroll_frame_widget._parent_canvas.yview_scroll(69, "units")
        return "break"
    
    def bind_mousewheel(self, widget):
        """Vincula eventos de scroll do mouse recursivamente"""
        widget.bind("<MouseWheel>", self.on_mousewheel, add="+")
        widget.bind("<Button-4>", self.on_mousewheel, add="+")
        widget.bind("<Button-5>", self.on_mousewheel, add="+")
        
        for child in widget.winfo_children():
            self.bind_mousewheel(child)
    
    def open_dropdown(self):
        """Abre o dropdown"""
        if self.is_closing:
            return
            
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            return
        
        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.withdraw()
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.attributes('-topmost', True)
        
        item_height = 35
        num_items = len(self.all_values)
        visible_items = min(max(num_items, 1), self.max_visible_items)
        dropdown_height = visible_items * item_height + 10
        dropdown_width = self.calculate_dropdown_width()
        
        self.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        self.dropdown_window.geometry(f"{dropdown_width}x{dropdown_height}+{x}+{y}")
        
        self.buttons = []
        
        if num_items > self.max_visible_items:
            scroll_frame = ctk.CTkScrollableFrame(self.dropdown_window, 
                                                 width=dropdown_width-20,
                                                 height=dropdown_height-10,
                                                 orientation="vertical")
            scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.scroll_frame_widget = scroll_frame
        else:
            scroll_frame = ctk.CTkFrame(self.dropdown_window)
            scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.scroll_frame_widget = scroll_frame
        
        if self.app and hasattr(self.app, 'current_theme'):
            is_dark = self.app.current_theme == "dark"
        else:
            is_dark = ctk.get_appearance_mode() == "Dark"
        
        text_color = "white" if is_dark else "black"
        
        for value in self.all_values:
            btn = ctk.CTkButton(scroll_frame, text=str(value), 
                              command=lambda v=value: self.select_value(v),
                              height=28,
                              fg_color="transparent",
                              text_color=text_color,
                              hover_color=("#d1d5db", "#374151"),
                              anchor="w",
                              width=dropdown_width-30)
            btn.pack(fill="x", pady=1, padx=2)
            
            # Vincular eventos de tooltip se callback definido
            if self.item_tooltip_callback:
                btn.bind("<Enter>", lambda e, v=value: self.show_item_tooltip(e, v))
                btn.bind("<Leave>", self.hide_item_tooltip)
            
            self.buttons.append((btn, value))
        
        self.bind_mousewheel(self.dropdown_window)
        
        # Bind para detectar cliques fora (com pequeno delay)
        self.after(100, self.bind_click_outside)
        
        self.dropdown_window.deiconify()
        
        self.entry.focus_set()
    
    def close_dropdown(self):
        """Fecha o dropdown"""
        # Esconder tooltip de item se existir
        self._destroy_item_tooltip()
        
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.is_closing = True
            self.dropdown_window.destroy()
            self.after(200, self.reset_closing_flag)
        
        # Remove binding de clique global
        self.unbind_click_outside()
        
        self.dropdown_window = None
        self.scroll_frame_widget = None
        self.buttons = []
    
    def reset_closing_flag(self):
        """Reseta a flag de fechamento"""
        self.is_closing = False
    
    def select_value(self, value):
        """Seleciona um valor"""
        self.variable.set(value)
        self.entry_var.set(value)
        self.close_dropdown()
    
    def configure(self, **kwargs):
        """Configurar o widget"""
        if "values" in kwargs:
            self.values = kwargs["values"]
            self.all_values = kwargs["values"].copy() if kwargs["values"] else []


class Tooltip:
    """Tooltip que aparece ao passar o mouse"""
    
    def __init__(self, widget, text, app=None):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.app = app
        
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Mostra o tooltip"""
        if self.tooltip_window or not self.text:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        if self.app and hasattr(self.app, 'current_theme'):
            is_dark = self.app.current_theme == "dark"
        else:
            is_dark = ctk.get_appearance_mode() == "Dark"
        
        bg_color = "#1f2937" if is_dark else "#f3f4f6"
        text_color = "white" if is_dark else "black"
        
        label = ctk.CTkLabel(self.tooltip_window, text=self.text,
                           fg_color=bg_color,
                           text_color=text_color,
                           corner_radius=6,
                           padx=10, pady=5)
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Esconde o tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None