import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, BertForSequenceClassification
import io
import re # Módulo de expressões regulares

# --- 1. CONFIGURAÇÃO DOS ARQUIVOS ---
arquivo_json_entrada = 'dados_noticias.json'
arquivo_json_saida = 'noticias_com_sentimento.json'

# --- 2. LEITURA E PARSE ROBUSTO DO JSON ---
print(f"Lendo e extraindo blocos do arquivo '{arquivo_json_entrada}'...")
try:
    with open(arquivo_json_entrada, 'r', encoding='utf-8') as f:
        conteudo_bruto = f.read()

    # --- NOVA ABORDAGEM: ENCONTRAR TODOS OS BLOCOS JSON VÁLIDOS ---
    # Encontra todas as ocorrências de texto que começam com '[' e terminam com ']'
    blocos_json_encontrados = re.findall(r'(\[.*?\])', conteudo_bruto, re.DOTALL)
    
    if not blocos_json_encontrados:
        raise ValueError("Nenhum bloco de dados JSON válido (começando com '[' e terminando com ']') foi encontrado no arquivo.")

    lista_de_dfs = []
    # Itera sobre cada bloco de texto JSON encontrado
    for i, bloco in enumerate(blocos_json_encontrados):
        # Converte cada bloco em um DataFrame e adiciona a uma lista
        df_bloco = pd.read_json(io.StringIO(bloco))
        lista_de_dfs.append(df_bloco)
        print(f"Bloco {i+1} processado com sucesso ({len(df_bloco)} linhas).")

    # Concatena todos os DataFrames da lista em um único DataFrame
    df = pd.concat(lista_de_dfs, ignore_index=True)
    print("Todos os blocos foram consolidados com sucesso!")

except FileNotFoundError:
    print(f"ERRO: Arquivo '{arquivo_json_entrada}' não encontrado.")
    exit()
except Exception as e:
    print(f"ERRO ao processar o arquivo JSON: {e}")
    exit()

# --- 3. LIMPEZA E PREPARAÇÃO DOS DADOS (sem alteração) ---
print("Limpando e preparando os textos...")
df['title'] = df['title'].fillna('')
df['content'] = df['content'].fillna('')
df['texto_completo'] = (df['title'].str.strip() + ' ' + df['content'].str.strip()).str.strip()

linhas_antes = len(df)
df = df[df['texto_completo'] != ''].reset_index(drop=True)
linhas_depois = len(df)
print(f"{linhas_antes - linhas_depois} linhas vazias foram removidas.")


# --- 4. LÓGICA DO MODELO DE SENTIMENTO (sem alteração) ---
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

# --- 5. APLICAÇÃO DO MODELO (sem alteração) ---
print(f"Iniciando a classificação de sentimento em {len(df)} notícias...")
df['sentimento_previsto'] = df['texto_completo'].apply(prever_sentimento)

# --- 6. SALVAR O RESULTADO FINAL (sem alteração) ---
print(f"Salvando os resultados em '{arquivo_json_saida}'...")
df.to_json(
    arquivo_json_saida,
    orient='records',
    indent=4,
    force_ascii=False
)

print("\n🚀 Processo concluído com sucesso!")
print(f"✅ O arquivo '{arquivo_json_saida}' foi gerado corretamente.")