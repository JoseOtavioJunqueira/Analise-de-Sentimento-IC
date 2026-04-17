"""
Script para COLETA HISTÓRICA EM LOTES.
Define um período exato (Data de Início e Fim) para filtrar as notícias brutas.
"""
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
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

# =====================================================================
# 🕒 CONFIGURE AQUI O LOTE QUE VOCÊ QUER COLETAR AGORA (Formato: YYYY-MM-DD)
# =====================================================================
DATA_INICIO = "2026-02-01" # Ex: 1º de Fevereiro de 2026
DATA_FIM    = "2026-04-17" # Ex: 17 de Abril de 2026
# =====================================================================

def normalizar_data(data_str: Optional[Any], source: Optional[str] = "") -> Optional[str]:
    """Nova função de data otimizada por site."""
    if not data_str:
        return None

    data_como_str = str(data_str).strip()
    source_lower = str(source).lower() if source else ""

    try:
        if "valor" in source_lower or "infomoney" in source_lower:
            return datetime.fromisoformat(data_como_str).isoformat()
        elif "bloomberg" in source_lower:
            texto_limpo = data_como_str.replace("|", " ").strip()
            data_obj = dateparser.parse(texto_limpo, languages=['pt', 'en'])
            return data_obj.isoformat() if data_obj else None
        elif "exame" in source_lower:
            if data_como_str.isdigit() and len(data_como_str) == 13:
                return datetime.fromtimestamp(int(data_como_str) / 1000.0).isoformat()
            data_obj = dateparser.parse(data_como_str, languages=['pt'])
            return data_obj.isoformat() if data_obj else None
        else:
            try:
                return datetime.fromisoformat(data_como_str).isoformat()
            except ValueError:
                data_obj = dateparser.parse(data_como_str, languages=['pt'])
                return data_obj.isoformat() if data_obj else None
    except Exception:
        return None

def data_dentro_periodo(iso_date: Optional[str], inicio: datetime, fim: datetime) -> bool:
    """Retorna True se iso_date estiver exatamente entre inicio e fim."""
    if not iso_date:
        return False # Ignora itens sem data para manter o lote cirúrgico
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00")[:19])
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return inicio <= dt <= fim
    except Exception:
        return False

def carregar_noticias_brutas(caminho: str) -> List[dict]:
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    blocos = re.findall(r"(\[.*?\])", conteudo, re.DOTALL)
    lista = []
    for bloco in blocos:
        try:
            lista.extend(json.loads(bloco))
        except json.JSONDecodeError:
            continue
    return lista

def filtrar_por_lote(noticias: List[dict], str_inicio: str, str_fim: str) -> List[dict]:
    inicio_dt = datetime.strptime(str_inicio, "%Y-%m-%d")
    fim_dt = datetime.strptime(str_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    
    filtradas = []
    for n in noticias:
        iso = normalizar_data(n.get("date"), n.get("source"))
        if data_dentro_periodo(iso, inicio_dt, fim_dt):
            filtradas.append(n)
    return filtradas

def run_scrapers(project_dir: str, spiders: List[str]) -> bool:
    original_dir = os.getcwd()
    try:
        os.chdir(project_dir)
        for spider in spiders:
            logger.info("Executando spider: %s", spider)
            subprocess.run(f"scrapy crawl {spider}", shell=True, check=True)
        return True
    except Exception as e:
        logger.error("Erro nos spiders: %s", e)
        return False
    finally:
        os.chdir(original_dir)

def run_script(nome: str) -> bool:
    try:
        subprocess.run([sys.executable, nome], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Erro ao executar %s", nome)
        return False

def main() -> None:
    logger.info("=" * 60)
    logger.info(f"COLETA DE LOTE HISTÓRICO: {DATA_INICIO} até {DATA_FIM}")
    logger.info("=" * 60)

    # 1) Rodar Spiders
    run_scrapers(SCRAPY_PROJECT_DIR, SPIDER_NAMES)

    # 2) Filtrar o Lote
    noticias = carregar_noticias_brutas(ARQUIVO_JSON_NOTICIAS)
    logger.info("Total bruto baixado: %d", len(noticias))
    
    filtradas = filtrar_por_lote(noticias, DATA_INICIO, DATA_FIM)
    logger.info("Notícias presas no filtro (%s a %s): %d", DATA_INICIO, DATA_FIM, len(filtradas))

    if not filtradas:
        logger.warning("Nenhuma notícia encontrada para esse período. O spider paginou fundo o suficiente?")
        return

    with open(ARQUIVO_JSON_NOTICIAS, "w", encoding="utf-8") as f:
        json.dump(filtradas, f, ensure_ascii=False, indent=2)

    # 3) Rodar a Esteira (Análise, Tickers e Preços)
    logger.info("Analisando sentimentos...")
    run_script("analisar_noticias.py")
    
    logger.info("Associando tickers e buscando preços...")
    run_script("associar_tickers.py")
    run_script(os.path.join("financial_scraper", "fetch_stock_data.py"))
    
    # 4) Contar o resultado final
    logger.info("=" * 60)
    logger.info("LOTE CONCLUÍDO. Contando sobreviventes:")
    run_script("contar_mapeadas.py")

    # MENSAGEM FINAL EXIGIDA
    logger.info("=" * 60)
    logger.info("ATENÇÃO: Se as notícias coletadas estiverem vindo vazias nos lotes mais antigos,")
    logger.info("você vai precisar abrir os arquivos dos spiders (na pasta financial_scraper/financial_scraper/spiders/)")
    logger.info("e aumentar o limite de páginas que eles podem navegar para eles conseguirem cavar até Maio de 2025!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()