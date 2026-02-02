# Arquitetura do Projeto

Este documento descreve a arquitetura do sistema de recomendação baseado em análise de sentimentos para o mercado financeiro (projeto de IC — ICMC/USP).

---

## Visão geral

O sistema é composto por três blocos principais:

1. **Coleta de dados** — Scrapy spiders que extraem notícias de portais financeiros.
2. **Processamento e classificação** — Pipeline de PLN que classifica o sentimento das notícias (FinBERT-PT-BR).
3. **Recomendação** — Algoritmo de decisão que gera sinais de compra/venda de ETFs com base nos sentimentos e, no futuro, em aprendizado por reforço.

---

## Fluxo de dados

```
[Portais: Infomoney, Valor, Exame, Bloomberg]
           │
           ▼
    [Scrapy Spiders]
           │
           ▼
  financial_news.json  (ou MongoDB, conforme configuração)
           │
           ▼
  analisar_noticias.py  (FinBERT-PT-BR)
           │
           ▼
  noticias_com_sentimento.json
           │
           ▼
  associar_tickers.py / criar_estrategia.py
           │
           ▼
  [API / Recomendações de compra e venda]
```

---

## Componentes

### 1. Coleta (financial_scraper)

- **Framework:** Scrapy.
- **Spiders:** `exame`, `valor`, `infomoney`, `bloomberg` (definidos em `config.py`).
- **Item:** `FinancialNewsItem` (title, url, date, content, source).
- **Saída:** JSON (`financial_news.json`) ou pipeline para MongoDB (se configurado).

### 2. Análise de sentimentos

- **Modelo:** FinBERT-PT-BR (Hugging Face: `lucas-leme/FinBERT-PT-BR`), adaptado para textos financeiros em português brasileiro.
- **Script:** `analisar_noticias.py` — carrega notícias, normaliza datas, aplica o modelo e salva em `noticias_com_sentimento.json`.
- **Saída:** Mesmo conjunto de notícias enriquecido com campo `sentimento_previsto` (POSITIVE, NEGATIVE, NEUTRAL).

### 3. Estratégia e recomendação

- **associar_tickers.py:** Associa notícias a tickers/ETFs (mapeamento).
- **criar_estrategia.py:** Utiliza sentimentos e dados históricos para gerar a estratégia de recomendação.
- **Perspectiva (proposta):** Integração com ambiente de RL (Q-Learning, DQN, PPO) para decisões sequenciais.

### 4. Orquestração

- **main.py:** Executa em sequência os spiders e, em seguida, o script de análise de sentimentos. Utiliza `config.py` para caminhos e lista de spiders.

---

## Configuração centralizada

O arquivo **config.py** na raiz do projeto define:

- `BASE_DIR`: diretório raiz do repositório.
- `SCRAPY_PROJECT_DIR`: pasta do projeto Scrapy.
- `SPIDER_NAMES`: spiders a serem executados.
- `ARQUIVO_JSON_NOTICIAS` e `ARQUIVO_JSON_SENTIMENTO`: caminhos dos JSONs de entrada e saída.

Assim, não é necessário usar caminhos absolutos em outros scripts.

---

## Dependências principais

- **Python 3.10+**
- **transformers**, **torch** — modelo BERT.
- **scrapy** — coleta.
- **pandas**, **numpy** — processamento.
- **yfinance**, **dateparser** — dados de mercado e datas.

Detalhes em `requirements.txt` e em [INSTALACAO.md](INSTALACAO.md).
