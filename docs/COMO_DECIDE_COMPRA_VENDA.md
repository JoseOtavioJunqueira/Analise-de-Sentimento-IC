# Como o sistema decide compra / venda / segurar?

Você perguntou: a IA que sugere compra/venda/hold deveria ter um **histórico** do tipo “notícia positiva → ação subiu”, “notícia negativa → ação caiu”, etc. **Como ela decide hoje?**

---

## 1. Como decide **hoje** (regra fixa, sem aprender com o passado)

Hoje a decisão **não** usa nenhum histórico “notícia → movimento do preço”. É uma **regra fixa** no código:

1. Para cada **dia** e cada **ticker**, somamos o sentimento das notícias daquele dia:
   - Notícia **positiva** → +1  
   - Notícia **negativa** → -1  
   - Notícia **neutra** → 0  
   - **Score do dia** = soma desses valores (ex.: 2 positivas e 1 negativa → score +1).

2. A decisão é **só em cima desse score**:
   - **Score > 1** → **compra**
   - **Score < -1** → **venda**
   - Entre -1 e 1 → **segurar**

Ou seja: **não há nenhum “aprendizado”** do tipo “no passado, quando o sentimento foi positivo, a ação subiu”. A “IA” que classifica a notícia (positivo/negativo/neutro) é o FinBERT; já a **decisão** compra/venda/segurar é só essa regra numérica fixa.

---

## 2. O que você descreveu (e que faz sentido)

O que você descreveu é um sistema que **aprende com o histórico**:

- **Histórico:** em muitos dias no passado, para cada dia/ticker: “sentimento agregado naquele dia” e “o que aconteceu com o preço depois” (subiu, caiu, ficou estável).
- **Aprendizado:** um modelo que usa esse histórico para aprender padrões do tipo:
  - “Quando o sentimento foi muito positivo, a ação tendeu a subir no dia seguinte.”
  - “Quando foi muito negativo, tendeu a cair.”
- **Decisão:** com base nesse modelo aprendido, **hoje** o sistema decide compra/venda/hold usando o sentimento atual e o que o histórico “ensinou”.

Isso **não está implementado** no projeto atual. O que existe é só a regra fixa acima.

---

## 3. O que foi adicionado no projeto (aprender com histórico)

Foi implementado um fluxo que **aprende** com esse histórico:

1. **Montar o histórico:** para cada (data, ticker):
   - **Entrada:** sentimento agregado do dia (soma de +1/-1/0 das notícias).
   - **Saída (alvo):** retorno no **dia seguinte** (preço amanhã vs hoje). Convertido em “subiu (1)” ou “caiu (0)” para treinar um classificador.

2. **Treinar um modelo:** o script **`treinar_modelo_decisao.py`** usa muitos (data, ticker) nesse formato e treina um modelo (Regressão Logística ou Random Forest) que **prevê** “o preço tende a subir ou cair no dia seguinte?” a partir do sentimento do dia. O modelo e o scaler são salvos em `modelo_decisao.joblib` e a config em `config_modelo_decisao.json`.

3. **Decisão:** o **`recomendacao.py`** verifica se existe `modelo_decisao.joblib`. Se existir, usa o modelo para decidir compra/venda/segurar (ex.: probabilidade de subir > 0,6 → compra; < 0,4 → venda; entre 0,4 e 0,6 → segurar). Se não existir, continua com a **regra fixa** (score > 1 → compra, score < -1 → venda).

**Como usar:** depois de ter **muitos meses** de dados (notícias mapeadas + preços), rode uma vez:
```bash
python treinar_modelo_decisao.py
```
A partir daí, as recomendações passam a usar o modelo treinado (histórico “notícia positiva → ação subiu”, etc.) em vez da regra fixa.

Resumo:
- **Regra fixa (sem modelo):** score > 1 → compra, score < -1 → venda, senão segurar. Não usa histórico de preço.
- **Com modelo treinado:** decisão baseada no que o modelo aprendeu com o histórico (sentimento do dia → retorno no dia seguinte). Exige **dados de muitos meses** para treinar (`treinar_modelo_decisao.py`).
