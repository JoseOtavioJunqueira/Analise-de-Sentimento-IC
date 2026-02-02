"""
Treina um modelo que aprende com o histórico: sentimento do dia → retorno no dia seguinte.
Usado para decidir compra/venda/segurar em vez da regra fixa (score > 1 → compra).
Requer muitos meses de dados (notícias + preços) para treinar.
"""
import json
import logging
import os
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_MODELO_DECISAO,
    ARQUIVO_CONFIG_MODELO_DECISAO,
    RANDOM_SEED,
)

warnings.simplefilter("ignore", category=FutureWarning)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Limiar de retorno para considerar "subiu" (1) vs "caiu" (0). Ex.: 0.001 = 0,1%
THRESHOLD_RETORNO: float = 0.0  # >0 = subiu, <0 = caiu (ou use 0.001 para filtrar ruído)
MIN_AMOSTRAS_POR_TICKER: int = 5  # Mínimo de dias com dados para incluir o ticker
TEST_SIZE: float = 0.2
MODELO_TIPO: str = "logistic"  # "logistic" ou "random_forest"


def carregar_sentimento_por_dia_ticker(caminho: str) -> Optional[pd.DataFrame]:
    """Carrega noticias_mapeadas e retorna DataFrame com (data, ticker, score)."""
    if not os.path.exists(caminho):
        logger.warning("Arquivo não encontrado: %s", caminho)
        return None
    try:
        df = pd.read_json(caminho)
        if df.empty or "sentimento_previsto" not in df.columns:
            return None
        sentimento_map = {"POSITIVE": 1, "NEGATIVE": -1, "NEUTRAL": 0}
        df["score"] = df["sentimento_previsto"].map(sentimento_map).fillna(0)
        df["data"] = pd.to_datetime(df["data_normalizada"]).dt.normalize()
        df_exploded = df.explode("tickers_citados").dropna(subset=["tickers_citados"])
        agg = (
            df_exploded.groupby([pd.Grouper(key="data", freq="D"), "tickers_citados"])["score"]
            .sum()
            .reset_index()
        )
        agg.columns = ["data", "ticker", "sentimento"]
        return agg
    except Exception as e:
        logger.exception("Erro ao carregar sentimento: %s", e)
        return None


def obter_retorno_dia_seguinte(
    tickers: List[str], start: pd.Timestamp, end: pd.Timestamp,
) -> pd.DataFrame:
    """Retorna DataFrame (data, ticker, retorno_dia_seguinte). Retorno = (preço_amanhã - preço_hoje) / preço_hoje."""
    precos = yf.download(tickers, start=start, end=end, repair=True, progress=False, threads=False)
    if precos.empty or "Close" not in precos.columns:
        return pd.DataFrame()
    if len(tickers) == 1:
        close = precos["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        precos = pd.DataFrame({tickers[0]: close})
    else:
        precos = precos["Close"]
    if isinstance(precos, pd.Series):
        precos = precos.to_frame()
    out = []
    for ticker in precos.columns:
        s = precos[ticker].dropna()
        ret = s.pct_change().shift(-1)  # retorno do dia seguinte (amanhã vs hoje)
        for d, r in ret.items():
            if pd.notna(r):
                out.append({"data": d, "ticker": ticker, "retorno_dia_seguinte": r})
    if not out:
        return pd.DataFrame()
    return pd.DataFrame(out)


def montar_tabela_treino(
    df_sent: pd.DataFrame, threshold_retorno: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Monta X (sentimento e opcionalmente outras features) e y (1 = subiu, 0 = caiu).
    y = 1 se retorno_dia_seguinte > threshold_retorno, senão 0.
    """
    datas = df_sent["data"].unique()
    if len(datas) < 2:
        return np.array([]), np.array([]), []
    start = pd.Timestamp(datas.min()) - pd.Timedelta(days=1)
    end = pd.Timestamp(datas.max()) + pd.Timedelta(days=5)
    tickers = df_sent["ticker"].unique().tolist()
    logger.info("Baixando preços para %d tickers, período %s a %s...", len(tickers), start.date(), end.date())
    df_ret = obter_retorno_dia_seguinte(tickers, start, end)
    if df_ret.empty:
        logger.warning("Nenhum retorno obtido. Verifique tickers e datas.")
        return np.array([]), np.array([]), []
    df_merge = df_sent.merge(
        df_ret,
        on=["data", "ticker"],
        how="inner",
    ).dropna(subset=["retorno_dia_seguinte"])
    if df_merge.empty or len(df_merge) < 30:
        logger.warning("Poucos dados para treino (mínimo 30 linhas). Tenha muitos meses de notícias + preços.")
        return np.array([]), np.array([]), []
    df_merge["y"] = (df_merge["retorno_dia_seguinte"] > threshold_retorno).astype(int)
    X = df_merge[["sentimento"]].values.astype(np.float64)
    y = df_merge["y"].values
    logger.info("Tabela de treino: %d amostras (%.1f%% subiu)", len(y), 100 * y.mean())
    return X, y, df_merge["ticker"].unique().tolist()


def treinar_e_salvar(
    X: np.ndarray,
    y: np.ndarray,
    modelo_tipo: str = "logistic",
    test_size: float = 0.2,
) -> Dict[str, Any]:
    """Treina o modelo, salva em joblib e retorna config (acuracia, etc.)."""
    if len(X) < 20:
        raise ValueError("Poucos dados para treino. Acumule muitos meses de notícias e rode de novo.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_SEED, stratify=y if len(np.unique(y)) > 1 else None
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    if modelo_tipo == "random_forest":
        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=RANDOM_SEED)
    else:
        model = LogisticRegression(random_state=RANDOM_SEED, max_iter=500)
    model.fit(X_train_s, y_train)
    acc_train = model.score(X_train_s, y_train)
    acc_test = model.score(X_test_s, y_test)
    config = {
        "modelo_tipo": modelo_tipo,
        "threshold_retorno": THRESHOLD_RETORNO,
        "accuracy_treino": round(float(acc_train), 4),
        "accuracy_teste": round(float(acc_test), 4),
        "n_amostras_treino": int(len(X_train)),
        "n_amostras_teste": int(len(X_test)),
        "features": ["sentimento"],
    }
    joblib.dump({"model": model, "scaler": scaler}, ARQUIVO_MODELO_DECISAO)
    with open(ARQUIVO_CONFIG_MODELO_DECISAO, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    logger.info("Modelo salvo em %s. Acurácia teste: %.2f%%", ARQUIVO_MODELO_DECISAO, 100 * acc_test)
    return config


def run() -> bool:
    """Carrega dados, monta tabela, treina e salva. Retorna True se treinou com sucesso."""
    df_sent = carregar_sentimento_por_dia_ticker(ARQUIVO_JSON_MAPEADAS)
    if df_sent is None or df_sent.empty:
        logger.warning("Sem dados de sentimento. Execute a coleta + análise + associar_tickers por muitos meses.")
        return False
    X, y, _ = montar_tabela_treino(df_sent, THRESHOLD_RETORNO)
    if len(X) == 0:
        return False
    treinar_e_salvar(X, y, modelo_tipo=MODELO_TIPO, test_size=TEST_SIZE)
    return True


if __name__ == "__main__":
    run()
