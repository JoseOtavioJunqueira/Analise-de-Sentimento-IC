# Visão do projeto e em que passo estamos

## O que é o projeto (objetivo final)

1. **Scrapy** puxa notícias financeiras e salva.
2. Uma **IA** classifica cada notícia em **positivo**, **negativo** ou **neutro** (análise de sentimento).
3. Com base nisso, o sistema deve dizer:
   - **Se deve investir** (sim/não)
   - **Quando** — em que dia e, se possível, em que hora
   - **Por quanto tempo** — duração da posição (ex.: 1 dia, 1 semana)
   - **Onde** — em qual ativo (ticker/ETF)
   - **Por quê** — qual notícia/qual sentimento motivou a recomendação
   - Tudo **visando lucro** com base nessas notícias.

Resumindo: **notícias → sentimento → recomendação de investimento (quando, onde, por quanto tempo, por quê)**.

---

## Etapas do pipeline

| # | Etapa | O que faz | Status |
|---|--------|-----------|--------|
| **1** | **Coleta de notícias** | Scrapy extrai notícias dos portais (Infomoney, Valor, Exame, Bloomberg) e salva (JSON ou MongoDB). | ✅ **Pronto** |
| **2** | **Classificação de sentimento** | IA (FinBERT-PT-BR) classifica cada notícia em POSITIVO, NEGATIVO ou NEUTRO. | ✅ **Pronto** |
| **3** | **Associar notícias a ativos** | Identifica quais empresas/ETFs são citados em cada notícia (NER + mapa empresa→ticker) e gera `noticias_mapeadas.json`. | ✅ **Pronto** |
| **4** | **Sinais de compra/venda (agregado)** | Agrega sentimento por dia e por ticker; regra simples: comprar se score do dia > limite, vender se < limite. | ✅ **Pronto** (em `criar_estrategia.py`) |
| **5** | **Backtest** | Simula se a estratégia teria dado lucro no passado (retorno %, Sharpe, drawdown). | ✅ **Pronto** (VectorBT em `criar_estrategia.py`) |
| **6** | **Recomendação explícita (quando, onde, por quanto tempo, por quê)** | Saída clara: “Investir em X no dia Y; manter por Z dias; motivo: notícias A, B (positivas)”. Incluir **hora** exige dados intraday. | ⬜ **Falta** |
| **7** | **Horário (que hora)** | Decidir *em que hora* do dia operar. Hoje só temos dados **diários** (dia da notícia); hora exata exige dados intraday ou regra (ex.: abertura/fechamento). | ⬜ **Falta** |
| **8** | **Explicação (“por quê”)** | Para cada recomendação, listar as notícias e sentimentos que justificam (ex.: “PETR4: 2 notícias positivas, 1 neutra”). | ⬜ **Parcial** (dados existem; falta formatar como “recomendação + motivo”) |

---

## Em que passo estamos

- **Já está feito:**  
  Coleta (1) → Sentimento (2) → Mapeamento notícia→ticker (3) → Geração de sinais agregados por dia (4) → Backtest (5).  
  Ou seja: **notícias puxadas, classificadas, ligadas a ativos, e uma estratégia diária já simulada.**

- **O que falta para o objetivo que você descreveu:**  
  - **Recomendação explícita:** um módulo/API que, dado o estado atual (notícias + sentimentos + mapeamento), **responda de forma clara**:  
    - Investir ou não  
    - Em **qual ativo** (onde)  
    - Em **qual dia** (e, se possível, **que hora** — quando tiver dados ou regra)  
    - **Por quanto tempo** (ex.: 1 dia para day trade, ou N dias)  
    - **Por quê** (quais notícias/sentimentos motivaram)  
  - **Horário (que hora):** hoje o sistema é **diário**. Para “que hora” é preciso ou ter dados intraday, ou definir uma regra (ex.: “sempre considerar abertura do pregão às 10h”).  
  - **Duração (“por quanto tempo”):** hoje a lógica é day trade (entra/sai no mesmo dia ou próximo). Formalizar “manter por X dias” e expor na recomendação.

---

## Resumo visual

```
[Scrapy] → notícias salvas          ✅ Passo 1
    ↓
[FinBERT] → positivo/negativo/neutro ✅ Passo 2
    ↓
[Associar tickers] → notícia → PETR4, VALE3…  ✅ Passo 3
    ↓
[Agregar por dia + regra] → comprar/vender    ✅ Passo 4
    ↓
[Backtest] → retorno, Sharpe, drawdown        ✅ Passo 5
    ↓
[Recomendação clara: quando, onde, por quanto tempo, por quê]  ✅ Passo 6 (recomendacao.py + Streamlit)
    ↓
[Que hora do dia]                             ⬜ Passo 7 (opcional: regra ou intraday)
```

---

## Próximos passos sugeridos (para alcançar o objetivo)

1. **Criar um módulo/script de “recomendação”** que:
   - Leia `noticias_mapeadas.json` (ou o resultado do backtest/sinais).
   - Para “hoje” (ou última data disponível), gere uma saída estruturada, por exemplo:
     - **Investir?** Sim/Não (e em quais tickers).
     - **Onde?** Lista de tickers (ex.: PETR4, VALE3).
     - **Quando?** Data (e, se houver regra, hora).
     - **Por quanto tempo?** Ex.: “1 dia (day trade)” ou “N dias”.
     - **Por quê?** Lista das notícias + sentimento que motivaram (título, link, POS/NEG/NEUTRO).
2. **Definir regra para “que hora”:**  
   - Opção A: usar apenas dia (como hoje) e documentar “recomendação para o dia”.  
   - Opção B: definir uma hora fixa (ex.: abertura 10h) ou integrar dados intraday depois.
3. **Expor isso como API ou relatório diário** (JSON/HTML/endpoint), para você ou um front consumir.

Assim, o projeto fica com o fluxo completo: **Scrapy puxa notícias → IA diz positivo/negativo/neutro → sistema diz se deve investir, quando, onde, por quanto tempo e por quê, visando lucro.**
