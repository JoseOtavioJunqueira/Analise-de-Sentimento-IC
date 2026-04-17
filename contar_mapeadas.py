import json
import os

def contar_noticias_mapeadas():
    arquivo = "noticias_mapeadas.json"
    
    if not os.path.exists(arquivo):
        print(f"O arquivo {arquivo} não foi encontrado.")
        return
        
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            noticias = json.load(f)
            
        print("="*50)
        print("RELATÓRIO DE NOTÍCIAS FINAIS (MAPEADAS)")
        print("="*50)
        print(f"Total de notícias únicas e úteis salvas: {len(noticias)}")
        print("="*50)
        
    except json.JSONDecodeError:
        print("Erro ao ler o arquivo JSON. Ele pode estar corrompido.")

if __name__ == "__main__":
    contar_noticias_mapeadas()
