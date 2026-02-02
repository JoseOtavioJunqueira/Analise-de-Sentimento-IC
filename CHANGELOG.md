# Changelog

Alterações notáveis do projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [Unreleased]

### Adicionado
- Documentação de arquitetura, instalação e citação em `docs/`.
- Proposta de pesquisa em PDF em `docs/Proposta_Pesquisa_IC_2025.pdf`.
- Configuração centralizada em `config.py` (caminhos, spiders, modelo, seeds).
- Logging estruturado em `main.py`, `analisar_noticias.py`, `associar_tickers.py`, `criar_estrategia.py`.
- Docstrings (estilo Google) e type hints nas funções principais.
- Seeds para reprodutibilidade (numpy/torch) em `analisar_noticias.py`.
- `.env.example` para variáveis de ambiente (MongoDB, Hugging Face).
- Testes unitários com pytest: `tests/test_config.py`, `tests/test_analisar_noticias.py`.
- Schema dos dados em `docs/DADOS_SCHEMA.md`.
- Checklist de profissionalização em `O_QUE_FALTA.md`.
- LICENSE (MIT) e CHANGELOG.md.

### Alterado
- Paths absolutos removidos: uso de `config.py` em todos os scripts.
- `requirements.txt`: apenas dependências (comandos pip removidos).
- `analisar_noticias.py`: pipeline executado em `run_pipeline()` e `if __name__ == "__main__"` para permitir import em testes.
- Modelo FinBERT referenciado por constante `FINBERT_MODEL_NAME` em `config.py`.

### Removido
- `help.txt` (conteúdo incorporado em `docs/INSTALACAO.md`).

---

## [0.1.0] - 2025

### Adicionado
- Coleta de notícias com Scrapy (spiders: exame, valor, infomoney, bloomberg).
- Classificação de sentimento com FinBERT-PT-BR em `analisar_noticias.py`.
- Associação notícias–tickers com spaCy NER em `associar_tickers.py`.
- Backtest da estratégia com VectorBT em `criar_estrategia.py`.
- Orquestração da rotina diária em `main.py`.

---

*Projeto de Iniciação Científica — ICMC/USP, 2025.*
