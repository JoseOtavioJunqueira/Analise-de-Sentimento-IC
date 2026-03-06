"""
Backtest da estratégia de day trade baseada em sentimento.
Gera sinais de compra/venda a partir de notícias mapeadas e simula portfólio com VectorBT.
Salva métricas em JSON para a interface Streamlit.
"""
import json
import logging
import os
import warnings
from datetime import datetime

import pandas as pd
import vectorbt as vbt
import yfinance as yf

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_RESULTADOS_BACKTEST,
    ARQUIVO_ULTIMO_BACKTEST_JSON,
    ARQUIVO_STATUS,
    ARQUIVO_MODELO_DECISAO,
    ARQUIVO_POLITICA_RL,
)

warnings.simplefilter(action="ignore", category=FutureWarning)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ARQUIVO_NOTICIAS = ARQUIVO_JSON_MAPEADAS
ARQUIVO_RESULTADOS = ARQUIVO_RESULTADOS_BACKTEST

# Fallback só para backtest se não houver modelo/RL (recomendação nunca usa regra fixa)
LIMITE_COMPRA = 1
LIMITE_VENDA = -1
UMBRAL_PROB_COMPRA = 0.6
UMBRAL_PROB_VENDA = 0.4

# --- 2. CARREGAR E PROCESSAR DADOS DE SENTIMENTO ---

logger.info("Carregando notícias de '%s'...", ARQUIVO_NOTICIAS)
try:
    df_noticias = pd.read_json(ARQUIVO_NOTICIAS)
except Exception as e:
    logger.exception("Erro ao ler '%s': %s", ARQUIVO_NOTICIAS, e)
    raise SystemExit(1)

logger.info("Processando e agregando sinais de sentimento...")

# 2.1. Mapear sentimento (texto) para score (número)
sentimento_map = {'POSITIVE': 1, 'NEGATIVE': -1, 'NEUTRAL': 0}
df_noticias['score'] = df_noticias['sentimento_previsto'].map(sentimento_map).fillna(0)

# 2.2. Garantir que a data está no formato correto (datetime)
# Usamos a data normalizada que você já criou
df_noticias['data'] = pd.to_datetime(df_noticias['data_normalizada'])

# 2.3. "Explodir" o DataFrame
# Se uma notícia tem 2 tickers [A, B], ela vira duas linhas: (Notícia1, A) e (Notícia1, B)
df_exploded = df_noticias.explode('tickers_citados')

# 2.4. Agregar sentimento por dia e por ticker
# Agrupamos por data (diário) e pelo ticker, e SOMAMOS os scores.
# Ex: PETR4 em 2025-10-28 teve 2 POS e 1 NEG = Score +1
df_sentimento_diario = df_exploded.groupby([
    pd.Grouper(key='data', freq='D'), 
    'tickers_citados'
])['score'].sum().reset_index()

# 2.5. Pivotar para o formato "Wide"
# O VectorBT precisa de um DataFrame onde:
# - Índice = Data
# - Colunas = Tickers
# - Valores = Score de Sentimento
df_sentimento_pivot = df_sentimento_diario.pivot(
    index='data', 
    columns='tickers_citados', 
    values='score'
).fillna(0)

# --- 3. OBTER DADOS DE PREÇO (MERCADO) ---

# Pega todos os tickers únicos que encontramos
tickers_unicos = list(df_sentimento_pivot.columns)

# Pega a data de início e fim das nossas notícias
start_date = df_sentimento_pivot.index.min()
end_date = df_sentimento_pivot.index.max() 

logger.info("Baixando dados de preço para %d tickers. Período: %s até %s", len(tickers_unicos), start_date.date(), end_date.date())

# Baixa os preços de FECHAMENTO ('Close') para todos os tickers
# O 'yf.download' já nos dá o formato "Wide" que precisamos
precos = yf.download(tickers_unicos, start=start_date, end=end_date, repair=True)['Close']

# --- 4. ALINHAR DADOS E DEFINIR ESTRATÉGIA ---

logger.info("Alinhando preços e sinais...")

# 4.1. Alinhar os dois DataFrames
# 'join='inner'': Só vamos operar em dias que temos AMBOS (preço e sentimento)
# 'ffill()': "Forward-fill". Se o sentimento de Domingo foi +3, esse sinal
#            se mantém para a Segunda-Feira (que é o próximo dia com preço).
sinais, precos_alinhados = df_sentimento_pivot.align(precos, join='inner', axis=0)
sinais = sinais.ffill() # Preenche "buracos" no sentimento (fins de semana)

# 4.2. **A ESTRATÉGIA**
# Usamos sentimento de ONTEM (D-1) para decisão de hoje (D).
sinais_atrasados = sinais.shift(1).fillna(0)

# 4.3. Gerar ordens (Entries/Exits) por IA (modelo ou RL) quando disponível
def _sinais_por_ia(sinais_df: pd.DataFrame) -> tuple:
    """Se houver modelo ou RL, gera entries/exits por IA; senão fallback por limiares."""
    import numpy as np
    # Tentar RL primeiro
    if os.path.exists(ARQUIVO_POLITICA_RL):
        try:
            from rl_agente import carregar_politica, acao_rl, ACAO_COMPRAR, ACAO_VENDER
            pol = carregar_politica()
            if pol:
                entries = pd.DataFrame(False, index=sinais_df.index, columns=sinais_df.columns)
                exits = pd.DataFrame(False, index=sinais_df.index, columns=sinais_df.columns)
                for i in range(len(sinais_df.index)):
                    for c in sinais_df.columns:
                        sc = sinais_df.iloc[i][c]
                        if pd.isna(sc):
                            continue
                        a = acao_rl(float(sc), pol)
                        idx = sinais_df.index[i]
                        if a == ACAO_COMPRAR:
                            entries.loc[idx, c] = True
                        elif a == ACAO_VENDER:
                            exits.loc[idx, c] = True
                entries = entries.astype(bool)
                exits = exits.astype(bool)
                logger.info("Backtest usando agente RL (Q-Learning).")
                return entries, exits
        except Exception as e:
            logger.debug("RL não usado no backtest: %s", e)
    # Tentar modelo (Random Forest / Logistic)
    if os.path.exists(ARQUIVO_MODELO_DECISAO):
        try:
            import joblib
            obj = joblib.load(ARQUIVO_MODELO_DECISAO)
            model, scaler = obj["model"], obj["scaler"]
            entries = pd.DataFrame(False, index=sinais_df.index, columns=sinais_df.columns)
            exits = pd.DataFrame(False, index=sinais_df.index, columns=sinais_df.columns)
            for i in range(len(sinais_df.index)):
                for c in sinais_df.columns:
                    sc = sinais_df.iloc[i][c]
                    if pd.isna(sc):
                        continue
                    X = np.array([[float(sc)]], dtype=np.float64)
                    X_s = scaler.transform(X)
                    idx = sinais_df.index[i]
                    if hasattr(model, "predict_proba"):
                        prob = model.predict_proba(X_s)[0, 1]
                        if prob >= UMBRAL_PROB_COMPRA:
                            entries.loc[idx, c] = True
                        elif prob <= UMBRAL_PROB_VENDA:
                            exits.loc[idx, c] = True
                    else:
                        pred = model.predict(X_s)[0]
                        if pred == 1:
                            entries.loc[idx, c] = True
                        else:
                            exits.loc[idx, c] = True
            logger.info("Backtest usando modelo treinado (Random Forest/Logistic).")
            return entries, exits
        except Exception as e:
            logger.debug("Modelo não usado no backtest: %s", e)
    # Fallback: limiares (apenas para o backtest rodar sem modelo/RL)
    entries = (sinais_atrasados > LIMITE_COMPRA)
    exits = (sinais_atrasados < LIMITE_VENDA)
    logger.info("Backtest usando limiares (fallback; rode treinar_modelo_decisao.py ou rl_agente.py para IA).")
    return entries, exits

entries, exits = _sinais_por_ia(sinais_atrasados)
logger.info("Sinais de compra/venda gerados.")

# --- 5. RODAR O BACKTEST (SIMULAÇÃO) ---

logger.info("Iniciando simulação do portfólio (Backtest)...")

# 'from_signals' é a função mágica do vectorbt.
# Ele simula a compra e venda baseado nos nossos sinais (entries/exits)
# e calcula o P/L baseado nos 'precos_alinhados'.
pf = vbt.Portfolio.from_signals(
    precos_alinhados, 
    entries=entries, 
    exits=exits,
    freq='D', # Frequência diária
    init_cash=100000, # Começa com 100 mil (simulação)
    fees=0.001, # Simula uma taxa de corretagem de 0.1%
    slippage=0.001 # Simula "derrapagem" de 0.1%
)

logger.info("Simulação concluída.")

# --- 6. ANALISAR RESULTADOS (LUCRO/PERCA) ---

logger.info("Gerando relatório de resultados...")

# Pega as estatísticas completas
stats = pf.stats()

# Salva um relatório HTML interativo
pf.plot(
    settings=dict(
        bm_returns=False # Não comparar com benchmark por enquanto
    )
).save(ARQUIVO_RESULTADOS)

logger.info(
    "RESULTADOS: Período %s a %s | Retorno %.2f%% | Win Rate %.2f%% | Max DD %.2f%% | Sharpe %.2f | Trades %s",
    stats["Start"], stats["End"],
    stats["Total Return [%]"], stats["Win Rate [%]"],
    stats["Max Drawdown [%]"], stats["Sharpe Ratio"],
    stats["Total Trades"],
)
logger.info("Relatório completo salvo em: %s", ARQUIVO_RESULTADOS)

# Salvar métricas em JSON para a interface Streamlit
backtest_json = {
    "data_geracao": datetime.now().isoformat(),
    "inicio": str(stats.get("Start", "")),
    "fim": str(stats.get("End", "")),
    "retorno_total_pct": float(stats.get("Total Return [%]", 0)),
    "win_rate_pct": float(stats.get("Win Rate [%]", 0)),
    "max_drawdown_pct": float(stats.get("Max Drawdown [%]", 0)),
    "sharpe_ratio": float(stats.get("Sharpe Ratio", 0)),
    "total_trades": int(stats.get("Total Trades", 0)),
    "arquivo_html": ARQUIVO_RESULTADOS,
}
with open(ARQUIVO_ULTIMO_BACKTEST_JSON, "w", encoding="utf-8") as f:
    json.dump(backtest_json, f, ensure_ascii=False, indent=2)
logger.info("Métricas do backtest salvas em: %s", ARQUIVO_ULTIMO_BACKTEST_JSON)

# Atualizar status
if os.path.exists(ARQUIVO_STATUS):
    with open(ARQUIVO_STATUS, "r", encoding="utf-8") as f:
        status = json.load(f)
else:
    status = {}
status["ultimo_backtest"] = backtest_json["data_geracao"]
with open(ARQUIVO_STATUS, "w", encoding="utf-8") as f:
    json.dump(status, f, ensure_ascii=False, indent=2)