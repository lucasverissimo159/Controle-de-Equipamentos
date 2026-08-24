*Read this in other languages: [English](#english), [Português](#português).*

---

# English

# 📦 Equipment Control System

Desktop system for managing equipment movements (deliveries and collections).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)
![License](https://img.shields.io/badge/License-View--Only-red.svg)

> ⚠️ **Repository available only for portfolio.** The code can be viewed, but **cannot** be copied, downloaded, used or reused in other projects. See the [License](#-license) section and the [`LICENSE`](./LICENSE) file.

---

## 📋 Features

### Main Window
- ✅ Registration of movements (DELIVERY 🔴 / COLLECTION 🟡)
- ✅ Editing of records
- ✅ History of changes
- ✅ Filters by date, collaborator, equipment, client, location and type
- ✅ Integrated calendar
- ✅ Vibrant colors by type of movement

### Registration Form — Client Identification
Three identification modes, selectable by radio buttons:
- **REGISTERED** — badge reading (registration number) with automatic name filling.
- **BY NAME** — searches for an already registered client by **name** (partial, *case-insensitive*) when the badge is not available. Upon choosing a result, registration number and name are filled exactly as in badge reading.
- **WITHOUT REGISTRATION** — manual entry of registration number and name.

### Management
- ✅ Registration of collaborators
- ✅ Registration of locations
- ✅ Registration of equipment
- ✅ Editing and deletion of items

### Old Records
- ✅ Automatic monthly archiving (JSON)
- ✅ Viewing of historical data
- ✅ Full filters by month/year/type

### Statistics
- ✅ Visual KPIs (Total, Deliveries, Collections, Collaborators, Locations, Equipment)
- ✅ Temporal evolution of movements (bars and line)
- ✅ Deliveries/Collections by Collaborator, Location and Equipment
- ✅ Pie charts by type
- ✅ Top 5 Rankings
- ✅ Performance metrics
- ✅ PDF and CSV Export

### Rankings
- ✅ By Equipment
- ✅ By Collaborators
- ✅ By Locations
- ✅ Medals (🥇🥈🥉🏅)
- ✅ PDF and CSV Export

### Interface
- ✅ Light and dark theme
- ✅ Modern interface (CustomTkinter)
- ✅ Informative tooltips
- ✅ ComboBox with scroll and search

---

## 🚀 Installation

### 1. Clone or download the project
```bash
git clone <repository-url>
cd equip_control
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the system
```bash
python main.py
```

---

## 📦 Dependencies

| Package | Version | Description |
|--------|--------|-----------|
| customtkinter | ≥5.2.0 | Modern interface |
| tkcalendar | ≥1.6.1 | Date picker |
| matplotlib | ≥3.7.0 | Charts |
| plotly | ≥5.15.0 | Interactive charts |
| openpyxl | ≥3.1.2 | Excel export |
| Pillow | ≥10.0.0 | Image manipulation |
| reportlab | ≥4.0.0 | PDF generation |
| numpy | ≥1.24.0 | Numerical calculations |

---

## 📁 Project Structure

```
equip_control/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md               # This file
│
├── config/
│   └── settings.py         # Configurations
│
├── models/
│   └── database.py         # Database
│
├── views/
│   ├── main_window.py      # Main window
│   ├── record_window.py    # Registration form
│   ├── stats_manager.py    # Statistics
│   ├── ranking_manager.py  # Rankings
│   └── widgets/
│       ├── scrollable_combobox.py
│       ├── progress_dialog.py
│       ├── history_dialog.py
│       ├── tooltip.py
│       ├── helpers.py
│       └── colors_helper.py
│
├── resources/
│   └── icons/
│       └── icon.ico        # App icon
│
└── arquivos_mensais/       # Monthly JSON files
```

---

## 🧪 Test Data

To test with fictitious data:

```bash
python gerar_dados_teste.py
```

This will:
- Register 10 collaborators
- Register 10 locations
- Register 20 equipment
- Generate ~1500 records (2023-2026)
- Create monthly JSON files

---

## 🗄️ Database

The system uses **SQLite** with the following tables:

| Table | Description |
|--------|-----------|
| `registros` | Movement records |
| `colaboradores` | Registration of collaborators |
| `locais` | Registration of locations |
| `equipamentos` | Registration of equipment |
| `config` | System settings |
| `registro_historico` | History of changes |

### `registros` Table Structure
| Column | Type | Description |
|--------|------|-----------|
| id | INTEGER | Primary key |
| data | TEXT | DD/MM/YYYY |
| colaborador | TEXT | Collaborator name |
| equipamento | TEXT | Equipment name |
| cliente | TEXT | Client (optional) |
| local | TEXT | Location name |
| horario | TEXT | HH:MM |
| tipo | TEXT | ENTREGA or RETIRADA |

---

## 🎨 System Colors

### Tables
| Type | Color |
|------|-----|
| ENTREGA | `#fca5a5` (vibrant coral red) |
| RETIRADA | `#fde047` (vibrant yellow) |

### Charts
| Type | Color |
|------|-----|
| ENTREGA | `#dc2626` (intense red) |
| RETIRADA | `#eab308` (golden yellow) |

---

## 📊 Monthly Archiving

The system automatically archives records into JSON files:

```
arquivos_mensais/
├── registros_2024-11.json
├── registros_2024-12.json
├── registros_2025-01.json
└── ...
```

---

## ⚙️ Configuration

Edit `config/settings.py` to customize:

```python
DATABASE_NAME = 'equip_control.db'  # Database name
DEFAULT_THEME = "light"              # Default theme: "light" or "dark"
```

---

## 🎨 Themes

Switch between light and dark theme by clicking the **THEME** button in the header.

| Theme | Description |
|------|-----------|
| Light | White background, black text |
| Dark | Dark background, light text |

---

## 📤 Exports

### PDF
- Full report with charts
- Statistical data
- A4 landscape format

### CSV/Excel
- Tabular data
- Excel compatible
- .csv or .xlsx format

---

## 🔧 Development

### MVC Architecture
- **Model:** `models/database.py`
- **View:** `views/*.py`
- **Controller:** Integrated in views

### Add new functionality
1. Create the widget in `views/widgets/`
2. Import in `views/main_window.py`
3. Add to TabView or where necessary

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for history of changes.

---

## 🆘 Support

If you encounter any problem:
1. Check if dependencies are installed
2. Check if you are in the correct directory
3. Try deleting `equip_control.db` and running again

```bash
rm equip_control.db
python main.py
```

---

## 📄 License

This repository is **not open source**. It is made publicly available solely for portfolio/technical demonstration purposes.

- ✅ Allowed: view the code via the GitHub interface.
- ❌ Prohibited: copy, download, clone for reuse, use, modify, execute or redistribute this code, in whole or in part, without prior written authorization from the author.

All rights reserved. See the full terms in [`LICENSE`](./LICENSE).

---

**Equipment Control System v2.0.0** 📦

---

# Português

# 📦 Sistema de Controle de Equipamentos

Sistema desktop para gerenciamento de movimentações de equipamentos (entregas e retiradas).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)
![License](https://img.shields.io/badge/License-View--Only-red.svg)

> ⚠️ **Repositório disponibilizado apenas para portfólio.** O código pode
> ser visualizado, mas **não** pode ser copiado, baixado, usado ou
> reaproveitado em outros projetos. Veja a seção [Licença](#-licença) e o
> arquivo [`LICENSE`](./LICENSE).

---

## 📋 Funcionalidades

### Janela Principal
- ✅ Registro de movimentações (ENTREGA 🔴 / RETIRADA 🟡)
- ✅ Edição de registros
- ✅ Histórico de alterações
- ✅ Filtros por data, colaborador, equipamento, cliente, local e tipo
- ✅ Calendário integrado
- ✅ Cores vibrantes por tipo de movimentação

### Formulário de Registro — Identificação do Cliente
Três modos de identificação, selecionáveis por botões de opção:
- **CADASTRADO** — leitura do crachá (matrícula) com preenchimento automático do nome.
- **POR NOME** — busca o cliente já cadastrado pelo **nome** (parcial, *case-insensitive*)
  quando o crachá não está em mãos. Ao escolher um resultado, matrícula e nome são
  preenchidos exatamente como na leitura do crachá.
- **SEM CADASTRO** — digitação manual de matrícula e nome.

### Gerenciamento
- ✅ Cadastro de colaboradores
- ✅ Cadastro de locais
- ✅ Cadastro de equipamentos
- ✅ Edição e exclusão de itens

### Registros Antigos
- ✅ Arquivamento mensal automático (JSON)
- ✅ Visualização de dados históricos
- ✅ Filtros completos por mês/ano/tipo

### Estatísticas
- ✅ KPIs visuais (Total, Entregas, Retiradas, Colaboradores, Locais, Equipamentos)
- ✅ Evolução temporal de movimentações (barras e linha)
- ✅ Entregas/Retiradas por Colaborador, Local e Equipamento
- ✅ Gráficos de pizza por tipo
- ✅ Top 5 Rankings
- ✅ Métricas de performance
- ✅ Exportação PDF e CSV

### Rankings
- ✅ Por Equipamentos
- ✅ Por Colaboradores
- ✅ Por Locais
- ✅ Medalhas (🥇🥈🥉🏅)
- ✅ Exportação PDF e CSV

### Interface
- ✅ Tema claro e escuro
- ✅ Interface moderna (CustomTkinter)
- ✅ Tooltips informativos
- ✅ ComboBox com scroll e busca

---

## 🚀 Instalação

### 1. Clone ou baixe o projeto
```bash
git clone <url-do-repositorio>
cd equip_control
```

### 2. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute o sistema
```bash
python main.py
```

---

## 📦 Dependências

| Pacote | Versão | Descrição |
|--------|--------|-----------|
| customtkinter | ≥5.2.0 | Interface moderna |
| tkcalendar | ≥1.6.1 | Seletor de data |
| matplotlib | ≥3.7.0 | Gráficos |
| plotly | ≥5.15.0 | Gráficos interativos |
| openpyxl | ≥3.1.2 | Exportação Excel |
| Pillow | ≥10.0.0 | Manipulação de imagens |
| reportlab | ≥4.0.0 | Geração de PDF |
| numpy | ≥1.24.0 | Cálculos numéricos |

---

## 📁 Estrutura do Projeto

```
equip_control/
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
├── README.md               # Este arquivo
│
├── config/
│   └── settings.py         # Configurações
│
├── models/
│   └── database.py         # Banco de dados
│
├── views/
│   ├── main_window.py      # Janela principal
│   ├── record_window.py    # Formulário de registro
│   ├── stats_manager.py    # Estatísticas
│   ├── ranking_manager.py  # Rankings
│   └── widgets/
│       ├── scrollable_combobox.py
│       ├── progress_dialog.py
│       ├── history_dialog.py
│       ├── tooltip.py
│       ├── helpers.py
│       └── colors_helper.py
│
├── resources/
│   └── icons/
│       └── icon.ico        # Ícone do app
│
└── arquivos_mensais/       # Arquivos JSON mensais
```

---

## 🧪 Dados de Teste

Para testar com dados fictícios:

```bash
python gerar_dados_teste.py
```

Isso irá:
- Cadastrar 10 colaboradores
- Cadastrar 10 locais
- Cadastrar 20 equipamentos
- Gerar ~1500 registros (2023-2026)
- Criar arquivos JSON mensais

---

## 🗄️ Banco de Dados

O sistema usa **SQLite** com as seguintes tabelas:

| Tabela | Descrição |
|--------|-----------|
| `registros` | Registros de movimentações |
| `colaboradores` | Cadastro de colaboradores |
| `locais` | Cadastro de locais |
| `equipamentos` | Cadastro de equipamentos |
| `config` | Configurações do sistema |
| `registro_historico` | Histórico de alterações |

### Estrutura da Tabela `registros`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| data | TEXT | DD/MM/AAAA |
| colaborador | TEXT | Nome do colaborador |
| equipamento | TEXT | Nome do equipamento |
| cliente | TEXT | Cliente (opcional) |
| local | TEXT | Nome do local |
| horario | TEXT | HH:MM |
| tipo | TEXT | ENTREGA ou RETIRADA |

---

## 🎨 Cores do Sistema

### Tabelas
| Tipo | Cor |
|------|-----|
| ENTREGA | `#fca5a5` (vermelho coral vibrante) |
| RETIRADA | `#fde047` (amarelo vibrante) |

### Gráficos
| Tipo | Cor |
|------|-----|
| ENTREGA | `#dc2626` (vermelho intenso) |
| RETIRADA | `#eab308` (amarelo dourado) |

---

## 📊 Arquivamento Mensal

O sistema arquiva automaticamente os registros em arquivos JSON:

```
arquivos_mensais/
├── registros_2024-11.json
├── registros_2024-12.json
├── registros_2025-01.json
└── ...
```

---

## ⚙️ Configurações

Edite `config/settings.py` para personalizar:

```python
DATABASE_NAME = 'equip_control.db'  # Nome do banco
DEFAULT_THEME = "light"              # Tema padrão: "light" ou "dark"
```

---

## 🎨 Temas

Alterne entre tema claro e escuro clicando no botão **TEMA** no cabeçalho.

| Tema | Descrição |
|------|-----------|
| Claro | Fundo branco, texto preto |
| Escuro | Fundo escuro, texto claro |

---

## 📤 Exportações

### PDF
- Relatório completo com gráficos
- Dados estatísticos
- Formato A4 paisagem

### CSV/Excel
- Dados tabulados
- Compatível com Excel
- Formato .csv ou .xlsx

---

## 🔧 Desenvolvimento

### Arquitetura MVC
- **Model:** `models/database.py`
- **View:** `views/*.py`
- **Controller:** Integrado nas views

### Adicionar nova funcionalidade
1. Crie o widget em `views/widgets/`
2. Importe em `views/main_window.py`
3. Adicione ao TabView ou onde necessário

---

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico de alterações.

---

## 🆘 Suporte

Se encontrar algum problema:
1. Verifique se as dependências estão instaladas
2. Verifique se está no diretório correto
3. Tente deletar `equip_control.db` e executar novamente

```bash
rm equip_control.db
python main.py
```

---

## 📄 Licença

Este repositório **não é open source**. Ele é disponibilizado publicamente
apenas para fins de portfólio/demonstração técnica.

- ✅ Permitido: visualizar o código pela interface do GitHub.
- ❌ Proibido: copiar, baixar, clonar para reuso, usar, modificar, executar
  ou redistribuir este código, no todo ou em parte, sem autorização prévia
  e por escrito do autor.

Todos os direitos são reservados. Veja os termos completos em
[`LICENSE`](./LICENSE).

---

**Sistema de Controle de Equipamentos v2.0.0** 📦
