# 📝 Changelog - Sistema de Controle de Equipamentos

## Versão 2.0.0 (Janeiro 2026)

### ✨ Nova Arquitetura MVC

O sistema foi completamente refatorado para uma arquitetura MVC (Model-View-Controller) limpa e modular.

---

## 🏗️ Mudanças Estruturais

### Database Centralizado
Agora **TODAS** as tabelas são criadas automaticamente pelo `models/database.py`:

- ✅ `registros` - Registros de movimentações (entregas/retiradas)
- ✅ `colaboradores` - Cadastro de colaboradores
- ✅ `locais` - Cadastro de locais
- ✅ `equipamentos` - Cadastro de equipamentos
- ✅ `config` - Configurações do sistema
- ✅ `registro_historico` - Histórico de alterações

### Antes:
```python
# main_window.py criava as tabelas
# gerar_dados_teste.py também criava as tabelas
# Código duplicado em 2 lugares
```

### Agora:
```python
# database.py cria TUDO automaticamente
# main.py → Database → cria tabelas
# gerar_dados_teste.py → Database → cria tabelas
# Código centralizado em 1 lugar!
```

---

## 📊 Estrutura de Arquivos

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `main.py` | 11 | Ponto de entrada |
| `settings.py` | 15 | Configurações |
| `database.py` | 160 | Model - Banco de dados |
| `main_window.py` | 1589 | View Principal |
| `stats_manager.py` | 1357 | Gerenciador de Estatísticas |
| `ranking_manager.py` | 645 | Gerenciador de Rankings |
| `record_window.py` | 399 | Janela de Registros |
| `scrollable_combobox.py` | 420 | Widget ComboBox |
| `progress_dialog.py` | 132 | Diálogo de Progresso |
| `history_dialog.py` | 100 | Diálogo de Histórico |
| `helpers.py` | 77 | Funções auxiliares |
| `tooltip.py` | 31 | Widget Tooltip |
| `colors_helper.py` | 100 | Helper de cores |
| `gerar_dados_teste.py` | 300 | Gerador de dados |
| **Total** | **~5300** | - |

---

## 🆕 Novidades

### Sistema de Movimentações
- **ENTREGA** 🔴 - Equipamento sai do estoque (cor: `#dc2626`)
- **RETIRADA** 🟡 - Equipamento volta ao estoque (cor: `#eab308`)
- Cores vibrantes nas tabelas (`#fca5a5` e `#fde047`)

### Campo Cliente (Opcional)
- Identifica para qual cliente foi a movimentação
- Filtro por cliente nas abas
- Campo opcional (pode ser interno)

### StatsManager com 9 Linhas de Gráficos
1. Evolução Temporal de Retiradas e Entregas (barras) + Linha Total
2. Entregas/Retiradas por Colaborador + Pizza Entregas vs Retiradas
3. Entregas/Retiradas por Local
4. Entregas/Retiradas por Equipamento
5. Entregas por Colaborador (pizza) + Retiradas por Colaborador (pizza)
6. Entregas por Local (pizza) + Retiradas por Local (pizza)
7. Entregas por Equipamento (pizza) + Retiradas por Equipamento (pizza)
8. Top 5 Colaboradores + Top 5 Locais
9. Top 5 Equipamentos + Métricas de Performance

### RankingManager Separado
- Aba dedicada para rankings
- Visualização por Equipamentos, Colaboradores ou Locais
- Medalhas: 🥇 Ouro, 🥈 Prata, 🥉 Bronze, 🏅 Cobre
- Exportação PDF e CSV

### Widgets Customizados
- `ScrollableComboBox` - ComboBox com scroll e busca
- `ProgressDialog` - Diálogo de progresso com barra
- `Tooltip` - Dicas ao passar o mouse

### Sistema de Histórico
- Rastreamento de todas alterações
- Criação, edição e exclusão registrados
- Visualização completa do histórico por registro

---

## 🎯 Benefícios

1. ✅ **Sem erros de tabela não encontrada**
   - Database sempre cria tudo automaticamente

2. ✅ **Código não duplicado**
   - Uma única fonte de verdade

3. ✅ **Mais fácil manutenção**
   - Mudar schema? Apenas em database.py

4. ✅ **Funciona em qualquer lugar**
   - `main.py` → cria banco
   - `gerar_dados_teste.py` → cria banco
   - Qualquer script → cria banco

5. ✅ **Estatísticas otimizadas**
   - Fechamento correto de figuras matplotlib
   - Sem memory leak

6. ✅ **Interface responsiva**
   - Tela de progresso em exportações
   - Feedback visual ao usuário

---

## 🔧 Correções

- Fix: Memory leak em gráficos matplotlib
- Fix: Scroll em ComboBox com muitos itens
- Fix: Cores do tema escuro em dropdowns
- Fix: Validação de datas e horários
- Fix: Arquivamento mensal automático
- Fix: Cores mais vibrantes nas tabelas

---

## 📦 Dependências

```
customtkinter>=5.2.0
tkcalendar>=1.6.1
matplotlib>=3.7.0
plotly>=5.15.0
openpyxl>=3.1.2
Pillow>=10.0.0
reportlab>=4.0.0
numpy>=1.24.0
```

---

**Sistema de Controle de Equipamentos v2.0.0** 🎉
