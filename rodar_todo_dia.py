"""
Rotina diária: um único arquivo para agendar (todo dia).

Faz:
  1. Coleta notícias (Scrapy) → pega as mais recentes das primeiras páginas
  2. Filtra para manter só notícias de HOJE e ONTEM
  3. Classificação de sentimento (FinBERT) → noticias_com_sentimento.json
  4. Associar notícias a tickers (NER + mapeamento) → noticias_mapeadas.json
  5. Recomendação (IA: Random Forest ou RL) → compra/venda/segurar → ultima_recomendacao.json
  6. Atualiza status.json

Agende para rodar todo dia (ex.: 8h):
  - Windows: Agendador de Tarefas, ação: python rodar_todo_dia.py, iniciar em: pasta do projeto
  - Linux: crontab -e → 0 8 * * * cd /caminho/projeto && venv/bin/python rodar_todo_dia.py

Execute na raiz do projeto, com venv ativado:
  python rodar_todo_dia.py
"""
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any, List, Optional

import dateparser

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_JSON_NOTICIAS,
    ARQUIVO_STATUS,
    SCRAPY_PROJECT_DIR,
    SPIDER_NAMES,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# --- Normalização de data (para filtrar hoje/ontem) ---
def _normalizar_data(data_str: Optional[Any]) -> Optional[str]:
    if data_str is None or (isinstance(data_str, str) and not str(data_str).strip()):
        return None
    s = str(data_str).strip()
    if not s:
        return None
    if s.isdigit():
        try:
            n = int(s)
            sec = n / 1000.0 if len(s) == 13 else float(n)
            if 946684800 < sec < 2524608000:
                return datetime.fromtimestamp(sec).isoformat()
        except Exception:
            pass
    try:
        obj = dateparser.parse(s, languages=["pt"])
        return obj.isoformat() if obj else None
    except Exception:
        return None


def _data_entre_ontem_e_hoje(iso_date: Optional[str]) -> bool:
    """True se a data estiver entre início de ontem e fim de hoje (horário local)."""
    if not iso_date:
        return True
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00")[:19])
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        ontem_inicio = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = datetime.now()
        return ontem_inicio <= dt <= hoje_fim
    except Exception:
        return True


def _carregar_noticias_brutas(caminho: str) -> List[dict]:
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    if not conteudo.strip():
        return []
    blocos = re.findall(r"(\[.*?\])", conteudo, re.DOTALL)
    lista = []
    for bloco in blocos:
        try:
            lista.extend(json.loads(bloco))
        except json.JSONDecodeError:
            continue
    return lista


def _filtrar_hoje_ontem(noticias: List[dict]) -> List[dict]:
    """Mantém apenas notícias com data de hoje ou ontem."""
    return [n for n in noticias if _data_entre_ontem_e_hoje(_normalizar_data(n.get("date")))]


# --- Execução dos passos ---
def _run_scrapers(project_dir: str, spiders: List[str]) -> bool:
    original = os.getcwd()
    try:
        os.chdir(project_dir)
        for spider in spiders:
            logger.info("Scraper: %s", spider)
            subprocess.run(f"scrapy crawl {spider}", shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.exception("Erro no scraper: %s", e)
        return False
    except FileNotFoundError:
        logger.error("Comando 'scrapy' não encontrado.")
        return False
    finally:
        os.chdir(original)


def _run_script(nome: str) -> bool:
    try:
        subprocess.run([sys.executable, nome], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao executar %s: %s", nome, e)
        return False


def _atualizar_status(campo: str, valor: str) -> None:
    status = {}
    if os.path.exists(ARQUIVO_STATUS):
        try:
            with open(ARQUIVO_STATUS, "r", encoding="utf-8") as f:
                status = json.load(f)
        except Exception:
            pass
    status[campo] = valor
    with open(ARQUIVO_STATUS, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def run() -> None:
    now = datetime.now()
    logger.info("=" * 60)
    logger.info("ROTINA DIÁRIA - %s", now.isoformat())
    logger.info("=" * 60)

    # 1) Coleta (Scrapy)
    ok = _run_scrapers(SCRAPY_PROJECT_DIR, SPIDER_NAMES)
    if not ok:
        logger.warning("Coleta falhou. Continuando com o que existir em %s.", ARQUIVO_JSON_NOTICIAS)

    _atualizar_status("ultima_coleta", now.isoformat())

    # 2) Filtrar só hoje/ontem
    noticias = _carregar_noticias_brutas(ARQUIVO_JSON_NOTICIAS)
    noticias = _filtrar_hoje_ontem(noticias)
    logger.info("Notícias de hoje/ontem: %d", len(noticias))
    with open(ARQUIVO_JSON_NOTICIAS, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

    if not noticias:
        logger.info("Nenhuma notícia de hoje/ontem. Pulando análise (recomendação usa base existente).")
    else:
        # 3) Classificação de sentimento (FinBERT)
        logger.info("Análise de sentimento...")
        _run_script("analisar_noticias.py")
        _atualizar_status("ultima_analise", datetime.now().isoformat())

        # 4) Associar tickers
        logger.info("Associando tickers...")
        _run_script("associar_tickers.py")

    # 5) Recomendação (IA: Random Forest ou RL → compra/venda/segurar)
    logger.info("Gerando recomendação (IA)...")
    try:
        from recomendacao import run_recomendacao
        run_recomendacao()
        _atualizar_status("ultima_recomendacao", datetime.now().isoformat())
    except Exception as e:
        logger.warning("Recomendação: %s", e)

    logger.info("=" * 60)
    logger.info("ROTINA DIÁRIA CONCLUÍDA - %s", datetime.now().isoformat())
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
