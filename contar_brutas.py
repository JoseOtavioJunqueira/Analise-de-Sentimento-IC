import re
import json

def contar_noticias():
    try:
        with open("financial_scraper/financial_news.json", "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        blocos = re.findall(r"(\[.*?\])", conteudo, re.DOTALL)
        total = 0
        for bloco in blocos:
            try:
                noticias = json.loads(bloco)
                total += len(noticias)
            except json.JSONDecodeError:
                continue
        print(f"Total de notícias no financial_news.json: {total}")
    except FileNotFoundError:
        print("Arquivo não encontrado.")

if __name__ == "__main__":
    contar_noticias()
