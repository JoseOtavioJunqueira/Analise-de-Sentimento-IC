# Aprimoramento de Sistemas de Recomendação em Investimentos Financeiros por meio da Análise de Sentimentos

[![USP](https://img.shields.io/badge/USP-ICMC%20São%20Carlos-blue)](https://www.icmc.usp.br/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)

Projeto de **Iniciação Científica** do Instituto de Ciências Matemáticas e de Computação (ICMC) da Universidade de São Paulo (USP), campus São Carlos. O objetivo é desenvolver um sistema de recomendação de carteiras para operações de day trade em ETFs, combinando **análise de sentimentos** em textos financeiros (PLN) com técnicas de **aprendizado por reforço**.

---

## Autores

- **José Otávio Junqueira Ramos**
- **Luísa Domingues Santello**

**Instituição:** Universidade de São Paulo (USP) — ICMC  
**Curso:** Engenharia de Computação  
**Ano:** 2025  

---

## Objetivos

- Utilizar **Processamento de Linguagem Natural (PLN)** para interpretar o sentimento de textos em português no domínio financeiro (modelo **FinBERT-PT-BR** / **SenFinBERT-PTBR**).
- Construir e ampliar uma **base de dados** de notícias financeiras (Scrapy + MongoDB).
- Desenvolver uma **API em Python** que utilize os dados classificados para recomendar operações de compra e venda de ETFs no mercado brasileiro.
- Validar o desempenho por meio de métricas financeiras (retorno, Sharpe ratio, drawdown) e comparação com indicadores como a taxa Selic.
- Explorar **aprendizado por reforço** (Q-Learning, DQN, PPO) para decisões sequenciais no ambiente de mercado.

---

## Estrutura do repositório

```
Analise-de-Sentimento-IC/
├── docs/                    # Documentação e proposta
│   ├── Proposta_Pesquisa_IC_2025.pdf
│   ├── ARCHITETURA.md
│   ├── INSTALACAO.md
│   └── CITACAO.md
├── financial_scraper/       # Projeto Scrapy (coleta de notícias)
│   └── financial_scraper/
│       ├── spiders/        # Spiders: Infomoney, Valor, Exame, Bloomberg
│       ├── items.py
│       ├── pipelines.py
│       └── settings.py
├── sentimentprevision/      # Modelo de sentimento (FinBERT-PT-BR)
├── analisar_noticias.py     # Pipeline: classificação de notícias
├── associar_tickers.py      # Associação notícias–tickers
├── criar_estrategia.py      # Backtest da estratégia (VectorBT)
├── recomendacao.py          # Recomendação (modelo treinado ou regra fixa)
├── treinar_modelo_decisao.py # Treino da IA: histórico sentimento → subiu/caiu
├── main.py                  # Orquestração: scrapers + análise + recomendação
├── app_streamlit.py         # Interface web (status, dados, recomendações, backtest, testes)
├── config.py                # Configurações e caminhos do projeto
├── tests/                   # Testes pytest (config, analisar_noticias)
├── scripts/                 # Scripts auxiliares (avaliacao_metricas.py)
├── requirements.txt
├── pytest.ini
├── O_QUE_FALTA.md           # Checklist de profissionalização (nível USP)
├── CHANGELOG.md
├── LICENSE                  # MIT
└── README.md
```

---

## Instalação e uso

1. **Clone o repositório** e crie um ambiente virtual:
   ```bash
   git clone https://github.com/<seu-usuario>/Analise-de-Sentimento-IC.git
   cd Analise-de-Sentimento-IC
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   # ou: venv\Scripts\activate  # Windows
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   Para uso do modelo de linguagem em português (opcional):
   ```bash
   pip install spacy
   python -m spacy download pt_core_news_lg
   ```

3. **Execute a rotina principal** (scrapers + análise de sentimentos + recomendação):
   ```bash
   python main.py
   ```

4. **Interface online (Streamlit)** — status, dados, recomendações, backtest e testes:
   ```bash
   streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
   ```
   Acesse em `http://localhost:8501` (ou `http://IP_DA_MAQUINA:8501` de outro PC na rede).

Para detalhes de instalação (MongoDB, Scrapy, variáveis de ambiente, agendamento), consulte **[docs/INSTALACAO.md](docs/INSTALACAO.md)**.

4. **Testes (opcional):**
   ```bash
   pip install pytest
   pytest
   ```
   Os testes estão em `tests/` (config, funções de normalização e deduplicação).

---

## Documentação adicional

| Documento | Descrição |
|-----------|-----------|
| [docs/ESSENCIA_DO_PROJETO.md](docs/ESSENCIA_DO_PROJETO.md) | **Essência do projeto:** coleta (notícia+data), sentimento, qual ação, subiu/caiu, IA aprende |
| [docs/COMO_RODAR_NO_LAB_E_PROXIMOS_PASSOS.md](docs/COMO_RODAR_NO_LAB_E_PROXIMOS_PASSOS.md) | **Como rodar no lab** e **quando fazer o quê** (tudo mastigado) |
| [docs/PARA_LUISA_E_DENIS_ATUALIZACOES.md](docs/PARA_LUISA_E_DENIS_ATUALIZACOES.md) | **Texto para Luísa e Denis:** o que há de novo no código e próximos passos |
| [docs/Proposta_Pesquisa_IC_2025.pdf](docs/Proposta_Pesquisa_IC_2025.pdf) | Proposta completa da pesquisa (PDF) |
| [docs/ARCHITETURA.md](docs/ARCHITETURA.md) | Arquitetura do sistema e fluxo de dados |
| [docs/INSTALACAO.md](docs/INSTALACAO.md) | Guia de instalação e pré-requisitos |
| [docs/CITACAO.md](docs/CITACAO.md) | Como citar o projeto e o modelo FinBERT-PT-BR |
| [O_QUE_FALTA.md](O_QUE_FALTA.md) | Checklist do que falta para nível USP |

---

## Base científica e citação

- O modelo de sentimento utilizado é o **FinBERT-PT-BR** (Santos 2022). Veja [docs/CITACAO.md](docs/CITACAO.md) para a citação correta.
- A base de notícias parte do trabalho de **Lucas L. Santos (2022)**; a expansão é feita via Scrapy a partir de fontes como Infomoney, Valor Econômico e Exame.

---

## Licença e uso acadêmico

Este repositório é parte de um projeto de Iniciação Científica da USP. O uso dos dados coletados deve respeitar os termos de uso dos sites de origem e as boas práticas de web scraping (robots.txt, rate limiting).

---

## Contato

Para dúvidas relacionadas ao projeto de IC, entre em contato através do ICMC/USP ou pelos canais indicados pela instituição.
