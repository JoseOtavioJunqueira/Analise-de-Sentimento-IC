import json
import pandas as pd
import yfinance as yf
from datetime import timedelta
import os

"""compra e venda baseado no sentimento só
    gera os csvs da pasta resultados_simulação e os expõe no app streamlit na página simulador_1
"""

def carregar_e_processar_sentimentos(caminho_arquivo, ticker_alvo): # <-- Adicione aqui
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        noticias = json.load(f)
        
    registros = []
    for noti in noticias:
        texto = noti.get('texto_completo', noti.get('titulo', '')).strip()
        tickers = noti.get('tickers_citados', []) 
        
        # Agora ele filtra dinamicamente o ticker que você pedir!
        if ticker_alvo in tickers:
            data = noti.get('data_normalizada')
            if data:
                registros.append({
                    'data': pd.to_datetime(data).date(), 
                    'sentimento': noti.get('sentimento_previsto'),
                    'texto': texto
                })
                
    df = pd.DataFrame(registros)
    if df.empty:
        raise ValueError(f"Nenhuma notícia encontrada para {ticker_alvo} no dataset.")
        
    mapa_score = {'POSITIVE': 1, 'NEGATIVE': -1, 'NEUTRAL': 0}
    df['valor'] = df['sentimento'].map(mapa_score)
    
    df_agrupado = df.groupby('data').agg({
        'valor': 'sum',
        'texto': lambda x: ' | '.join(x)
    }).reset_index()
    
    def define_sentimento(v):
        if v > 0: return 'POSITIVO'
        elif v < 0: return 'NEGATIVO'
        return 'NEUTRO'
        
    df_agrupado['sentimento_dia'] = df_agrupado['valor'].apply(define_sentimento)
    return df_agrupado.sort_values('data')

"""def carregar_e_processar_sentimentos(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        noticias = json.load(f)
        
    registros = []
                   
    for noti in noticias:
        texto = noti.get('texto_completo', noti.get('titulo', '')).strip()
        tickers = noti.get('tickers_citados', []) # Pega a lista gerada pelo seu spaCy
        
        # Confia na inteligência do NLP que você já desenvolveu
        if 'PETR4.SA' in tickers:
            data = noti.get('data_normalizada')
            if data:
                registros.append({
                    'data': pd.to_datetime(data).date(), 
                    'sentimento': noti.get('sentimento_previsto'),
                    'texto': texto
                })

    df = pd.DataFrame(registros)
    if df.empty:
        raise ValueError("Nenhuma notícia da Petrobras encontrada no dataset.")
        
    mapa_score = {'POSITIVE': 1, 'NEGATIVE': -1, 'NEUTRAL': 0}
    df['valor'] = df['sentimento'].map(mapa_score)
    
    # Agrupa as notícias por dia (soma o sentimento e junta os textos)
    df_agrupado = df.groupby('data').agg({
        'valor': 'sum',
        'texto': lambda x: ' | '.join(x) # Junta várias notícias do mesmo dia
    }).reset_index()
    
    # Define o sentimento consolidado do dia
    def define_sentimento(v):
        if v > 0: return 'POSITIVO'
        elif v < 0: return 'NEGATIVO'
        return 'NEUTRO'
        
    df_agrupado['sentimento_dia'] = df_agrupado['valor'].apply(define_sentimento)
    return df_agrupado.sort_values('data')"""

def executar_backtest(df_sentimentos, ticker='PETR4.SA', capital_inicial=10000.0):
    data_inicio = df_sentimentos['data'].min()
    data_fim = df_sentimentos['data'].max() + pd.Timedelta(days=15)
    
    # Baixa os dados em tempo real do yfinance para ter o 'Open'
    cotacoes = yf.download(ticker, start=data_inicio, end=data_fim, progress=False)
    datas_pregao = cotacoes.index.date
    
    capital_caixa = capital_inicial
    quantidade_acoes = 0
    posicionado = False
    preco_compra = 0.0
    
    log_streamlit = []
    
    for _, row in df_sentimentos.iterrows():
        data_atual = row['data']
        score = row['valor']
        textos = row['texto']
        sentimento = row['sentimento_dia']
        
        if score == 0:
            continue
            
        dias_futuros = [d for d in datas_pregao if d > data_atual]
        if not dias_futuros:
            continue
            
        proximo_pregao = dias_futuros[0]
        preco_execucao = float(cotacoes.loc[str(proximo_pregao)]['Open'].iloc[0])
        
        acao_tomada = "NENHUMA"
        diferenca_monetaria = 0.0
        
        if score > 0:
            if not posicionado:
                quantidade_acoes = int(capital_caixa // preco_execucao)
                if quantidade_acoes > 0:
                    capital_caixa -= quantidade_acoes * preco_execucao
                    posicionado = True
                    preco_compra = preco_execucao
                    acao_tomada = "COMPRA"
            else:
                acao_tomada = "MANTIDO (Comprado)"
                
        elif score < 0:
            if posicionado:
                valor_venda = quantidade_acoes * preco_execucao
                custo_compra = quantidade_acoes * preco_compra
                diferenca_monetaria = valor_venda - custo_compra
                
                capital_caixa += valor_venda
                posicionado = False
                acao_tomada = "VENDA"
                quantidade_acoes = 0 # Zera a quantidade DEPOIS de calcular a venda
            else:
                acao_tomada = "MANTIDO (Zerado)"
                
        # Cálculos de tela
        valor_investido = quantidade_acoes * preco_execucao
        patrimonio_total = capital_caixa + valor_investido
                
        log_streamlit.append({
            'Data': data_atual,
            'Sentimento': sentimento,
            'Decisão': acao_tomada,
            'Preço Unitário': round(preco_execucao, 2),
            'Qtd. Ações': quantidade_acoes,
            'Valor Investido': round(valor_investido, 2),
            'Caixa Livre': round(capital_caixa, 2),
            'Patrimônio Total': round(patrimonio_total, 2),
            'Lucro/Prejuízo': round(diferenca_monetaria, 2) if acao_tomada == "VENDA" else None,
            'Resumo da Notícia': textos
        })

    df_log = pd.DataFrame(log_streamlit)
    return df_log

"""if __name__ == "__main__":
    caminho_base = 'noticias_mapeadas.json' # Ajuste o caminho se necessário
    
    try:
        print("Processando sentimentos...")
        df_scores = carregar_e_processar_sentimentos(caminho_base)
        
        print("Executando backtest...")
        df_resultado = executar_backtest(df_scores, ticker='PETR4.SA')
        
        # EXPORTANDO PARA O STREAMLIT
        df_resultado.to_csv("resultado_estrategia.csv", index=False)
        print("Arquivo 'resultado_estrategia.csv' gerado com sucesso!")
        print(f"Patrimônio Final: R$ {df_resultado['Patrimônio Total (R$)'].iloc[-1]}")
        
    except Exception as e:
        print(f"Erro ao executar o backtest: {e}")"""

if __name__ == "__main__":
    caminho_base = 'noticias_mapeadas.json'
    pasta_resultados = 'resultados_simulacao' # O nome da sua nova pasta
    
    # 1. Cria a pasta magicamente se ela não existir
    if not os.path.exists(pasta_resultados):
        os.makedirs(pasta_resultados)
        print(f"📁 Pasta '{pasta_resultados}' criada com sucesso!")
        
    try:
        with open(caminho_base, 'r', encoding='utf-8') as f:
            noticias = json.load(f)
            
        tickers_dinamicos = set()
        for noti in noticias:
            for t in noti.get('tickers_citados', []):
                tickers_dinamicos.add(t)
                
        print(f"🔍 Tickers encontrados automaticamente: {len(tickers_dinamicos)} empresas.")
        
        # 2. Roda a estratégia e salva DENTRO da pasta
        for ticker_atual in tickers_dinamicos:
            print(f"\n--- Simulando: {ticker_atual} ---")
            try:
                df_scores = carregar_e_processar_sentimentos(caminho_base, ticker_alvo=ticker_atual)
                df_resultado = executar_backtest(df_scores, ticker=ticker_atual)
                
                nome_limpo = ticker_atual.replace('.SA', '')
                # Coloca o caminho da pasta antes do nome do arquivo
                nome_arquivo_csv = f"{pasta_resultados}/resultado_estrategia_{nome_limpo}.csv"
                
                df_resultado.to_csv(nome_arquivo_csv, index=False)
                print(f"✅ Salvo em: {nome_arquivo_csv} (Lucro: R$ {df_resultado['Patrimônio Total'].iloc[-1]:.2f})")
                #print(f"✅ Salvo em: {nome_arquivo_csv} (Lucro: R$ {df_resultado['Patrimônio Total (R$)'].iloc[-1]:.2f})")
            except Exception as e:
                print(f"⚠️ Pulo: Não foi possível testar {ticker_atual}. Motivo: {e}")
                
    except Exception as erro_geral:
        print(f"Erro ao ler os dados: {erro_geral}")