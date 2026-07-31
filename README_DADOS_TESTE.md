# 📊 Dados de Teste - Sistema de Controle de Equipamentos

## Visão Geral

O script `gerar_dados_teste.py` cria um conjunto completo de dados fictícios para testar todas as funcionalidades do sistema.

---

## 📅 Período dos Dados

| Período | Meses | Quantidade Aprox. |
|---------|-------|-------------------|
| **2023** | Janeiro - Dezembro | ~360 registros |
| **2024** | Janeiro - Dezembro | ~360 registros |
| **2025** | Janeiro - Dezembro | ~360 registros |
| **2026** | Janeiro - Dezembro | ~360 registros |
| **Total** | 48 meses | ~1440 registros |

---

## 👷 Colaboradores Cadastrados

```
1. JOÃO SILVA
2. MARIA SANTOS
3. PEDRO OLIVEIRA
4. ANA COSTA
5. CARLOS SOUZA
6. JULIANA LIMA
7. RICARDO ALVES
8. FERNANDA ROCHA
9. BRUNO MARTINS
10. PATRICIA FERNANDES
```

---

## 📍 Locais Cadastrados

```
1. FILIAL CENTRO
2. FILIAL NORTE
3. FILIAL SUL
4. FILIAL LESTE
5. FILIAL OESTE
6. MATRIZ
7. ALMOXARIFADO CENTRAL
8. LOJA SHOPPING
9. DEPÓSITO A
10. UNIDADE INDUSTRIAL
```

---

## 📦 Equipamentos Cadastrados

```
NOTEBOOK-001, NOTEBOOK-002, NOTEBOOK-003, NOTEBOOK-004, NOTEBOOK-005
TABLET-001, TABLET-002, TABLET-003, TABLET-004, TABLET-005
MONITOR-001, MONITOR-002, MONITOR-003, MONITOR-004, MONITOR-005
IMPRESSORA-001, IMPRESSORA-002, SCANNER-001, PROJETOR-001, CAMERA-001
```

Total: 20 equipamentos

---

## 🏢 Clientes Cadastrados

```
EMPRESA ABC LTDA
COMERCIO XYZ
INDUSTRIA 123
LOJA DO JOÃO
SUPERMERCADO BOM PREÇO
FARMÁCIA SAÚDE
CONSTRUTORA ALFA
ESCRITÓRIO BETA
CLINICA VIDA
RESTAURANTE SABOR
(SEM CLIENTE) - Movimentações internas
```

Alguns registros têm cliente NULL (movimentações internas).

---

## 🎲 Características dos Dados

### Distribuição de Registros
- **20 a 60 registros por mês** (aleatório)
- **Distribuição uniforme** entre colaboradores, locais e equipamentos

### Tipos de Movimentação
| Tipo | Probabilidade | Cor |
|------|--------------|-----|
| ENTREGA 🔴 | 50% | Vermelho |
| RETIRADA 🟡 | 50% | Amarelo |

### Horários
- **Entre 07:00 e 18:00**
- **Minutos:** 00, 15, 30 ou 45

---

## 📁 Arquivos JSON Criados

```
arquivos_mensais/
├── registros_2023-01.json
├── registros_2023-02.json
├── registros_2023-03.json
├── ...
├── registros_2025-12.json
├── registros_2026-01.json
├── ...
└── registros_2026-12.json
```

### Formato do JSON
```json
[
  {
    "id": 1,
    "data": "15/01/2024",
    "colaborador": "JOÃO SILVA",
    "equipamento": "NOTEBOOK-005",
    "cliente": "EMPRESA ABC LTDA",
    "local": "FILIAL CENTRO",
    "horario": "08:30",
    "tipo": "ENTREGA"
  },
  {
    "id": 2,
    "data": "15/01/2024",
    "colaborador": "MARIA SANTOS",
    "equipamento": "TABLET-003",
    "cliente": null,
    "local": "MATRIZ",
    "horario": "14:00",
    "tipo": "RETIRADA"
  },
  ...
]
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela `registros`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| data | TEXT | DD/MM/AAAA |
| colaborador | TEXT | Nome do colaborador |
| equipamento | TEXT | Nome do equipamento |
| cliente | TEXT | Cliente (pode ser NULL) |
| local | TEXT | Nome do local |
| horario | TEXT | HH:MM |
| tipo | TEXT | ENTREGA ou RETIRADA |

### Tabela `colaboradores`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome único |

### Tabela `locais`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome único |

### Tabela `equipamentos`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome único |

---

## 🚀 Como Usar

### Gerar dados (limpa anteriores)
```bash
python gerar_dados_teste.py
# Responda "S" para limpar dados anteriores
```

### Adicionar mais dados
```bash
python gerar_dados_teste.py
# Responda "N" para manter dados existentes
```

### Saída esperada
```
============================================================
🎲 GERADOR DE DADOS DE TESTE
Sistema de Controle de Equipamentos
============================================================

📆 Período: Janeiro/2023 até Dezembro/2026
📊 Tipos: ENTREGA (🔴) e RETIRADA (🟡)

⚠️  Limpar dados existentes? (S/N): S

🔧 Inicializando banco de dados...
✅ Estrutura do banco criada automaticamente
🗑️  Limpando dados anteriores...
✅ Dados anteriores removidos

👷 Cadastrando colaboradores...
✅ 10 colaboradores cadastrados

📍 Cadastrando locais...
✅ 10 locais cadastrados

📦 Cadastrando equipamentos...
✅ 20 equipamentos cadastrados

📊 Gerando registros para 2023...
   Mês 01/2023: 35 registros
   Mês 02/2023: 42 registros
   ...

✅ Total 2023: 380 registros gerados
   🔴 Entregas: 195
   🟡 Retiradas: 185

📊 Gerando registros para 2024...
...

📁 Criando arquivos mensais...
   ✅ arquivos_mensais/registros_2023-01.json (35 registros)
   ✅ arquivos_mensais/registros_2023-02.json (42 registros)
   ...

============================================================
📊 ESTATÍSTICAS DOS DADOS GERADOS
============================================================

📌 Total de Registros: 1520
🔴 Total de Entregas: 760
🟡 Total de Retiradas: 760

📅 Registros por Ano:
   2023: 380 registros (🔴 195 entregas, 🟡 185 retiradas)
   2024: 385 registros (🔴 190 entregas, 🟡 195 retiradas)
   2025: 378 registros (🔴 188 entregas, 🟡 190 retiradas)
   2026: 377 registros (🔴 187 entregas, 🟡 190 retiradas)

👷 Top 5 Colaboradores:
   1. MARIA SANTOS: 165 registros
   2. JOÃO SILVA: 158 registros
   ...

📍 Top 5 Locais:
   1. MATRIZ: 180 registros
   ...

📦 Top 5 Equipamentos:
   1. NOTEBOOK-003: 95 registros
   ...

============================================================
✅ DADOS DE TESTE GERADOS COM SUCESSO!
============================================================
```

---

## 📈 Estatísticas Típicas

Após gerar os dados, você verá estatísticas como:

| Métrica | Valor Típico |
|---------|-------------|
| Total de registros | 1400-1600 |
| Registros por mês | 20-60 |
| Total de entregas | ~50% |
| Total de retiradas | ~50% |
| Colaboradores ativos | 10 |
| Locais utilizados | 10 |
| Equipamentos em uso | 20 |

---

## 💡 Dicas

### Testar filtros
Com ~1500 registros distribuídos em 48 meses, você tem dados suficientes para:
- Filtrar por diferentes anos e meses
- Ver variações nos gráficos
- Comparar entregas vs retiradas
- Testar exportações completas

### Testar por tipo
Use o filtro de tipo para ver:
- Apenas ENTREGAS 🔴
- Apenas RETIRADAS 🟡
- Todos os registros

### Resetar o ambiente
```bash
rm equip_control.db
rm -rf arquivos_mensais/
python gerar_dados_teste.py
```

---

## ⚠️ Observações

1. **Dados são aleatórios** - cada execução gera valores diferentes
2. **IDs são sequenciais** - começam em 1 após limpar
3. **Arquivos JSON** - são recriados a cada execução
4. **Banco SQLite** - arquivo `equip_control.db` na raiz do projeto
5. **Clientes podem ser NULL** - simula movimentações internas

---

**Gerador de Dados v2.0** 🎲
