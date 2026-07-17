"""import pandas as pd
import yfinance as yf
import json
from datetime import timedelta

def gerar_matriz_mestra(ticker_bolsa, caminho_json_noticias):
    print(f"Iniciando processamento analítico para o ativo {ticker_bolsa}...")

    # 1. Carregamento da base de dados mapeada
    with open(caminho_json_noticias, 'r', encoding='utf-8') as f:
        noticias_brutas = json.load(f)

    # 2. Filtragem estrita iterando sobre a matriz 'tickers_citados'
    noticias_empresa = [
        n for n in noticias_brutas 
        if n.get('tickers_citados') and ticker_bolsa in n['tickers_citados']
    ]
    
    df_noticias = pd.DataFrame(noticias_empresa)
    
    if df_noticias.empty:
        print(f"Nenhuma ocorrência documental encontrada para o ticker {ticker_bolsa}.")
        return

    # 3. Tratamento da dimensão temporal
    # Eliminação de vetores onde a normalização temporal falhou (NaN/null)
    df_noticias = df_noticias.dropna(subset=['data_normalizada']).copy()
    df_noticias['data'] = pd.to_datetime(df_noticias['data_normalizada']).dt.tz_localize(None)

    # 4. Encoding do Espaço de Observação (Conversão Categórica para Escalar)
    mapa_sentimento = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
    df_noticias['sentimento_valor'] = df_noticias['sentimento_previsto'].map(mapa_sentimento)
    
    # Ordenação cronológica estrita
    df_noticias = df_noticias.sort_values('data').reset_index(drop=True)

    # 5. Extração de Série Temporal via API Yahoo Finance
    data_inicio = df_noticias['data'].min() - timedelta(days=30)
    data_fim = df_noticias['data'].max() + timedelta(days=5)
    
    print(f"Extraindo série histórica de preços ({data_inicio.date()} a {data_fim.date()})...")
    df_bolsa = yf.download(ticker_bolsa, start=data_inicio, end=data_fim, progress=False)
    
    if df_bolsa.empty:
        print("Erro: Falha na extração de dados da API.")
        return

    # Isolamento do parâmetro de Fechamento (Close)
    df_bolsa = df_bolsa[['Close']].copy()
    df_bolsa.columns = ['preco_d']
    df_bolsa.index = df_bolsa.index.tz_localize(None)
    
    # 6. Construção da Matriz de Defasagem (Shift de D-1 a D-5)
    for i in range(1, 6):
        df_bolsa[f'preco_d{i}'] = df_bolsa['preco_d'].shift(i)

    # 7. Cálculo Analítico das Derivadas Discretas (Variações Percentuais)
    df_bolsa['var_d1'] = (df_bolsa['preco_d'] - df_bolsa['preco_d1']) / df_bolsa['preco_d1']
    df_bolsa['var_d2'] = (df_bolsa['preco_d1'] - df_bolsa['preco_d2']) / df_bolsa['preco_d2']
    df_bolsa['var_d3'] = (df_bolsa['preco_d2'] - df_bolsa['preco_d3']) / df_bolsa['preco_d3']
    df_bolsa['var_d4'] = (df_bolsa['preco_d3'] - df_bolsa['preco_d4']) / df_bolsa['preco_d4']
    df_bolsa['var_d5'] = (df_bolsa['preco_d4'] - df_bolsa['preco_d5']) / df_bolsa['preco_d5']

    df_bolsa['var_acumulada_3d'] = (df_bolsa['preco_d'] - df_bolsa['preco_d3']) / df_bolsa['preco_d3']
    df_bolsa['var_acumulada_5d'] = (df_bolsa['preco_d'] - df_bolsa['preco_d5']) / df_bolsa['preco_d5']

    # Remoção de ruídos nos contornos da janela temporal
    df_bolsa = df_bolsa.dropna().reset_index()

    # 8. Fusão Assíncrona Orientada a Eventos (Merge As-of)
    # Sincroniza o vetor da notícia com o pregão subsequente viável
    df_noticias = df_noticias.sort_values('data')
    df_bolsa = df_bolsa.sort_values('Date')
    
    matriz_mestra = pd.merge_asof(
        df_noticias, 
        df_bolsa, 
        left_on='data', 
        right_on='Date', 
        direction='forward'
    )

    # 9. Definição do Esquema Final de Variáveis
    colunas_finais = [
        'data', 'source', 'title', 'sentimento_previsto', 'sentimento_valor',
        'preco_d', 'preco_d1', 'preco_d2', 'preco_d3', 'preco_d4', 'preco_d5',
        'var_d1', 'var_d2', 'var_d3', 'var_d4', 'var_d5',
        'var_acumulada_3d', 'var_acumulada_5d'
    ]
    
    colunas_disponiveis = [c for c in colunas_finais if c in matriz_mestra.columns]
    matriz_mestra = matriz_mestra[colunas_disponiveis]

    # Exportação do dataset estruturado
    nome_arquivo = f"dataset_rl_mestra_{ticker_bolsa.replace('.SA', '')}.csv"
    matriz_mestra.to_csv(nome_arquivo, index=False)
    
    print(f"\nMatriz Mestra compilada com êxito: {nome_arquivo}")
    print(f"Total de instâncias de eventos mapeadas: {len(matriz_mestra)}")

if __name__ == "__main__":
    TICKER_ALVO = "PETR4.SA" 
    CAMINHO_JSON_MAPEADO = "noticias_mapeadas.json"
    
    gerar_matriz_mestra(TICKER_ALVO, CAMINHO_JSON_MAPEADO)"""
import pandas as pd
import yfinance as yf
import json
import os
from datetime import timedelta

# Cria a pasta para organizar as matrizes, se ela não existir
PASTA_MATRIZES = "matrizes_rl"
os.makedirs(PASTA_MATRIZES, exist_ok=True)

def extrair_todos_tickers(caminho_json):
    """Lê o JSON e descobre todos os tickers únicos que temos notícias."""
    with open(caminho_json, 'r', encoding='utf-8') as f:
        noticias = json.load(f)
    
    tickers_unicos = set()
    for n in noticias:
        for t in n.get('tickers_citados', []):
            tickers_unicos.add(t)
            
    return list(tickers_unicos), noticias

def gerar_matriz_mestra(ticker_bolsa, noticias_brutas):
    print(f"\nProcessando {ticker_bolsa}...")

    # Filtra as notícias específicas deste ticker
    noticias_empresa = [n for n in noticias_brutas if n.get('tickers_citados') and ticker_bolsa in n['tickers_citados']]
    df_noticias = pd.DataFrame(noticias_empresa)
    
    if df_noticias.empty:
        print(f"-> Nenhuma notícia válida para {ticker_bolsa}. Pulando.")
        return

    df_noticias = df_noticias.dropna(subset=['data_normalizada']).copy()
    if df_noticias.empty:
        return
        
    df_noticias['data'] = pd.to_datetime(df_noticias['data_normalizada']).dt.tz_localize(None)

    mapa_sentimento = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
    df_noticias['sentimento_valor'] = df_noticias['sentimento_previsto'].map(mapa_sentimento)
    df_noticias = df_noticias.sort_values('data').reset_index(drop=True)

    data_inicio = df_noticias['data'].min() - timedelta(days=30)
    data_fim = df_noticias['data'].max() + timedelta(days=5)
    
    # Baixa os dados
    df_bolsa = yf.download(ticker_bolsa, start=data_inicio, end=data_fim, progress=False)
    if df_bolsa.empty:
        print(f"-> Erro ao baixar preços de {ticker_bolsa} no yfinance. Pulando.")
        return

    df_bolsa = df_bolsa[['Close']].copy()
    df_bolsa.columns = ['preco_d']
    df_bolsa.index = df_bolsa.index.tz_localize(None)
    
    # Calcula os lags e variações
    for i in range(1, 6):
        df_bolsa[f'preco_d{i}'] = df_bolsa['preco_d'].shift(i)

    df_bolsa['var_d1'] = (df_bolsa['preco_d'] - df_bolsa['preco_d1']) / df_bolsa['preco_d1']
    df_bolsa['var_d2'] = (df_bolsa['preco_d1'] - df_bolsa['preco_d2']) / df_bolsa['preco_d2']
    df_bolsa['var_d3'] = (df_bolsa['preco_d2'] - df_bolsa['preco_d3']) / df_bolsa['preco_d3']
    df_bolsa['var_d4'] = (df_bolsa['preco_d3'] - df_bolsa['preco_d4']) / df_bolsa['preco_d4']
    df_bolsa['var_d5'] = (df_bolsa['preco_d4'] - df_bolsa['preco_d5']) / df_bolsa['preco_d5']
    df_bolsa['var_acumulada_3d'] = (df_bolsa['preco_d'] - df_bolsa['preco_d3']) / df_bolsa['preco_d3']
    df_bolsa['var_acumulada_5d'] = (df_bolsa['preco_d'] - df_bolsa['preco_d5']) / df_bolsa['preco_d5']

    df_bolsa = df_bolsa.dropna().reset_index()

    df_noticias = df_noticias.sort_values('data')
    df_bolsa = df_bolsa.sort_values('Date')
    
    matriz_mestra = pd.merge_asof(
        df_noticias, df_bolsa, left_on='data', right_on='Date', direction='forward'
    )

    colunas_finais = [
        'data', 'source', 'title', 'sentimento_previsto', 'sentimento_valor',
        'preco_d', 'preco_d1', 'preco_d2', 'preco_d3', 'preco_d4', 'preco_d5',
        'var_d1', 'var_d2', 'var_d3', 'var_d4', 'var_d5',
        'var_acumulada_3d', 'var_acumulada_5d'
    ]
    
    colunas_disponiveis = [c for c in colunas_finais if c in matriz_mestra.columns]
    matriz_mestra = matriz_mestra[colunas_disponiveis]

    # Salva DENTRO da nova pasta
    nome_arquivo = os.path.join(PASTA_MATRIZES, f"dataset_rl_{ticker_bolsa.replace('.SA', '')}.csv")
    matriz_mestra.to_csv(nome_arquivo, index=False)
    print(f"-> Sucesso! Salvo em {nome_arquivo} ({len(matriz_mestra)} eventos).")

if __name__ == "__main__":
    CAMINHO_JSON = "noticias_mapeadas.json"
    print("Mapeando todos os ativos...")
    tickers, noticias = extrair_todos_tickers(CAMINHO_JSON)
    print(f"Encontrados {len(tickers)} ativos diferentes para processar.")
    
    for ticker in tickers:
        gerar_matriz_mestra(ticker, noticias)