import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, BertForSequenceClassification
import io
import re  # Módulo de expressões regulares
import os  # Para verificar se o arquivo existe
import dateparser # Nova biblioteca para normalizar datas
from datetime import datetime

# --- 1. CONFIGURAÇÃO DOS ARQUIVOS ---
arquivo_json_entrada = r'C:\Users\José Otávio\Documents\GitHub\Analise-de-Sentimento-IC\financial_scraper\financial_news.json'
arquivo_json_saida = 'noticias_com_sentimento.json'

# --- 2. NOVAS FUNÇÕES DE AJUDA ---

def normalizar_data(data_str):
    """
    Tenta converter vários formatos de string OU NÚMERO de data para um 
    formato padronizado (ISO 8601).
    Agora trata timestamps de 10 (segundos) e 13 (milissegundos) dígitos.
    """
    if not data_str:
        return None

    # Converte para string para checagem, caso seja int/float
    data_como_str = str(data_str) 
    
    # --- NOVO: Tratamento de Timestamps (Unix) ---
    # Se for numérico (int ou string de dígitos)
    if data_como_str.isdigit():
        try:
            num_data = int(data_como_str)
            num_digitos = len(data_como_str)

            timestamp_sec = None
            if num_digitos == 13: # Provavelmente milissegundos
                timestamp_sec = num_data / 1000.0
            elif num_digitos == 10: # Provavelmente segundos
                timestamp_sec = float(num_data) # Converte para float para consistência
            
            if timestamp_sec is not None:
                # Verificação de sanidade: garante que o timestamp esteja 
                # em um intervalo razoável (ex: entre 2000 e 2050)
                # 946684800 = 2000-01-01
                # 2524608000 = 2050-01-01
                if 946684800 < timestamp_sec < 2524608000:
                     data_obj = datetime.fromtimestamp(timestamp_sec)
                     return data_obj.isoformat()
                else:
                    # É um número, mas fora do intervalo de timestamp esperado
                    # Deixa o dateparser tentar, mas é improvável que funcione
                    pass

        except Exception:
            # Falhou a conversão numérica, deixa o dateparser tentar abaixo
            pass 
    
    # --- Lógica Anterior (Dateparser) ---
    # Se não for um timestamp válido ou for uma string (ex: "6 de maio...")
    try:
        # Usamos 'pt' (português) como língua prioritária
        # O str(data_str) garante que o dateparser receba uma string
        data_obj = dateparser.parse(str(data_str), languages=['pt']) 
        if data_obj:
            # Retorna a data no formato padrão ISO (YYYY-MM-DDTHH:MM:SS)
            return data_obj.isoformat()
        return None
    except Exception:
        # Falha final, não foi possível converter
        return None
    
def carregar_noticias_existentes(arquivo_saida):
    """
    Carrega as notícias já processadas do arquivo de saída.
    Retorna um DataFrame com os dados e um set() com os títulos para deduplicação.
    """
    if not os.path.exists(arquivo_saida):
        print(f"Arquivo '{arquivo_saida}' não encontrado. Um novo será criado.")
        return pd.DataFrame(), set()
        
    try:
        df_existente = pd.read_json(arquivo_saida, orient='records')
        # Cria um conjunto de títulos para verificação rápida de duplicatas
        titulos_existentes = set(df_existente['title'].dropna())
        print(f"Encontradas {len(df_existente)} notícias já processadas.")
        return df_existente, titulos_existentes
    except Exception as e:
        print(f"AVISO: Não foi possível ler o arquivo '{arquivo_saida}'. Ele pode estar vazio ou corrompido. Começando do zero. Erro: {e}")
        return pd.DataFrame(), set()

def ler_novas_noticias(arquivo_entrada):
    """
    Lê o arquivo de entrada bruto, tratando múltiplos blocos JSON.
    """
    print(f"Lendo e extraindo blocos do arquivo '{arquivo_entrada}'...")
    try:
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            conteudo_bruto = f.read()

        if not conteudo_bruto.strip():
            print("Arquivo de entrada está vazio. Nada a processar.")
            return None

        # Encontra todas as ocorrências de texto que começam com '[' e terminam com ']'
        blocos_json_encontrados = re.findall(r'(\[.*?\])', conteudo_bruto, re.DOTALL)
        
        if not blocos_json_encontrados:
            print("Nenhum bloco de dados JSON válido (começando com '[' e terminando com ']') foi encontrado no arquivo de entrada.")
            return None

        lista_de_dfs = []
        for i, bloco in enumerate(blocos_json_encontrados):
            df_bloco = pd.read_json(io.StringIO(bloco))
            lista_de_dfs.append(df_bloco)
        
        df_novas = pd.concat(lista_de_dfs, ignore_index=True)
        print(f"Arquivo de entrada consolidado com sucesso ({len(df_novas)} notícias brutas).")
        return df_novas

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{arquivo_entrada}' não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO ao processar o arquivo de entrada JSON: {e}")
        return None

def limpar_arquivo_entrada(arquivo_entrada):
    """
    Limpa o arquivo de entrada após o processamento bem-sucedido.
    """
    try:
        # Escreve uma lista vazia para manter o arquivo como um JSON válido (opcional)
        with open(arquivo_entrada, 'w', encoding='utf-8') as f:
            f.write("[]") 
        print(f"Arquivo de entrada '{arquivo_entrada}' foi limpo.")
    except Exception as e:
        print(f"ERRO ao limpar o arquivo de entrada '{arquivo_entrada}': {e}")


# --- 3. INÍCIO DO PIPELINE DE PROCESSAMENTO ---

# 3.1. Carregar dados existentes para evitar duplicatas
df_existente, titulos_existentes = carregar_noticias_existentes(arquivo_json_saida)

# 3.2. Ler as novas notícias do arquivo de entrada
df_novas_noticias = ler_novas_noticias(arquivo_json_entrada)

# Se não houver novas notícias, encerra o script
if df_novas_noticias is None or df_novas_noticias.empty:
    print("Nenhuma notícia nova encontrada para processar. Encerrando.")
    exit()

# 3.3. **NOVO: Deduplicação**
# Filtra o DataFrame de novas notícias, mantendo apenas aquelas
# cujo 'title' NÃO ESTÁ no conjunto de 'titulos_existentes'.
df_para_processar = df_novas_noticias[~df_novas_noticias['title'].isin(titulos_existentes)].reset_index(drop=True)

if df_para_processar.empty:
    print("Todas as notícias do arquivo de entrada já foram processadas anteriormente.")
    # Limpamos o arquivo de entrada mesmo assim, pois já foram processadas
    limpar_arquivo_entrada(arquivo_json_entrada)
    print("Encerrando.")
    exit()

print(f"Encontradas {len(df_para_processar)} notícias realmente novas para processar.")

# --- 4. LIMPEZA E PREPARAÇÃO DOS DADOS (Agora em 'df_para_processar') ---
print("Limpando e preparando os textos...")
df_para_processar['title'] = df_para_processar['title'].fillna('')
df_para_processar['content'] = df_para_processar['content'].fillna('')
df_para_processar['texto_completo'] = (df_para_processar['title'].str.strip() + ' ' + df_para_processar['content'].str.strip()).str.strip()

linhas_antes = len(df_para_processar)
df_para_processar = df_para_processar[df_para_processar['texto_completo'] != ''].reset_index(drop=True)
linhas_depois = len(df_para_processar)
print(f"{linhas_antes - linhas_depois} linhas vazias foram removidas.")

# 4.1. **NOVO: Normalização da Data**
# Vamos supor que sua coluna de data se chama 'date'. 
# Se o nome for outro (ex: 'data', 'timestamp'), apenas troque 'date' abaixo.
if 'date' in df_para_processar.columns:
    print("Normalizando datas...")
    df_para_processar['data_normalizada'] = df_para_processar['date'].apply(normalizar_data)
else:
    print("AVISO: Coluna 'date' não encontrada. Pulando normalização de data.")


# --- 5. LÓGICA DO MODELO DE SENTIMENTO ---
pred_mapper = {0: "POSITIVE", 1: "NEGATIVE", 2: "NEUTRAL"}

print("Carregando o modelo FinBERT... (Isso pode demorar um pouco)")
tokenizer = AutoTokenizer.from_pretrained("lucas-leme/FinBERT-PT-BR")
model = BertForSequenceClassification.from_pretrained("lucas-leme/FinBERT-PT-BR")

def prever_sentimento(texto):
    if not isinstance(texto, str) or not texto:
        return "TEXTO_INVALIDO"
    inputs = tokenizer(texto, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    prediction = np.argmax(logits.numpy())
    return pred_mapper[prediction]

# --- 6. APLICAÇÃO DO MODELO ---
print(f"Iniciando a classificação de sentimento em {len(df_para_processar)} notícias...")
# Usamos .copy() para evitar o SettingWithCopyWarning
df_processado = df_para_processar.copy()
df_processado['sentimento_previsto'] = df_processado['texto_completo'].apply(prever_sentimento)


# --- 7. **NOVO: COMBINAR E SALVAR O RESULTADO FINAL** ---
print("Combinando notícias existentes com as novas processadas...")
# Concatena o DataFrame antigo com o novo DataFrame já processado
df_final_completo = pd.concat([df_existente, df_processado], ignore_index=True)

print(f"Salvando {len(df_final_completo)} notícias no total em '{arquivo_json_saida}'...")
try:
    df_final_completo.to_json(
        arquivo_json_saida,
        orient='records',
        indent=4,
        force_ascii=False
    )
    
    print("\n🚀 Processo concluído com sucesso!")
    print(f"✅ O arquivo '{arquivo_json_saida}' foi atualizado.")

    # 7.1. **NOVO: Limpar arquivo de entrada**
    # Somente limpa o arquivo de entrada se o salvamento foi bem-sucedido
    limpar_arquivo_entrada(arquivo_json_entrada)

except Exception as e:
    print(f"\nERRO CRÍTICO ao salvar o arquivo final: {e}")
    print("ATENÇÃO: O arquivo de entrada NÃO foi limpo para evitar perda de dados.")