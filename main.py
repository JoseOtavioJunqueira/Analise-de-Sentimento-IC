import subprocess
import os
import sys
import datetime

# --- 1. CONFIGURAÇÕES (AJUSTE AQUI) ---

# !! IMPORTANTE !!
# Coloque o caminho COMPLETO para a pasta do seu projeto Scrapy 
# (a pasta que contém o arquivo 'scrapy.cfg')
SCRAPY_PROJECT_DIR = r"C:\Users\José Otávio\Documents\GitHub\Analise-de-Sentimento-IC\financial_scraper"

# !! IMPORTANTE !!
# Coloque os nomes exatos dos seus 4 spiders aqui
SPIDER_NAMES = [
    "exame", 
    "valor", 
    "infomoney", 
    "bloomberg"
]

# --- 2. FUNÇÕES DE EXECUÇÃO ---

def run_scrapers(project_dir, spiders):
    """
    Muda para o diretório do Scrapy e executa uma lista de spiders
    sequencialmente.
    """
    print(f"Mudando para o diretório do Scrapy: {project_dir}")
    try:
        # Guarda o diretório original para poder voltar depois
        original_dir = os.getcwd()
        os.chdir(project_dir)
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: Diretório do Scrapy não encontrado: {project_dir}")
        return False # Indica falha

    print("Iniciando execução dos spiders...")
    
    for spider in spiders:
        print(f"\n--- Iniciando scraper: {spider} ---")
        try:
            # 'shell=True' é recomendado no Windows para encontrar o comando 'scrapy'
            # 'check=True' garante que um erro no scraper vai parar o script
            subprocess.run(f"scrapy crawl {spider}", shell=True, check=True)
            print(f"--- Scraper {spider} concluído com sucesso ---")
        
        except subprocess.CalledProcessError as e:
            print(f"ERRO ao executar o scraper {spider}: {e}")
            print("A rotina será interrompida.")
            os.chdir(original_dir) # Volta ao diretório original
            return False # Indica falha
        except FileNotFoundError:
            print(f"ERRO: O comando 'scrapy' não foi encontrado.")
            print("Verifique se o Scrapy está instalado e no PATH do sistema.")
            os.chdir(original_dir)
            return False

    print("\nTodos os scrapers foram executados com sucesso.")
    os.chdir(original_dir) # Sempre volte ao diretório original
    return True # Indica sucesso

def run_analysis(script_name):
    """
    Executa um script Python (ex: analisar_noticias.py) usando o mesmo
    interpretador Python que está rodando o main.py
    """
    print(f"\n--- Iniciando script de análise: {script_name} ---")
    
    # 'sys.executable' é o caminho para o 'python.exe' que está rodando este script
    # Isso garante que a mesma venv/ambiente seja usada.
    try:
        subprocess.run([sys.executable, script_name], check=True)
        print(f"--- Script de análise {script_name} concluído com sucesso ---")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar o script de análise {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"ERRO: Script de análise não encontrado: {script_name}")
        return False

# --- 3. EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    print("="*60)
    print(f"INICIANDO ROTINA DIÁRIA - {datetime.datetime.now()}")
    print("="*60)
    
    # Define o nome do script de análise (assume que está na mesma pasta do main.py)
    analysis_script_file = "analisar_noticias.py"
    
    # Passo 1: Rodar os Scrapers
    success_scrapers = run_scrapers(SCRAPY_PROJECT_DIR, SPIDER_NAMES)
    
    # Passo 2: Rodar a Análise (SÓ SE os scrapers tiverem sucesso)
    if success_scrapers:
        run_analysis(analysis_script_file)
    else:
        print("\nA análise não foi executada devido a uma falha nos scrapers.")
        
    print("\n" + "="*60)
    print(f"ROTINA DIÁRIA FINALIZADA - {datetime.datetime.now()}")
    print("="*60)