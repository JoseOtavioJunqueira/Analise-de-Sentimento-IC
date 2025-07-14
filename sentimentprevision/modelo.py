from transformers import AutoTokenizer, BertForSequenceClassification
import torch
import numpy as np
import pandas as pd

df = pd.read_csv('base-sentimentos.csv')

df = df[df['sentiment'] != 'Não se aplica'].reset_index(drop=True)

pred_mapper = {
    0: "POSITIVE",
    1: "NEGATIVE",
    2: "NEUTRAL"
}

tokenizer = AutoTokenizer.from_pretrained("lucas-leme/FinBERT-PT-BR")
model = BertForSequenceClassification.from_pretrained("lucas-leme/FinBERT-PT-BR")

def prever_sentimento(texto):
    inputs = tokenizer(texto, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    prediction = np.argmax(logits.numpy())
    return pred_mapper[prediction]

df['sentimento_previsto'] = df['text'].apply(prever_sentimento)

df.to_csv('resultados_com_sentimento.csv', index=False)

print("Classificação concluída! Resultado salvo como 'resultados_com_sentimento.csv'.")
