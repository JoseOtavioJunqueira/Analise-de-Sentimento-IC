# Guia de Instalação

Instruções para configurar o ambiente do projeto de IC (Análise de Sentimentos — Mercado Financeiro) em padrão USP.

---

## Pré-requisitos

- **Python 3.10** ou superior.
- **Git** (para clonar o repositório).
- Opcional: **MongoDB** (se for usar banco NoSQL em vez de apenas JSON).
- Opcional: **spaCy** e modelo `pt_core_news_lg` para etapas adicionais de PLN.

---

## Passo a passo

### 1. Clonar o repositório

```bash
git clone https://github.com/<usuario>/Analise-de-Sentimento-IC.git
cd Analise-de-Sentimento-IC
```

### 2. Ambiente virtual

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. (Opcional) Modelo de linguagem em português

Para uso de spaCy em tarefas de PLN em português:

```bash
pip install spacy
python -m spacy download pt_core_news_lg
```

### 5. Verificar instalação do Scrapy

Na raiz do projeto:

```bash
cd financial_scraper
scrapy list
```

Devem aparecer os spiders: `bloomberg`, `exame`, `infomoney`, `valor` (e possivelmente `yahoo`).

### 6. Executar a rotina principal

Na **raiz** do projeto (onde está `main.py`):

```bash
python main.py
```

Isso irá:

1. Executar os spiders definidos em `config.py`.
2. Gerar/atualizar `financial_scraper/financial_news.json`.
3. Rodar `analisar_noticias.py` e gerar `noticias_com_sentimento.json`.
4. Atualizar `status.json` (última coleta, última análise).
5. Se existir `noticias_mapeadas.json`, gerar `ultima_recomendacao.json` (recomendação atual).

### 7. Interface Streamlit (dashboard online)

Na **raiz** do projeto:

```bash
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
```

- **Local:** abra no navegador: `http://localhost:8501`
- **Rede:** de outro PC na mesma rede: `http://IP_DA_MAQUINA:8501` (substitua pelo IP da máquina onde o Streamlit está rodando)

A interface exibe: status da última execução, dados coletados, recomendações (investir? onde? quando? por quê?), métricas do backtest (lucro, Sharpe, drawdown) e execução dos testes (pytest).

**Manter rodando em segundo plano (Linux):**
```bash
nohup streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501 > streamlit.log 2>&1 &
```

**Agendar a rotina diária (coleta + análise):** use o **Agendador de Tarefas** (Windows) ou **cron** (Linux) para executar `python main.py` na raiz do projeto (ex.: todo dia às 8h).

---

## Configuração avançada

### Caminhos e spiders

Todas as pastas e nomes de spiders são definidos em **config.py**. Não é necessário editar caminhos absolutos em `main.py` ou `analisar_noticias.py`.

### MongoDB (opcional)

Se quiser usar MongoDB em vez de JSON:

1. Instale e inicie o MongoDB.
2. Configure a URI em variável de ambiente (ex.: `MONGODB_URI`).
3. Ajuste o pipeline do Scrapy em `financial_scraper/financial_scraper/pipelines.py` para gravar no MongoDB.
4. Crie um `.env.example` com `MONGODB_URI=` (sem valor) e documente no README.

### GPU (PyTorch)

Para uso de GPU no modelo BERT:

- Instale PyTorch com suporte CUDA conforme [pytorch.org](https://pytorch.org/get-started/locally/).
- O script `analisar_noticias.py` utiliza o dispositivo disponível automaticamente quando usa `torch`.

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: config` | Executar os scripts a partir da **raiz** do projeto (onde está `config.py`). |
| `scrapy: command not found` | Ativar o venv e garantir que Scrapy está instalado (`pip install scrapy`). |
| Erro ao baixar modelo Hugging Face | Verificar conexão e, se necessário, definir `HF_HOME` ou usar cache local. |
| Caminho não encontrado no Windows | Usar `config.py`; não usar caminhos absolutos em outros arquivos. |

---

## Referências

- [Scrapy — Documentação](https://docs.scrapy.org/)
- [Hugging Face — FinBERT-PT-BR](https://huggingface.co/lucas-leme/FinBERT-PT-BR)
- [Proposta do projeto](Proposta_Pesquisa_IC_2025.pdf)
