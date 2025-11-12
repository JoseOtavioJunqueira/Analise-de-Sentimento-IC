import spacy
import pandas as pd
import json
import os

# --- 1. CONFIGURAÇÃO ---
ARQUIVO_ENTRADA = "noticias_com_sentimento.json"
MAPA_TICKERS_ARQ = "mapeamento_tickers.json"
ARQUIVO_SAIDA = "noticias_mapeadas.json"

# --- 2. FUNÇÕES DE PROCESSAMENTO ---

def carregar_modelo_spacy():
    """Carrega o modelo 'pt_core_news_lg' do spaCy."""
    print("Carregando modelo spaCy 'pt_core_news_lg'...")
    try:
        # Tenta carregar o modelo
        nlp = spacy.load("pt_core_news_lg")
        print("Modelo spaCy carregado com sucesso.")
        return nlp
    except OSError:
        print("\n--- ERRO ---")
        print("Modelo 'pt_core_news_lg' do spaCy não encontrado.")
        print("Execute o comando abaixo no seu terminal para instalá-lo:")
        print("pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-v3.7.0/pt_core_news_lg-3.7.0.tar.gz")
        print("------------\n")
        exit() # Encerra o script se o modelo não estiver instalado

def extrair_empresas(texto, nlp_model):
    """
    Usa o modelo spaCy (NER) para extrair entidades 'ORG' (Organização) do texto.
    """
    if not isinstance(texto, str) or not texto:
        return []
        
    doc = nlp_model(texto)
    empresas = []
    for ent in doc.ents:
        if ent.label_ == "ORG":
            # Adiciona o nome da empresa, limpando espaços
            empresas.append(ent.text.strip())
            
    # Remove duplicatas e retorna a lista
    return list(set(empresas))

def carregar_mapa_tickers(arquivo_mapa):
    """
    Carrega o arquivo JSON de mapeamento de Nomes para Tickers.
    """
    if not os.path.exists(arquivo_mapa):
        print(f"ERRO: Arquivo de mapeamento '{arquivo_mapa}' não encontrado.")
        print("Certifique-se de que ele está na mesma pasta que este script.")
        exit()
        
    print(f"Carregando mapa de tickers de '{arquivo_mapa}'...")
    with open(arquivo_mapa, 'r', encoding='utf-8') as f:
        mapa_tickers = json.load(f)
    print("Mapa carregado.")
    return mapa_tickers

def mapear_tickers(lista_empresas, mapa_tickers):
    """
    Converte uma lista de nomes de empresas em uma lista de tickers,
    usando o mapa. Ignora valores 'null'.
    """
    tickers = []
    for empresa in lista_empresas:
        # Verifica se a empresa está no mapa
        if empresa in mapa_tickers:
            ticker_mapeado = mapa_tickers[empresa]
            
            # Adiciona APENAS se o ticker não for 'null'
            if ticker_mapeado is not None:
                tickers.append(ticker_mapeado)
                
    # Retorna a lista de tickers únicos
    return list(set(tickers))

# --- 3. EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    
    # --- PASSO 1: CARREGAR DADOS E MODELOS ---
    nlp = carregar_modelo_spacy()
    mapa_tickers = carregar_mapa_tickers(MAPA_TICKERS_ARQ)
    
    print(f"Lendo notícias de entrada: '{ARQUIVO_ENTRADA}'...")
    try:
        df = pd.read_json(ARQUIVO_ENTRADA)
    except Exception as e:
        print(f"ERRO ao ler o arquivo '{ARQUIVO_ENTRADA}': {e}")
        exit()
        
    if 'texto_completo' not in df.columns:
        print("ERRO: O arquivo de entrada não contém a coluna 'texto_completo'.")
        exit()

    print(f"Encontradas {len(df)} notícias para processar.")

    # --- PASSO 2: EXTRAIR ENTIDADES (NER) ---
    print("Iniciando extração de entidades (NER) com spaCy...")
    print("(Isso pode demorar alguns minutos se o arquivo for grande...)")
    df['empresas_citadas'] = df['texto_completo'].apply(lambda texto: extrair_empresas(texto, nlp))
    print("Extração de entidades concluída.")

    # --- PASSO 3: MAPEAMENTO EMPRESA -> TICKER ---
    print("Iniciando mapeamento de tickers...")
    df['tickers_citados'] = df['empresas_citadas'].apply(lambda lista: mapear_tickers(lista, mapa_tickers))
    print("Mapeamento concluído.")

    # --- PASSO 4: FILTRAR E SALVAR ---
    
    # Filtra o DataFrame, mantendo APENAS notícias que
    # resultaram em pelo menos UM ticker mapeado.
    df_mapeado = df[df['tickers_citados'].apply(len) > 0].copy()

    # Reinicia o índice para um arquivo limpo (opcional)
    df_mapeado.reset_index(drop=True, inplace=True)

    print("-" * 50)
    print(f"Processo finalizado.")
    print(f"Notícias originais: {len(df)}")
    print(f"Notícias acionáveis (mapeadas): {len(df_mapeado)}")
    print(f"Notícias filtradas (sem ticker): {len(df) - len(df_mapeado)}")
    
    # Salva o resultado final
    print(f"\nSalvando notícias mapeadas em '{ARQUIVO_SAIDA}'...")
    df_mapeado.to_json(
        ARQUIVO_SAIDA,
        orient='records',
        indent=4,
        force_ascii=False # Mantém acentos
    )

    print("\n🚀 Sucesso! O arquivo 'noticias_mapeadas.json' está pronto.")
    print("Próximo passo: 'criar_estrategia.py' (Backtesting).")