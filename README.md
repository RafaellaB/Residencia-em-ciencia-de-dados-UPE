# Dashboard Coordenações UPE

Dashboard Streamlit para visualização de dados das coordenações de **Pós Lato-Sensu** e **Inovação** da UPE.

## 📋 Requisitos

- Python 3.12.3+
- Bibliotecas listadas em `requirements.txt`

## 🚀 Instalação e Execução

### 1. Instalar dependências

```bash
python -m pip install --user -r requirements.txt
```

### 2. Executar o dashboard

```bash
python -m streamlit run app.py
```

O dashboard abrirá em `http://localhost:8501`

## 📊 Estrutura do Dashboard

### Tab 1: Pós Lato-Sensu

**Filtros:**
- **UNIDADE**: Filtra dados por unidade acadêmica

**Gráficos:**
1. **Quantidade de Cursos em Andamento** - Gráfico de barras mostrando o total de cursos com status "EM ANDAMENTO"
2. **Top 10 Denominações com Mais Alunos Matriculados** - Gráfico de barras horizontal com as 10 denominações de cursos que possuem mais alunos matriculados (filtrados pela unidade selecionada)

### Tab 2: Inovação

**Filtros:**
- **Ano de Criação**: Filtra projetos por ano

**Gráficos:**
1. **Quantidade de Projetos por Unidade** - Gráfico de barras horizontal mostrando a distribuição de projetos por unidade
2. **Quantidade de Projetos por Via** - Gráfico de barras vertical mostrando a quantidade de projetos agrupados por via (IAUPE, UPE, RESITEC, etc.)
3. **Top 15 Cidades com Mais Projetos** - Gráfico de barras horizontal com as 15 cidades que possuem mais projetos de inovação
4. **Quantidade de Projetos por Natureza** - Gráfico de barras vertical mostrando os tipos de natureza dos projetos (PD&I, RESITEC, etc.)

## 📁 Arquivos

- `app.py` - Aplicação principal do Streamlit
- `dados_coordenacoes.csv` - Arquivo de dados com informações combinadas das coordenações
- `requirements.txt` - Dependências Python do projeto

## 🎨 Características

- ✅ Todos os gráficos são de barras (sem gráficos de pizza)
- ✅ Suporte a múltiplos filtros dinâmicos por coordenação
- ✅ Interface responsiva com layout wide
- ✅ Tratamento de dados e limpeza automatizados
- ✅ Tabs para organizar dados por coordenação

## 🧹 Tratamento de Dados (limpeza e transformação)

- **Leitura e concatenação**: as abas "pós lato sensu" e "inov" são lidas e concatenadas em um único DataFrame.
- **Normalização de colunas**: nomes de colunas são normalizados (minúsculo, sem acentos, com `_`) para identificar campos mesmo em MAIÚSCULO.
- **Números inteiros**: `parse_int_series` remove caracteres não numéricos e converte para `int` (vazios viram 0).
- **Valores monetários**: `parse_money_series` remove símbolos e converte vírgula para ponto, retornando `float`.
- **Filtragem por seleção**: filtros de unidade (Pós) e ano (Inovação) aplicam recortes no DataFrame.
- **Remoção de nulos/vazios**: antes das agregações, linhas com valores vazios são descartadas.
- **Agregações**:
	- Pós: cursos em andamento e top 10 denominações com mais alunos.
	- Inovação: projetos por unidade, via, cidade e natureza.

## 🔎 Fluxo de Dados (resumo)

```mermaid
flowchart LR
		A[Google Sheets: abas "pós lato sensu" + "inov"] --> B[Leitura das abas]
		B --> C[Concatenação dos dados]
		C --> D[Normalização dos nomes das colunas]
		D --> E[Limpeza: nulos, vazios, conversões]
		E --> F[Filtros: unidade (Pós) e ano (Inovação)]
		F --> G[Agregações e métricas]
		G --> H[Gráficos e KPIs no Streamlit]
```

## 📡 Google Sheets (leitura online)

O projeto pode carregar dados diretamente de uma planilha Google (padrão definido para a planilha fornecida). Para funcionar corretamente:

1. Crie uma Service Account no Google Cloud e baixe o arquivo JSON de credenciais.
2. Compartilhe a planilha no Drive com o e-mail da service account (ex.: `xxxx@xxxx.iam.gserviceaccount.com`).
3. Defina a variável de ambiente `GOOGLE_SERVICE_ACCOUNT_FILE` apontando para o JSON:

```powershell
$env:GOOGLE_SERVICE_ACCOUNT_FILE = 'C:\caminho\para\service-account.json'
```

Você pode sobrescrever a planilha padrão definindo `SPREADSHEET_URL` ou `SPREADSHEET_ID`:

```powershell
$env:SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/SEU_ID'
# ou apenas o ID
$env:SPREADSHEET_ID = 'SEU_ID'
```

Após configurar, rode:

```bash
streamlit run app.py
```
