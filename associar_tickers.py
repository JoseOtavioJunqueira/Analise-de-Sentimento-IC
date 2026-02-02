"""
Associa notícias classificadas a tickers de ações/ETFs via NER (spaCy) e mapeamento.
"""
import json
import logging
import os
from typing import Any, List, Optional

import pandas as pd
import spacy

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_JSON_SENTIMENTO,
    ARQUIVO_MAPEAMENTO_TICKERS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ARQUIVO_ENTRADA = ARQUIVO_JSON_SENTIMENTO
MAPA_TICKERS_ARQ = ARQUIVO_MAPEAMENTO_TICKERS
ARQUIVO_SAIDA = ARQUIVO_JSON_MAPEADAS

# --- 2. FUNÇÕES DE PROCESSAMENTO ---

def carregar_modelo_spacy() -> Any:
    """Carrega o modelo 'pt_core_news_lg' do spaCy para NER em português."""
    logger.info("Carregando modelo spaCy 'pt_core_news_lg'...")
    try:
        nlp = spacy.load("pt_core_news_lg")
        logger.info("Modelo spaCy carregado com sucesso.")
        return nlp
    except OSError:
        logger.error(
            "Modelo 'pt_core_news_lg' não encontrado. Instale com: "
            "pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-v3.7.0/pt_core_news_lg-3.7.0.tar.gz"
        )
        raise SystemExit(1)

def extrair_empresas(texto: Optional[str], nlp_model: Any) -> List[str]:
    """
    Extrai entidades ORG/MISC do texto usando NER do spaCy.

    Args:
        texto: Texto a processar.
        nlp_model: Modelo spaCy carregado.

    Returns:
        Lista de nomes de empresas/organizações únicos.
    """
    if not isinstance(texto, str) or not texto:
        return []
        
    doc = nlp_model(texto)
    empresas = []
    for ent in doc.ents:
        if ent.label_ == "ORG" or ent.label_ == "MISC":
            # Adiciona o nome da empresa, limpando espaços
            empresas.append(ent.text.strip())
            
    # Remove duplicatas e retorna a lista
    return list(set(empresas))

def carregar_mapa_tickers(arquivo_mapa: str) -> dict:
    """
    Carrega o arquivo JSON de mapeamento nome de empresa -> ticker.

    Args:
        arquivo_mapa: Caminho do arquivo mapeamento_tickers.json.

    Returns:
        Dicionário {nome_empresa: ticker}.

    Raises:
        SystemExit: Se o arquivo não existir.
    """
    if not os.path.exists(arquivo_mapa):
        logger.error("Arquivo de mapeamento '%s' não encontrado.", arquivo_mapa)
        raise SystemExit(1)
    logger.info("Carregando mapa de tickers de '%s'...", arquivo_mapa)
    with open(arquivo_mapa, "r", encoding="utf-8") as f:
        mapa_tickers = json.load(f)
    logger.info("Mapa carregado.")
    return mapa_tickers

def mapear_tickers(lista_empresas: List[str], mapa_tickers: dict) -> List[str]:
    """
    Converte nomes de empresas em tickers usando o mapa. Ignora entradas null.
    """
    tickers = []
    for empresa in lista_empresas:
        # Verifica se a empresa está no mapa
        if empresa in mapa_tickers:
            ticker_mapeado = mapa_tickers[empresa]
            
            # Adiciona APENAS se o ticker não for 'null'
            if ticker_mapeado is not None:
                tickers.append(ticker_mapeado)
                
    # Retorna a lista de tickers únicos
    return list(set(tickers))

# --- 3. EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    
    # --- PASSO 1: CARREGAR DADOS E MODELOS ---
    nlp = carregar_modelo_spacy()
    mapa_tickers = carregar_mapa_tickers(MAPA_TICKERS_ARQ)
    
    logger.info("Lendo notícias de entrada: '%s'...", ARQUIVO_ENTRADA)
    try:
        df = pd.read_json(ARQUIVO_ENTRADA)
    except Exception as e:
        logger.exception("Erro ao ler '%s': %s", ARQUIVO_ENTRADA, e)
        raise SystemExit(1)
    if "texto_completo" not in df.columns:
        logger.error("Arquivo de entrada não contém a coluna 'texto_completo'.")
        raise SystemExit(1)
    logger.info("Encontradas %d notícias para processar.", len(df))

    logger.info("Iniciando extração de entidades (NER) com spaCy...")
    df["empresas_citadas"] = df["texto_completo"].apply(lambda t: extrair_empresas(t, nlp))
    logger.info("Extração de entidades concluída.")

    logger.info("Iniciando mapeamento de tickers...")
    df["tickers_citados"] = df["empresas_citadas"].apply(lambda l: mapear_tickers(l, mapa_tickers))
    logger.info("Mapeamento concluído.")

    df_mapeado = df[df["tickers_citados"].apply(len) > 0].copy()
    df_mapeado.reset_index(drop=True, inplace=True)

    logger.info(
        "Processo finalizado. Originais: %d | Mapeadas: %d | Filtradas: %d",
        len(df), len(df_mapeado), len(df) - len(df_mapeado),
    )
    df_mapeado.to_json(ARQUIVO_SAIDA, orient="records", indent=4, force_ascii=False)
    logger.info("Notícias mapeadas salvas em '%s'. Próximo passo: criar_estrategia.py", ARQUIVO_SAIDA)