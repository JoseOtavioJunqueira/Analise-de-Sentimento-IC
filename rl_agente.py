"""
Agente de Aprendizado por Reforço (Q-Learning) para decisão compra/venda/segurar.

Estado: sentimento agregado do dia (discretizado em buckets).
Ações: 0 = segurar, 1 = compra, 2 = venda.
Recompensa: retorno do dia seguinte (se comprou e subiu = positivo; se vendeu e caiu = positivo; etc.).

Uso:
  - Treinar: python rl_agente.py  (usa noticias_mapeadas.json + yfinance, salva politica_rl_qlearning.json)
  - Recomendação: recomendacao.py carrega a política e usa action = argmax Q(estado, a)
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_POLITICA_RL,
    RANDOM_SEED,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Discretização do sentimento: score contínuo -> índice de estado (0 a N_BUCKETS-1)
SENTIMENTO_MIN = -10
SENTIMENTO_MAX = 10
N_BUCKETS = 11  # estados 0..10 (sentimento de -10 a 10 em steps de 2)
# Ações
ACAO_SEGURAR = 0
ACAO_COMPRAR = 1
ACAO_VENDER = 2
N_ACOES = 3
# Q-Learning
ALPHA = 0.1
GAMMA = 0.95
EPSILON_DECAY = 0.995
MIN_EPSILON = 0.05
EPISODIOS = 500


def _discretizar_sentimento(score: float) -> int:
    """Mapeia score contínuo para bucket [0, N_BUCKETS-1]."""
    s = np.clip(score, SENTIMENTO_MIN, SENTIMENTO_MAX)
    bucket = int((s - SENTIMENTO_MIN) / (SENTIMENTO_MAX - SENTIMENTO_MIN) * (N_BUCKETS - 1))
    return min(bucket, N_BUCKETS - 1)


def _recompensa(acao: int, retorno_dia_seguinte: float) -> float:
    """
    Recompensa: comprar e subir = ganho; comprar e cair = perda;
    vender e cair = ganho (short); vender e subir = perda; segurar = 0.
    """
    if acao == ACAO_SEGURAR:
        return 0.0
    if acao == ACAO_COMPRAR:
        return float(retorno_dia_seguinte)
    # acao == ACAO_VENDER: lucro quando o ativo cai
    return float(-retorno_dia_seguinte)


def carregar_dados_treino(caminho: str) -> Optional[pd.DataFrame]:
    """Monta DataFrame (data, ticker, sentimento, retorno_dia_seguinte) a partir de noticias_mapeadas + yfinance."""
    if not os.path.exists(caminho):
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
    except Exception as e:
        logger.exception("Erro ao carregar dados: %s", e)
        return None

    datas = agg["data"].unique()
    if len(datas) < 2:
        return None
    start = pd.Timestamp(datas.min()) - pd.Timedelta(days=1)
    end = pd.Timestamp(datas.max()) + pd.Timedelta(days=5)
    tickers = agg["ticker"].unique().tolist()
    logger.info("Baixando preços para %d tickers (RL)...", len(tickers))
    precos = yf.download(tickers, start=start, end=end, repair=True, progress=False, threads=False)
    if precos.empty or "Close" not in precos.columns:
        return None
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
        ret = s.pct_change().shift(-1)
        for d, r in ret.items():
            if pd.notna(r):
                out.append({"data": d, "ticker": ticker, "retorno_dia_seguinte": r})
    if not out:
        return None
    df_ret = pd.DataFrame(out)
    df_merge = agg.merge(df_ret, on=["data", "ticker"], how="inner").dropna(subset=["retorno_dia_seguinte"])
    if len(df_merge) < 20:
        return None
    return df_merge


def treinar_qlearning(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Treina Q-Learning no histórico (sentimento, retorno_dia_seguinte).
    Cada linha é um passo: estado = discretizar(sentimento), reward = f(acao, retorno).
    Política aleatória para explorar (epsilon-greedy); atualiza Q(s,a).
    """
    np.random.seed(RANDOM_SEED)
    Q: Dict[Tuple[int, int], float] = {}
    for s in range(N_BUCKETS):
        for a in range(N_ACOES):
            Q[(s, a)] = 0.0

    epsilon = 1.0
    for ep in range(EPISODIOS):
        df_ = df.sample(frac=1.0, random_state=RANDOM_SEED + ep).reset_index(drop=True)
        for _, row in df_.iterrows():
            sent = float(row["sentimento"])
            ret = float(row["retorno_dia_seguinte"])
            state = _discretizar_sentimento(sent)
            # Escolha da ação (epsilon-greedy)
            if np.random.random() < epsilon:
                action = np.random.randint(0, N_ACOES)
            else:
                action = max(range(N_ACOES), key=lambda a: Q.get((state, a), 0.0))
            reward = _recompensa(action, ret)
            # Q(s,a) <- Q(s,a) + alpha * (r + gamma * max_a' Q(s',a') - Q(s,a))
            # Aqui simplificamos: s' = state (não temos próximo estado no mesmo passo), então TD(0): target = r
            target = reward
            Q[(state, action)] = Q.get((state, action), 0.0) + ALPHA * (target - Q.get((state, action), 0.0))
        epsilon = max(MIN_EPSILON, epsilon * EPSILON_DECAY)
        if (ep + 1) % 100 == 0:
            logger.info("RL episódio %d, epsilon=%.3f", ep + 1, epsilon)

    # Salvar Q como dict serializável (chave "s_a" -> valor)
    policy = {
        "Q": {f"{s}_{a}": Q[(s, a)] for s in range(N_BUCKETS) for a in range(N_ACOES)},
        "N_BUCKETS": N_BUCKETS,
        "N_ACOES": N_ACOES,
        "SENTIMENTO_MIN": SENTIMENTO_MIN,
        "SENTIMENTO_MAX": SENTIMENTO_MAX,
    }
    with open(ARQUIVO_POLITICA_RL, "w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2)
    logger.info("Política RL (Q-Learning) salva em %s", ARQUIVO_POLITICA_RL)
    return policy


def carregar_politica(caminho: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Carrega política RL do JSON. Retorna dict com 'Q' e metadados ou None."""
    path = caminho or ARQUIVO_POLITICA_RL
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def acao_rl(score: float, policy: Dict[str, Any]) -> int:
    """
    Dado score de sentimento e política treinada, retorna ação: 0=segurar, 1=compra, 2=venda.
    """
    Q = policy.get("Q", {})
    state = _discretizar_sentimento(score)
    best_a = 0
    best_q = float("-inf")
    for a in range(N_ACOES):
        q = Q.get(f"{state}_{a}", 0.0)
        if q > best_q:
            best_q = q
            best_a = a
    return best_a


def acao_para_str(acao: int) -> str:
    if acao == ACAO_COMPRAR:
        return "compra"
    if acao == ACAO_VENDER:
        return "venda"
    return "segurar"


def run_treino() -> bool:
    """Carrega dados, treina Q-Learning e salva política. Retorna True se treinou com sucesso."""
    df = carregar_dados_treino(ARQUIVO_JSON_MAPEADAS)
    if df is None or len(df) < 20:
        logger.warning("Dados insuficientes para treinar RL. Execute coleta + associar_tickers.")
        return False
    treinar_qlearning(df)
    return True


if __name__ == "__main__":
    run_treino()
