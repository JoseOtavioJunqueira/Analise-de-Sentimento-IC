# Como rodar no lab e próximos passos (tudo mastigado)

Este documento explica **como deixar o projeto rodando no lab** e **quando fazer cada coisa**, passo a passo.

---

## Parte 1: Preparar a máquina do lab (uma vez)

### 1.1 Clonar o repositório e criar o ambiente

No PC do lab (Windows ou Linux):

```bash
cd C:\...\   # ou o caminho onde você quer o projeto (ex.: D:\IC\)
git clone https://github.com/SEU_USUARIO/Analise-de-Sentimento-IC.git
cd Analise-de-Sentimento-IC
```

Criar ambiente virtual e instalar dependências:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

(Opcional) Para associar notícias a tickers (NER em português):

```bash
pip install spacy
python -m spacy download pt_core_news_lg
```

### 1.2 Testar se tudo funciona

Na **raiz** do projeto (pasta onde está `main.py`):

```bash
python main.py
```

Isso vai: rodar os spiders (coleta), depois analisar sentimento (FinBERT). Se der erro, confira [docs/INSTALACAO.md](INSTALACAO.md).

---

## Parte 2: Deixar rodando no lab

### 2.1 O que deve rodar sozinho (coleta + análise)

A ideia é **agendar** a execução de `main.py` para rodar **todo dia** (ex.: às 8h), assim o sistema acumula notícias + datas + sentimentos sem você precisar ligar o PC manualmente.

**Windows (Agendador de Tarefas):**

1. Abra o **Agendador de Tarefas** (Task Scheduler).
2. Criar Tarefa Básica (ou Nova Tarefa).
3. **Gatilho:** Diariamente, às 8:00 (ou o horário que quiser).
4. **Ação:** Iniciar um programa.
   - **Programa/script:** caminho do `python.exe` do venv (ex.: `D:\IC\Analise-de-Sentimento-IC\venv\Scripts\python.exe`).
   - **Argumentos:** `main.py`
   - **Iniciar em:** a pasta do projeto (ex.: `D:\IC\Analise-de-Sentimento-IC`).
5. Salvar. A partir daí, todo dia o sistema vai rodar coleta + análise.

**Linux (cron):**

```bash
crontab -e
```

Adicione uma linha (ex.: todo dia às 8h):

```
0 8 * * * cd /caminho/para/Analise-de-Sentimento-IC && /caminho/para/venv/bin/python main.py
```

(Substitua os caminhos pelos reais.)

### 2.2 Interface para acompanhar (Streamlit)

Para **ver** os dados, recomendações e backtest de outro PC (ou no próprio lab), deixe o Streamlit rodando na máquina do lab:

```bash
cd C:\...\Analise-de-Sentimento-IC   # raiz do projeto
venv\Scripts\activate
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
```

- **No próprio lab:** abra no navegador: `http://localhost:8501`
- **De outro PC na mesma rede:** abra `http://IP_DA_MAQUINA_DO_LAB:8501` (substitua pelo IP da máquina do lab).

Para **manter rodando em segundo plano** (Linux):

```bash
nohup streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501 > streamlit.log 2>&1 &
```

No Windows, você pode deixar uma janela do terminal aberta com o comando acima ou usar um script que inicia o Streamlit ao logar (ex.: atalho na pasta Inicializar).

---

## Parte 3: Quando fazer o quê (próximos passos mastigados)

### Fase 1: Acumular dados (primeiras semanas/meses)

**O que fazer:** só deixar a **coleta + análise** rodando (agendamento do `main.py`).

**Quando:** desde o primeiro dia. Quanto mais tempo rodar, mais notícias + datas + sentimentos você terá.

**O que você NÃO precisa fazer ainda:**  
- Não precisa rodar `associar_tickers.py` todo dia no início, a menos que queira já ir gerando notícias mapeadas.  
- Não precisa treinar o modelo de decisão até ter **muitos meses** de dados (ou uma base histórica).

**Resumo:**  
- **Semana 1–4 (ou mais):** apenas garantir que `main.py` está agendado e que `noticias_com_sentimento.json` está crescendo.

---

### Fase 2: Associar notícias às ações (tickers)

**O que fazer:** rodar `associar_tickers.py` para que cada notícia ganhe a lista de **quais ações (tickers)** ela se refere.

**Quando:** quando você tiver **um volume razoável** de notícias com sentimento (ex.: centenas ou milhares de linhas em `noticias_com_sentimento.json`). Pode rodar uma vez por semana ou quando quiser atualizar o mapeamento.

**Como:**

```bash
cd C:\...\Analise-de-Sentimento-IC
venv\Scripts\activate
python associar_tickers.py
```

**Arquivo gerado:** `noticias_mapeadas.json`.  
**Dependência:** o arquivo `mapeamento_tickers.json` (nome da empresa → ticker) precisa existir e estar preenchido; senão, muitas notícias não serão mapeadas.

**Resumo:**  
- **Quando:** depois de ter um bom volume de notícias com sentimento.  
- **Frequência:** por exemplo 1x por semana ou após cada rodada grande de coleta.

---

### Fase 3: Treinar a IA de decisão (compra/venda/segurar)

**O que fazer:** rodar `treinar_modelo_decisao.py` para a IA **aprender** com o histórico: “notícia positiva (agregada) → ação subiu”, “notícia negativa → ação caiu”, etc.

**Quando:** quando você tiver **muitos meses** de dados em `noticias_mapeadas.json` (e preços correspondentes no yfinance). Quanto mais histórico, melhor o treino. Ex.: 3–6 meses ou mais.

**Como:**

```bash
python treinar_modelo_decisao.py
```

**Arquivos gerados:** `modelo_decisao.joblib`, `config_modelo_decisao.json`.  
A partir daí, `recomendacao.py` passa a usar esse modelo para decidir compra/venda/segurar (em vez da regra fixa).

**Resumo:**  
- **Quando:** só depois de acumular **muitos meses** de notícias mapeadas (e ter preços para esses tickers/datas).  
- **Frequência:** pode repetir de tempos em tempos (ex.: mensal) para “retreinar” com dados novos.

---

### Fase 4: Recomendações e backtest

**Recomendações:**  
- Se você **não** treinou o modelo ainda: o sistema usa a **regra fixa** (score > 1 → compra, score < -1 → venda).  
- Se você **já** treinou: o sistema usa o **modelo treinado** (IA que aprendeu com o histórico).

**Quando:**  
- Recomendações: sempre que rodar `main.py` (ou `recomendacao.py`) depois de ter `noticias_mapeadas.json`.  
- Backtest: quando quiser **ver** se a estratégia teria dado lucro no passado. Rode quando tiver dados suficientes (meses de notícias mapeadas + preços).

**Como (backtest):**

```bash
python criar_estrategia.py
```

**Arquivos gerados:** `resultados_backtest_v1.html`, `ultimo_backtest.json`. A interface Streamlit mostra essas métricas.

**Resumo:**  
- **Recomendações:** automáticas após cada `main.py` (se houver notícias mapeadas).  
- **Backtest:** quando quiser avaliar lucro passado; pode rodar 1x por mês ou após retreinar o modelo.

---

## Parte 4: Ordem resumida (linha do tempo)

| Quando | O que fazer |
|--------|-------------|
| **Dia 1** | Instalar projeto, criar venv, instalar `requirements.txt`, testar `python main.py`. |
| **Dia 1** | Configurar agendamento (Task Scheduler ou cron) para `main.py` rodar todo dia (ex.: 8h). |
| **Dia 1 (opcional)** | Subir a interface: `streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501`. |
| **Semana 1–4+** | Deixar só a coleta rodando; conferir na interface se `noticias_com_sentimento.json` está crescendo. |
| **Quando tiver volume de notícias** | Rodar `associar_tickers.py` (1x por semana ou quando quiser). Verificar `noticias_mapeadas.json`. |
| **Depois de muitos meses de dados** | Rodar `treinar_modelo_decisao.py` uma vez (e repetir de tempos em tempos). |
| **A partir daí** | Recomendações passam a usar a IA treinada; backtest com `criar_estrategia.py` quando quiser ver lucro passado. |

---

## Parte 5: Onde está cada coisa no código

| O que | Onde |
|-------|------|
| Coleta (notícia + data) | Scrapy: `financial_scraper/`, spiders em `financial_scraper/financial_scraper/spiders/`. |
| Sentimento (positivo/negativo/neutro) | `analisar_noticias.py` (FinBERT-PT-BR). |
| Qual ação (ticker) | `associar_tickers.py` (NER + `mapeamento_tickers.json`). |
| Ver se ação subiu/caiu + treinar IA | `treinar_modelo_decisao.py` (usa preços yfinance + noticias_mapeadas). |
| Recomendações (compra/venda/segurar) | `recomendacao.py` (usa modelo treinado ou regra fixa). |
| Backtest (lucro passado) | `criar_estrategia.py`. |
| Interface (ver tudo) | `app_streamlit.py` (Streamlit). |
| Orquestração (coleta + análise + recomendação) | `main.py`. |

---

## Parte 6: Problemas comuns

- **“Não tenho notícias mapeadas”**  
  Rode `associar_tickers.py` e confira se `mapeamento_tickers.json` existe e tem empresas que aparecem nas notícias.

- **“Modelo de decisão não encontrado”**  
  É esperado até você rodar `treinar_modelo_decisao.py` com bastante histórico. Até lá, o sistema usa a regra fixa.

- **“Poucos dados para treino”**  
  O treino precisa de muitos (data, ticker) com sentimento + preço. Deixe a coleta rodar por vários meses e tente de novo.

- **Streamlit não abre de outro PC**  
  Use `--server.address 0.0.0.0` e confira firewall (porta 8501 liberada). Acesse com `http://IP_DA_MAQUINA:8501`.

Se algo falhar, consulte [INSTALACAO.md](INSTALACAO.md) e [ARCHITETURA.md](ARCHITETURA.md).
