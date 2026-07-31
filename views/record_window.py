"""
Janela de cadastro/edição de registros
Com opções CADASTRADO/SEM CADASTRO para cliente
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import re
import os
import sys
import json
from views.widgets.scrollable_combobox import ScrollableComboBox

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class RecordWindow:
    def __init__(self, parent, mode="new", record_id=None):
        self.parent = parent
        self.mode = mode
        self.record_id = record_id
        
        self.window = ctk.CTkToplevel(parent.root)
        self.window.title("Novo Registro" if mode == "new" else "Editar Registro")
        self.window.geometry("515x515")
        self.window.grab_set()
        self.window.transient(parent.root)

        # Centralizar janela
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 257
        y = (self.window.winfo_screenheight() // 2) - 400
        self.window.geometry(f"515x515+{x}+{y}")

        # Definir ícone da janela
        self.set_window_icon()
        
        # Flag para evitar loop infinito no preenchimento automático
        self._updating = False
        
        # Múltiplos equipamentos (apenas modo novo)
        self._multi_equip_var   = ctk.BooleanVar(value=False)
        self._equip_check_vars  = {}
        self._equip_qty_vars    = {}
        self._equip_qty_entries = {}
        self._main_frame_ref    = None
        self._main_scroll_canvas = None
        self._equip_scroll_canvas = None
        self._scroll_step_pixels = 38
        
        # Variáveis
        self.vars = {
            'data': ctk.StringVar(value=datetime.now().strftime("%d/%m/%Y")),
            'colaborador': ctk.StringVar(),
            'colaborador_matricula': ctk.StringVar(),  # NOVO: matrícula do colaborador
            'equipamento': ctk.StringVar(),
            'quantidade': ctk.StringVar(value="1"),
            'tipo_cliente': ctk.StringVar(value="CADASTRADO"),
            'matricula': ctk.StringVar(),
            'cliente': ctk.StringVar(),
            'busca_nome': ctk.StringVar(),  # NOVO: busca do cliente por nome
            'local': ctk.StringVar(),
            'horario': ctk.StringVar(value=datetime.now().strftime("%H:%M")),
            'tipo': ctk.StringVar(value="ENTREGA")
        }
        
        # Guardar valores originais para comparação no histórico
        self.original_values = {}
        
        # Guardar último valor válido do cliente para validação
        self._last_valid_cliente = ""
        
        # Mapas de display de colaboradores (populados em build_colaborador_display_list)
        self._colab_display_to_mat  = {}
        self._colab_display_to_nome = {}
        
        # Carregar lista de clientes/matrículas existentes
        self.clientes_matriculas = self.load_clientes_matriculas()
        
        if mode == "edit":
            self.load_record()
            # Atualizar último cliente válido após carregar registro
            self._last_valid_cliente = self.vars['cliente'].get()
        
        self.create_widgets()
        
        # Configurar bindings para preenchimento automático APÓS criar widgets
        self.setup_auto_fill_bindings()

    def set_window_icon(self):
        """Define o ícone para a janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")
    
    def build_colaborador_display_list(self):
        """Constrói lista de colaboradores para o combobox.
        Homônimos recebem sufixo '(MAT)' para serem distinguíveis.
        Popula self._colab_display_to_mat {display_label: matricula}
        e self._colab_display_to_nome {display_label: nome_real}.
        """
        self._colab_display_to_mat  = {}
        self._colab_display_to_nome = {}

        try:
            self.parent.cursor.execute(
                "SELECT nome, matricula FROM colaboradores ORDER BY nome"
            )
            rows = self.parent.cursor.fetchall()
        except Exception as e:
            print(f"Erro ao carregar colaboradores: {e}")
            rows = []

        # Contar ocorrências de cada nome
        from collections import Counter
        name_count = Counter(r[0].upper().strip() for r in rows if r[0])

        display_list = []
        for nome_raw, mat_raw in rows:
            if not nome_raw:
                continue
            nome = nome_raw.upper().strip()
            mat  = mat_raw.upper().strip() if mat_raw else ""

            if name_count[nome] > 1 and mat:
                label = f"{nome} ({mat})"
            else:
                label = nome

            self._colab_display_to_mat[label]  = mat
            self._colab_display_to_nome[label] = nome
            display_list.append(label)

        return display_list

    def get_display_label_for_record(self, nome, mat):
        """Retorna o display label correto para um registro já salvo (modo edição)."""
        nome_up = nome.upper().strip() if nome else ""
        mat_up  = mat.upper().strip()  if mat  else ""
        # Tentar match exato com sufixo (homônimo)
        label_com_mat = f"{nome_up} ({mat_up})" if mat_up else nome_up
        if label_com_mat in self._colab_display_to_mat:
            return label_com_mat
        # Fallback: nome sem sufixo
        if nome_up in self._colab_display_to_mat:
            return nome_up
        return nome_up

    def get_colaborador_matricula_tooltip(self, display_label):
        """Retorna texto do tooltip com a matrícula do colaborador."""
        if not display_label:
            return None
        mat = self._colab_display_to_mat.get(display_label.upper().strip())
        if mat:
            return f"📋 Matrícula: {mat}"
        return None
    
    def load_clientes_matriculas(self):
        """Carrega lista de clientes e matrículas existentes no banco"""
        try:
            self.parent.cursor.execute('''
                SELECT DISTINCT cliente, matricula 
                FROM registros 
                WHERE cliente IS NOT NULL AND cliente != '' 
                   AND matricula IS NOT NULL AND matricula != ''
            ''')
            results = self.parent.cursor.fetchall()
            
            # Criar dicionários para busca rápida
            cliente_to_matricula = {}
            matricula_to_cliente = {}
            matriculas = []
            clientes = []
            
            for row in results:
                if row[0] and row[1]:
                    cliente_norm = row[0].upper().strip()
                    matricula_norm = row[1].upper().strip()
                    cliente_to_matricula[cliente_norm] = matricula_norm
                    matricula_to_cliente[matricula_norm] = cliente_norm
                    if matricula_norm not in matriculas:
                        matriculas.append(matricula_norm)
                    if cliente_norm not in clientes:
                        clientes.append(cliente_norm)
            
            return {
                'cliente_to_matricula': cliente_to_matricula,
                'matricula_to_cliente': matricula_to_cliente,
                'matriculas': sorted(matriculas),
                'clientes': sorted(clientes)
            }
        except Exception as e:
            print(f"Erro ao carregar clientes/matrículas: {e}")
            return {
                'cliente_to_matricula': {},
                'matricula_to_cliente': {},
                'matriculas': [],
                'clientes': []
            }
    
    def setup_auto_fill_bindings(self):
        """Configura os bindings para preenchimento automático"""
        # Trace na variável de matrícula para preenchimento automático (apenas modo CADASTRADO)
        self.vars['matricula'].trace_add('write', self.on_matricula_changed)
        # Trace na variável de cliente para validação (apenas modo SEM CADASTRO)
        self.vars['cliente'].trace_add('write', self.on_cliente_changed)
        # Trace na variável de colaborador para buscar matrícula automaticamente
        self.vars['colaborador'].trace_add('write', self.on_colaborador_changed)
    
    def on_colaborador_changed(self, *args):
        """Quando o colaborador muda, busca a matrícula correspondente pelo display label."""
        if self._updating:
            return

        display_label = self.vars['colaborador'].get().strip().upper()

        if display_label:
            mat = self._colab_display_to_mat.get(display_label, "")
            self.vars['colaborador_matricula'].set(mat)
        else:
            self.vars['colaborador_matricula'].set("")
    
    def verificar_cliente_existente(self, cliente, exclude_id=None):
        """Verifica se um cliente já existe no banco e retorna a matrícula associada
        Args:
            cliente: Nome do cliente a verificar
            exclude_id: ID do registro a excluir da verificação (para edição)
        """
        if not cliente:
            return None
        
        cliente_upper = cliente.upper().strip()
        
        # Verifica no dicionário em cache
        if cliente_upper in self.clientes_matriculas['cliente_to_matricula']:
            # Se for edição, verifica se o cliente está associado a outro registro
            if exclude_id is not None:
                try:
                    # Verifica se há outro registro com o mesmo cliente
                    self.parent.cursor.execute('''
                        SELECT id, matricula FROM registros 
                        WHERE UPPER(cliente) = ? AND id != ?
                        LIMIT 1
                    ''', (cliente_upper, exclude_id))
                    result = self.parent.cursor.fetchone()
                    if result:
                        return result[1].upper().strip() if result[1] else None
                except Exception as e:
                    print(f"Erro ao verificar cliente no banco: {e}")
                    return self.clientes_matriculas['cliente_to_matricula'].get(cliente_upper)
            else:
                return self.clientes_matriculas['cliente_to_matricula'].get(cliente_upper)
        
        # Verifica no banco diretamente (caso o cache não esteja atualizado)
        try:
            query = '''
                SELECT id, matricula FROM registros 
                WHERE UPPER(cliente) = ? AND matricula IS NOT NULL AND matricula != ''
            '''
            params = [cliente_upper]
            
            if exclude_id is not None:
                query += ' AND id != ?'
                params.append(exclude_id)
            
            query += ' LIMIT 1'
            
            self.parent.cursor.execute(query, params)
            result = self.parent.cursor.fetchone()
            
            if result:
                matricula = result[1].upper().strip() if result[1] else None
                return matricula
        except Exception as e:
            print(f"Erro ao verificar cliente no banco: {e}")
        
        return None
    
    def on_cliente_changed(self, *args):
        """Quando o cliente muda no modo SEM CADASTRO, verifica se a matrícula já pertence a outro cliente"""
        if self._updating:
            return
        
        tipo_cliente = self.vars['tipo_cliente'].get()
        
        # Só valida no modo SEM CADASTRO
        if tipo_cliente != "SEM CADASTRO":
            self._last_valid_cliente = self.vars['cliente'].get()
            return
        
        cliente = self.vars['cliente'].get()
        matricula_atual = self.vars['matricula'].get().upper().strip() if self.vars['matricula'].get() else ""
        
        if not cliente:
            self._last_valid_cliente = ""
            return
        
        cliente_upper = cliente.upper().strip()
        
        # Verifica se a MATRÍCULA atual já está associada a um cliente DIFERENTE do digitado
        # Isso impede usar uma matrícula já cadastrada para outro cliente
        if matricula_atual:
            cliente_da_matricula = self.clientes_matriculas.get('matricula_to_cliente', {}).get(matricula_atual)
            
            if cliente_da_matricula and cliente_da_matricula != cliente_upper:
                # A matrícula já pertence a outro cliente - bloquear alteração
                self._updating = True
                
                messagebox.showerror(
                    "Erro de Matrícula",
                    f"A matrícula {matricula_atual} já está cadastrada para o cliente:\n"
                    f"{cliente_da_matricula}\n\n"
                    f"Use o modo CADASTRADO ou use uma matrícula diferente."
                )
                
                # Reverte para o valor ORIGINAL do registro
                original_cliente = self.original_values.get('cliente', '') or ''
                self.vars['cliente'].set(original_cliente)
                self._last_valid_cliente = original_cliente
                self._updating = False
                return
        
        # NOTA: Não bloqueamos mais clientes com o mesmo nome e matrículas diferentes
        # Clientes homônimos são permitidos (assim como colaboradores)
        
        # Atualiza o último valor válido
        self._last_valid_cliente = cliente
    
    def verificar_matricula_existente(self, matricula, exclude_id=None):
        """Verifica se uma matrícula já existe no banco e retorna o cliente associado
        Args:
            matricula: Matrícula a verificar
            exclude_id: ID do registro a excluir da verificação (para edição)
        """
        if not matricula:
            return None
        
        matricula_upper = matricula.upper().strip()
        
        # Verifica no dicionário em cache (sem excluir ID)
        if matricula_upper in self.clientes_matriculas['matricula_to_cliente']:
            # Se for edição, verifica se a matrícula está associada a outro registro
            if exclude_id is not None:
                try:
                    # Verifica se há outro registro com a mesma matrícula
                    self.parent.cursor.execute('''
                        SELECT id, cliente FROM registros 
                        WHERE matricula = ? AND id != ?
                        LIMIT 1
                    ''', (matricula_upper, exclude_id))
                    result = self.parent.cursor.fetchone()
                    if result:
                        return result[1].upper().strip()
                except Exception as e:
                    print(f"Erro ao verificar matrícula no banco: {e}")
                    # Em caso de erro, retorna do cache
                    return self.clientes_matriculas['matricula_to_cliente'][matricula_upper]
            else:
                return self.clientes_matriculas['matricula_to_cliente'][matricula_upper]
        
        # Verifica no banco diretamente (caso o cache não esteja atualizado)
        try:
            query = '''
                SELECT id, cliente FROM registros 
                WHERE matricula = ? AND cliente IS NOT NULL AND cliente != ''
            '''
            params = (matricula_upper,)
            
            if exclude_id is not None:
                query += ' AND id != ?'
                params = (matricula_upper, exclude_id)
            
            query += ' LIMIT 1'
            
            self.parent.cursor.execute(query, params)
            result = self.parent.cursor.fetchone()
            if result:
                cliente = result[1].upper().strip()
                # Atualiza cache (apenas se não for exclusão)
                if exclude_id is None:
                    self.clientes_matriculas['matricula_to_cliente'][matricula_upper] = cliente
                    self.clientes_matriculas['cliente_to_matricula'][cliente] = matricula_upper
                    if matricula_upper not in self.clientes_matriculas['matriculas']:
                        self.clientes_matriculas['matriculas'].append(matricula_upper)
                        self.clientes_matriculas['matriculas'].sort()
                    if cliente not in self.clientes_matriculas['clientes']:
                        self.clientes_matriculas['clientes'].append(cliente)
                        self.clientes_matriculas['clientes'].sort()
                return cliente
        except Exception as e:
            print(f"Erro ao verificar matrícula no banco: {e}")
        
        return None
    
    def on_matricula_changed(self, *args):
        """Quando a matrícula muda, verifica se já existe e age conforme o modo"""
        if self._updating:
            return
        
        matricula = self.vars['matricula'].get()
        tipo_cliente = self.vars['tipo_cliente'].get()
        
        # Verifica se a matrícula já existe no banco
        if matricula and tipo_cliente == "SEM CADASTRO":
            cliente_existente = self.verificar_matricula_existente(matricula, self.record_id)
            
            if cliente_existente:
                # Pergunta ao usuário se quer usar o cliente já cadastrado
                resposta = messagebox.askyesno(
                    "Matrícula Já Cadastrada",
                    f"A matrícula {matricula.upper()} já está cadastrada para o cliente: {cliente_existente}\n\n"
                    f"Deseja usar o cliente cadastrado?"
                )
                
                if resposta:
                    # Muda para modo CADASTRADO e preenche os dados
                    self._updating = True
                    self.vars['tipo_cliente'].set("CADASTRADO")
                    self.vars['matricula'].set(matricula.upper().strip())
                    self.vars['cliente'].set(cliente_existente)
                    self._last_valid_cliente = cliente_existente
                    
                    # Atualiza a interface
                    self.on_tipo_cliente_changed(force_update=True)
                    self._updating = False
                    return
                else:
                    # Usuário recusou - reverter cliente para o valor ORIGINAL do registro
                    self._updating = True
                    original_cliente = self.original_values.get('cliente', '') or ''
                    self.vars['cliente'].set(original_cliente)
                    self._last_valid_cliente = original_cliente
                    self._updating = False
                    return
        
        # Preenchimento automático normal (modo CADASTRADO)
        if tipo_cliente == "CADASTRADO":
            matricula_clean = matricula.strip().upper()
            
            if matricula_clean:
                cliente_existente = self.verificar_matricula_existente(matricula_clean, self.record_id)
                if cliente_existente:
                    self._updating = True
                    self.vars['cliente'].set(cliente_existente)
                    self._last_valid_cliente = cliente_existente
                    self._updating = False
                elif matricula_clean in self.clientes_matriculas['matricula_to_cliente']:
                    # Se está no cache mas não no banco (considerando exclusão), usa cache
                    self._updating = True
                    cliente = self.clientes_matriculas['matricula_to_cliente'][matricula_clean]
                    self.vars['cliente'].set(cliente)
                    self._last_valid_cliente = cliente
                    self._updating = False
    
    def on_matricula_enter_pressed(self, valor_digitado=None):
        """Quando ENTER é pressionado no campo de matrícula (modo CADASTRADO)
        
        Funciona com:
        - Digitação manual + ENTER
        - Leitor de crachá (que envia ENTER automaticamente)
        
        Lógica:
        - Se matrícula existe no banco → preenche cliente automaticamente
        - Se não existe → muda para SEM CADASTRO
        """
        if self._updating:
            return
        
        # Usar valor passado ou pegar da variável
        if valor_digitado:
            matricula = valor_digitado.strip().upper()
        else:
            matricula = self.vars['matricula'].get().strip().upper()
        
        if not matricula:
            return
        
        # Buscar no banco se a matrícula existe
        cliente_existente = self.verificar_matricula_existente(matricula, self.record_id)
        
        if cliente_existente:
            # Matrícula encontrada - preencher cliente automaticamente
            self._updating = True
            self.vars['matricula'].set(matricula)
            self.vars['cliente'].set(cliente_existente)
            self._last_valid_cliente = cliente_existente
            self._updating = False
            
            # Mover foco para o próximo campo (Local)
            if hasattr(self, 'local_combo') and hasattr(self.local_combo, 'entry'):
                self.local_combo.entry.focus_set()
        else:
            # Matrícula NÃO encontrada - mudar para SEM CADASTRO
            resposta = messagebox.askyesno(
                "Matrícula Não Encontrada",
                f"A matrícula '{matricula}' não está cadastrada no sistema.\n\n"
                f"Deseja cadastrar um novo cliente com esta matrícula?\n"
                f"(Será alterado para modo 'SEM CADASTRO')"
            )
            
            if resposta:
                self._updating = True
                self.vars['tipo_cliente'].set("SEM CADASTRO")
                self.vars['matricula'].set(matricula)
                self.vars['cliente'].set("")  # Limpar cliente para preencher manualmente
                self._last_valid_cliente = ""
                
                # Atualizar interface
                self.on_tipo_cliente_changed(force_update=True)
                self._updating = False
                
                # Mover foco para o campo de cliente
                self.cliente_entry.focus_set()
            else:
                # Usuário cancelou - limpar matrícula
                self._updating = True
                self.vars['matricula'].set("")
                self._updating = False
    
    def on_tipo_cliente_changed(self, force_update=False):
        """Quando o tipo de cliente muda, atualiza a interface
        
        Args:
            force_update: Se True, força a atualização dos campos mesmo em modo edição
        """
        tipo = self.vars['tipo_cliente'].get()

        # Esconder todos os frames primeiro
        self.matricula_combo_frame.pack_forget()
        self.cliente_label_frame.pack_forget()
        self.matricula_entry_frame.pack_forget()
        self.cliente_entry_frame.pack_forget()
        if hasattr(self, 'busca_nome_frame'):
            self.busca_nome_frame.pack_forget()

        if tipo == "CADASTRADO":
            # Mostrar combo de matrícula e label do cliente
            self.matricula_combo_frame.pack(fill="x", pady=(0, 5))
            self.cliente_label_frame.pack(fill="x")
        elif tipo == "BUSCA_NOME":
            # Campo de busca por nome ACIMA + nome do cliente selecionado abaixo
            self.busca_nome_frame.pack(fill="x", pady=(0, 5))
            self.cliente_label_frame.pack(fill="x")
            # Popular a lista de resultados e focar o campo de busca
            self.on_busca_nome_changed()
            try:
                self.busca_nome_entry.focus_set()
            except Exception:
                pass
        else:
            # SEM CADASTRO: mostrar entries de matrícula e cliente
            self.matricula_entry_frame.pack(fill="x", pady=(0, 5))
            self.cliente_entry_frame.pack(fill="x")

        # Limpar campos ao trocar apenas se não estiver no modo edição ou se for forçado
        if self.mode == "new" or force_update:
            self._updating = True
            # Só limpa se os campos estiverem vazios no modo atual
            if tipo == "CADASTRADO" and not self.vars['matricula'].get():
                self.vars['cliente'].set("")
            elif tipo == "SEM CADASTRO" and not self.vars['matricula'].get():
                self.vars['cliente'].set("")
            elif tipo == "BUSCA_NOME":
                # Ao entrar no modo busca, limpa o termo de busca anterior
                self.vars['busca_nome'].set("")
            self._updating = False

    def on_busca_nome_changed(self, event=None):
        """Filtra os clientes cadastrados pelo nome digitado.

        Busca parcial e case-insensitive sobre todos os pares (nome, matrícula)
        conhecidos (inclui homônimos, pois cada matrícula é uma entrada distinta).
        """
        if getattr(self, 'busca_nome_results', None) is None:
            return

        termo = self.vars['busca_nome'].get().strip().upper()

        self.busca_nome_results.delete(0, tk.END)
        self._busca_nome_pairs = []

        # matricula_to_cliente preserva todas as matrículas (uma por linha),
        # portanto homônimos aparecem como resultados separados.
        pares = sorted(
            ((nome, mat) for mat, nome in
             self.clientes_matriculas.get('matricula_to_cliente', {}).items()),
            key=lambda x: (x[0], x[1])
        )

        matches = 0
        for nome, mat in pares:
            if termo and termo not in nome.upper():
                continue
            self._busca_nome_pairs.append((nome, mat))
            self.busca_nome_results.insert(tk.END, f"{nome}  —  {mat}")
            matches += 1
            if matches >= 100:
                break

        if matches == 0:
            self.busca_nome_results.insert(tk.END, "(nenhum cliente encontrado)")

    def on_busca_nome_select(self, event=None):
        """Preenche matrícula + nome a partir do resultado escolhido.

        Equivale à leitura do crachá: define matrícula e cliente e alterna para
        o modo CADASTRADO, exibindo os campos já preenchidos.
        """
        if getattr(self, 'busca_nome_results', None) is None:
            return
        sel = self.busca_nome_results.curselection()
        if not sel:
            return
        idx = sel[0]
        # Linha de placeholder ("nenhum cliente encontrado") não é selecionável
        if idx >= len(self._busca_nome_pairs):
            return

        nome, mat = self._busca_nome_pairs[idx]

        self._updating = True
        try:
            self.vars['matricula'].set(mat)
            self.vars['cliente'].set(nome)
            self._last_valid_cliente = nome
            # Alterna para o modo CADASTRADO para exibir os campos preenchidos
            self.vars['tipo_cliente'].set("CADASTRADO")
        finally:
            self._updating = False

        # Atualiza a interface (mostra combo de matrícula + nome do cliente)
        self.on_tipo_cliente_changed(force_update=False)

        # Move o foco para o próximo campo (Local), como no fluxo do crachá
        if hasattr(self, 'local_combo') and hasattr(self.local_combo, 'entry'):
            try:
                self.local_combo.entry.focus_set()
            except Exception:
                pass

    def _busca_nome_focus_results(self, event=None):
        """Seta ↓ no campo de busca: move o foco para a lista de resultados."""
        if self._busca_nome_pairs:
            self.busca_nome_results.focus_set()
            self.busca_nome_results.selection_clear(0, tk.END)
            self.busca_nome_results.selection_set(0)
            self.busca_nome_results.activate(0)
        return "break"

    def _busca_nome_select_first(self, event=None):
        """Enter no campo de busca: seleciona o primeiro resultado."""
        if self._busca_nome_pairs:
            self.busca_nome_results.selection_clear(0, tk.END)
            self.busca_nome_results.selection_set(0)
            self.busca_nome_results.activate(0)
            self.on_busca_nome_select()
        return "break"

    def load_record(self):
        """Carrega dados do registro para edição"""
        # SELECT com colunas explícitas para evitar problemas de ordem
        self.parent.cursor.execute('''
            SELECT id, data, colaborador, colaborador_matricula, equipamento, 
                   cliente, local, horario, tipo, matricula 
            FROM registros WHERE id = ?
        ''', (self.record_id,))
        record = self.parent.cursor.fetchone()
        
        # Estrutura: id, data, colaborador, colaborador_matricula, equipamento, 
        #            cliente, local, horario, tipo, matricula
        if record:
            self.vars['data'].set(record[1] or "")
            self.vars['colaborador'].set(record[2] or "")
            self.vars['colaborador_matricula'].set(record[3] or "")
            self.vars['equipamento'].set(record[4] or "")
            self.vars['quantidade'].set("1")  # Para edição, sempre 1
            self.vars['cliente'].set(record[5] or "")
            self.vars['local'].set(record[6] or "")
            self.vars['horario'].set(record[7] or "")
            self.vars['tipo'].set(record[8] or "ENTREGA")
            self.vars['matricula'].set(record[9] or "")
            
            # Se colaborador_matricula não estiver definida, tentar buscar
            if not record[3] and record[2]:
                try:
                    self.parent.cursor.execute(
                        "SELECT matricula FROM colaboradores WHERE nome = ? LIMIT 1",
                        (record[2],)
                    )
                    mat_result = self.parent.cursor.fetchone()
                    if mat_result:
                        self.vars['colaborador_matricula'].set(mat_result[0])
                except:
                    pass
            
            # Determinar se é cliente cadastrado ou não
            matricula = record[9] or ""
            cliente = record[5] or ""
            
            # Verifica se a matrícula existe no sistema (exceto no próprio registro)
            if matricula and self.verificar_matricula_existente(matricula, self.record_id):
                self.vars['tipo_cliente'].set("CADASTRADO")
            elif matricula and cliente:  # Se tem matrícula e cliente, mas não está no dicionário
                self.vars['tipo_cliente'].set("SEM CADASTRO")
            else:
                self.vars['tipo_cliente'].set("SEM CADASTRO")
            
            # Guardar valores originais para comparação
            self.original_values = {
                'data': record[1] or "",
                'colaborador': record[2] or "",
                'colaborador_matricula': record[3] or "",
                'equipamento': record[4] or "",
                'cliente': record[5] or "",
                'local': record[6] or "",
                'horario': record[7] or "",
                'tipo': record[8] or "",
                'matricula': record[9] or ""
            }
    
    def create_widgets(self):
        """Cria interface da janela de registro"""
        # Frame principal com scroll
        main_frame = ctk.CTkScrollableFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        self._main_frame_ref = main_frame
        self._main_scroll_canvas = getattr(main_frame, "_parent_canvas", None)
        
        title = ctk.CTkLabel(main_frame, 
                            text="NOVO REGISTRO" if self.mode == "new" else "EDITAR REGISTRO",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(0, 30))
        
        # Data
        ctk.CTkLabel(main_frame, text="Data *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        data_entry = ctk.CTkEntry(main_frame, textvariable=self.vars['data'], 
                    placeholder_text="Ex: 25/12/2023",
                    height=40)
        data_entry.pack(fill="x", pady=(0, 15))
        data_entry.bind('<KeyRelease>', self.parent.format_date_input)
        
        # Horário
        ctk.CTkLabel(main_frame, text="Horário *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        horario_entry = ctk.CTkEntry(main_frame, textvariable=self.vars['horario'], 
                    placeholder_text="Ex: 14:30",
                    height=40)
        horario_entry.pack(fill="x", pady=(0, 15))
        horario_entry.bind('<KeyRelease>', self.parent.format_time_input)
        
        # Colaborador
        ctk.CTkLabel(main_frame, text="Colaborador *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        colab_values = self.build_colaborador_display_list()
        # Em modo edição, garantir que o display label correto esteja selecionado
        if self.mode == "edit":
            nome_salvo = self.vars['colaborador'].get()
            mat_salva  = self.vars['colaborador_matricula'].get()
            display_label = self.get_display_label_for_record(nome_salvo, mat_salva)
            self._updating = True
            self.vars['colaborador'].set(display_label)
            self._updating = False
        colaborador_combo = ScrollableComboBox(main_frame, 
                       variable=self.vars['colaborador'],
                       values=colab_values, 
                       height=40,
                       max_visible_items=6,
                       app=self.parent,
                       item_tooltip_callback=self.get_colaborador_matricula_tooltip)
        colaborador_combo.pack(fill="x", pady=(0, 15))
        
        # === SEÇÃO EQUIPAMENTO E QUANTIDADE ===

        # Linha 1: checkbox Múltiplos (só no modo novo)
        if self.mode == "new":
            multi_row = ctk.CTkFrame(main_frame, fg_color="transparent")
            multi_row.pack(fill="x", pady=(10, 0))
            ctk.CTkCheckBox(
                multi_row,
                text="Múltiplos Equipamentos",
                variable=self._multi_equip_var,
                font=ctk.CTkFont(size=12),
                fg_color="#3b82f6",
                hover_color="#2563eb",
                command=self._on_multi_equip_toggled
            ).pack(side="left")

        # Container fixo — mantém posição no layout
        self._equip_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        self._equip_container.pack(fill="x", pady=(5, 15))

        # ── Painel simples (padrão) ──────────────────────────────────────────
        self._equip_single_panel = ctk.CTkFrame(self._equip_container, fg_color="transparent")
        self._equip_single_panel.pack(fill="x")

        equip_left = ctk.CTkFrame(self._equip_single_panel, fg_color="transparent", width=350)
        equip_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        qty_right = ctk.CTkFrame(self._equip_single_panel, fg_color="transparent", width=120)
        qty_right.pack(side="right", fill="both")

        ctk.CTkLabel(equip_left, text="Equipamento *",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        ScrollableComboBox(equip_left,
                           variable=self.vars['equipamento'],
                           values=self.parent.get_items("equipamentos"),
                           height=40, max_visible_items=6,
                           app=self.parent).pack(fill="x")

        ctk.CTkLabel(qty_right, text="Quantidade",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))

        def validate_quantidade(P):
            return P == "" or P.isdigit()

        if self.mode == "new":
            _qty_entry = ctk.CTkEntry(qty_right, textvariable=self.vars['quantidade'],
                        placeholder_text="Ex: 1", height=40, justify="center")
            _qty_entry.pack(fill="x")
            vcmd = (self.window.register(validate_quantidade), '%P')
            _qty_entry.configure(validate="key", validatecommand=vcmd)
        else:
            ctk.CTkEntry(qty_right, textvariable=self.vars['quantidade'],
                        height=40, justify="center", state="disabled",
                        fg_color="#e5e5e5", text_color="#374151").pack(fill="x")
            ctk.CTkLabel(qty_right, text="(Edição unitária)",
                        font=ctk.CTkFont(size=11),
                        text_color="#6b7280").pack(anchor="center", pady=(2, 0))

        # ── Painel múltiplos (oculto por padrão) ────────────────────────────
        self._equip_multi_panel = ctk.CTkFrame(
            self._equip_container,
            fg_color=("#f8fafc", "#1f2937"),
            border_width=1,
            border_color=("#cbd5e1", "#475569"),
            corner_radius=8
        )
        self._build_multi_equip_ui()
        
        # === SEÇÃO CLIENTE ===
        # Separador
        separator1 = ctk.CTkFrame(main_frame, height=2, fg_color="#475569")
        separator1.pack(fill="x", pady=15)
        
        # Label Cliente
        ctk.CTkLabel(main_frame, text="Cliente", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 10))
        
        # Radiobuttons para tipo de cliente
        tipo_cliente_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tipo_cliente_frame.pack(fill="x", pady=(0, 10))
        
        self.radio_cadastrado = ctk.CTkRadioButton(tipo_cliente_frame, 
                                                   text="CADASTRADO", 
                                                   variable=self.vars['tipo_cliente'], 
                                                   value="CADASTRADO",
                                                   font=ctk.CTkFont(size=13),
                                                   fg_color="#3b82f6",
                                                   hover_color="#2563eb",
                                                   command=lambda: self.on_tipo_cliente_changed(force_update=True))
        self.radio_cadastrado.pack(side="left", padx=(0, 30))
        
        self.radio_sem_cadastro = ctk.CTkRadioButton(tipo_cliente_frame,
                                                     text="SEM CADASTRO",
                                                     variable=self.vars['tipo_cliente'],
                                                     value="SEM CADASTRO",
                                                     font=ctk.CTkFont(size=13),
                                                   fg_color="#6b7280",
                                                   hover_color="#4b5563",
                                                   command=lambda: self.on_tipo_cliente_changed(force_update=True))
        self.radio_sem_cadastro.pack(side="left")

        # NOVO: busca do cliente cadastrado pelo NOME (quando nao ha o cracha)
        self.radio_busca_nome = ctk.CTkRadioButton(tipo_cliente_frame,
                                                   text="POR NOME",
                                                   variable=self.vars['tipo_cliente'],
                                                   value="BUSCA_NOME",
                                                   font=ctk.CTkFont(size=13),
                                                   fg_color="#10b981",
                                                   hover_color="#059669",
                                                   command=lambda: self.on_tipo_cliente_changed(force_update=True))
        self.radio_busca_nome.pack(side="left", padx=(30, 0))
        
        # === CONTAINER FIXO PARA CAMPOS DE CLIENTE ===
        # Este frame mantém a posição fixa e contém ambos os modos
        self.cliente_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.cliente_container.pack(fill="x", pady=(0, 15))
        
        # === MODO CADASTRADO: ComboBox de Matrícula + Label Cliente ===
        
        # Frame para ComboBox de Matrícula (CADASTRADO)
        self.matricula_combo_frame = ctk.CTkFrame(self.cliente_container, fg_color="transparent")
        
        ctk.CTkLabel(self.matricula_combo_frame, text="Matrícula:", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        self.matricula_combo = ScrollableComboBox(self.matricula_combo_frame, 
                       variable=self.vars['matricula'],
                       values=self.clientes_matriculas['matriculas'], 
                       height=40,
                       max_visible_items=6,
                       app=self.parent,
                       on_enter_callback=self.on_matricula_enter_pressed,
                       numeric_only=True)
        self.matricula_combo.pack(fill="x")
        
        # Frame para Label do Cliente (CADASTRADO)
        self.cliente_label_frame = ctk.CTkFrame(self.cliente_container, fg_color="transparent")
        
        ctk.CTkLabel(self.cliente_label_frame, text="Nome do Cliente:", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 3))
        self.cliente_display = ctk.CTkEntry(self.cliente_label_frame, 
                                           textvariable=self.vars['cliente'],
                                           height=40,
                                           state="disabled",
                                           fg_color="#e5e5e5",
                                           text_color="#374151")
        self.cliente_display.pack(fill="x")
        
        # === MODO SEM CADASTRO: Entry Matrícula + Entry Cliente ===
        
        # Frame para Entry Matrícula (SEM CADASTRO)
        self.matricula_entry_frame = ctk.CTkFrame(self.cliente_container, fg_color="transparent")
        
        ctk.CTkLabel(self.matricula_entry_frame, text="Matrícula:", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        self.matricula_entry = ctk.CTkEntry(self.matricula_entry_frame, 
                                           textvariable=self.vars['matricula'],
                                           placeholder_text="Digite a matrícula",
                                           height=40)
        self.matricula_entry.pack(fill="x")
        
        # Validação: aceitar apenas números e caracteres especiais (-, /)
        self.matricula_entry.bind('<KeyPress>', self.validate_matricula_keypress)
        
        # Frame para Entry Cliente (SEM CADASTRO)
        self.cliente_entry_frame = ctk.CTkFrame(self.cliente_container, fg_color="transparent")
        
        ctk.CTkLabel(self.cliente_entry_frame, text="Nome do Cliente:", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(5, 3))
        self.cliente_entry = ctk.CTkEntry(self.cliente_entry_frame, 
                                         textvariable=self.vars['cliente'],
                                         placeholder_text="Digite o nome do cliente",
                                         height=40)
        self.cliente_entry.pack(fill="x")
        self.cliente_entry.bind('<KeyRelease>', self.parent.make_uppercase)

        # === MODO BUSCA POR NOME: campo de busca ACIMA + lista de resultados ===
        # Localiza um cliente ja cadastrado pelo NOME (parcial, case-insensitive)
        # quando o cracha/matricula nao esta em maos. Ao escolher um resultado,
        # a matricula e o nome sao preenchidos como se o cracha tivesse sido lido.
        self.busca_nome_frame = ctk.CTkFrame(self.cliente_container, fg_color="transparent")

        ctk.CTkLabel(self.busca_nome_frame, text="Buscar por nome:",
                    font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        self.busca_nome_entry = ctk.CTkEntry(self.busca_nome_frame,
                                            textvariable=self.vars['busca_nome'],
                                            placeholder_text="Digite parte do nome do cliente",
                                            height=40)
        self.busca_nome_entry.pack(fill="x")
        self.busca_nome_entry.bind('<KeyRelease>', self.on_busca_nome_changed)
        self.busca_nome_entry.bind('<Down>', self._busca_nome_focus_results)
        self.busca_nome_entry.bind('<Return>', self._busca_nome_select_first)

        # Lista de resultados (tkinter puro: leve e sem vazamento de recursos)
        results_container = tk.Frame(self.busca_nome_frame, bg="#e5e5e5")
        results_container.pack(fill="x", pady=(6, 0))
        self.busca_nome_results = tk.Listbox(results_container, height=5,
                                            activestyle="dotbox",
                                            font=("Segoe UI", 10),
                                            highlightthickness=1,
                                            highlightbackground="#cccccc",
                                            exportselection=False)
        results_scroll = tk.Scrollbar(results_container, orient="vertical",
                                      command=self.busca_nome_results.yview)
        self.busca_nome_results.configure(yscrollcommand=results_scroll.set)
        self.busca_nome_results.pack(side="left", fill="both", expand=True)
        results_scroll.pack(side="right", fill="y")
        self.busca_nome_results.bind('<Double-Button-1>', self.on_busca_nome_select)
        self.busca_nome_results.bind('<Return>', self.on_busca_nome_select)

        # Pares (nome, matricula) correspondentes a cada linha exibida na lista
        self._busca_nome_pairs = []

        # Inicializar visibilidade conforme tipo_cliente, mas sem limpar dados em edição
        if self.mode == "edit":
            # Forçar a atualização da interface sem limpar dados
            self._updating = True
            tipo = self.vars['tipo_cliente'].get()
            
            # Esconder todos os frames primeiro
            self.matricula_combo_frame.pack_forget()
            self.cliente_label_frame.pack_forget()
            self.matricula_entry_frame.pack_forget()
            self.cliente_entry_frame.pack_forget()
            self.busca_nome_frame.pack_forget()

            if tipo == "CADASTRADO":
                # Mostrar combo de matrícula e label do cliente
                self.matricula_combo_frame.pack(fill="x", pady=(0, 5))
                self.cliente_label_frame.pack(fill="x")
            else:
                # Mostrar entries de matrícula e cliente
                self.matricula_entry_frame.pack(fill="x", pady=(0, 5))
                self.cliente_entry_frame.pack(fill="x")

            self._updating = False
        else:
            self.on_tipo_cliente_changed()
        
        # Separador
        separator2 = ctk.CTkFrame(main_frame, height=2, fg_color="#475569")
        separator2.pack(fill="x", pady=15)
        
        # Local
        ctk.CTkLabel(main_frame, text="Local *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        self.local_combo = ScrollableComboBox(main_frame, 
                       variable=self.vars['local'],
                       values=self.parent.get_items("locais"), 
                       height=40,
                       max_visible_items=6,
                       app=self.parent)
        self.local_combo.pack(fill="x", pady=(0, 15))
        
        # Tipo (ENTREGA ou RETIRADA)
        ctk.CTkLabel(main_frame, text="Tipo de Movimentação *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        tipo_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tipo_frame.pack(fill="x", pady=(0, 15))
        
        # Radiobuttons para tipo
        self.radio_entrega = ctk.CTkRadioButton(tipo_frame, 
                                                text="ENTREGA", 
                                                variable=self.vars['tipo'], 
                                                value="ENTREGA",
                                                font=ctk.CTkFont(size=14),
                                                fg_color="#ef4444",
                                                hover_color="#dc2626")
        self.radio_entrega.pack(side="left", padx=(0, 30))
        
        self.radio_retirada = ctk.CTkRadioButton(tipo_frame, 
                                                 text="RETIRADA", 
                                                 variable=self.vars['tipo'], 
                                                 value="RETIRADA",
                                                 font=ctk.CTkFont(size=14),
                                                fg_color="#f59e0b",
                                                hover_color="#d97706")
        self.radio_retirada.pack(side="left")
        
        # Legenda de cores
        legenda_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        legenda_frame.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(legenda_frame, 
                    text="🔴 ENTREGA = Equipamento volta ao estoque ou é descartado",
                    font=ctk.CTkFont(size=11),
                    text_color="#ef4444").pack(anchor="w")
        
        ctk.CTkLabel(legenda_frame, 
                    text="🟡 RETIRADA = Equipamento sai do estoque",
                    font=ctk.CTkFont(size=11),
                    text_color="#f59e0b").pack(anchor="w")
        
        # Botões
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(btn_frame, text="SALVAR REGISTRO", 
                     command=self.save_record,
                     fg_color="#10b981", hover_color="#059669",
                     height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="CANCELAR", 
                     command=self.window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563",
                     height=45).pack(fill="x")

        self._setup_scroll_routing()
    
    def _bind_mousewheel_recursively(self, widget, callback):
        """Aplica o bind de scroll no widget e em todos os filhos."""
        if widget is None:
            return

        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                widget.bind(sequence, callback, add="+")
            except Exception:
                pass

        try:
            children = widget.winfo_children()
        except Exception:
            children = []

        for child in children:
            self._bind_mousewheel_recursively(child, callback)

    def _get_scroll_pixels(self, event):
        """Converte o wheel em deslocamento vertical mais fluido."""
        step = getattr(self, "_scroll_step_pixels", 38)
        event_num = getattr(event, "num", None)
        if event_num == 4:
            return -step
        if event_num == 5:
            return step

        delta = getattr(event, "delta", 0)
        if not delta:
            return 0

        return (-delta / 120.0) * step

    def _scroll_canvas_smooth(self, canvas, pixels):
        """Aplica scroll suave no canvas usando fração da área total."""
        if canvas is None or not pixels:
            return False

        try:
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if not bbox:
                return False

            content_height = max(0, bbox[3] - bbox[1])
            viewport_height = max(1, canvas.winfo_height())
            max_scroll = max(0, content_height - viewport_height)
            if max_scroll <= 0:
                return False

            start_fraction = canvas.yview()[0]
            current_offset = start_fraction * max_scroll
            new_offset = min(max(current_offset + pixels, 0), max_scroll)
            if new_offset == current_offset:
                return False

            canvas.yview_moveto(new_offset / max_scroll)
            return True
        except Exception:
            return False

    def _is_pointer_inside_widget(self, widget, x_root=None, y_root=None):
        """Verifica se o ponteiro está dentro da área visível de um widget."""
        if widget is None:
            return False

        try:
            if not widget.winfo_exists() or not widget.winfo_ismapped():
                return False

            if x_root is None:
                x_root = self.window.winfo_pointerx()
            if y_root is None:
                y_root = self.window.winfo_pointery()

            left = widget.winfo_rootx()
            top = widget.winfo_rooty()
            right = left + widget.winfo_width()
            bottom = top + widget.winfo_height()
            return left <= x_root < right and top <= y_root < bottom
        except Exception:
            return False

    def _resolve_scroll_target(self, event=None):
        """Decide se o scroll vai para a janela principal ou para a lista de equipamentos."""
        x_root = getattr(event, "x_root", None) if event is not None else None
        y_root = getattr(event, "y_root", None) if event is not None else None

        if (
            self.mode == "new"
            and self._multi_equip_var.get()
            and self._equip_scroll_canvas is not None
            and self._is_pointer_inside_widget(self._equip_multi_panel, x_root, y_root)
        ):
            return self._equip_scroll_canvas

        return self._main_scroll_canvas

    def _route_mousewheel(self, event):
        """Roteia o scroll do mouse conforme a área atual do cursor."""
        canvas = self._resolve_scroll_target(event)
        if canvas is None:
            return None

        pixels = self._get_scroll_pixels(event)
        if self._scroll_canvas_smooth(canvas, pixels):
            return "break"

        return None

    def _setup_scroll_routing(self):
        """Garante que toda a janela responda ao scroll principal."""
        self.window.update_idletasks()
        self._bind_mousewheel_recursively(self.window, self._route_mousewheel)

        if self._main_scroll_canvas is not None:
            for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                try:
                    self._main_scroll_canvas.bind(sequence, self._route_mousewheel, add="+")
                except Exception:
                    pass

    def _build_multi_equip_ui(self):
        """Constrói a lista de equipamentos com checkbox + quantidade."""
        for w in self._equip_multi_panel.winfo_children():
            w.destroy()
        self._equip_check_vars  = {}
        self._equip_qty_vars    = {}
        self._equip_qty_entries = {}

        equipamentos = self.parent.get_items("equipamentos")

        scroll = ctk.CTkScrollableFrame(
            self._equip_multi_panel,
            height=200,
            fg_color="transparent"
        )
        scroll.pack(fill="x", padx=10, pady=10)
        self._equip_scroll_canvas = getattr(scroll, "_parent_canvas", None)

        # Cabeçalho
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Equipamento",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(hdr, text="Qtd",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=65, anchor="center").pack(side="right")

        vcmd = (self.window.register(lambda P: P == "" or P.isdigit()), '%P')

        def make_toggle(nome):
            def _toggle():
                entry = self._equip_qty_entries.get(nome)
                if entry:
                    if self._equip_check_vars[nome].get():
                        entry.configure(state="normal",
                                        fg_color=("white", "#2b2b2b"),
                                        text_color=("black", "white"))
                    else:
                        entry.configure(state="disabled",
                                        fg_color="#e5e5e5",
                                        text_color="#374151")
            return _toggle

        for equip in equipamentos:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            chk_var = ctk.BooleanVar(value=False)
            qty_var = ctk.StringVar(value="1")
            self._equip_check_vars[equip] = chk_var
            self._equip_qty_vars[equip]   = qty_var

            chk = ctk.CTkCheckBox(row, text=equip, variable=chk_var,
                            font=ctk.CTkFont(size=12),
                            fg_color="#3b82f6", hover_color="#2563eb",
                            command=make_toggle(equip))
            chk.pack(side="left", fill="x", expand=True)

            entry = ctk.CTkEntry(row, textvariable=qty_var,
                                 width=65, height=30, justify="center",
                                 state="disabled", fg_color="#e5e5e5",
                                 text_color="#374151")
            entry.configure(validate="key", validatecommand=vcmd)
            entry.pack(side="right")
            self._equip_qty_entries[equip] = entry

    def _on_multi_equip_toggled(self):
        """Alterna entre painel simples e painel múltiplos."""
        if self._multi_equip_var.get():
            self._equip_single_panel.pack_forget()
            self._equip_multi_panel.pack(fill="x")
        else:
            self._equip_multi_panel.pack_forget()
            self._equip_single_panel.pack(fill="x")

    def validate_fields(self):
        """Valida os campos de data e horário"""
        errors = []
        
        # Validar data
        if not self.parent.validate_date(self.vars['data'].get()):
            errors.append("Data inválida. Use o formato DD/MM/AAAA")
        
        # Validar horário
        if not self.parent.validate_time(self.vars['horario'].get()):
            errors.append("Horário inválido. Use o formato HH:MM")
        
        # Validar equipamento / quantidade (apenas para novo registro)
        if self.mode == "new":
            if self._multi_equip_var.get():
                selecionados = [e for e, v in self._equip_check_vars.items() if v.get()]
                if not selecionados:
                    errors.append("Selecione ao menos um equipamento")
                else:
                    for equip in selecionados:
                        qty_str = self._equip_qty_vars[equip].get().strip()
                        if not qty_str or not qty_str.isdigit() or int(qty_str) < 1:
                            errors.append(f"Quantidade inválida para: {equip}")
                        elif int(qty_str) > 100:
                            errors.append(f"Quantidade máxima é 100 para: {equip}")
            else:
                quantidade_str = self.vars['quantidade'].get().strip()
                if not quantidade_str:
                    errors.append("Quantidade é obrigatória")
                elif not quantidade_str.isdigit():
                    errors.append("Quantidade deve ser um número inteiro")
                else:
                    quantidade = int(quantidade_str)
                    if quantidade < 1:
                        errors.append("Quantidade deve ser maior que 0")
                    elif quantidade > 100:
                        errors.append("Quantidade máxima permitida é 100")
        
        return errors
    
    def validate_matricula_keypress(self, event):
        """Valida teclas pressionadas no campo de matrícula - aceita apenas números"""
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
    
    def validate_matricula_cliente(self):
        """Valida se a matrícula não está sendo usada por outro cliente
        e se no modo CADASTRADO a matrícula corresponde ao cliente"""
        matricula = self.vars['matricula'].get().strip().upper()
        cliente = self.vars['cliente'].get().strip().upper()
        tipo_cliente = self.vars['tipo_cliente'].get()
        
        # Se não há matrícula, não há o que validar
        if not matricula:
            return None
        
        # Em modo edição, precisamos verificar mesmo se a matrícula não mudou
        # porque o cliente pode estar sendo alterado
        exclude_id = self.record_id if self.mode == "edit" else None
        
        # Verifica se a matrícula já existe (excluindo o registro atual em edição)
        cliente_existente = self.verificar_matricula_existente(matricula, exclude_id)
        
        if cliente_existente:
            # Se estamos no modo SEM CADASTRO e a matrícula já existe para OUTRO cliente, é um erro
            # MAS se o cliente é o mesmo (homônimo com mesma matrícula), permite
            if tipo_cliente == "SEM CADASTRO" and cliente != cliente_existente:
                return f"A matrícula {matricula} já está cadastrada para o cliente: {cliente_existente}\nUse o modo CADASTRADO ou use uma matrícula diferente."
            
            # Se estamos no modo CADASTRADO mas o cliente é diferente, também é um erro
            if tipo_cliente == "CADASTRADO" and cliente != cliente_existente:
                # Em modo edição, se a matrícula original era diferente, pode ser que esteja corrigindo
                if self.mode == "edit" and self.original_values.get('matricula', '').upper() != matricula:
                    return f"A matrícula {matricula} já está associada ao cliente: {cliente_existente}\nNão pode ser associada a um cliente diferente."
                elif self.mode == "new":
                    return f"A matrícula {matricula} já está associada ao cliente: {cliente_existente}\nNão pode ser associada a um cliente diferente."
        
        # Validação adicional: no modo CADASTRADO, o cliente deve estar preenchido
        if tipo_cliente == "CADASTRADO" and not cliente:
            return "No modo CADASTRADO, o campo cliente deve ser preenchido automaticamente pela matrícula."
        
        # VALIDAÇÃO EXTRA: No modo CADASTRADO, verificar se matrícula corresponde ao cliente selecionado
        if tipo_cliente == "CADASTRADO" and matricula and cliente:
            # Buscar qual cliente deveria ter essa matrícula
            cliente_correto = self.clientes_matriculas.get('matricula_to_cliente', {}).get(matricula)
            
            # Se não está no cache, buscar no banco
            if not cliente_correto:
                try:
                    self.parent.cursor.execute('''
                        SELECT cliente FROM registros 
                        WHERE matricula = ? AND cliente IS NOT NULL AND cliente != ''
                        LIMIT 1
                    ''', (matricula,))
                    result = self.parent.cursor.fetchone()
                    if result:
                        cliente_correto = result[0].upper().strip()
                except:
                    pass
            
            # Se encontrou um cliente associado e é diferente do selecionado, erro
            if cliente_correto and cliente_correto != cliente:
                return (f"Inconsistência detectada!\n\n"
                        f"Matrícula: {matricula}\n"
                        f"Cliente esperado: {cliente_correto}\n"
                        f"Cliente informado: {cliente}\n\n"
                        f"No modo CADASTRADO, a matrícula deve corresponder ao cliente.")
        
        # NOTA: Não validamos mais se o cliente já existe com outra matrícula
        # Clientes homônimos são permitidos (assim como colaboradores)
        # Cada cliente pode ter sua própria matrícula, mesmo com nomes iguais
        
        return None
    
    def save_record(self):
        """Salva o registro (ou múltiplos registros se quantidade > 1)"""
        # Validar campos primeiro
        validation_errors = self.validate_fields()
        if validation_errors:
            messagebox.showerror("Erro de Validação", "\n".join(validation_errors))
            return
        
        # Validar matrícula para evitar duplicidade
        matricula_error = self.validate_matricula_cliente()
        if matricula_error:
            messagebox.showerror("Erro de Matrícula", matricula_error)
            return
        
        equip_ok = (
            any(v.get() for v in self._equip_check_vars.values())
            if (self.mode == "new" and self._multi_equip_var.get())
            else bool(self.vars['equipamento'].get())
        )
        if not all([self.vars['data'].get(),
                   self.vars['colaborador'].get(),
                   self.vars['local'].get(),
                   self.vars['horario'].get(),
                   self.vars['tipo'].get()]) or not equip_ok:
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios marcados com *")
            return
        
        # Preparar valores comuns
        colab_display = self.vars['colaborador'].get().strip().upper()
        colab_nome_real = self._colab_display_to_nome.get(colab_display, colab_display)

        common_values = {
            'data': self.vars['data'].get(),
            'colaborador': colab_nome_real,
            'colaborador_matricula': self.vars['colaborador_matricula'].get().upper() if self.vars['colaborador_matricula'].get() else "",
            'equipamento': self.vars['equipamento'].get().upper(),
            'cliente': self.vars['cliente'].get().upper() if self.vars['cliente'].get() else "",
            'matricula': self.vars['matricula'].get().upper() if self.vars['matricula'].get() else "",
            'local': self.vars['local'].get().upper(),
            'horario': self.vars['horario'].get(),
            'tipo': self.vars['tipo'].get()
        }

        campo_labels = {
            'data': 'Data', 'colaborador': 'Colaborador',
            'colaborador_matricula': 'Matrícula Colaborador',
            'equipamento': 'Equipamento', 'cliente': 'Cliente',
            'matricula': 'Matrícula', 'local': 'Local',
            'horario': 'Horário', 'tipo': 'Tipo'
        }

        def _insert_registros(equip, quantidade):
            criados = 0
            for _ in range(quantidade):
                self.parent.cursor.execute('''
                    INSERT INTO registros (data, colaborador, colaborador_matricula, equipamento,
                                          cliente, local, horario, tipo, matricula)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (common_values['data'], common_values['colaborador'],
                      common_values['colaborador_matricula'] or None, equip,
                      common_values['cliente'] or None, common_values['local'],
                      common_values['horario'], common_values['tipo'],
                      common_values['matricula'] or None))
                new_id = self.parent.cursor.lastrowid
                criados += 1
                try:
                    self.parent.cursor.execute('''
                        INSERT INTO registro_historico
                        (registro_id, campo_alterado, valor_anterior, valor_novo,
                         data_alteracao, tipo_operacao)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (new_id, 'Registro', None,
                          f"Colaborador: {common_values['colaborador']}, Equipamento: {equip}, "
                          f"Cliente: {common_values['cliente'] or '(vazio)'}, "
                          f"Matrícula: {common_values['matricula'] or '(vazio)'}, "
                          f"Local: {common_values['local']}, Tipo: {common_values['tipo']}",
                          datetime.now().strftime('%d/%m/%Y %H:%M:%S'), 'CRIAÇÃO'))
                except Exception as e:
                    print(f"Aviso: Não foi possível registrar histórico: {e}")
            return criados

        if self.mode == "new":
            total_criados = 0
            if self._multi_equip_var.get():
                for equip, chk_var in self._equip_check_vars.items():
                    if chk_var.get():
                        try:
                            qty = int(self._equip_qty_vars[equip].get().strip())
                        except:
                            qty = 1
                        total_criados += _insert_registros(equip.upper(), qty)
            else:
                try:
                    quantidade = int(self.vars['quantidade'].get().strip())
                except:
                    quantidade = 1
                total_criados = _insert_registros(common_values['equipamento'], quantidade)

            self.parent.conn.commit()

            if common_values['matricula'] and common_values['cliente']:
                self.clientes_matriculas['matricula_to_cliente'][common_values['matricula']] = common_values['cliente']
                self.clientes_matriculas['cliente_to_matricula'][common_values['cliente']] = common_values['matricula']
                if common_values['matricula'] not in self.clientes_matriculas['matriculas']:
                    self.clientes_matriculas['matriculas'].append(common_values['matricula'])
                    self.clientes_matriculas['matriculas'].sort()
                if common_values['cliente'] not in self.clientes_matriculas['clientes']:
                    self.clientes_matriculas['clientes'].append(common_values['cliente'])
                    self.clientes_matriculas['clientes'].sort()

            if total_criados == 1:
                messagebox.showinfo("Sucesso", "Registro salvo com sucesso!")
            else:
                messagebox.showinfo("Sucesso", f"{total_criados} registros criados com sucesso!")
            
        else:
            # MODO EDIÇÃO - Registrar alterações no histórico (apenas 1 registro)
            self.parent.cursor.execute('''
                UPDATE registros 
                SET data=?, colaborador=?, colaborador_matricula=?, equipamento=?, cliente=?, 
                    local=?, horario=?, tipo=?, matricula=?
                WHERE id=?
            ''', (common_values['data'], 
                  common_values['colaborador'],
                  common_values['colaborador_matricula'] or None,
                  common_values['equipamento'],
                  common_values['cliente'] or None,
                  common_values['local'],
                  common_values['horario'],
                  common_values['tipo'],
                  common_values['matricula'] or None,
                  self.record_id))
            
            # Comparar e registrar cada campo alterado (usando a mesma conexão)
            for campo, novo_valor in common_values.items():
                antigo_valor = self.original_values.get(campo, "")
                
                # Normalizar para comparação (tratar None e "" como iguais)
                antigo_norm = (antigo_valor or "").strip().upper() if campo in ['colaborador', 'colaborador_matricula', 'equipamento', 'cliente', 'local', 'matricula'] else (antigo_valor or "").strip()
                novo_norm = (novo_valor or "").strip()
                
                if antigo_norm != novo_norm:
                    try:
                        self.parent.cursor.execute('''
                            INSERT INTO registro_historico 
                            (registro_id, campo_alterado, valor_anterior, valor_novo, 
                             data_alteracao, tipo_operacao)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (self.record_id, 
                              campo_labels.get(campo, campo), 
                              antigo_valor or "(vazio)", 
                              novo_valor or "(vazio)",
                              datetime.now().strftime('%d/%m/%Y %H:%M:%S'), 
                              'EDIÇÃO'))
                    except Exception as e:
                        print(f"Aviso: Não foi possível registrar histórico de edição: {e}")
            
            self.parent.conn.commit()
            
            # Atualizar cache se necessário
            if (common_values['matricula'] and common_values['cliente'] and 
                (common_values['matricula'] != self.original_values.get('matricula', '').upper() or
                 common_values['cliente'] != self.original_values.get('cliente', '').upper())):
                
                # Remover associações antigas do cache
                old_matricula = self.original_values.get('matricula', '').upper()
                old_cliente = self.original_values.get('cliente', '').upper()
                
                if old_matricula in self.clientes_matriculas['matricula_to_cliente']:
                    del self.clientes_matriculas['matricula_to_cliente'][old_matricula]
                if old_cliente in self.clientes_matriculas['cliente_to_matricula']:
                    del self.clientes_matriculas['cliente_to_matricula'][old_cliente]
                
                # Adicionar novas associações
                self.clientes_matriculas['matricula_to_cliente'][common_values['matricula']] = common_values['cliente']
                self.clientes_matriculas['cliente_to_matricula'][common_values['cliente']] = common_values['matricula']
                
                # Atualizar listas
                if common_values['matricula'] not in self.clientes_matriculas['matriculas']:
                    self.clientes_matriculas['matriculas'].append(common_values['matricula'])
                    self.clientes_matriculas['matriculas'].sort()
                if common_values['cliente'] not in self.clientes_matriculas['clientes']:
                    self.clientes_matriculas['clientes'].append(common_values['cliente'])
                    self.clientes_matriculas['clientes'].sort()
                
                # Remover antigos se não estiverem mais em uso
                if old_matricula and old_matricula not in self.clientes_matriculas['matricula_to_cliente']:
                    if old_matricula in self.clientes_matriculas['matriculas']:
                        self.clientes_matriculas['matriculas'].remove(old_matricula)
                if old_cliente and old_cliente not in self.clientes_matriculas['cliente_to_matricula']:
                    if old_cliente in self.clientes_matriculas['clientes']:
                        self.clientes_matriculas['clientes'].remove(old_cliente)
            
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
        
        self.parent.load_main_data()
        self.parent.update_filters()
        
        self.window.destroy()
    
    def archive_record(self):
        """Arquiva registro em arquivo mensal"""
        mes_registro = datetime.strptime(self.vars['data'].get(), "%d/%m/%Y").strftime("%Y-%m")
        arquivo = f"arquivos_mensais/registros_{mes_registro}.json"
        
        # Criar diretório se não existir
        if not os.path.exists("arquivos_mensais"):
            os.makedirs("arquivos_mensais")
        
        # Carregar registros existentes ou criar nova lista
        registros = []
        if os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
            except:
                registros = []
        
        # Gerar novo ID
        novo_id = 1
        if registros:
            ids = [r[0] for r in registros if isinstance(r, list) and len(r) > 0]
            if ids:
                novo_id = max(ids) + 1
        
        # Criar novo registro
        # Estrutura: id, data, colaborador, equipamento, cliente, local, horario, tipo, matricula
        novo_registro = [
            novo_id,
            self.vars['data'].get(),
            self.vars['colaborador'].get().upper(),
            self.vars['equipamento'].get().upper(),
            self.vars['cliente'].get().upper() if self.vars['cliente'].get() else None,
            self.vars['local'].get().upper(),
            self.vars['horario'].get(),
            self.vars['tipo'].get(),
            self.vars['matricula'].get().upper() if self.vars['matricula'].get() else None
        ]
        
        registros.append(novo_registro)
        
        # Salvar arquivo
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(registros, f, indent=4, ensure_ascii=False)