"""
Pipeline de classificação de sentimento em notícias financeiras com FinBERT-PT-BR.
Carrega notícias brutas, normaliza datas, aplica o modelo e salva resultado com sentimento.
"""
import io
import logging
import os
import re
from datetime import datetime
from typing import Optional, Tuple

import dateparser
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, BertForSequenceClassification

from config import (
    ARQUIVO_JSON_NOTICIAS,
    ARQUIVO_JSON_SENTIMENTO,
    FINBERT_MODEL_NAME,
    RANDOM_SEED,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Seeds para reprodutibilidade (Santos 2022 — FinBERT; classificações consistentes)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)

arquivo_json_entrada = ARQUIVO_JSON_NOTICIAS
arquivo_json_saida = ARQUIVO_JSON_SENTIMENTO

# --- 2. NOVAS FUNÇÕES DE AJUDA ---

'''
def normalizar_data(data_str: Optional[str]) -> Optional[str]:
    """
    Converte string ou número de data para formato ISO 8601.
    Aceita timestamps Unix (10 ou 13 dígitos) e strings em português (dateparser).
    """
    if not data_str:
        return None

    # Converte para string para checagem, caso seja int/float
    data_como_str = str(data_str) 
    
    # --- NOVO: Tratamento de Timestamps (Unix) ---
    # Se for numérico (int ou string de dígitos)
    if data_como_str.isdigit():
        try:
            num_data = int(data_como_str)
            num_digitos = len(data_como_str)

            timestamp_sec = None
            if num_digitos == 13: # Provavelmente milissegundos
                timestamp_sec = num_data / 1000.0
            elif num_digitos == 10: # Provavelmente segundos
                timestamp_sec = float(num_data) # Converte para float para consistência
            
            if timestamp_sec is not None:
                # Verificação de sanidade: garante que o timestamp esteja 
                # em um intervalo razoável (ex: entre 2000 e 2050)
                # 946684800 = 2000-01-01
                # 2524608000 = 2050-01-01
                if 946684800 < timestamp_sec < 2524608000:
                     data_obj = datetime.fromtimestamp(timestamp_sec)
                     return data_obj.isoformat()
                else:
                    # É um número, mas fora do intervalo de timestamp esperado
                    # Deixa o dateparser tentar, mas é improvável que funcione
                    pass

        except Exception:
            # Falhou a conversão numérica, deixa o dateparser tentar abaixo
            pass 
    
    # --- Lógica Anterior (Dateparser) ---
    # Se não for um timestamp válido ou for uma string (ex: "6 de maio...")
    try:
        # Usamos 'pt' (português) como língua prioritária
        # O str(data_str) garante que o dateparser receba uma string
        data_obj = dateparser.parse(str(data_str), languages=['pt']) 
        if data_obj:
            # Retorna a data no formato padrão ISO (YYYY-MM-DDTHH:MM:SS)
            return data_obj.isoformat()
        return None
    except Exception:
        # Falha final, não foi possível converter
        return None
'''
    
# NOVA FUNÇÃO PARA TRATAR DATA 
def normalizar_data(data_str: Optional[str], source: Optional[str] = "") -> Optional[str]:
    """
    Converte string para ISO 8601 aplicando regras específicas por site (source).
    """
    if not data_str:
        return None

    data_como_str = str(data_str).strip()
    source_lower = str(source).lower() if source else ""

    try:
        # REGRA 1: Valor Econômico e InfoMoney (Formato ISO exato com fuso horário)
        # Ex: "2026-04-01T05:03:35.388-03:00"
        if "valor" in source_lower or "infomoney" in source_lower:
            return datetime.fromisoformat(data_como_str).isoformat()
        
        # REGRA 2: Bloomberg Linea (Tem o caractere "|" e usa AM/PM)
        # Ex: "02 de Março, 2026 | 06:53 AM"
        elif "bloomberg" in source_lower:
            texto_limpo = data_como_str.replace("|", " ").strip()
            data_obj = dateparser.parse(texto_limpo, languages=['pt', 'en'])
            return data_obj.isoformat() if data_obj else None
            
        # REGRA 3: Exame (Texto simples em português ou Timestamp numérico)
        # Ex: "21 de outubro de 2025" ou "1712750000"
        elif "exame" in source_lower:
            if data_como_str.isdigit() and len(data_como_str) == 13:
                return datetime.fromtimestamp(int(data_como_str) / 1000.0).isoformat()
            
            data_obj = dateparser.parse(data_como_str, languages=['pt'])
            return data_obj.isoformat() if data_obj else None

        # FALLBACK: Se for um site novo não mapeado
        else:
            try:
                return datetime.fromisoformat(data_como_str).isoformat()
            except ValueError:
                data_obj = dateparser.parse(data_como_str, languages=['pt'])
                return data_obj.isoformat() if data_obj else None

    except Exception as e:
        logger.warning(f"Falha na data '{data_str}' do site '{source}': {e}")
        return None
    
def carregar_noticias_existentes(arquivo_saida: str) -> Tuple[pd.DataFrame, set]:
    """
    Carrega notícias já processadas para deduplicação.
    Retorna (DataFrame existente, set de títulos).
    """
    if not os.path.exists(arquivo_saida):
        logger.info("Arquivo '%s' não encontrado. Um novo será criado.", arquivo_saida)
        return pd.DataFrame(), set()
    try:
        '''df_existente = pd.read_json(arquivo_saida, orient="records")
        titulos_existentes = set(df_existente["title"].dropna())
        logger.info("Encontradas %d notícias já processadas.", len(df_existente))
        return df_existente, titulos_existentes'''
        df_existente = pd.read_json(arquivo_saida, orient="records")
        urls_existentes = set(df_existente["url"].dropna())
        logger.info("Encontradas %d notícias já processadas.", len(df_existente))
        return df_existente, urls_existentes
    except Exception as e:
        logger.warning("Não foi possível ler '%s'. Começando do zero. Erro: %s", arquivo_saida, e)
        return pd.DataFrame(), set()

def ler_novas_noticias(arquivo_entrada: str) -> Optional[pd.DataFrame]:
    """Lê o arquivo de entrada bruto, extraindo blocos JSON (suporta múltiplos arrays)."""
    logger.info("Lendo e extraindo blocos do arquivo '%s'...", arquivo_entrada)
    try:
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            conteudo_bruto = f.read()

        if not conteudo_bruto.strip():
            logger.info("Arquivo de entrada está vazio. Nada a processar.")
            return None
        blocos_json_encontrados = re.findall(r"(\[.*?\])", conteudo_bruto, re.DOTALL)
        if not blocos_json_encontrados:
            logger.warning("Nenhum bloco JSON válido encontrado no arquivo de entrada.")
            return None
        lista_de_dfs = [pd.read_json(io.StringIO(bloco)) for bloco in blocos_json_encontrados]
        df_novas = pd.concat(lista_de_dfs, ignore_index=True)
        logger.info("Arquivo de entrada consolidado: %d notícias brutas.", len(df_novas))
        return df_novas
    except FileNotFoundError:
        logger.error("Arquivo '%s' não encontrado.", arquivo_entrada)
        return None
    except Exception as e:
        logger.exception("Erro ao processar JSON de entrada: %s", e)
        return None

def limpar_arquivo_entrada(arquivo_entrada: str) -> None:
    """Limpa o arquivo de entrada (escreve []) após processamento bem-sucedido."""
    try:
        with open(arquivo_entrada, "w", encoding="utf-8") as f:
            f.write("[]")
        logger.info("Arquivo de entrada '%s' foi limpo.", arquivo_entrada)
    except Exception as e:
        logger.error("Erro ao limpar '%s': %s", arquivo_entrada, e)


def run_pipeline() -> None:
    """Executa o pipeline completo: carrega notícias, classifica sentimento e salva."""
    '''df_existente, titulos_existentes = carregar_noticias_existentes(arquivo_json_saida)
    df_novas_noticias = ler_novas_noticias(arquivo_json_entrada)

    if df_novas_noticias is None or df_novas_noticias.empty:
        logger.info("Nenhuma notícia nova para processar. Encerrando.")
        return

    
    df_para_processar = df_novas_noticias[~df_novas_noticias["title"].isin(titulos_existentes)].reset_index(drop=True)
    if df_para_processar.empty:'''
    df_existente, urls_existentes = carregar_noticias_existentes(arquivo_json_saida)
    df_novas_noticias = ler_novas_noticias(arquivo_json_entrada)

    if df_novas_noticias is None or df_novas_noticias.empty:
        logger.info("Nenhuma notícia nova para processar. Encerrando.")
        return

    df_para_processar = df_novas_noticias[~df_novas_noticias["url"].isin(urls_existentes)].reset_index(drop=True)
    if df_para_processar.empty:
        logger.info("Todas as notícias já foram processadas. Limpando entrada e encerrando.")
        limpar_arquivo_entrada(arquivo_json_entrada)
        return

    logger.info("Notícias novas para processar: %d.", len(df_para_processar))
    logger.info("Limpando e preparando os textos...")
    df_para_processar["title"] = df_para_processar["title"].fillna("")
    df_para_processar["content"] = df_para_processar["content"].fillna("")
    df_para_processar["texto_completo"] = (df_para_processar["title"].str.strip() + " " + df_para_processar["content"].str.strip()).str.strip()
    linhas_antes = len(df_para_processar)
    df_para_processar = df_para_processar[df_para_processar["texto_completo"] != ""].reset_index(drop=True)
    logger.info("%d linhas vazias removidas.", linhas_antes - len(df_para_processar))

    if "date" in df_para_processar.columns:
        logger.info("Normalizando datas...")
        ##df_para_processar["data_normalizada"] = df_para_processar["date"].apply(normalizar_data)
        df_para_processar["data_normalizada"] = df_para_processar.apply(lambda row: normalizar_data(row.get("date"), row.get("source")), axis=1)
    else:
        logger.warning("Coluna 'date' não encontrada. Pulando normalização de data.")

    pred_mapper = {0: "POSITIVE", 1: "NEGATIVE", 2: "NEUTRAL"}
    logger.info("Carregando o modelo %s (pode demorar na primeira vez)...", FINBERT_MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_NAME)
    model = BertForSequenceClassification.from_pretrained(FINBERT_MODEL_NAME)
    model.eval()

    def prever_sentimento(texto: str) -> str:
        if not isinstance(texto, str) or not texto:
            return "TEXTO_INVALIDO"
        inputs = tokenizer(texto, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        prediction = int(np.argmax(outputs.logits.numpy()))
        return pred_mapper.get(prediction, "NEUTRAL")

    logger.info("Classificando sentimento em %d notícias...", len(df_para_processar))
    df_processado = df_para_processar.copy()
    df_processado["sentimento_previsto"] = df_processado["texto_completo"].apply(prever_sentimento)

    logger.info("Combinando notícias existentes com as novas processadas...")
    df_final_completo = pd.concat([df_existente, df_processado], ignore_index=True)
    logger.info("Salvando %d notícias em '%s'...", len(df_final_completo), arquivo_json_saida)
    df_final_completo.to_json(arquivo_json_saida, orient="records", indent=4, force_ascii=False)
    logger.info("Processo concluído. Arquivo atualizado: %s", arquivo_json_saida)
    limpar_arquivo_entrada(arquivo_json_entrada)


if __name__ == "__main__":
    run_pipeline()