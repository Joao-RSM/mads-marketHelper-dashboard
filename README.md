# Análise dos dados do Mads Market Helper

Aplicação web em Flask que lê dados de um Google Sheets e apresenta tabelas, mapa interativo, dashboard e validação de dados, com controlo de acesso por chaves.

Relatório do projeto desenvolvido disponível em: [docs.google.com](https://docs.google.com/document/d/13gSFjmzMoq2zGprYOtWKZ1EMkF2OzDOVnUL1zNi6VSw/edit?tab=t.0#heading=h.2ktf1rf4d27p)

> Projeto disponível na plataforma Render.com [Link do Projeto](https://mads-markethelper-dashboard.onrender.com). As chaves de acesso aos dados privados estão disponíveis no relatório do projeto.

> Com apoio de [Gemini](https://gemini.google.com) e [ChatGPT](https://chatgpt.com)

>Aviso: Os dados incluídos neste projeto são fictícios e utilizados exclusivamente em contexto educacional e de demonstração.

--- 

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Tabelas** | Acesso individual para leitura das abas de Utilizadores, Compras e Categorias com chaves dedicadas. |
| **Mapa** | Marcadores geográficos das superfícies comerciais registadas. |
| **Dashboard** | Painel analítico de métricas de negócio (Vendas e Lucro por loja, Distribuição de categorias, Preços médios). |
| **Integridade** | Validação automática dos dados com relatório de erros estruturais e órfãos. |
| **Acesso** | Controlo por chaves configuráveis. |

---

## Pré-requisitos

- Python 3.9+
- Conta Google com acesso ao [Google Cloud Console](https://console.cloud.google.com)
- Google Sheets (`Base de Dados - Utilizadores - Grupo 2`) partilhada com a conta de serviço
- Ficheiro JSON com as credenciais do Google

---

## Instalação

```bash
# 1. Entrar na pasta do projeto
cd mads-marketHelper

# 2. Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Instalar dependências
pip install -r requirements.txt

```

---

## Configuração

### 1. Credenciais do Google

No [Google Cloud Console](https://console.cloud.google.com):

1. Criar um projeto e ativar a **Google Sheets API** e a **Google Drive API**
2. Criar uma **conta de serviço** e descarregar o ficheiro JSON
3. Guardar o ficheiro em `secrets/`
4. Partilhar a folha de cálculo com o email da conta de serviço

Em `app.py`, ajustar conforme necessário:

```python
scope = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]
creds = ServiceAccountCredentials.from_json_keyfile_name(service_file_path, scope)
gc = gspread.authorize(creds)
sheet = gc.open("Base de Dados - Utilizadores - Grupo 2")

```

### 2. Chaves de acesso

Criar `secrets/chave.json` com o mapeamento das chaves do projeto:

```json
{
  "dados_privados": "coloque_a_sua_chave_aqui",
  "integridade_admin": "coloque_a_sua_chave_aqui",
  "item_carne": "coloque_a_sua_chave_aqui",
  "item_frango": "coloque_a_sua_chave_aqui",
  "item_leite": "coloque_a_sua_chave_aqui",
  "ver_utilizadores": "coloque_a_sua_chave_aqui",
  "ver_compras": "coloque_a_sua_chave_aqui",
  "ver_categorias": "coloque_a_sua_chave_aqui",
}

```

Em produção (ex.: Render), definir `isProduction=true`. A aplicação irá procurar as credenciais em `/etc/secrets/`.

---

## Execução

**Desenvolvimento:**

```bash
python app.py
# Disponível em [http://127.0.0.1:5000](http://127.0.0.1:5000)

```

**Produção (Render):**

* Build command: `pip install -r requirements.txt`
* Start command: `python app.py`
* Variável de ambiente: `isProduction=true`
* Credenciais disponíveis em `/etc/secrets/`

---

## Estrutura do projeto

```text
├── app.py                # Aplicação Flask principal (Rotas e controlo de chaves)
├── integridade.py        # Módulo de validação de dados e auditoria
├── mapa.py               # Módulo de geolocalização e mapa interativo das lojas
├── dashboard.py          # Módulo de extração analítica e geração de gráficos
├── requirements.txt      # Dependências do projeto
├── README.md             # Este ficheiro
└── templates/            # Ficheiros HTML estruturados com Jinja2
    ├── base.html         # Navbar e estrutura base comum
    ├── landing.html      # Landing Page pública com mapa e caixa de acesso
    ├── dados.html        # Painel comparativo de métricas de negócio
    ├── ver_tabela.html   # Visualização dinâmica e flexível das tabelas da Cloud
    └── integridade.html  # Relatório visual de erros estruturais

```

---

## Validações de integridade

**Todas as tabelas**

* Tabela ou cabeçalho vazios, colunas duplicadas, número de colunas inconsistente ou registos nulos.

**Lojas**

* Nome/Localização vazios ou registos geográficos duplicados na mesma localidade, categoria ou especialidade inexistente fora da lista fechada (*Padaria, Talho, Peixaria, Supermercado*).

**Utilizadores**

* NIF vazio ou duplicado, NIF com comprimento inválido fora dos 9 dígitos, género inválido (apenas M, F ou O), idade calculada através da data de nascimento não positiva.

**Compras**

* NIFs de utilizador ou IDs de lojas inexistentes nas tabelas base (dados órfãos), preço não positivo (float <= 0), tipo de pagamento inválido quando especificado, produto guardado automaticamente em minúsculas via `.lower()`.

---

## Autores

João Martins, José Mendonça, Rodrigo Santos, Mário Pinto

**Unidade Curricular:** Metodologias Ágeis de Desenvolvimento de Software · Projeto 2

**Data:** Maio de 2026 · **Instituição:** Instituto Politécnico da Maia (IPMAIA)
