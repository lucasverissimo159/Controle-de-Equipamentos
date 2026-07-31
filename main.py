#!/usr/bin/env python3
"""Sistema de Controle de Equipamentos - MVC Completo"""
import customtkinter as ctk
from config.settings import DEFAULT_THEME
from views.main_window import EquipControlApp

if __name__ == "__main__":
    ctk.set_appearance_mode(DEFAULT_THEME)
    ctk.set_default_color_theme("blue")
    app = EquipControlApp()
    app.run()
