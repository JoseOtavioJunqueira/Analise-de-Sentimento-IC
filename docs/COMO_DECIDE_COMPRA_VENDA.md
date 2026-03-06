# Como o sistema decide compra / venda / segurar?

O sistema **não usa regra fixa**. A decisão é sempre por **IA**: modelo treinado (Random Forest ou Regressão Logística) ou agente de **Aprendizado por Reforço (Q-Learning)**.

---

## 1. Entrada: score de sentimento do dia

Para cada **dia** e cada **ticker**, o sistema agrega o sentimento das notícias daquele dia:

- Notícia **positiva** → +1  
- Notícia **negativa** → -1  
- Notícia **neutra** → 0  
- **Score do dia** = soma (ex.: 2 positivas e 1 negativa → score +1).

Esse score é a **entrada** para a IA (modelo ou RL).

---

## 2. Opção A: Modelo treinado (Random Forest ou Regressão Logística)

- **Histórico:** para cada (data, ticker): sentimento agregado do dia e **retorno no dia seguinte** (preço amanhã vs hoje) → “subiu (1)” ou “caiu (0)”.
- **Treino:** `treinar_modelo_decisao.py` treina um **Random Forest** (padrão) ou Regressão Logística nesse histórico e salva em `modelo_decisao.joblib`.
- **Decisão:** dado o score de hoje, o modelo devolve a probabilidade de “subir”.  
  - Prob(subir) ≥ 0,6 → **compra**  
  - Prob(subir) ≤ 0,4 → **venda**  
  - Entre 0,4 e 0,6 → **segurar**

**Como usar:** com dados suficientes (notícias mapeadas + preços), rode:
```bash
python treinar_modelo_decisao.py
```
O padrão é **Random Forest**; para Regressão Logística, altere `MODELO_TIPO` em `treinar_modelo_decisao.py`.

---

## 3. Opção B: Agente RL (Q-Learning)

- **Estado:** score de sentimento **discretizado** em buckets.
- **Ações:** 0 = segurar, 1 = compra, 2 = venda.
- **Recompensa:** retorno do dia seguinte (comprou e subiu = ganho; vendeu e caiu = ganho; etc.).
- **Treino:** `rl_agente.py` treina um agente **Q-Learning** no histórico (sentimento → retorno) e salva a política em `politica_rl_qlearning.json`.
- **Decisão:** dado o score de hoje, o agente escolhe a ação com maior valor Q(estado, ação).

**Como usar:**
```bash
python rl_agente.py
```

---

## 4. Ordem de uso na recomendação

1. Se existir **política RL** e `PREFERIR_RL = True` em `recomendacao.py` → usa **Q-Learning**.
2. Senão, se existir **modelo treinado** (`modelo_decisao.joblib`) → usa **Random Forest** (ou Logistic).
3. Se não houver nenhum dos dois, o sistema **tenta treinar** (primeiro o modelo, depois o RL) com os dados disponíveis.
4. Se ainda assim não houver modelo nem RL → todas as recomendações ficam em **segurar** e é exibida mensagem para rodar `treinar_modelo_decisao.py` e/ou `rl_agente.py`.

**Não há regra fixa** (ex.: “score > 1 → compra”). A decisão é sempre baseada em IA (modelo ou RL).

---

## 5. Backtest

O script `criar_estrategia.py` (backtest) também usa **modelo ou RL** quando existirem para gerar os sinais de entrada/saída. Se não houver modelo nem RL, usa limiares apenas como **fallback** para o backtest rodar (a recomendação em si nunca usa esse fallback).
