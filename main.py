"""
Orquestração da rotina diária: execução dos spiders Scrapy e do pipeline de análise de sentimento.
Atualiza status.json e, se houver notícias mapeadas, gera recomendação.
"""
import datetime
import json
import logging
import os
import subprocess
import sys
from typing import List

from config import ARQUIVO_STATUS, SCRAPY_PROJECT_DIR, SPIDER_NAMES

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_scrapers(project_dir: str, spiders: List[str]) -> bool:
    """
    Executa os spiders Scrapy em sequência no diretório do projeto.

    Args:
        project_dir: Caminho da pasta que contém scrapy.cfg.
        spiders: Lista de nomes dos spiders (ex: exame, valor, infomoney, bloomberg).

    Returns:
        True se todos os spiders concluíram com sucesso; False caso contrário.
    """
    logger.info("Mudando para o diretório do Scrapy: %s", project_dir)
    try:
        # Guarda o diretório original para poder voltar depois
        original_dir = os.getcwd()
        os.chdir(project_dir)
    except FileNotFoundError:
        logger.error("Diretório do Scrapy não encontrado: %s", project_dir)
        return False

    logger.info("Iniciando execução dos spiders...")
    for spider in spiders:
        logger.info("Iniciando scraper: %s", spider)
        try:
            subprocess.run(f"scrapy crawl {spider}", shell=True, check=True)
            logger.info("Scraper %s concluído com sucesso.", spider)
        except subprocess.CalledProcessError as e:
            logger.exception("Erro ao executar o scraper %s: %s. Rotina interrompida.", spider, e)
            os.chdir(original_dir)
            return False
        except FileNotFoundError:
            logger.error("Comando 'scrapy' não encontrado. Verifique instalação e PATH.")
            os.chdir(original_dir)
            return False

    os.chdir(original_dir)
    logger.info("Todos os scrapers foram executados com sucesso.")
    return True

def run_analysis(script_name: str) -> bool:
    """
    Executa um script Python (ex: analisar_noticias.py) com o mesmo interpretador do main.

    Args:
        script_name: Nome do arquivo .py (deve estar na raiz do projeto).

    Returns:
        True se o script terminou com sucesso; False caso contrário.
    """
    logger.info("Iniciando script de análise: %s", script_name)
    try:
        subprocess.run([sys.executable, script_name], check=True)
        logger.info("Script de análise %s concluído com sucesso.", script_name)
        return True
    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao executar %s: %s", script_name, e)
        return False
    except FileNotFoundError:
        logger.error("Script de análise não encontrado: %s", script_name)
        return False

def atualizar_status_json(campo: str, valor: str) -> None:
    """Atualiza status.json com um campo (ultima_coleta, ultima_analise)."""
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
    logger.info("Status atualizado: %s = %s", campo, valor)


if __name__ == "__main__":
    now = datetime.datetime.now()
    now_iso = now.isoformat()
    logger.info("=" * 60)
    logger.info("INICIANDO ROTINA DIÁRIA - %s", now)
    logger.info("=" * 60)

    success_scrapers = run_scrapers(SCRAPY_PROJECT_DIR, SPIDER_NAMES)
    if success_scrapers:
        atualizar_status_json("ultima_coleta", now_iso)
        run_analysis("analisar_noticias.py")
        atualizar_status_json("ultima_analise", datetime.datetime.now().isoformat())
        # Gera recomendação se existir notícias mapeadas (associar_tickers já foi rodado)
        try:
            from recomendacao import run_recomendacao
            run_recomendacao()
        except Exception as e:
            logger.warning("Recomendação não executada (pode faltar noticias_mapeadas.json): %s", e)
    else:
        logger.warning("Análise não executada devido a falha nos scrapers.")

    logger.info("=" * 60)
    logger.info("ROTINA DIÁRIA FINALIZADA - %s", datetime.datetime.now())
    logger.info("=" * 60)