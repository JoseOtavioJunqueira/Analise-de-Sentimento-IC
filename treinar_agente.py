"""para rodar deve-se executar 
    pip install stable-baselines3 gymnasium
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from stable_baselines3 import PPO

# ==========================================
# 1. O MOTOR (O Ambiente de Simulação)
# ==========================================
class ICGymTradingEnv(gym.Env):
    """
    Ambiente de Trading Modular.
    O espaço de observação adapta-se à lista de features fornecida.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, df_dados, features):
        super(ICGymTradingEnv, self).__init__()
        
        self.df = df_dados.reset_index(drop=True)
        self.features = features
        self.max_steps = len(self.df) - 1
        
        # AÇÕES: 0 = Manter, 1 = Comprar, 2 = Vender
        self.action_space = spaces.Discrete(3)
        
        # OBSERVAÇÃO: Tamanho dinâmico
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(len(self.features),), 
            dtype=np.float32
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
        obs = linha_atual[self.features].values.astype(np.float32)
        return obs

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
            else:
                movimentacao_texto = f"[{data_atual}] MANTER (Já estava comprado)"

        elif action == 2: # VENDER
            if self.position == 1:
                lucro_trade = (preco_atual - self.entry_price) / self.entry_price
                reward = lucro_trade 
                self.lucro_acumulado += lucro_trade
                
                status = "LUCRO" if lucro_trade > 0 else "PREJUÍZO"
                movimentacao_texto = f"[{data_atual}] VENDA  : R$ {preco_atual:.2f} | {status}: {(lucro_trade*100):.2f}%"
                
                self.position = 0 
                self.entry_price = 0.0
            else:
                movimentacao_texto = f"[{data_atual}] MANTER (Sem ações para vender)"

        elif action == 0: # MANTER
            estado = "Comprado" if self.position == 1 else "Líquido"
            movimentacao_texto = f"[{data_atual}] MANTER ({estado})"

        self.historico_movimentacoes.append(movimentacao_texto)

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        obs = self._get_obs() if not terminated else np.zeros(len(self.features), dtype=np.float32)
        info = {"lucro_acumulado": self.lucro_acumulado}

        return obs, reward, terminated, truncated, info

    def render(self):
        print("\n" + "="*50)
        print(" RELATÓRIO DE MOVIMENTAÇÕES (BACKTEST RL)")
        print("="*50)
        for mov in self.historico_movimentacoes:
            if "COMPRA" in mov or "VENDA" in mov: 
                print(mov)
        print("="*50)
        print(f" LUCRO TOTAL ACUMULADO NO PERÍODO: {(self.lucro_acumulado * 100):.2f}%")
        print("="*50 + "\n")


# ==========================================
# 2. O VOLANTE (Treino e Teste com Datas)
# ==========================================
def rodar_experimento(caminho_csv, configuracao_features, total_timesteps=10000, 
                      data_inicio=None, data_fim=None, data_corte_treino=None):
    """
    Instancia o ambiente, treina no passado (Treino) e simula o resultado no futuro (Teste).
    """
    print(f"\n" + "="*50)
    print(f" INICIANDO EXPERIMENTO ")
    print(f" Features: {configuracao_features}")
    print("="*50)
    
    # Carrega e prepara os dados
    df = pd.read_csv(caminho_csv)
    df['data'] = pd.to_datetime(df['data'])
    
    # Filtro global de datas (opcional)
    if data_inicio:
        df = df[df['data'] >= pd.to_datetime(data_inicio)]
    if data_fim:
        df = df[df['data'] <= pd.to_datetime(data_fim)]
        
    df = df.sort_values('data').reset_index(drop=True)
    
    # Separação Treino e Teste (Time-Series Split)
    if data_corte_treino:
        data_corte = pd.to_datetime(data_corte_treino)
        df_treino = df[df['data'] <= data_corte].reset_index(drop=True)
        df_teste = df[df['data'] > data_corte].reset_index(drop=True)
    else:
        # Divide automaticamente 80% Treino / 20% Teste
        corte_idx = int(len(df) * 0.8)
        df_treino = df.iloc[:corte_idx].reset_index(drop=True)
        df_teste = df.iloc[corte_idx:].reset_index(drop=True)

    print(f"-> Base de TREINO: {len(df_treino)} eventos (De {df_treino['data'].min().date()} a {df_treino['data'].max().date()})")
    print(f"-> Base de TESTE : {len(df_teste)} eventos (De {df_teste['data'].min().date()} a {df_teste['data'].max().date()})")
    print("-" * 50)
    
    # Fase de Treinamento
    print("Fase 1: A treinar o agente na base histórica...")
    env_treino = ICGymTradingEnv(df_treino, features=configuracao_features)
    modelo = PPO("MlpPolicy", env_treino, verbose=0, learning_rate=0.0005)
    modelo.learn(total_timesteps=total_timesteps)
    
    # Fase de Validação/Backtest
    print("Fase 2: Simulação na base de teste (dados desconhecidos)...")
    env_teste = ICGymTradingEnv(df_teste, features=configuracao_features)
    obs, info = env_teste.reset()
    done = False
    
    while not done:
        action, _states = modelo.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env_teste.step(action)
        done = terminated or truncated
        
    # Exibe o log formatado SOMENTE para o período de teste
    env_teste.render()


# ==========================================
# 3. O PAINEL DE CONTROLO
# ==========================================
if __name__ == "__main__":
    
    ARQUIVO_DADOS = "dataset_rl_mestra_PETR4.csv" 
    
    config_1 = ['sentimento_valor', 'var_d1']
    config_2 = ['sentimento_valor', 'var_acumulada_3d']
    config_3 = ['sentimento_valor', 'var_d1', 'var_d2', 'var_d3', 'var_d4', 'var_d5']
    
    # EXEMPLO 1: A usar todas as notícias e deixar o script dividir sozinho (80/20)
    rodar_experimento(
        caminho_csv=ARQUIVO_DADOS, 
        configuracao_features=config_1, 
        total_timesteps=20000
    )
    
    # EXEMPLO 2: A definir datas exatas de início, fim e corte (Descomente para usar)
    """
    rodar_experimento(
        caminho_csv=ARQUIVO_DADOS, 
        configuracao_features=config_3, 
        total_timesteps=30000,
        data_inicio="2022-01-01",        
        data_fim="2024-12-31",           
        data_corte_treino="2024-01-01"   
    )
    """