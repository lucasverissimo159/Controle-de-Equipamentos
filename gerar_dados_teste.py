#!/usr/bin/env python3
"""
Gerador de Dados de Teste para o Sistema de Controle de Equipamentos
Versão 2.0 - Atualizado com campo colaborador_matricula
Gera registros para todos os meses de 2023, 2024, 2025 e 2026
"""
import sqlite3
import random
from datetime import datetime, timedelta
import os
import json
from models.database import Database

# Configurações
DB_NAME = 'equip_control.db'
ARCHIVE_DIR = 'arquivos_mensais'

# ===== COLABORADORES COM MATRÍCULA =====
# Estrutura: (Matrícula, Nome)
# Observação: NOMES PODEM SE REPETIR (diferentes matrículas)
COLABORADORES = [
    ("COL-001", "JOÃO SILVA"),
    ("COL-002", "MARIA SANTOS"),
    ("COL-003", "PEDRO OLIVEIRA"),
    ("COL-004", "ANA COSTA"),
    ("COL-005", "CARLOS SOUZA"),
    ("COL-006", "JULIANA LIMA"),
    ("COL-007", "RICARDO ALVES"),
    ("COL-008", "FERNANDA ROCHA"),
    ("COL-009", "BRUNO MARTINS"),
    ("COL-010", "PATRICIA FERNANDES"),
    ("COL-011", "LUCAS PEREIRA"),
    ("COL-012", "CAMILA RODRIGUES"),
    ("COL-013", "RAFAEL BARBOSA"),
    ("COL-014", "GABRIELA MENDES"),
    ("COL-015", "THIAGO FERREIRA"),
    
    # ===== COLABORADORES COM NOMES DUPLICADOS (HOMÔNIMOS) =====
    # Demonstração: Mesmo nome, matrículas diferentes
    ("COL-016", "JOÃO SILVA"),        # Homônimo do COL-001
    ("COL-017", "MARIA SANTOS"),      # Homônimo do COL-002
    ("COL-018", "PEDRO OLIVEIRA"),    # Homônimo do COL-003
    ("COL-019", "ANA COSTA"),         # Homônimo do COL-004
    ("COL-020", "CARLOS SOUZA"),      # Homônimo do COL-005
]

LOCAIS = [
    "FILIAL CENTRO",
    "FILIAL NORTE", 
    "FILIAL SUL",
    "FILIAL LESTE", 
    "FILIAL OESTE",
    "MATRIZ",
    "ALMOXARIFADO CENTRAL",
    "LOJA SHOPPING NORTE", 
    "LOJA SHOPPING SUL",
    "DEPÓSITO A",
    "DEPÓSITO B", 
    "UNIDADE INDUSTRIAL",
    "ESCRITÓRIO REGIONAL",
    "CENTRO DE DISTRIBUIÇÃO",
    "POLO TECNOLÓGICO"
]

EQUIPAMENTOS = [
    # Notebooks
    "NOTEBOOK-001", "NOTEBOOK-002", "NOTEBOOK-003", "NOTEBOOK-004", "NOTEBOOK-005",
    "NOTEBOOK-006", "NOTEBOOK-007", "NOTEBOOK-008", "NOTEBOOK-009", "NOTEBOOK-010",
    
    # Tablets
    "TABLET-001", "TABLET-002", "TABLET-003", "TABLET-004", "TABLET-005",
    "TABLET-006", "TABLET-007", "TABLET-008",
    
    # Monitores
    "MONITOR-001", "MONITOR-002", "MONITOR-003", "MONITOR-004", "MONITOR-005",
    "MONITOR-006", "MONITOR-007", "MONITOR-008", "MONITOR-009", "MONITOR-010",
    
    # Impressoras
    "IMPRESSORA-001", "IMPRESSORA-002", "IMPRESSORA-003", "IMPRESSORA-004",
    
    # Outros
    "SCANNER-001", "SCANNER-002",
    "PROJETOR-001", "PROJETOR-002", "PROJETOR-003",
    "CAMERA-001", "CAMERA-002",
    "MOUSE-001", "MOUSE-002", "MOUSE-003", "MOUSE-004", "MOUSE-005",
    "TECLADO-001", "TECLADO-002", "TECLADO-003", "TECLADO-004",
    "HEADSET-001", "HEADSET-002", "HEADSET-003"
]

# ===== CLIENTES COM MATRÍCULA =====
# Estrutura: (Nome da Pessoa, Matrícula)
# Observação: NOMES PODEM SE REPETIR (diferentes matrículas)
CLIENTES = [
    ("ANTONIO PEREIRA", "CLI-001"),
    ("BEATRIZ GOMES", "CLI-002"),
    ("CLAUDIO FERREIRA", "CLI-003"),
    ("DANIELA SOUZA", "CLI-004"),
    ("EDUARDO LIMA", "CLI-005"),
    ("FABIANA COSTA", "CLI-006"),
    ("GUSTAVO ALVES", "CLI-007"),
    ("HELENA MARTINS", "CLI-008"),
    ("IGOR SANTOS", "CLI-009"),
    ("JULIA ROCHA", "CLI-010"),
    ("LEONARDO BARROS", "CLI-011"),
    ("MARIANA SILVA", "CLI-012"),
    ("NICOLAS CARDOSO", "CLI-013"),
    ("OLIVIA MELO", "CLI-014"),
    ("PAULO RIBEIRO", "CLI-015"),
    ("QUEZIA NUNES", "CLI-016"),
    ("RODRIGO TEIXEIRA", "CLI-017"),
    ("SABRINA DIAS", "CLI-018"),
    ("TIAGO CAMPOS", "CLI-019"),
    ("VANESSA ARAUJO", "CLI-020"),
    
    # ===== CLIENTES COM NOMES DUPLICADOS (HOMÔNIMOS) =====
    ("ANTONIO PEREIRA", "CLI-021"),   # Homônimo do CLI-001
    ("BEATRIZ GOMES", "CLI-022"),     # Homônimo do CLI-002
    ("CLAUDIO FERREIRA", "CLI-023"),  # Homônimo do CLI-003
    ("DANIELA SOUZA", "CLI-024"),     # Homônimo do CLI-004
    ("EDUARDO LIMA", "CLI-025"),      # Homônimo do CLI-005
]

TIPOS = ["ENTREGA", "RETIRADA"]

def criar_banco():
    """Cria conexão com banco e inicializa estrutura"""
    print("🔧 Inicializando banco de dados...")
    db = Database(DB_NAME)
    print("✅ Estrutura do banco criada automaticamente")
    print("   ➜ Tabela 'registros' inclui campo 'colaborador_matricula'")
    return db.conn, db.cursor

def limpar_dados_anteriores(cursor, conn):
    """Limpa dados de teste anteriores"""
    print("\n🗑️  Limpando dados anteriores...")
    
    cursor.execute("DELETE FROM registros")
    cursor.execute("DELETE FROM colaboradores")
    cursor.execute("DELETE FROM locais")
    cursor.execute("DELETE FROM equipamentos")
    cursor.execute("DELETE FROM registro_historico")
    
    conn.commit()
    print("✅ Dados anteriores removidos")

def cadastrar_colaboradores(cursor, conn):
    """Cadastra colaboradores COM MATRÍCULA"""
    print("\n👷 Cadastrando colaboradores...")
    
    for matricula, nome in COLABORADORES:
        cursor.execute(
            "INSERT INTO colaboradores (matricula, nome) VALUES (?, ?)", 
            (matricula, nome)
        )
    
    conn.commit()
    print(f"✅ {len(COLABORADORES)} colaboradores cadastrados")
    
    # Mostrar colaboradores com nomes duplicados
    print("\n📋 Demonstração de homônimos (nomes duplicados):")
    cursor.execute("""
        SELECT matricula, nome 
        FROM colaboradores 
        WHERE nome IN (
            SELECT nome 
            FROM colaboradores 
            GROUP BY nome 
            HAVING COUNT(*) > 1
        ) 
        ORDER BY nome, matricula
    """)
    
    homonimos = cursor.fetchall()
    if homonimos:
        nome_atual = None
        for mat, nome in homonimos:
            if nome != nome_atual:
                print(f"\n   👥 {nome}:")
                nome_atual = nome
            print(f"      ├─ {mat}")
    else:
        print("   Nenhum homônimo encontrado")

def cadastrar_locais(cursor, conn):
    """Cadastra locais"""
    print("\n📍 Cadastrando locais...")
    
    for local in LOCAIS:
        cursor.execute("INSERT INTO locais (nome) VALUES (?)", (local,))
    
    conn.commit()
    print(f"✅ {len(LOCAIS)} locais cadastrados")

def cadastrar_equipamentos(cursor, conn):
    """Cadastra equipamentos"""
    print("\n📦 Cadastrando equipamentos...")
    
    for equipamento in EQUIPAMENTOS:
        cursor.execute("INSERT INTO equipamentos (nome) VALUES (?)", (equipamento,))
    
    conn.commit()
    print(f"✅ {len(EQUIPAMENTOS)} equipamentos cadastrados")

def gerar_horario_aleatorio():
    """Gera horário aleatório"""
    hora = random.randint(7, 18)
    minuto = random.choice([0, 15, 30, 45])
    return f"{hora:02d}:{minuto:02d}"

def obter_dias_mes(mes, ano):
    """Retorna o número de dias do mês"""
    if mes == 2:
        # Ano bissexto
        if (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0):
            return 29
        return 28
    elif mes in [4, 6, 9, 11]:
        return 30
    else:
        return 31

def gerar_registros_ano(cursor, conn, ano, mes_inicio=1, mes_fim=12, dia_max_ultimo_mes=None):
    """Gera registros para um ano específico"""
    print(f"\n📊 Gerando registros para {ano}...")
    
    total_registros = 0
    total_entregas = 0
    total_retiradas = 0
    
    for mes in range(mes_inicio, mes_fim + 1):
        # Determinar número máximo de dias para o mês
        dias_mes = obter_dias_mes(mes, ano)
        
        # Se for o último mês e houver limite de dia, usar esse limite
        if mes == mes_fim and dia_max_ultimo_mes:
            dias_mes = min(dias_mes, dia_max_ultimo_mes)
        
        # Número de registros para o mês (entre 30 e 80)
        num_registros = random.randint(30, 80)
        
        print(f"   Mês {mes:02d}/{ano}: {num_registros} registros", end=" ")
        
        mes_entregas = 0
        mes_retiradas = 0
        
        for _ in range(num_registros):
            dia = random.randint(1, dias_mes)
            data = f"{dia:02d}/{mes:02d}/{ano}"
            
            # Seleciona colaborador (matrícula e nome)
            colaborador_matricula, colaborador_nome = random.choice(COLABORADORES)
            
            local = random.choice(LOCAIS)
            equipamento = random.choice(EQUIPAMENTOS)
            
            # Seleciona cliente e sua matrícula
            cliente_nome, cliente_matricula = random.choice(CLIENTES)
            
            horario = gerar_horario_aleatorio()
            
            # Tipo: 50% ENTREGA, 50% RETIRADA (aproximadamente)
            tipo = random.choice(TIPOS)
            
            if tipo == "ENTREGA":
                total_entregas += 1
                mes_entregas += 1
            else:
                total_retiradas += 1
                mes_retiradas += 1
            
            # ===== INSERÇÃO COM CAMPO colaborador_matricula =====
            cursor.execute('''
                INSERT INTO registros 
                (data, colaborador, equipamento, cliente, local, horario, tipo, 
                 matricula, colaborador_matricula)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data, colaborador_nome, equipamento, cliente_nome, local, 
                  horario, tipo, cliente_matricula, colaborador_matricula))
            
            total_registros += 1
        
        print(f"(🔴 {mes_entregas} entregas, 🟡 {mes_retiradas} retiradas)")
    
    conn.commit()
    
    print(f"\n✅ Total {ano}: {total_registros} registros gerados")
    print(f"   🔴 Entregas: {total_entregas}")
    print(f"   🟡 Retiradas: {total_retiradas}")
    
    return total_registros, total_entregas, total_retiradas

def criar_arquivos_mensais(cursor):
    """Cria arquivos JSON mensais (simulando arquivamento)"""
    print("\n📁 Criando arquivos JSON mensais...")
    
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    
    total_arquivos = 0
    
    # Para cada ano de 2023 a 2026
    for ano in [2023, 2024, 2025, 2026]:
        # Para cada mês
        for mes in range(1, 13):
            cursor.execute('''
                SELECT id, data, colaborador, equipamento, cliente, local, 
                       horario, tipo, matricula, colaborador_matricula
                FROM registros 
                WHERE substr(data, 4, 2) = ? 
                AND substr(data, 7, 4) = ?
            ''', (f"{mes:02d}", str(ano)))
            
            registros = cursor.fetchall()
            
            if not registros:
                continue
            
            filename = f"{ARCHIVE_DIR}/registros_{ano}-{mes:02d}.json"
            
            # ===== ESTRUTURA JSON ATUALIZADA COM colaborador_matricula =====
            dados = []
            for reg in registros:
                dados.append({
                    'id': reg[0],
                    'data': reg[1],
                    'colaborador': reg[2],
                    'equipamento': reg[3],
                    'cliente': reg[4],
                    'local': reg[5],
                    'horario': reg[6],
                    'tipo': reg[7],
                    'matricula': reg[8],                    # Matrícula do cliente
                    'colaborador_matricula': reg[9]         # Matrícula do colaborador (NOVO)
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ {filename} ({len(registros)} registros)")
            total_arquivos += 1
    
    print(f"\n✅ {total_arquivos} arquivos mensais criados")

def exibir_estatisticas(cursor):
    """Exibe estatísticas dos dados gerados"""
    print("\n" + "="*70)
    print("📊 ESTATÍSTICAS DOS DADOS GERADOS")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM registros")
    total = cursor.fetchone()[0]
    print(f"\n📌 Total de Registros: {total}")
    
    # Entregas e Retiradas
    cursor.execute("SELECT COUNT(*) FROM registros WHERE tipo = 'ENTREGA'")
    entregas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM registros WHERE tipo = 'RETIRADA'")
    retiradas = cursor.fetchone()[0]
    print(f"🔴 Total de Entregas: {entregas} ({entregas/total*100:.1f}%)")
    print(f"🟡 Total de Retiradas: {retiradas} ({retiradas/total*100:.1f}%)")
    
    # Registros por ano
    print("\n📅 Registros por Ano:")
    for ano in [2023, 2024, 2025, 2026]:
        cursor.execute('''
            SELECT COUNT(*) FROM registros 
            WHERE substr(data, 7, 4) = ?
        ''', (str(ano),))
        count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM registros 
            WHERE substr(data, 7, 4) = ? AND tipo = 'ENTREGA'
        ''', (str(ano),))
        ent = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM registros 
            WHERE substr(data, 7, 4) = ? AND tipo = 'RETIRADA'
        ''', (str(ano),))
        ret = cursor.fetchone()[0]
        
        print(f"   {ano}: {count:4d} registros (🔴 {ent:3d} entregas, 🟡 {ret:3d} retiradas)")
    
    # Top 5 colaboradores (agrupados por matrícula)
    print("\n👷 Top 5 Colaboradores (por matrícula):")
    cursor.execute('''
        SELECT colaborador_matricula, colaborador, COUNT(*) as total 
        FROM registros 
        WHERE colaborador_matricula IS NOT NULL
        GROUP BY colaborador_matricula
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (matricula, nome, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {matricula} - {nome}: {total} registros")
    
    # Demonstração de homônimos nos registros
    print("\n👥 Demonstração: Registros de colaboradores homônimos")
    cursor.execute("""
        SELECT colaborador, colaborador_matricula, COUNT(*) as total
        FROM registros
        WHERE colaborador IN (
            SELECT colaborador 
            FROM registros 
            WHERE colaborador_matricula IS NOT NULL
            GROUP BY colaborador 
            HAVING COUNT(DISTINCT colaborador_matricula) > 1
        )
        GROUP BY colaborador, colaborador_matricula
        ORDER BY colaborador, colaborador_matricula
    """)
    
    homonimos_registros = cursor.fetchall()
    if homonimos_registros:
        nome_atual = None
        for nome, matricula, total in homonimos_registros:
            if nome != nome_atual:
                print(f"\n   👥 {nome}:")
                nome_atual = nome
            print(f"      ├─ {matricula}: {total} registros")
    
    # Lista de colaboradores cadastrados (com matrícula)
    print("\n🎫 Colaboradores Cadastrados:")
    cursor.execute("SELECT matricula, nome FROM colaboradores ORDER BY nome, matricula")
    
    nome_anterior = None
    for matricula, nome in cursor.fetchall():
        if nome != nome_anterior:
            if nome_anterior is not None:
                print()  # Linha em branco entre grupos
            nome_anterior = nome
        print(f"   {matricula}: {nome}")
    
    # Top 5 locais
    print("\n📍 Top 5 Locais:")
    cursor.execute('''
        SELECT local, COUNT(*) as total 
        FROM registros 
        GROUP BY local 
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (local, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {local}: {total} registros")
    
    # Top 5 equipamentos
    print("\n📦 Top 5 Equipamentos:")
    cursor.execute('''
        SELECT equipamento, COUNT(*) as total 
        FROM registros 
        GROUP BY equipamento 
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (equipamento, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {equipamento}: {total} registros")
    
    # Top 5 clientes (com matrícula)
    print("\n👤 Top 5 Clientes (por matrícula):")
    cursor.execute('''
        SELECT cliente, matricula, COUNT(*) as total 
        FROM registros 
        WHERE matricula IS NOT NULL
        GROUP BY matricula
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (cliente, matricula, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {matricula} - {cliente}: {total} registros")
    
    # Clientes homônimos
    print("\n👥 Demonstração: Clientes homônimos nos registros")
    cursor.execute("""
        SELECT cliente, matricula, COUNT(*) as total
        FROM registros
        WHERE cliente IN (
            SELECT cliente 
            FROM registros 
            WHERE matricula IS NOT NULL
            GROUP BY cliente 
            HAVING COUNT(DISTINCT matricula) > 1
        )
        GROUP BY cliente, matricula
        ORDER BY cliente, matricula
    """)
    
    clientes_homonimos = cursor.fetchall()
    if clientes_homonimos:
        nome_atual = None
        for nome, matricula, total in clientes_homonimos:
            if nome != nome_atual:
                print(f"\n   👥 {nome}:")
                nome_atual = nome
            print(f"      ├─ {matricula}: {total} registros")
    
    print("\n" + "="*70)

def main():
    """Função principal"""
    print("="*70)
    print("🎲 GERADOR DE DADOS DE TESTE - VERSÃO 2.0")
    print("Sistema de Controle de Equipamentos")
    print("="*70)
    print("\n📆 Período: Janeiro/2023 até Dezembro/2026")
    print("📊 Tipos: ENTREGA (🔴) e RETIRADA (🟡)")
    print("👷 Colaboradores: Nome + Matrícula (permite homônimos)")
    print("👤 Clientes: Nome + Matrícula (permite homônimos)")
    print("\n🆕 NOVIDADE: Campo 'colaborador_matricula' nos registros")
    print("   ➜ Permite identificar unicamente cada colaborador")
    print("   ➜ Homônimos não afetam mais atualizações em massa")
    
    conn, cursor = criar_banco()
    
    resposta = input("\n⚠️  Limpar dados existentes? (S/N): ").strip().upper()
    if resposta == 'S':
        limpar_dados_anteriores(cursor, conn)
    
    cadastrar_colaboradores(cursor, conn)
    cadastrar_locais(cursor, conn)
    cadastrar_equipamentos(cursor, conn)
    
    total_geral = 0
    entregas_geral = 0
    retiradas_geral = 0
    
    # Gerar registros para 2023 (ano completo)
    t, e, r = gerar_registros_ano(cursor, conn, 2023)
    total_geral += t
    entregas_geral += e
    retiradas_geral += r
    
    # Gerar registros para 2024 (ano completo)
    t, e, r = gerar_registros_ano(cursor, conn, 2024)
    total_geral += t
    entregas_geral += e
    retiradas_geral += r
    
    # Gerar registros para 2025 (ano completo)
    t, e, r = gerar_registros_ano(cursor, conn, 2025)
    total_geral += t
    entregas_geral += e
    retiradas_geral += r
    
    # Gerar registros para 2026 (ano completo)
    t, e, r = gerar_registros_ano(cursor, conn, 2026)
    total_geral += t
    entregas_geral += e
    retiradas_geral += r
    
    criar_arquivos_mensais(cursor)
    
    exibir_estatisticas(cursor)
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ DADOS DE TESTE GERADOS COM SUCESSO!")
    print("="*70)
    print(f"\n📊 Total: {total_geral} registros criados")
    print(f"   🔴 Entregas: {entregas_geral} ({entregas_geral/total_geral*100:.1f}%)")
    print(f"   🟡 Retiradas: {retiradas_geral} ({retiradas_geral/total_geral*100:.1f}%)")
    print(f"\n📁 Arquivos JSON salvos em: {ARCHIVE_DIR}/")
    print(f"💾 Banco de dados: {DB_NAME}")
    print("\n✨ Recursos testáveis:")
    print("   ✓ Colaboradores com nomes duplicados (homônimos)")
    print("   ✓ Clientes com nomes duplicados (homônimos)")
    print("   ✓ Edição de colaboradores sem afetar homônimos")
    print("   ✓ Campo colaborador_matricula para identificação única")
    print("\n🚀 Execute 'python main.py' para testar o sistema!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()