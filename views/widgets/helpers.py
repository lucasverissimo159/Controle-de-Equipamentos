"""
Funções auxiliares para as views
"""
import re
from datetime import datetime
from tkinter import messagebox


def validate_date(date_string):
    """Valida se a data é válida"""
    try:
        datetime.strptime(date_string, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validate_time(time_string):
    """Valida se o horário é válido"""
    try:
        datetime.strptime(time_string, "%H:%M")
        return True
    except ValueError:
        return False


def format_date_input(event):
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


def format_time_input(event):
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


def make_uppercase(event):
    """Converte o texto para maiúsculas automaticamente"""
    widget = event.widget
    content = widget.get()
    if content != content.upper():
        widget.delete(0, 'end')
        widget.insert(0, content.upper())
