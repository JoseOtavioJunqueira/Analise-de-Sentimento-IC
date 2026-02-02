"""
Configurações centralizadas do projeto.
Usa caminhos relativos à raiz do repositório para portabilidade.
"""
import os
from typing import List

# Diretório raiz do projeto (onde estão main.py, config.py, etc.)
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Diretório do projeto Scrapy (contém scrapy.cfg)
SCRAPY_PROJECT_DIR: str = os.path.join(BASE_DIR, "financial_scraper")

# Spiders a serem executados na rotina principal
SPIDER_NAMES: List[str] = [
    "exame",
    "valor",
    "infomoney",
    "bloomberg",
]

# Arquivos de dados (relativos a BASE_DIR)
ARQUIVO_JSON_NOTICIAS: str = os.path.join(SCRAPY_PROJECT_DIR, "financial_news.json")
ARQUIVO_JSON_SENTIMENTO: str = os.path.join(BASE_DIR, "noticias_com_sentimento.json")
ARQUIVO_JSON_MAPEADAS: str = os.path.join(BASE_DIR, "noticias_mapeadas.json")
ARQUIVO_MAPEAMENTO_TICKERS: str = os.path.join(BASE_DIR, "mapeamento_tickers.json")
ARQUIVO_RESULTADOS_BACKTEST: str = os.path.join(BASE_DIR, "resultados_backtest_v1.html")
ARQUIVO_ULTIMA_RECOMENDACAO: str = os.path.join(BASE_DIR, "ultima_recomendacao.json")
ARQUIVO_ULTIMO_BACKTEST_JSON: str = os.path.join(BASE_DIR, "ultimo_backtest.json")
ARQUIVO_STATUS: str = os.path.join(BASE_DIR, "status.json")
# Modelo treinado para decisão compra/venda/segurar (histórico: sentimento → retorno)
ARQUIVO_MODELO_DECISAO: str = os.path.join(BASE_DIR, "modelo_decisao.joblib")
ARQUIVO_CONFIG_MODELO_DECISAO: str = os.path.join(BASE_DIR, "config_modelo_decisao.json")

# Modelo de sentimento (FinBERT-PT-BR) — versionamento para reprodutibilidade
# Ref: Santos (2022) — docs/CITACAO.md
FINBERT_MODEL_NAME: str = "lucas-leme/FinBERT-PT-BR"

# Seeds para reprodutibilidade (numpy, torch)
RANDOM_SEED: int = 42
