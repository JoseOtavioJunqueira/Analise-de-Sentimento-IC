""" para rodar deve-se executar 
    pip install stable-baselines3 gymnasium
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import os
import glob

"""
    estratégia 2 com método de aprendizado melhor
    precisa do gerar_matriz_mestra 

    quero fazer com que a matriz mestra do gerar matriz mestrar e o resultado desse agente 
    sejam direcionados para astas e rodem para todos os ativos que tenho já igual o estratégia 
    1 rodou.
    Depois montar uma pasta para exibir os resultados no streamlite
    Adicinar o gráfico de compra e venda da estratégia 1 que o Denis pediu.
    Treinar os dois modelos q o Denis passou 
    melhorar com o Claude a coleta  
"""

# Cria a pasta onde os logs do Streamlit vão morar
PASTA_RESULTADOS = "resultados_rl"
os.makedirs(PASTA_RESULTADOS, exist_ok=True)

class ICGymTradingEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, df_dados, features):
        super(ICGymTradingEnv, self).__init__()
        self.df = df_dados.reset_index(drop=True)
        self.features = features
        self.max_steps = len(self.df) - 1
        
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(self.features),), dtype=np.float32
        )
        
        self.current_step = 0
        self.position = 0         
        self.entry_price = 0.0    
        self.lucro_acumulado = 0.0
        self.historico_movimentacoes = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.position = 0
        self.entry_price = 0.0
        self.lucro_acumulado = 0.0
        self.historico_movimentacoes = []
        return self._get_obs(), {}

    def _get_obs(self):
        linha_atual = self.df.iloc[self.current_step]
        return linha_atual[self.features].values.astype(np.float32)

    def step(self, action):
        linha_atual = self.df.iloc[self.current_step]
        preco_atual = linha_atual['preco_d']
        data_atual = linha_atual['data']
        
        reward = 0.0
        movimentacao_texto = ""

        if action == 1: # COMPRAR
            if self.position == 0:
                self.position = 1
                self.entry_price = preco_atual
                movimentacao_texto = f"[{data_atual}] COMPRA : R$ {preco_atual:.2f}"
        elif action == 2: # VENDER
            if self.position == 1:
                lucro_trade = (preco_atual - self.entry_price) / self.entry_price
                reward = lucro_trade 
                self.lucro_acumulado += lucro_trade
                status = "LUCRO" if lucro_trade > 0 else "PREJUÍZO"
                movimentacao_texto = f"[{data_atual}] VENDA  : R$ {preco_atual:.2f} | {status}: {(lucro_trade*100):.2f}%"
                self.position = 0 
                self.entry_price = 0.0

        if movimentacao_texto: 
            self.historico_movimentacoes.append(movimentacao_texto)

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        
        obs = self._get_obs() if not terminated else np.zeros(len(self.features), dtype=np.float32)
        return obs, reward, terminated, False, {}

    def gerar_log_texto(self):
        """Retorna o relatório completo em texto para ser salvo no arquivo"""
        linhas = ["=== RELATÓRIO DE MOVIMENTAÇÕES (RL) ==="]
        linhas.extend(self.historico_movimentacoes)
        linhas.append("="*50)
        linhas.append(f"LUCRO TOTAL ACUMULADO NO PERÍODO: {(self.lucro_acumulado * 100):.2f}%")
        return "\n".join(linhas)

def treinar_ticker(caminho_csv, configuracao_features, total_timesteps=10000):
    
    # Extrai o nome do ticker do nome do arquivo
    nome_arquivo = os.path.basename(caminho_csv)
    ticker = nome_arquivo.replace('dataset_rl_', '').replace('.csv', '')
    
    print(f"\nIniciando treinamento para: {ticker}")
    df = pd.read_csv(caminho_csv)
    df['data'] = pd.to_datetime(df['data'])
    df = df.sort_values('data').reset_index(drop=True)
    
    # Separação Treino (80%) e Teste (20%)
    corte_idx = int(len(df) * 0.8)
    if corte_idx == 0:
        print(f"Poucos dados para {ticker}. Pulando.")
        return

    df_treino = df.iloc[:corte_idx].reset_index(drop=True)
    df_teste = df.iloc[corte_idx:].reset_index(drop=True)
    
    # Fase 1: Treinamento
    env_treino = ICGymTradingEnv(df_treino, features=configuracao_features)
    modelo = PPO("MlpPolicy", env_treino, verbose=0, learning_rate=0.0005)
    modelo.learn(total_timesteps=total_timesteps)
    
    # Fase 2: Teste
    env_teste = ICGymTradingEnv(df_teste, features=configuracao_features)
    obs, info = env_teste.reset()
    done = False
    
    while not done:
        action, _states = modelo.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env_teste.step(action)
        done = terminated or truncated
        
    # Salva o resultado na nova pasta
    log_texto = env_teste.gerar_log_texto()
    caminho_saida = os.path.join(PASTA_RESULTADOS, f"log_rl_{ticker}.txt")
    
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(log_texto)
        
    print(f"Concluído! Log salvo em: {caminho_saida}")

if __name__ == "__main__":
    # Define as regras de quais colunas o robô deve ler
    CONFIG_ESCOLHIDA = ['sentimento_valor', 'var_d1']
    
    # Lista todos os arquivos que geramos no passo anterior
    arquivos_disponiveis = glob.glob("matrizes_rl/*.csv")
    print(f"Iniciando treinamento em lote para {len(arquivos_disponiveis)} ativos...")
    
    for arquivo in arquivos_disponiveis:
        treinar_ticker(arquivo, CONFIG_ESCOLHIDA, total_timesteps=10000)