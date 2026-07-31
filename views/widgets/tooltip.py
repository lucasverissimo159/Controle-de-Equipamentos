"""Tooltip"""
import tkinter as tk


class Tooltip:
    """Tooltip para mostrar informações ao passar o mouse.

    Usa tkinter puro (tk.Toplevel/tk.Label) em vez de CustomTkinter: criar e
    destruir um ctk.CTkToplevel a cada passagem do mouse acumulava loops
    'after' internos do CustomTkinter que não eram totalmente liberados no
    destroy(), degradando a responsividade da interface ao longo do tempo.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text,
                         bg="#f0f0f0", fg="black",
                         padx=10, pady=5,
                         relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
