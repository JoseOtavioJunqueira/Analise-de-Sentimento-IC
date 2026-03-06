"""
Script para AGORA: coleta notícias dos últimos 3 meses e preenche a base.

Use quando você não deixou a coleta rodando por meses e precisa de dados
históricos de uma vez: roda os spiders (com paginação), filtra por data,
analisa sentimento e associa tickers.

Uso (na raiz do projeto, com venv ativado):
    python coletar_ultimos_3_meses.py
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
    SCRAPY_PROJECT_DIR,
    SPIDER_NAMES,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MESES_ATRAS = 3


def normalizar_data(data_str: Optional[Any]) -> Optional[str]:
    """
    Converte string ou número de data para ISO 8601.
    Cópia da lógica de analisar_noticias (sem depender de torch).
    """
    if data_str is None or (isinstance(data_str, str) and not data_str.strip()):
        return None
    data_como_str = str(data_str).strip()
    if not data_como_str:
        return None

    if data_como_str.isdigit():
        try:
            num_data = int(data_como_str)
            num_digitos = len(data_como_str)
            timestamp_sec = None
            if num_digitos == 13:
                timestamp_sec = num_data / 1000.0
            elif num_digitos == 10:
                timestamp_sec = float(num_data)
            if timestamp_sec is not None and 946684800 < timestamp_sec < 2524608000:
                return datetime.fromtimestamp(timestamp_sec).isoformat()
        except Exception:
            pass

    try:
        data_obj = dateparser.parse(data_como_str, languages=["pt"])
        return data_obj.isoformat() if data_obj else None
    except Exception:
        return None


def data_dentro_periodo(iso_date: Optional[str], limite: datetime) -> bool:
    """Retorna True se iso_date for >= limite (dentro dos últimos N meses)."""
    if not iso_date:
        return True  # mantém itens sem data para o pipeline decidir
    try:
        # ISO pode ter 'Z' ou timezone
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00")[:19])
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt >= limite
    except Exception:
        return True


def carregar_noticias_brutas(caminho: str) -> List[dict]:
    """Carrega e consolida blocos JSON do arquivo de notícias (formato Scrapy)."""
    if not os.path.exists(caminho):
        logger.warning("Arquivo não encontrado: %s", caminho)
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    if not conteudo.strip():
        return []
    blocos = re.findall(r"(\[.*?\])", conteudo, re.DOTALL)
    if not blocos:
        return []
    lista = []
    for bloco in blocos:
        try:
            lista.extend(json.loads(bloco))
        except json.JSONDecodeError:
            continue
    return lista


def filtrar_ultimos_meses(noticias: List[dict], meses: int) -> List[dict]:
    """Mantém apenas notícias com data nos últimos `meses`."""
    limite = datetime.now() - timedelta(days=meses * 31)
    filtradas = []
    for n in noticias:
        data_str = n.get("date")
        iso = normalizar_data(data_str)
        if data_dentro_periodo(iso, limite):
            filtradas.append(n)
        # opcional: adicionar data_normalizada ao item para consistência
        if iso:
            n["data_normalizada_filtro"] = iso
    return filtradas


def run_scrapers(project_dir: str, spiders: List[str]) -> bool:
    """Executa os spiders Scrapy em sequência."""
    original_dir = os.getcwd()
    try:
        os.chdir(project_dir)
    except FileNotFoundError:
        logger.error("Diretório do Scrapy não encontrado: %s", project_dir)
        return False
    try:
        for spider in spiders:
            logger.info("Executando spider: %s", spider)
            subprocess.run(f"scrapy crawl {spider}", shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao executar spider: %s", e)
        return False
    finally:
        os.chdir(original_dir)


def run_script(nome: str) -> bool:
    """Executa um script Python da raiz do projeto (ex: analisar_noticias.py)."""
    try:
        subprocess.run([sys.executable, nome], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao executar %s: %s", nome, e)
        return False


def main() -> None:
    logger.info("=" * 60)
    logger.info("COLETA ÚLTIMOS %d MESES - Iniciando", MESES_ATRAS)
    logger.info("=" * 60)

    # 1) Rodar spiders (com paginação já configurada em Valor e Exame)
    ok = run_scrapers(SCRAPY_PROJECT_DIR, SPIDER_NAMES)
    if not ok:
        logger.warning("Falha nos spiders. Continuando com o que existir em %s.", ARQUIVO_JSON_NOTICIAS)

    # 2) Carregar, filtrar por data e salvar de volta
    noticias = carregar_noticias_brutas(ARQUIVO_JSON_NOTICIAS)
    logger.info("Total de notícias coletadas (bruto): %d", len(noticias))

    if not noticias:
        logger.warning("Nenhuma notícia no arquivo. Execute os spiders antes ou verifique %s.", ARQUIVO_JSON_NOTICIAS)
        return

    filtradas = filtrar_ultimos_meses(noticias, MESES_ATRAS)
    logger.info("Notícias nos últimos %d meses: %d", MESES_ATRAS, len(filtradas))

    # Remover campo auxiliar antes de salvar
    for n in filtradas:
        n.pop("data_normalizada_filtro", None)

    with open(ARQUIVO_JSON_NOTICIAS, "w", encoding="utf-8") as f:
        json.dump(filtradas, f, ensure_ascii=False, indent=2)
    logger.info("Arquivo filtrado salvo em: %s", ARQUIVO_JSON_NOTICIAS)

    # 3) Análise de sentimento
    logger.info("Executando análise de sentimento (FinBERT)...")
    if not run_script("analisar_noticias.py"):
        logger.error("Falha na análise de sentimento.")
        return

    # 4) Associar tickers
    logger.info("Associando tickers...")
    if not run_script("associar_tickers.py"):
        logger.warning("Falha ao associar tickers. Verifique mapeamento_tickers.json.")

    # 5) Treinar IA: Random Forest e RL (Q-Learning) para decisão compra/venda (não regra fixa)
    logger.info("Treinando modelo de decisão (Random Forest)...")
    run_script("treinar_modelo_decisao.py")
    logger.info("Treinando agente RL (Q-Learning)...")
    run_script("rl_agente.py")

    # 6) Recomendação (usa modelo ou RL, nunca regra fixa)
    try:
        from recomendacao import run_recomendacao
        run_recomendacao()
        logger.info("Recomendação atualizada (IA: Random Forest ou RL).")
    except Exception as e:
        logger.warning("Recomendação não executada: %s", e)

    logger.info("=" * 60)
    logger.info("COLETA ÚLTIMOS %d MESES - Concluído", MESES_ATRAS)
    logger.info("Arquivos: noticias_com_sentimento.json, %s", ARQUIVO_JSON_MAPEADAS)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
