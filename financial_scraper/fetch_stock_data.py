import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import numpy as np # Importado para checar tipos

# --- ARQUIVOS ---
# O script está em 'financial_scraper/', então usamos '../' para voltar para a raiz
ARQUIVO_NOTICIAS = "../noticias_mapeadas.json"
ARQUIVO_SAIDA_PRECOS = "../dados_historicos_acoes.json"

def fetch_stock_data(tickers, start_date, end_date):
    """
    Busca dados históricos para uma lista de tickers.
    'tickers' deve ser uma lista de strings.
    """
    if not tickers:
        print("Nenhum ticker fornecido para busca.")
        return None
        
    # Converte a lista de tickers em uma string separada por espaços (formato do yfinance)
    tickers_str = " ".join(tickers)
    
    print(f"Buscando dados para {len(tickers)} tickers de {start_date} até {end_date}...")
    
    try:
        # Baixa os dados
        # group_by='ticker' é útil se um ticker falhar, os outros continuam
        data = yf.download(tickers_str, start=start_date, end=end_date, interval="1d", group_by='ticker')
        return data
    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        return None

# --- NOVA FUNÇÃO ---
def get_prices_for_row(row, price_data_df):
    """
    Para uma linha (notícia), encontra os preços de fechamento
    dos tickers citados na data da notícia.
    
    row: Uma linha do DataFrame de notícias.
    price_data_df: O DataFrame completo com dados históricos (Índice=Data, Colunas=Tickers).
    """
    
    # --- INÍCIO DA CORREÇÃO ---
    # Primeiro, checa se a data é Nula/NaT (Not a Time)
    # Isso acontece se 'analisar_noticias.py' não conseguiu normalizar a data.
    if pd.isna(row['data_normalizada']):
        # Se a data for inválida, não podemos buscar preços.
        # Retorna None para todos os tickers citados.
        precos_dict = {}
        lista_tickers = row['tickers_citados']
        if isinstance(lista_tickers, list):
            for ticker in lista_tickers:
                precos_dict[ticker] = None
        return precos_dict
    # --- FIM DA CORREÇÃO ---

    # Garante que a data esteja no formato string 'YYYY-MM-DD' para busca no índice
    try:
        # Tenta formatar se for um objeto datetime
        data_noticia_str = row['data_normalizada'].strftime('%Y-%m-%d')
    except AttributeError:
        # Se já for string (ou outro tipo), converte e pega a data
        data_noticia_str = str(row['data_normalizada']).split('T')[0]
        
    lista_tickers = row['tickers_citados']
    precos_dict = {}
    
    if not isinstance(lista_tickers, list):
        return {} # Retorna dict vazio se não for uma lista
        
    # Verifica se a data da notícia existe no nosso DF de preços
    if data_noticia_str not in price_data_df.index:
        # Dia sem pregão (fim de semana/feriado)
        # Preenche com None para todos os tickers
        for ticker in lista_tickers:
            precos_dict[ticker] = None
        return precos_dict
        
    # Se a data existe, busca o preço de cada ticker
    for ticker in lista_tickers:
        try:
            # Busca o preço na data e ticker específicos
            preco = price_data_df.loc[data_noticia_str, ticker]
            
            # Converte numpy.float64 para float nativo e trata NaNs
            if pd.isna(preco):
                precos_dict[ticker] = None
            else:
                # Garante que é um float nativo do Python (melhor para JSON)
                precos_dict[ticker] = float(preco) 
                
        except (KeyError, TypeError):
            # KeyError: Ticker não encontrado nas colunas (ex: falha no download)
            # TypeError: Algo deu errado na busca
            precos_dict[ticker] = None
            
    return precos_dict
# --- FIM DA NOVA FUNÇÃO ---


if __name__ == "__main__":
    
    # --- 1. LER O ARQUIVO DE NOTÍCIAS MAPEADAS ---
    print(f"Lendo notícias de '{ARQUIVO_NOTICIAS}' para encontrar tickers...")
    try:
        df_noticias = pd.read_json(ARQUIVO_NOTICIAS)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{ARQUIVO_NOTICIAS}' não encontrado.")
        print("Certifique-se de que 'associar_tickers.py' foi executado com sucesso.")
        exit()
    except Exception as e:
        print(f"Erro ao ler o arquivo JSON: {e}")
        exit()

    if df_noticias.empty:
        print("Arquivo de notícias está vazio. Nada para processar.")
        exit()

    # --- 2. EXTRAIR LISTA ÚNICA DE TICKERS ---
    # Pega todas as listas de 'tickers_citados'
    listas_de_tickers = df_noticias['tickers_citados'].tolist()
    
    # Cria um conjunto (set) para armazenar tickers únicos
    tickers_unicos = set()
    for lista in listas_de_tickers:
        for ticker in lista:
            tickers_unicos.add(ticker)
            
    lista_unica_tickers = list(tickers_unicos)
    
    if not lista_unica_tickers:
        print("Nenhum ticker foi encontrado nas notícias mapeadas.")
        exit()
        
    print(f"Encontrados {len(lista_unica_tickers)} tickers únicos para buscar.")
    # print(lista_unica_tickers) # Descomente para ver a lista

    # --- 3. DETERMINAR O PERÍODO (DATAS) ---
    try:
        # Converte a coluna de data para objetos datetime
        df_noticias['data_normalizada'] = pd.to_datetime(df_noticias['data_normalizada'])
        # Encontra a data da notícia mais antiga
        data_mais_antiga = df_noticias['data_normalizada'].min()
    except Exception as e:
        print(f"Erro ao processar 'data_normalizada': {e}")
        print("Usando um período padrão de 1 ano.")
        data_mais_antiga = datetime.now() - timedelta(days=365)

    # Data de início: A data mais antiga (menos 1 dia por segurança)
    data_inicio_busca = data_mais_antiga - timedelta(days=1)
    
    # Data de fim: O dia de "hoje" (adicionamos 1 dia pois o yfinance não inclui o 'end_date')
    data_fim_busca = datetime.now() + timedelta(days=1)
    
    # Formata as datas para string no formato YYYY-MM-DD
    start_str = data_inicio_busca.strftime('%Y-%m-%d')
    end_str = data_fim_busca.strftime('%Y-%m-%d')

    # --- 4. BUSCAR OS DADOS ---
    dados_historicos_raw = fetch_stock_data(lista_unica_tickers, start_str, end_str)
    
    if dados_historicos_raw is None or dados_historicos_raw.empty:
        print("Não foi possível baixar os dados históricos. Encerrando.")
        exit()
        
    print("\nDados baixados com sucesso.")

    # --- 5. PROCESSAR E SALVAR OS DADOS DE PREÇO (PARA BACKTEST) ---
    
    # Para o backtest, geralmente só nos importamos com o preço de 'Fechamento' ('Close')
    # Com group_by='ticker', as colunas são um MultiIndex (Ticker, PriceType)
    # Ex: ('PETR4.SA', 'Open'), ('PETR4.SA', 'Close'), ('VALE3.SA', 'Open'), ...
    
    dados_fechamento = None
    
    try:
        if isinstance(dados_historicos_raw.columns, pd.MultiIndex):
            # Caso 1: Múltiplos tickers baixados com sucesso. Colunas = MultiIndex (e.g., ('PETR4.SA', 'Close'))
            # O group_by='ticker' faz o Ticker ser o level 0.
            print("Múltiplos tickers detectados (MultiIndex). Extraindo 'Close' (Nível 1)...")
            # Pega todas as sub-colunas 'Close' de todos os tickers (level=1)
            dados_fechamento = dados_historicos_raw.xs('Close', level=1, axis=1)
            
        else:
            # Caso 2: Apenas um ticker baixado com sucesso. Colunas = ['Open', 'High', 'Low', 'Close']
            print("Ticker único detectado (SingleIndex). Extraindo 'Close'.")
            if 'Close' in dados_historicos_raw.columns:
                 dados_fechamento = dados_historicos_raw[['Close']] # Pega como DataFrame
                 
                 # Tenta nomear a coluna
                 # Lista de falhas do SEU LOG
                 failed_downloads = ['KERI34.SA', 'BYDD34.SA', 'LRLC34.SA', 'UNIL34.SA', 'DECO34.SA', 'WBDC34.SA', 'JBSS3.SA', 'GEOC34.SA', 'TRIL34.SA']
                 successful_set = tickers_unicos - set(failed_downloads)
                 if len(successful_set) == 1:
                    ticker_name = list(successful_set)[0]
                    dados_fechamento.columns = [ticker_name]
                    print(f"Ticker único nomeado como: {ticker_name}")
                 else:
                    # Isso pode acontecer se o único ticker de sucesso não estava na lista de falhas?
                    # Ou se o yfinance retornou SingleIndex mesmo com >1 sucesso
                    print("Aviso: Não foi possível determinar o nome do ticker único. Usando 'Close'.")
            else:
                print("Erro: SingleIndex retornado, mas sem coluna 'Close'.")
                dados_fechamento = pd.DataFrame() # Vazio
                
    except Exception as e:
        print(f"ERRO CRÍTICO ao processar estrutura de dados do yfinance: {e}")
        print("É provável que a estrutura de dados tenha mudado.")
        dados_fechamento = pd.DataFrame() # Vazio

    # Remove linhas que só contêm NaN (dias sem negociação para todos)
    if dados_fechamento is not None and not dados_fechamento.empty:
        dados_fechamento = dados_fechamento.dropna(how='all')
    else:
        print("Erro ao processar os dados de fechamento, o DataFrame está vazio. Encerrando.")
        exit()

    # Converte o índice (Datas) para string no formato YYYY-MM-DD
    # Isso é essencial para salvar em JSON e para o script de estratégia ler
    try:
        dados_fechamento.index = dados_fechamento.index.strftime('%Y-%m-%d')
    except AttributeError:
        print("Aviso: O índice de datas já estava formatado, ou ocorreu um erro.")
        pass # Ignora o erro se já estiver no formato correto

    # Salva os dados de fechamento em um JSON
    # O formato 'index' cria um objeto onde as chaves são as DATAS:
    # { "2023-01-01": { "PETR4.SA": 30.00, "VALE3.SA": 90.00, ... }, ... }
    # Este é um formato excelente para o backtest (fácil de buscar preço por data)
    print(f"Salvando dados de preços em '{ARQUIVO_SAIDA_PRECOS}'...")
    dados_fechamento.to_json(ARQUIVO_SAIDA_PRECOS, orient='index', indent=4, date_format='iso')

    print(f"\n✅ Arquivo '{ARQUIVO_SAIDA_PRECOS}' foi criado na pasta principal.")
    
    
    # --- 6. NOVO: ENRIQUECER 'noticias_mapeadas.json' COM PREÇOS ---
    print("\n--- 6. ENRIQUECENDO 'noticias_mapeadas.json' COM PREÇOS ---")
    print("Adicionando preços do dia da notícia...")

    # Certifica que a coluna de data está em datetime para strftime funcionar
    # (O passo 3 já fez isso, mas garantimos aqui)
    try:
        df_noticias['data_normalizada'] = pd.to_datetime(df_noticias['data_normalizada'])
    except Exception as e:
        print(f"Aviso ao re-converter data: {e}")

    # Aplica a função 'get_prices_for_row' para criar a nova coluna
    # 'dados_fechamento' é o DataFrame com (Índice=Data, Colunas=Tickers)
    # 'df_noticias' é o DataFrame com as notícias
    df_noticias['precos_no_dia'] = df_noticias.apply(
        get_prices_for_row, 
        axis=1,            # Aplica por linha
        price_data_df=dados_fechamento # Passa o DF de preços como argumento extra
    )

    print("Preços adicionados. Salvando arquivo de notícias atualizado...")
    
    # Salva o df_noticias MODIFICADO de volta ao arquivo original
    # Usamos 'date_format='iso'' para manter as datas padronizadas
    df_noticias.to_json(
        ARQUIVO_NOTICIAS,
        orient='records',
        indent=4,
        force_ascii=False,
        date_format='iso' 
    )

    print("\n🚀 Sucesso!")
    print(f"✅ O arquivo '{ARQUIVO_NOTICIAS}' foi ATUALIZADO com os preços do dia.")
    # print("Próximo passo: Executar 'criar_estrategia.py'.") # Removido da linha de cima