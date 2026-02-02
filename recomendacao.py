"""
Módulo de recomendação: gera saída estruturada (investir? onde? quando? por quê?).
Se existir modelo treinado (histórico sentimento → retorno), usa esse modelo para decidir
compra/venda/segurar; senão usa regra fixa (score > 1 → compra, score < -1 → venda).
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_ULTIMA_RECOMENDACAO,
    ARQUIVO_STATUS,
    ARQUIVO_MODELO_DECISAO,
    ARQUIVO_CONFIG_MODELO_DECISAO,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

LIMITE_COMPRA = 1   # Regra fixa: score > 1 → compra
LIMITE_VENDA = -1   # Regra fixa: score < -1 → venda
POR_QUANTO_TEMPO = "1 dia (day trade)"
# Quando usar modelo treinado: prob(subiu) > UMBRAL_COMPRA → compra, < UMBRAL_VENDA → venda, senão segurar
UMBRAL_PROB_COMPRA = 0.6
UMBRAL_PROB_VENDA = 0.4


def _carregar_modelo_decisao() -> Optional[Tuple[Any, Any]]:
    """Carrega modelo e scaler salvos por treinar_modelo_decisao.py. Retorna (model, scaler) ou None."""
    if not os.path.exists(ARQUIVO_MODELO_DECISAO):
        return None
    try:
        import joblib
        obj = joblib.load(ARQUIVO_MODELO_DECISAO)
        return (obj["model"], obj["scaler"])
    except Exception as e:
        logger.warning("Não foi possível carregar modelo de decisão: %s. Usando regra fixa.", e)
        return None


def _decisao_com_modelo(score: float, model: Any, scaler: Any) -> str:
    """Usa modelo treinado (sentimento → retorno) para decidir compra/venda/segurar."""
    X = np.array([[float(score)]], dtype=np.float64)
    X_s = scaler.transform(X)
    if hasattr(model, "predict_proba"):
        prob = model.predict_proba(X_s)[0, 1]  # P(subiu)
        if prob >= UMBRAL_PROB_COMPRA:
            return "compra"
        if prob <= UMBRAL_PROB_VENDA:
            return "venda"
        return "segurar"
    pred = model.predict(X_s)[0]
    return "compra" if pred == 1 else "venda"


def _decisao_regra_fixa(score: float) -> str:
    """Regra fixa: score > 1 → compra, score < -1 → venda, senão segurar."""
    if score > LIMITE_COMPRA:
        return "compra"
    if score < LIMITE_VENDA:
        return "venda"
    return "segurar"


def carregar_noticias_mapeadas(caminho: str) -> Optional[pd.DataFrame]:
    """Carrega noticias_mapeadas.json. Retorna None se arquivo não existir ou estiver vazio."""
    if not os.path.exists(caminho):
        logger.warning("Arquivo não encontrado: %s", caminho)
        return None
    try:
        df = pd.read_json(caminho)
        if df.empty:
            logger.warning("Arquivo vazio: %s", caminho)
            return None
        return df
    except Exception as e:
        logger.exception("Erro ao ler %s: %s", caminho, e)
        return None


def agregar_sentimento_por_dia_ticker(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega score de sentimento por (data, ticker)."""
    sentimento_map = {"POSITIVE": 1, "NEGATIVE": -1, "NEUTRAL": 0}
    df = df.copy()
    df["score"] = df["sentimento_previsto"].map(sentimento_map).fillna(0)
    df["data"] = pd.to_datetime(df["data_normalizada"])
    df_exploded = df.explode("tickers_citados").dropna(subset=["tickers_citados"])
    return (
        df_exploded.groupby([pd.Grouper(key="data", freq="D"), "tickers_citados"])["score"]
        .sum()
        .reset_index()
    )


def noticias_por_data_ticker(df: pd.DataFrame) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Retorna estrutura: (data_str -> ticker -> lista de {titulo, url, sentimento}).
    Data no formato YYYY-MM-DD para chave.
    """
    df = df.copy()
    df["data"] = pd.to_datetime(df["data_normalizada"]).dt.strftime("%Y-%m-%d")
    df_exploded = df.explode("tickers_citados").dropna(subset=["tickers_citados"])
    out: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for (data_str, ticker), grp in df_exploded.groupby(["data", "tickers_citados"]):
        if data_str not in out:
            out[data_str] = {}
        out[data_str][ticker] = [
            {
                "titulo": row.get("title", ""),
                "url": row.get("url", ""),
                "sentimento": row.get("sentimento_previsto", ""),
            }
            for _, row in grp.iterrows()
        ]
    return out


def gerar_recomendacao(
    df: pd.DataFrame,
    data_alvo: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gera recomendação para uma data (última disponível se data_alvo for None).
    Retorna dict com: data_recomendacao, quando, por_quanto_tempo, investir, onde, por_que, resumo.
    """
    df_sent = agregar_sentimento_por_dia_ticker(df)
    noticias_por_dt = noticias_por_data_ticker(df)

    if df_sent.empty:
        return {
            "data_recomendacao": datetime.now().isoformat(),
            "quando": None,
            "por_quanto_tempo": POR_QUANTO_TEMPO,
            "investir": [],
            "onde": [],
            "por_que": {},
            "resumo": "Sem dados de sentimento agregado.",
            "erro": True,
        }

    datas_disponiveis = sorted(df_sent["data"].dt.strftime("%Y-%m-%d").unique())
    if not datas_disponiveis:
        return {
            "data_recomendacao": datetime.now().isoformat(),
            "quando": None,
            "por_quanto_tempo": POR_QUANTO_TEMPO,
            "investir": [],
            "onde": [],
            "por_que": {},
            "resumo": "Nenhuma data disponível.",
            "erro": True,
        }

    data_uso = data_alvo if data_alvo and data_alvo in datas_disponiveis else datas_disponiveis[-1]
    linha = df_sent[df_sent["data"].dt.strftime("%Y-%m-%d") == data_uso]

    modelo_dec = _carregar_modelo_decisao()
    usar_modelo = modelo_dec is not None
    if usar_modelo:
        logger.info("Usando modelo treinado (histórico sentimento → retorno) para decidir compra/venda/segurar.")
    else:
        logger.info("Modelo de decisão não encontrado. Usando regra fixa (score > 1 → compra, < -1 → venda).")

    investir: List[Dict[str, Any]] = []
    onde: List[str] = []
    por_que: Dict[str, List[Dict[str, Any]]] = {}

    for _, row in linha.iterrows():
        ticker = row["tickers_citados"]
        score = float(row["score"])
        if usar_modelo and modelo_dec:
            model, scaler = modelo_dec
            acao = _decisao_com_modelo(score, model, scaler)
        else:
            acao = _decisao_regra_fixa(score)

        noticias_ticker = noticias_por_dt.get(data_uso, {}).get(ticker, [])
        investir.append({
            "ticker": ticker,
            "acao": acao,
            "score": score,
            "quantidade_noticias": len(noticias_ticker),
            "usou_modelo_treinado": usar_modelo,
        })
        if acao != "segurar":
            onde.append(ticker)
        por_que[ticker] = noticias_ticker

    metodo = "modelo treinado (histórico sentimento → retorno)" if usar_modelo else "regra fixa (score > 1 compra, < -1 venda)"
    resumo = (
        f"Recomendação para {data_uso} ({metodo}): "
        f"{len([x for x in investir if x['acao'] == 'compra'])} compra(s), "
        f"{len([x for x in investir if x['acao'] == 'venda'])} venda(s), "
        f"{len([x for x in investir if x['acao'] == 'segurar'])} segurar."
    )

    return {
        "data_recomendacao": datetime.now().isoformat(),
        "quando": data_uso,
        "por_quanto_tempo": POR_QUANTO_TEMPO,
        "investir": investir,
        "onde": list(set(onde)),
        "por_que": por_que,
        "resumo": resumo,
        "erro": False,
        "usou_modelo_treinado": usar_modelo,
        "datas_disponiveis": datas_disponiveis[-10:],
    }


def salvar_recomendacao(recomendacao: Dict[str, Any], caminho: str) -> None:
    """Salva recomendação em JSON (serializando listas/dicts aninhados)."""
    def default(o: Any) -> Any:
        if hasattr(o, "isoformat"):
            return o.isoformat()
        raise TypeError(type(o).__name__)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(recomendacao, f, ensure_ascii=False, indent=2, default=default)
    logger.info("Recomendação salva em %s", caminho)


def atualizar_status(campo: str, valor: str) -> None:
    """Atualiza status.json com um campo (ex: ultima_recomendacao)."""
    status: Dict[str, str] = {}
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


def run_recomendacao() -> bool:
    """
    Carrega notícias mapeadas, gera recomendação, salva em ultima_recomendacao.json
    e atualiza status. Retorna True se gerou recomendação com sucesso.
    """
    df = carregar_noticias_mapeadas(ARQUIVO_JSON_MAPEADAS)
    if df is None:
        atualizar_status("ultima_recomendacao", datetime.now().isoformat() + " (sem dados)")
        return False
    rec = gerar_recomendacao(df)
    salvar_recomendacao(rec, ARQUIVO_ULTIMA_RECOMENDACAO)
    atualizar_status("ultima_recomendacao", rec["data_recomendacao"])
    return not rec.get("erro", True)


if __name__ == "__main__":
    run_recomendacao()
