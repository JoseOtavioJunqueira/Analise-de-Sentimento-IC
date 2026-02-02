"""
Testes do módulo config: caminhos relativos e constantes.
"""
import os

import pytest

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_JSON_NOTICIAS,
    ARQUIVO_JSON_SENTIMENTO,
    ARQUIVO_MAPEAMENTO_TICKERS,
    ARQUIVO_RESULTADOS_BACKTEST,
    BASE_DIR,
    FINBERT_MODEL_NAME,
    RANDOM_SEED,
    SCRAPY_PROJECT_DIR,
    SPIDER_NAMES,
)


def test_base_dir_exists():
    """BASE_DIR deve ser um diretório existente (raiz do projeto)."""
    assert os.path.isdir(BASE_DIR), "BASE_DIR deve existir e ser um diretório"


def test_scrapy_project_dir_under_base():
    """SCRAPY_PROJECT_DIR deve estar dentro de BASE_DIR."""
    assert SCRAPY_PROJECT_DIR.startswith(BASE_DIR)
    assert "financial_scraper" in SCRAPY_PROJECT_DIR


def test_spider_names_non_empty():
    """SPIDER_NAMES deve conter pelo menos um spider."""
    assert isinstance(SPIDER_NAMES, list)
    assert len(SPIDER_NAMES) >= 1
    assert all(isinstance(s, str) and s for s in SPIDER_NAMES)


def test_arquivos_json_paths():
    """Caminhos de JSON devem terminar com os nomes esperados."""
    assert ARQUIVO_JSON_NOTICIAS.endswith("financial_news.json") or "financial_news" in ARQUIVO_JSON_NOTICIAS
    assert "noticias_com_sentimento" in ARQUIVO_JSON_SENTIMENTO
    assert "noticias_mapeadas" in ARQUIVO_JSON_MAPEADAS
    assert "mapeamento_tickers" in ARQUIVO_MAPEAMENTO_TICKERS
    assert "resultados_backtest" in ARQUIVO_RESULTADOS_BACKTEST or "backtest" in ARQUIVO_RESULTADOS_BACKTEST


def test_finbert_model_name():
    """Modelo FinBERT deve ser o esperado (Santos 2022)."""
    assert "FinBERT" in FINBERT_MODEL_NAME or "finbert" in FINBERT_MODEL_NAME.lower()


def test_random_seed_integer():
    """RANDOM_SEED deve ser inteiro para reprodutibilidade."""
    assert isinstance(RANDOM_SEED, int)
    assert RANDOM_SEED >= 0
