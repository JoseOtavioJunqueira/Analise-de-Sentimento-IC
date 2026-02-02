# Atualizações do projeto — para Luísa e Prof. Denis

Texto resumido das **novidades do código** e do **estado atual do projeto**, para compartilhar com a Luísa e o orientador Denis.

---

## Resumo em uma frase

O projeto agora tem **todo o fluxo da essência** implementado: coleta (notícia + data), sentimento (positivo/negativo/neutro), identificação da ação (ticker), verificação se a ação subiu ou caiu no dia seguinte, **treino de uma IA** que aprende com esse histórico para decidir compra/venda/segurar, interface online para acompanhar tudo, e documentação de como rodar no lab e quando fazer cada passo.

---

## O que há de novo no código

### 1. Essência do projeto (fluxo completo)

- **Coleta:** Scrapy continua coletando **notícia + data** (título, URL, data, conteúdo, fonte). Nada mudou na estrutura; só está documentado de forma explícita.
- **Sentimento:** FinBERT-PT-BR continua classificando cada notícia em **positivo, negativo ou neutro**. Saída em `noticias_com_sentimento.json`.
- **Qual ação:** O script `associar_tickers.py` identifica **sobre qual(is) ação(ões)** cada notícia se refere (NER + mapa empresa → ticker). Saída em `noticias_mapeadas.json`.
- **Subiu ou caiu:** O sistema agora usa os **preços** (yfinance) para calcular, para cada (data, ticker), se a ação **subiu ou caiu no dia seguinte**. Isso vira o “alvo” para a IA aprender.
- **IA que aprende:** Foi implementado o **treino de um modelo de decisão** que aprende com o histórico “sentimento do dia → retorno no dia seguinte” (ex.: notícia positiva agregada → ação subiu). Esse modelo decide **compra / venda / segurar** em vez de uma regra fixa.
  - **Script novo:** `treinar_modelo_decisao.py` — monta o histórico (sentimento + retorno), treina um classificador (Regressão Logística ou Random Forest) e salva o modelo (`modelo_decisao.joblib`).
  - **Integração:** O `recomendacao.py` passou a usar esse modelo quando ele existir; caso contrário, continua com a regra fixa (score > 1 → compra, score < -1 → venda).

### 2. Interface e uso no lab

- **Interface Streamlit:** O arquivo `app_streamlit.py` oferece uma **interface web** que mostra: status da última execução, dados coletados, recomendações atuais (investir? onde? quando? por quê?), métricas do backtest (lucro, Sharpe, drawdown) e execução dos testes (pytest). Pode ser acessada de outro PC na rede (`--server.address 0.0.0.0`).
- **Como rodar no lab:** Foi criado o documento **`docs/COMO_RODAR_NO_LAB_E_PROXIMOS_PASSOS.md`**, que explica:
  - como preparar a máquina (clone, venv, dependências),
  - como **agendar** a execução diária de `main.py` (Task Scheduler no Windows ou cron no Linux),
  - como subir a interface Streamlit e acessá-la de outro PC,
  - **quando fazer o quê** (acumular dados → associar tickers → treinar o modelo → recomendações e backtest), tudo mastigado.

### 3. Documentação nova

- **`docs/ESSENCIA_DO_PROJETO.md`:** Descreve a essência do projeto: coleta (notícia + data), sentimento, qual ação, ver se a ação subiu/caiu, e como a IA aprende (“se eu tivesse comprado, teria tido lucro?”).
- **`docs/COMO_DECIDE_COMPRA_VENDA.md`:** Explica como o sistema decide compra/venda/segurar: regra fixa vs modelo treinado com histórico.
- **`docs/COMO_RODAR_NO_LAB_E_PROXIMOS_PASSOS.md`:** Guia completo para rodar no lab e próximos passos (quando fazer cada coisa).
- **`docs/DADOS_E_TREINAMENTO.md`:** Esclarece a diferença entre “usar modelo pré-treinado” (FinBERT) e “treinar a IA” (modelo de decisão compra/venda/segurar) e por que o professor falou em “coletar dados de muitos meses”.

### 4. Outros ajustes

- **Config centralizado:** Caminhos e constantes em `config.py` (incluindo caminho do modelo de decisão).
- **Status e recomendações:** `main.py` atualiza `status.json` (última coleta, última análise, última recomendação) e chama a geração de recomendação após a análise quando existir `noticias_mapeadas.json`.
- **Backtest em JSON:** `criar_estrategia.py` salva métricas em `ultimo_backtest.json` para a interface exibir lucro, Sharpe, drawdown, etc.

---

## O que precisamos fazer daqui pra frente (próximos passos)

1. **Acumular dados:** Deixar a coleta + análise rodando no lab (agendamento diário) por **muitos meses** (ou usar base histórica, ex.: Santos 2022, se disponível).
2. **Associar tickers:** Rodar `associar_tickers.py` com certa periodicidade (ex.: 1x por semana) e manter o `mapeamento_tickers.json` atualizado.
3. **Treinar o modelo de decisão:** Quando houver histórico suficiente (muitos meses de notícias mapeadas + preços), rodar `treinar_modelo_decisao.py`; a partir daí as recomendações passam a usar a IA treinada.
4. **Relatório e divulgação:** Conforme cronograma da proposta (relatório final, vídeo, etc.).

Tudo isso está detalhado em **`docs/COMO_RODAR_NO_LAB_E_PROXIMOS_PASSOS.md`**.

---

## Onde está cada coisa no repositório

- **Essência do projeto:** `docs/ESSENCIA_DO_PROJETO.md`
- **Como rodar no lab e quando fazer o quê:** `docs/COMO_RODAR_NO_LAB_E_PROXIMOS_PASSOS.md`
- **Como a IA decide compra/venda/segurar:** `docs/COMO_DECIDE_COMPRA_VENDA.md`
- **Dados e treinamento (muitos meses):** `docs/DADOS_E_TREINAMENTO.md`
- **Interface:** executar `streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501` na raiz do projeto.

Se quiserem, podemos marcar uma reunião rápida para mostrar a interface e o fluxo no código.

---

*Documento preparado para alinhamento com Luísa e Prof. Denis — projeto de IC, ICMC/USP, 2025.*
