# Essência do projeto

Este documento descreve o **núcleo** do projeto: o que é coletado, como se descobre se a notícia é positiva/negativa e sobre qual ação, como se verifica se a ação subiu ou caiu, e como a IA aprende com isso (ex.: “se eu tivesse comprado, teria tido lucro?”).

---

## 1. Coleta de dados

**O que é coletado:** cada **notícia** e a **data** em que ela foi publicada.

- **Onde:** Scrapy extrai de portais (Infomoney, Valor Econômico, Exame, Bloomberg).
- **Campos salvos:** título da notícia, URL, **data**, conteúdo (texto), fonte.
- **Arquivo:** `financial_scraper/financial_news.json` (ou MongoDB, se configurado).

Ou seja: a coleta entrega **notícia + data** para cada item.

---

## 2. Sentimento: a notícia é positiva ou negativa?

**O que é feito:** para cada notícia, a IA (FinBERT-PT-BR) classifica o **sentimento** do texto.

- **Saída:** POSITIVO, NEGATIVO ou NEUTRO.
- **Arquivo gerado:** `noticias_com_sentimento.json` (mesmas notícias + campo `sentimento_previsto`).

Assim, temos **notícia + data + sentimento**.

---

## 3. Sobre qual ação (ticker) a notícia se refere?

**O que é feito:** para cada notícia, o sistema identifica **quais ações (tickers)** são citadas.

- **Como:** NER (spaCy) extrai nomes de empresas no texto; um mapa (ex.: “Petrobras” → PETR4) converte para ticker na B3.
- **Arquivo gerado:** `noticias_mapeadas.json` (notícias com sentimento + lista de `tickers_citados` por notícia).

Resultado: para cada notícia sabemos **data**, **sentimento** e **qual(is) ação(ões)** ela se refere.

---

## 4. A ação referida subiu ou caiu?

**O que é feito:** para cada (data, ticker), o sistema verifica o que aconteceu com o **preço** daquela ação depois (no dia seguinte).

- **Fonte de preços:** yfinance (dados de mercado).
- **Cálculo:** retorno no dia seguinte = (preço no dia D+1 − preço no dia D) / preço no dia D.  
  Se retorno > 0 → **subiu**; se < 0 → **caiu**.
- **Uso:** esse “subiu/caiu” é o **alvo** que a IA usa para aprender (ver passo 5).

Ou seja: para cada (data, ticker) temos **sentimento do dia** e **a ação subiu ou caiu no dia seguinte**.

---

## 5. A IA aprende: “se eu tivesse comprado, teria tido lucro?”

**O que é feito:** o sistema monta um **histórico** em que cada linha é algo como:

- **Entrada:** sentimento agregado do dia para aquele ticker (ex.: 2 notícias positivas e 1 negativa → score +1).
- **Saída (alvo):** a ação **subiu (1)** ou **caiu (0)** no dia seguinte.

Com **muitos meses** desses dados, um modelo (ex.: Regressão Logística ou Random Forest) **treina** para prever: “dado o sentimento de hoje, a ação tende a subir ou cair amanhã?”.  
A partir dessa previsão, o sistema decide **compra** (espera subida), **venda** (espera queda) ou **segurar**.

- **Script de treino:** `treinar_modelo_decisao.py` (usa `noticias_mapeadas.json` + preços).
- **Arquivos gerados:** `modelo_decisao.joblib` (modelo treinado), `config_modelo_decisao.json`.
- **Uso na recomendação:** `recomendacao.py` usa esse modelo para decidir compra/venda/segurar quando o arquivo do modelo existir; senão usa uma regra fixa.

Resumo: a IA **aprende com o histórico** “notícia positiva (agregada) → ação subiu” / “notícia negativa → ação caiu” e passa a sugerir compra/venda/segurar com base nisso (incluindo a ideia de “se eu tivesse comprado naquele dia, teria tido lucro?” via o retorno no dia seguinte).

---

## Fluxo em uma frase

**Coleta (notícia + data) → Sentimento (positivo/negativo/neutro) → Qual ação (ticker) → Ver se a ação subiu/caiu no dia seguinte → Treinar a IA nesse histórico → Usar a IA para recomendar compra/venda/segurar.**

Todos os passos acima estão implementados no código; o que depende de você é **acumular dados** (coletar por muitos meses ou usar uma base histórica) para o treino da IA de decisão ser robusto.
