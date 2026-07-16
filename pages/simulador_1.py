"""import streamlit as st
import pandas as pd
import os

st.title("📈 Simulador de Estratégia de Trading (IC)")

caminho_csv = 'resultado_estrategia.csv'

if os.path.exists(caminho_csv):
    df_estrategia = pd.read_csv(caminho_csv)
    
    # Métricas de Resumo
    patrimonio_inicial = 10000.00
    patrimonio_final = df_estrategia['Patrimônio Total (R$)'].iloc[-1]
    lucro = patrimonio_final - patrimonio_inicial
    rentabilidade = (lucro / patrimonio_inicial) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Inicial", f"R$ {patrimonio_inicial:,.2f}")
    col2.metric("Patrimônio Final", f"R$ {patrimonio_final:,.2f}", f"{rentabilidade:.2f}%")
    col3.metric("Lucro / Prejuízo", f"R$ {lucro:,.2f}")
    
    st.divider()
    
    # Gráfico do Patrimônio ao longo do tempo
    st.subheader("Evolução do Patrimônio")
    df_grafico = df_estrategia[['Data da Notícia', 'Patrimônio Total (R$)']].set_index('Data da Notícia')
    st.line_chart(df_grafico)
    
    st.divider()
    
    # Tabela Detalhada (A que você pediu no ponto 3)
    st.subheader("Log Detalhado das Operações")
    
    # Estilizando a tabela para ficar mais bonita
    st.dataframe(
        df_estrategia,
        column_config={
            "Diferença Monetária (R$)": st.column_config.TextColumn("Lucro da Operação"),
            "Notícias": st.column_config.TextColumn("Resumo das Notícias", width="large")
        },
        use_container_width=True,
        hide_index=True
    )
    
else:
    st.warning("Arquivo 'resultado_estrategia.csv' não encontrado. Rode o script simulador_estrategia.py primeiro.")

import streamlit as st
import pandas as pd
import glob
import os

st.title("📈 Simulador Dinâmico de Estratégias (IC)")

pasta_resultados = 'resultados_simulacao'

# Agora o glob procura os arquivos DENTRO da pasta
arquivos_encontrados = glob.glob(f"{pasta_resultados}/resultado_estrategia_*.csv")

if not arquivos_encontrados:
    st.warning(f"Nenhum CSV encontrado. Rode o simulador_estrategia.py primeiro para popular a pasta '{pasta_resultados}'!")
else:
    # os.path.basename pega só o nome do arquivo, ignorando o caminho da pasta
    opcoes_tickers = [os.path.basename(arq).replace("resultado_estrategia_", "").replace(".csv", "") for arq in arquivos_encontrados]
    
    ticker_escolhido = st.selectbox("Selecione o Ativo para visualizar os resultados:", sorted(opcoes_tickers))
    
    # Reconstrói o caminho completo para o pandas conseguir ler
    caminho_csv = f"{pasta_resultados}/resultado_estrategia_{ticker_escolhido}.csv"
    
    df_estrategia = pd.read_csv(caminho_csv)
    
    # Métricas de Resumo
    patrimonio_inicial = 10000.00
    patrimonio_final = df_estrategia['Patrimônio Total (R$)'].iloc[-1]
    lucro = patrimonio_final - patrimonio_inicial
    rentabilidade = (lucro / patrimonio_inicial) * 100
    
    st.subheader(f"📊 Desempenho: {ticker_escolhido}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Inicial", f"R$ {patrimonio_inicial:,.2f}")
    
    # A cor da setinha muda verde/vermelho dependendo se deu lucro ou prejuízo!
    cor_delta = "normal" if lucro >= 0 else "inverse"
    col2.metric("Patrimônio Final", f"R$ {patrimonio_final:,.2f}", f"{rentabilidade:.2f}%", delta_color=cor_delta)
    col3.metric("Lucro / Prejuízo", f"R$ {lucro:,.2f}")
    
    st.divider()
    
    # Gráfico do Patrimônio
    st.subheader("Evolução do Patrimônio ao Longo do Tempo")
    df_grafico = df_estrategia[['Data da Notícia', 'Patrimônio Total (R$)']].set_index('Data da Notícia')
    st.line_chart(df_grafico)
    
    st.divider()
    
    # Tabela de operações com formatação avançada
    st.subheader("Log Detalhado das Operações")
    
    st.dataframe(
        df_estrategia,
        column_config={
            "Data": st.column_config.DateColumn("Data"),
            "Decisão": st.column_config.TextColumn("Decisão"),
            "Preço Unitário": st.column_config.NumberColumn("Preço da Ação", format="R$ %.2f"),
            "Qtd. Ações": st.column_config.NumberColumn("Qtd. Ações"),
            "Valor Investido": st.column_config.NumberColumn("Valor Investido", format="R$ %.2f"),
            "Caixa Livre": st.column_config.NumberColumn("Caixa Livre", format="R$ %.2f"),
            "Patrimônio Total": st.column_config.NumberColumn("Patrimônio Total", format="R$ %.2f"),
            "Lucro/Prejuízo": st.column_config.NumberColumn("Resultado da Venda", format="R$ %.2f"),
            "Resumo da Notícia": st.column_config.TextColumn("Motivo", width="large")
        },
        use_container_width=True,
        hide_index=True
    )"""

import streamlit as st
import pandas as pd
import glob
import os

st.title("📈 Simulador Dinâmico de Estratégias (IC)")

pasta_resultados = 'resultados_simulacao'
arquivos_encontrados = glob.glob(f"{pasta_resultados}/resultado_estrategia_*.csv")

if not arquivos_encontrados:
    st.warning(f"Nenhum CSV encontrado. Rode o simulador_estrategia.py primeiro para popular a pasta '{pasta_resultados}'!")
else:
    opcoes_tickers = [os.path.basename(arq).replace("resultado_estrategia_", "").replace(".csv", "") for arq in arquivos_encontrados]
    
    ticker_escolhido = st.selectbox("Selecione o Ativo para visualizar os resultados:", sorted(opcoes_tickers))
    
    caminho_csv = f"{pasta_resultados}/resultado_estrategia_{ticker_escolhido}.csv"
    df_estrategia = pd.read_csv(caminho_csv)
    
    patrimonio_inicial = 10000.00
    patrimonio_final = df_estrategia['Patrimônio Total'].iloc[-1]
    lucro = patrimonio_final - patrimonio_inicial
    rentabilidade = (lucro / patrimonio_inicial) * 100
    
    st.subheader(f"📊 Desempenho: {ticker_escolhido}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Inicial", f"R$ {patrimonio_inicial:,.2f}")
    cor_delta = "normal" if lucro >= 0 else "inverse"
    col2.metric("Patrimônio Final", f"R$ {patrimonio_final:,.2f}", f"{rentabilidade:.2f}%", delta_color=cor_delta)
    col3.metric("Lucro / Prejuízo", f"R$ {lucro:,.2f}")
    
    st.divider()

    st.subheader("Log Detalhado das Operações")
    
    # Exibe a tabela completa com todos os dias e notícias, sem filtros
    st.dataframe(
        df_estrategia,
        column_config={
            "Data": st.column_config.DateColumn("Data"),
            "Sentimento": st.column_config.TextColumn("Sentimento"), # <--- AQUI ESTÁ ELE!
            "Decisão": st.column_config.TextColumn("Decisão"),
            "Preço Unitário": st.column_config.NumberColumn("Preço da Ação", format="R$ %.2f"),
            "Qtd. Ações": st.column_config.NumberColumn("Qtd. Ações"),
            "Valor Investido": st.column_config.NumberColumn("Valor Investido", format="R$ %.2f"),
            "Caixa Livre": st.column_config.NumberColumn("Caixa Livre", format="R$ %.2f"),
            "Patrimônio Total": st.column_config.NumberColumn("Patrimônio Total", format="R$ %.2f"),
            "Lucro/Prejuízo": st.column_config.NumberColumn("Resultado da Venda", format="R$ %.2f"),
            "Resumo da Notícia": st.column_config.TextColumn("Motivo", width="large")
        },
        use_container_width=True,
        hide_index=True
    )