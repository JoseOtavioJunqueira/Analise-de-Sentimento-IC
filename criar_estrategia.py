import pandas as pd
import yfinance as yf
import vectorbt as vbt
import warnings

# Ignora alguns avisos comuns do yfinance
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- 1. CONFIGURAÇÕES ---
ARQUIVO_NOTICIAS = "noticias_mapeadas.json"
ARQUIVO_RESULTADOS = "resultados_backtest_v1.html"

# Define os limites da sua estratégia
# Vamos começar com regras simples:
LIMITE_COMPRA = 1  # Comprar se score agregado do dia for > 1
LIMITE_VENDA = -1 # Vender (fechar posição) se score agregado for < -1

# --- 2. CARREGAR E PROCESSAR DADOS DE SENTIMENTO ---

print(f"Carregando notícias de '{ARQUIVO_NOTICIAS}'...")
try:
    df_noticias = pd.read_json(ARQUIVO_NOTICIAS)
except Exception as e:
    print(f"ERRO ao ler '{ARQUIVO_NOTICIAS}': {e}")
    exit()

print("Processando e agregando sinais de sentimento...")

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

print(f"Baixando dados de preço para {len(tickers_unicos)} tickers...")
print(f"Período: {start_date.date()} até {end_date.date()}")

# Baixa os preços de FECHAMENTO ('Close') para todos os tickers
# O 'yf.download' já nos dá o formato "Wide" que precisamos
precos = yf.download(tickers_unicos, start=start_date, end=end_date, repair=True)['Close']

# --- 4. ALINHAR DADOS E DEFINIR ESTRATÉGIA ---

print("Alinhando preços e sinais...")

# 4.1. Alinhar os dois DataFrames
# 'join='inner'': Só vamos operar em dias que temos AMBOS (preço e sentimento)
# 'ffill()': "Forward-fill". Se o sentimento de Domingo foi +3, esse sinal
#            se mantém para a Segunda-Feira (que é o próximo dia com preço).
sinais, precos_alinhados = df_sentimento_pivot.align(precos, join='inner', axis=0)
sinais = sinais.ffill() # Preenche "buracos" no sentimento (fins de semana)

# 4.2. **A ESTRATÉGIA**
# IMPORTANTE: Usamos .shift(1)
# Nós usamos o sentimento de ONTEM (D-1) para tomar a decisão de hoje (D).
# Não podemos usar o sentimento de hoje, pois isso seria "olhar o futuro".
sinais_atrasados = sinais.shift(1).fillna(0)

# 4.3. Gerar ordens de Compra (Entries) e Venda (Exits)
# Nossa regra (definida no passo 1):
entries = (sinais_atrasados > LIMITE_COMPRA)
exits = (sinais_atrasados < LIMITE_VENDA)

print("Sinais de Compra/Venda gerados.")

# --- 5. RODAR O BACKTEST (SIMULAÇÃO) ---

print("Iniciando simulação do portfólio (Backtest)...")

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

print("Simulação concluída!")

# --- 6. ANALISAR RESULTADOS (LUCRO/PERCA) ---

print("Gerando relatório de resultados...")

# Pega as estatísticas completas
stats = pf.stats()

# Salva um relatório HTML interativo
pf.plot(
    settings=dict(
        bm_returns=False # Não comparar com benchmark por enquanto
    )
).save(ARQUIVO_RESULTADOS)

print("\n" + "="*50)
print("     RESULTADOS DO BACKTEST (ESTRATÉGIA V1)     ")
print("="*50)

# Imprime as métricas mais importantes
print(f"Período Analisado:    {stats['Start']} até {stats['End']}")
print(f"Retorno Total (%):    {stats['Total Return [%]']:.2f}%")
print(f"Taxa de Acerto (%):   {stats['Win Rate [%]']:.2f}%")
print(f"Pior Queda (Max DD %): {stats['Max Drawdown [%]']:.2f}%")
print(f"Sharpe Ratio:         {stats['Sharpe Ratio']:.2f}")
print(f"Total de Trades:      {stats['Total Trades']}")

print("\n🚀 Relatório completo salvo em:")
print(f"{ARQUIVO_RESULTADOS}")