# 🧪 Como Testar o Sistema Completo

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

---

## Passo a Passo

### 1️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

**Dependências instaladas:**
- customtkinter (interface moderna)
- tkcalendar (seletor de data)
- matplotlib (gráficos)
- plotly (gráficos interativos)
- openpyxl (Excel)
- Pillow (imagens)
- reportlab (PDF)
- numpy (cálculos)

---

### 2️⃣ Gerar dados de teste

```bash
python gerar_dados_teste.py
```

**O que acontece:**
- ✅ Cria banco de dados SQLite (`equip_control.db`)
- ✅ Cadastra 10 colaboradores
- ✅ Cadastra 10 locais
- ✅ Cadastra 20 equipamentos
- ✅ Gera ~1500 registros (2023-2026)
- ✅ 50% ENTREGAS 🔴 e 50% RETIRADAS 🟡
- ✅ Cria arquivos JSON mensais

---

### 3️⃣ Executar o sistema

```bash
python main.py
```

---

## 4️⃣ Testar funcionalidades

### ✅ Janela Principal
- Veja os registros carregados com **cores por tipo**:
  - 🔴 **ENTREGA** - fundo vermelho coral
  - 🟡 **RETIRADA** - fundo amarelo vibrante
- Teste os filtros:
  - Por **Data** (digite ou use o calendário 📅)
  - Por **Colaborador**
  - Por **Equipamento**
  - Por **Cliente**
  - Por **Local**
  - Por **Tipo** (Todos/ENTREGA/RETIRADA)
- Clique no botão **ℹ️ INFO** para ver histórico de um registro
- Clique em **NOVA RETIRADA** 🟡 para registrar devolução
- Clique em **NOVA ENTREGA** 🔴 para registrar saída
- Clique em **EDITAR** para modificar um existente

---

### ✅ Gerenciar Colaboradores/Locais/Equipamentos
- Navegue pelas abas correspondentes
- **Adicione** novos itens
- **Edite** itens existentes (selecione e clique Editar)
- **Exclua** itens (selecione e clique Excluir)
- Observe que os valores são convertidos para MAIÚSCULAS automaticamente

---

### ✅ Registros Antigos
- Veja dados de meses anteriores (arquivos JSON)
- Teste filtros por **Mês/Ano**
- Teste filtro por **Data específica**
- Teste filtros por **Colaborador/Equipamento/Cliente/Local/Tipo**
- Clique em **ℹ️ INFO** para ver histórico

---

### ✅ Estatísticas
- Veja os **6 KPIs** coloridos no topo:
  - 📊 Total de Movimentações
  - 🔴 Total de Entregas
  - 🟡 Total de Retiradas
  - 👷 Colaboradores Ativos
  - 📍 Locais Diferentes
  - 📦 Equipamentos Movimentados
- Veja os **9 tipos de gráficos**:
  - Evolução temporal (barras e linha)
  - Entregas/Retiradas por Colaborador, Local, Equipamento
  - Gráficos de pizza por tipo
  - Top 5 Rankings
  - Métricas de Performance

---

### ✅ Rankings
- Alterne entre **Equipamentos**, **Colaboradores** e **Locais**
- Veja medalhas: 🥇 Ouro, 🥈 Prata, 🥉 Bronze, 🏅 Cobre
- Exporte para PDF ou CSV

---

### ✅ Exportações
- Na aba **Estatísticas**:
  - Clique em **📄 EXPORTAR PDF** para gerar relatório
  - Clique em **📊 EXPORTAR CSV** para exportar dados
- Na aba **Rankings**:
  - Clique em **📄 EXPORTAR PDF** ou **📊 EXPORTAR CSV**

---

### ✅ Tema
- Clique no botão **TEMA ESCURO/CLARO** no canto superior direito
- Observe as cores se adaptarem em toda a interface

---

## 📊 O que você vai ver

### Tipos de Gráficos:
- 📊 Barras agrupadas (Entregas vs Retiradas)
- 📈 Gráfico de linha (evolução temporal)
- 🥧 Gráficos de pizza (distribuição)
- 📊 Barras horizontais (Top 5)
- 📉 Métricas de performance (barras de progresso)

### Arquivos Criados:
```
equip_control/
├── equip_control.db          (banco de dados SQLite)
└── arquivos_mensais/
    ├── registros_2023-01.json
    ├── registros_2023-02.json
    ├── ...
    └── registros_2026-12.json
```

---

## 🎯 Recursos para Testar

| Recurso | Como Testar |
|---------|-------------|
| **Filtros** | Combine diferentes filtros na aba principal |
| **Calendário** | Clique no ícone 📅 ao lado do campo de data |
| **Tipo** | Filtre por ENTREGA, RETIRADA ou Todos |
| **Gráficos** | Clique nos gráficos para ampliar |
| **Exportações** | Exporte PDF e CSV nas abas |
| **Histórico** | Selecione um registro e clique INFO |
| **Temas** | Alterne entre claro/escuro no cabeçalho |
| **Arquivos** | Navegue por diferentes meses em Registros Antigos |
| **CRUD** | Adicione, edite e exclua itens em Gerenciar |
| **Rankings** | Alterne entre Equipamentos/Colaboradores/Locais |

---

## 💡 Dicas

### Limpar dados e começar do zero:
```bash
python gerar_dados_teste.py
# Responda "S" quando perguntar se quer limpar dados
```

### Adicionar mais dados:
```bash
python gerar_dados_teste.py
# Responda "N" para manter dados existentes
```

### Testar filtros:
- Use diferentes combinações de Mês/Ano
- Filtre por data específica
- Combine filtros de Colaborador + Local + Tipo

### Ver detalhes de um registro:
1. Selecione o registro na tabela
2. Clique no botão **ℹ️ INFO**
3. Veja o histórico de criação e alterações

### Testar validações:
- Tente salvar registro com campos obrigatórios vazios
- Tente inserir data inválida (ex: 32/13/2025)
- Tente inserir horário inválido (ex: 25:99)

---

## 🐛 Resolução de Problemas

### Erro de importação de módulo:
```bash
# Certifique-se de estar no diretório correto
cd equip_control
python main.py
```

### Erro de dependência:
```bash
pip install --upgrade -r requirements.txt
```

### Banco de dados corrompido:
```bash
# Delete o arquivo e gere novamente
rm equip_control.db
python gerar_dados_teste.py
```

### Gráficos não aparecem:
```bash
# Reinstale matplotlib
pip install --upgrade matplotlib
```

---

## 📝 Checklist de Testes

- [ ] Instalar dependências
- [ ] Gerar dados de teste
- [ ] Executar sistema
- [ ] Testar filtros na aba principal
- [ ] Testar filtro por tipo (ENTREGA/RETIRADA)
- [ ] Criar novo registro de ENTREGA
- [ ] Criar novo registro de RETIRADA
- [ ] Editar registro existente
- [ ] Ver histórico de registro
- [ ] Navegar por Registros Antigos
- [ ] Ver estatísticas e gráficos
- [ ] Ver rankings com medalhas
- [ ] Exportar PDF
- [ ] Exportar CSV
- [ ] Alternar tema claro/escuro
- [ ] Gerenciar colaboradores
- [ ] Gerenciar locais
- [ ] Gerenciar equipamentos

---

**Divirta-se testando! 🎉**
