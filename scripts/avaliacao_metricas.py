"""
Módulo de métricas financeiras para avaliação de estratégias.
Calcula retorno acumulado, Sharpe ratio e drawdown a partir de série de retornos.
Uso: importar em criar_estrategia ou em scripts de comparação com Selic/benchmark.
"""
from typing import Optional, Tuple

import numpy as np
import pandas as pd


def retorno_acumulado(retornos: pd.Series) -> float:
    """
    Retorno total acumulado (produtório (1 + r) - 1).

    Args:
        retornos: Série de retornos (ex: diários).

    Returns:
        Retorno acumulado em decimal (ex: 0.05 = 5%).
    """
    return float((1 + retornos).prod() - 1)


def sharpe_ratio(
    retornos: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: Optional[float] = 252.0,
) -> float:
    """
    Sharpe ratio anualizado (excesso de retorno / volatilidade).

    Args:
        retornos: Série de retornos.
        risk_free_rate: Taxa livre de risco por período (ex: diária).
        periods_per_year: Número de períodos por ano (252 para diário).

    Returns:
        Sharpe ratio anualizado.
    """
    excess = retornos - risk_free_rate
    if excess.std() == 0:
        return 0.0
    if periods_per_year is None:
        return float(excess.mean() / excess.std())
    return float((excess.mean() / excess.std()) * np.sqrt(periods_per_year))


def max_drawdown(retornos: pd.Series) -> Tuple[float, Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """
    Drawdown máximo e datas de pico e fundo.

    Args:
        retornos: Série de retornos.

    Returns:
        (max_drawdown em decimal, data_pico, data_fundo).
    """
    cum = (1 + retornos).cumprod()
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = float(drawdown.min())
    if max_dd >= 0:
        return 0.0, None, None
    idx_min = drawdown.idxmin()
    # Pico = último máximo antes do fundo
    peak = cum.loc[:idx_min].idxmax() if isinstance(idx_min, pd.Timestamp) else None
    return max_dd, peak, idx_min


def resumo_metricas(retornos: pd.Series) -> dict:
    """
    Dicionário com retorno acumulado, Sharpe e max drawdown.

    Args:
        retornos: Série de retornos (ex: diários).

    Returns:
        {'retorno_acumulado', 'sharpe_ratio', 'max_drawdown', 'max_drawdown_pct'}.
    """
    ret = retorno_acumulado(retornos)
    sharpe = sharpe_ratio(retornos)
    max_dd, _, _ = max_drawdown(retornos)
    return {
        "retorno_acumulado": ret,
        "retorno_acumulado_pct": ret * 100,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd * 100,
    }


if __name__ == "__main__":
    # Exemplo: série de retornos fictícia
    np.random.seed(42)
    r = pd.Series(np.random.randn(252) * 0.01)
    m = resumo_metricas(r)
    print("Exemplo resumo_metricas:", m)
