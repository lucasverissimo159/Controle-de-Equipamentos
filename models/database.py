"""
Gerenciamento de banco de dados com suporte a histórico
Sistema de Controle de Equipamentos
Cria e gerencia todas as tabelas do sistema
"""
import sqlite3
from datetime import datetime


class Database:
    """Classe para gerenciar banco de dados"""
    
    def __init__(self, db_name='equip_control.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_all_tables()
        self.migrate_database()
    
    def create_all_tables(self):
        """Cria TODAS as tabelas do sistema se não existirem"""
        
        # Tabela de colaboradores - COM MATRÍCULA (identificador único)
        # Nome pode repetir, matrícula é única
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS colaboradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL
            )
        ''')
        
        # Tabela de locais
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS locais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Tabela de equipamentos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Tabela de registros (movimentações)
        # ESTRUTURA ATUALIZADA:
        # - colaborador = nome do colaborador
        # - colaborador_matricula = matrícula do colaborador (NOVO!)
        # - cliente = nome do cliente
        # - matricula = matrícula do cliente
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                colaborador TEXT NOT NULL,
                colaborador_matricula TEXT,
                equipamento TEXT NOT NULL,
                cliente TEXT,
                local TEXT NOT NULL,
                horario TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('ENTREGA', 'RETIRADA')),
                matricula TEXT
            )
        ''')
        
        # Tabela de configurações
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        
        # Tabela de histórico de alterações
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS registro_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registro_id INTEGER NOT NULL,
                campo_alterado TEXT NOT NULL,
                valor_anterior TEXT,
                valor_novo TEXT,
                data_alteracao TEXT NOT NULL,
                tipo_operacao TEXT NOT NULL,
                FOREIGN KEY (registro_id) REFERENCES registros(id)
            )
        ''')
        
        # Criar índices para melhorar performance
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_data 
            ON registros(data)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_colaborador 
            ON registros(colaborador)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_colaborador_matricula 
            ON registros(colaborador_matricula)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_equipamento 
            ON registros(equipamento)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_local 
            ON registros(local)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_tipo 
            ON registros(tipo)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_matricula 
            ON registros(matricula)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_cliente 
            ON registros(cliente)
        ''')
        
        # Índice para matrícula dos colaboradores
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_colaboradores_matricula 
            ON colaboradores(matricula)
        ''')
        
        self.conn.commit()
    
    def migrate_database(self):
        """Migra banco de dados existente para nova estrutura"""
        # Verificar colunas da tabela registros
        self.cursor.execute("PRAGMA table_info(registros)")
        registros_columns = [column[1] for column in self.cursor.fetchall()]
        
        # Adicionar coluna matricula (do cliente) se não existir
        if 'matricula' not in registros_columns:
            try:
                self.cursor.execute('ALTER TABLE registros ADD COLUMN matricula TEXT')
                self.conn.commit()
                print("✅ Coluna 'matricula' (cliente) adicionada à tabela registros!")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Migração registros (matricula): {e}")
        
        # Adicionar coluna colaborador_matricula se não existir
        if 'colaborador_matricula' not in registros_columns:
            try:
                self.cursor.execute('ALTER TABLE registros ADD COLUMN colaborador_matricula TEXT')
                self.conn.commit()
                print("✅ Coluna 'colaborador_matricula' adicionada à tabela registros!")
                
                # Tentar preencher colaborador_matricula para registros existentes
                self._fill_colaborador_matricula()
                
            except sqlite3.OperationalError as e:
                print(f"⚠️ Migração registros (colaborador_matricula): {e}")
        
        # Verificar e migrar tabela colaboradores (coluna matricula)
        self.cursor.execute("PRAGMA table_info(colaboradores)")
        colab_columns = [column[1] for column in self.cursor.fetchall()]
        
        if 'matricula' not in colab_columns:
            try:
                # Adicionar coluna matricula
                self.cursor.execute('ALTER TABLE colaboradores ADD COLUMN matricula TEXT')
                
                # Gerar matrículas para colaboradores existentes
                self.cursor.execute("SELECT id, nome FROM colaboradores WHERE matricula IS NULL")
                colaboradores = self.cursor.fetchall()
                
                for colab_id, nome in colaboradores:
                    # Gerar matrícula baseada no ID (COL-XXX)
                    matricula = f"COL-{colab_id:03d}"
                    self.cursor.execute(
                        "UPDATE colaboradores SET matricula = ? WHERE id = ?", 
                        (matricula, colab_id)
                    )
                
                self.conn.commit()
                print(f"✅ Coluna 'matricula' adicionada à tabela colaboradores!")
                print(f"✅ {len(colaboradores)} colaboradores atualizados com matrícula!")
                
            except sqlite3.OperationalError as e:
                print(f"⚠️ Migração colaboradores: {e}")
        
        # Verificar estrutura da tabela colaboradores
        self._ensure_colaboradores_structure()
    
    def _fill_colaborador_matricula(self):
        """Preenche colaborador_matricula para registros existentes"""
        try:
            # Buscar registros sem colaborador_matricula
            self.cursor.execute('''
                SELECT DISTINCT r.colaborador 
                FROM registros r 
                WHERE r.colaborador_matricula IS NULL
            ''')
            colaboradores_sem_mat = self.cursor.fetchall()
            
            updated = 0
            for (nome_colab,) in colaboradores_sem_mat:
                # Buscar matrícula do colaborador pelo nome
                self.cursor.execute(
                    "SELECT matricula FROM colaboradores WHERE nome = ? LIMIT 1",
                    (nome_colab,)
                )
                result = self.cursor.fetchone()
                
                if result:
                    # Atualizar registros com a matrícula encontrada
                    self.cursor.execute('''
                        UPDATE registros 
                        SET colaborador_matricula = ? 
                        WHERE colaborador = ? AND colaborador_matricula IS NULL
                    ''', (result[0], nome_colab))
                    updated += self.cursor.rowcount
            
            self.conn.commit()
            if updated > 0:
                print(f"✅ {updated} registros atualizados com colaborador_matricula!")
                
        except Exception as e:
            print(f"⚠️ Erro ao preencher colaborador_matricula: {e}")
    
    def _ensure_colaboradores_structure(self):
        """Garante que a estrutura da tabela colaboradores está correta"""
        # Verificar se a estrutura atual tem UNIQUE no nome
        self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='colaboradores'")
        result = self.cursor.fetchone()
        
        if result:
            create_sql = result[0]
            # Se o nome tem UNIQUE mas matrícula não existe ou não tem UNIQUE, precisamos recriar
            if 'nome TEXT NOT NULL UNIQUE' in create_sql and 'matricula TEXT NOT NULL UNIQUE' not in create_sql:
                self._recreate_colaboradores_table()
    
    def _recreate_colaboradores_table(self):
        """Recria tabela colaboradores com estrutura correta (matrícula UNIQUE, nome não-UNIQUE)"""
        try:
            print("🔄 Recriando tabela colaboradores com nova estrutura...")
            
            # Buscar dados existentes
            self.cursor.execute("SELECT id, nome FROM colaboradores")
            dados_existentes = self.cursor.fetchall()
            
            # Verificar se tem coluna matricula
            self.cursor.execute("PRAGMA table_info(colaboradores)")
            has_matricula = 'matricula' in [col[1] for col in self.cursor.fetchall()]
            
            if has_matricula:
                self.cursor.execute("SELECT id, matricula, nome FROM colaboradores")
                dados_com_matricula = self.cursor.fetchall()
            else:
                dados_com_matricula = [(d[0], f"COL-{d[0]:03d}", d[1]) for d in dados_existentes]
            
            # Renomear tabela antiga
            self.cursor.execute("ALTER TABLE colaboradores RENAME TO colaboradores_old")
            
            # Criar nova tabela com estrutura correta
            self.cursor.execute('''
                CREATE TABLE colaboradores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matricula TEXT NOT NULL UNIQUE,
                    nome TEXT NOT NULL
                )
            ''')
            
            # Inserir dados na nova tabela
            for colab_id, matricula, nome in dados_com_matricula:
                try:
                    self.cursor.execute(
                        "INSERT INTO colaboradores (id, matricula, nome) VALUES (?, ?, ?)",
                        (colab_id, matricula, nome)
                    )
                except sqlite3.IntegrityError:
                    # Matrícula duplicada, gerar nova
                    nova_matricula = f"COL-{colab_id:03d}-{datetime.now().strftime('%H%M%S')}"
                    self.cursor.execute(
                        "INSERT INTO colaboradores (id, matricula, nome) VALUES (?, ?, ?)",
                        (colab_id, nova_matricula, nome)
                    )
            
            # Remover tabela antiga
            self.cursor.execute("DROP TABLE colaboradores_old")
            
            self.conn.commit()
            print(f"✅ Tabela colaboradores recriada com {len(dados_com_matricula)} registros!")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erro ao recriar tabela colaboradores: {e}")
    
    def add_history(self, registro_id, tipo, campo, anterior, novo):
        """Adiciona entrada no histórico"""
        self.cursor.execute('''
            INSERT INTO registro_historico 
            (registro_id, campo_alterado, valor_anterior, valor_novo, 
             data_alteracao, tipo_operacao)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (registro_id, campo, anterior, novo, 
              datetime.now().strftime('%d/%m/%Y %H:%M:%S'), tipo))
        self.conn.commit()
    
    def get_history(self, registro_id):
        """Busca histórico de um registro"""
        self.cursor.execute('''
            SELECT campo_alterado, valor_anterior, valor_novo, 
                   data_alteracao, tipo_operacao
            FROM registro_historico
            WHERE registro_id=?
            ORDER BY data_alteracao DESC
        ''', (registro_id,))
        return self.cursor.fetchall()
    
    def close(self):
        """Fecha a conexão com o banco"""
        if self.conn:
            self.conn.close()
    
    def get_estatisticas(self):
        """Retorna estatísticas do banco"""
        stats = {}
        
        self.cursor.execute("SELECT COUNT(*) FROM registros")
        stats['total_registros'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM registros WHERE tipo = 'ENTREGA'")
        stats['total_entregas'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM registros WHERE tipo = 'RETIRADA'")
        stats['total_retiradas'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM colaboradores")
        stats['total_colaboradores'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM locais")
        stats['total_locais'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM equipamentos")
        stats['total_equipamentos'] = self.cursor.fetchone()[0]
        
        return stats
    
    def get_colaborador_by_matricula(self, matricula):
        """Busca colaborador pela matrícula"""
        self.cursor.execute(
            "SELECT id, matricula, nome FROM colaboradores WHERE matricula = ?",
            (matricula,)
        )
        return self.cursor.fetchone()
    
    def get_all_colaboradores(self):
        """Retorna todos os colaboradores com matrícula"""
        self.cursor.execute(
            "SELECT id, matricula, nome FROM colaboradores ORDER BY nome"
        )
        return self.cursor.fetchall()
    
    def add_colaborador(self, matricula, nome):
        """Adiciona novo colaborador"""
        self.cursor.execute(
            "INSERT INTO colaboradores (matricula, nome) VALUES (?, ?)",
            (matricula, nome)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def update_colaborador(self, colab_id, matricula, nome):
        """Atualiza colaborador existente"""
        self.cursor.execute(
            "UPDATE colaboradores SET matricula = ?, nome = ? WHERE id = ?",
            (matricula, nome, colab_id)
        )
        self.conn.commit()