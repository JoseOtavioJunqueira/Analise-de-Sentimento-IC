import json
import os
from datetime import datetime
from collections import Counter

# Caminhos dos arquivos
ARQUIVO_ENTRADA = 'noticias_mapeadas.json'
ARQUIVO_SAIDA = 'analise_frequencia.json'

def processar_frequencia():
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"Erro: O arquivo {ARQUIVO_ENTRADA} não foi encontrado.")
        return

    with open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f:
        try:
            noticias = json.load(f)
        except json.JSONDecodeError:
            print("Erro: Falha ao ler o JSON.")
            return

    contagem_ticker = Counter()
    # Dicionário para guardar a relação Ticker -> Nome da Empresa
    mapeamento_nome = {}

    for item in noticias:
        tickers = item.get('tickers_citados', [])
        empresas = item.get('empresas_citadas', [])
        
        # Como o seu JSON tem listas, precisamos iterar sobre elas
        for i, ticker in enumerate(tickers):
            contagem_ticker[ticker] += 1
            
            # Tenta pegar o nome da empresa correspondente na mesma posição da lista
            if ticker not in mapeamento_nome:
                if i < len(empresas):
                    mapeamento_nome[ticker] = empresas[i]
                elif empresas: # Se não estiver na mesma posição, pega a primeira disponível
                    mapeamento_nome[ticker] = empresas[0]
                else:
                    mapeamento_nome[ticker] = "N/A"

    # Montar o objeto de saída
    resultado = {
        "ultima_execucao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_noticias_processadas": len(noticias),
        "estatisticas": []
    }

    for ticker, qtd in contagem_ticker.items():
        resultado["estatisticas"].append({
            "ticker": ticker,
            "empresa": mapeamento_nome.get(ticker, "N/A"),
            "vezes_que_apareceu": qtd,
            "nivel_informacao": "ALTO" if qtd >= 10 else "MEDIO" if qtd >= 5 else "BAIXO"
        })

    # Ordenar por maior número de aparições
    resultado["estatisticas"] = sorted(
        resultado["estatisticas"], 
        key=lambda x: x["vezes_que_apareceu"], 
        reverse=True
    )

    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    print(f"Relatório gerado em: {ARQUIVO_SAIDA}")
    print(f"Total de ativos diferentes encontrados: {len(contagem_ticker)}")

if __name__ == "__main__":
    processar_frequencia()