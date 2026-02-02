# Dados de muitos meses e “treinar a IA” — como isso se encaixa

Seu professor disse que você **precisa coletar dados de muitos meses para treinar a IA**. Isso faz sentido, mas depende do que se entende por “treinar”. Este documento deixa claro como está o projeto hoje e o que falta, se for o caso.

---

## 1. O que o projeto faz hoje com a “IA”

Hoje a **IA de sentimento** é o **FinBERT-PT-BR** (Santos 2022): um modelo **já treinado** em textos financeiros em português. No código nós **não treinamos** esse modelo — só **usamos** ele para **classificar** (inferência):

- Entrada: texto da notícia  
- Saída: POSITIVO, NEGATIVO ou NEUTRO  

Ou seja: **não há etapa de “treinar a IA” no pipeline atual.** O modelo já veio treinado; a gente só aplica nas notícias que o Scrapy coleta.

Por isso, **para a etapa de sentimento em si**, não é obrigatório “coletar muitos meses para treinar”: o modelo já está pronto. O que a gente precisa é **ter notícias** (de muitos meses ou da base do Santos) para **rodar o backtest e as recomendações** com histórico — isso sim exige bastante dado.

---

## 2. Quando “coletar dados de muitos meses” é necessário

Faz sentido em dois casos:

### A) Ter histórico para backtest e recomendações (o que o projeto já está preparado para usar)

Para o **backtest** e as **recomendações** serem confiáveis, você precisa de **muito histórico**: muitas notícias ao longo do tempo (muitos meses/anos).  
Esse histórico pode vir de:

1. **Base do Santos (2022)**  
   A proposta cita a base com notícias de **2006 a 2022**. Se você tiver acesso a ela, já são muitos anos de dados para rodar backtest e estratégia.

2. **Rodar o Scrapy por muitos meses**  
   Deixar o sistema coletando notícias (por exemplo, todo dia com `main.py`). Com o tempo você acumula “muitos meses” de dados e aí consegue:
   - classificar tudo com o FinBERT (sem treinar),
   - rodar backtest e recomendações em cima desse histórico.

Ou seja: **“coletar dados de muitos meses”** aqui significa **acumular dados para o sistema usar**, não necessariamente para “treinar” a IA de sentimento. O projeto já está pronto para **usar** esses dados quando você tiver (via base Santos ou meses de coleta).

### B) Treinar ou fine-tunar um modelo (o que o projeto ainda não faz)

Se o professor quis dizer que você **vai treinar (ou fine-tunar) uma IA** com dados que vocês mesmos coletarem, aí sim entra:

- Coletar notícias por **muitos meses**
- Ter (ou criar) **rótulos** (positivo/negativo/neutro) para essas notícias
- **Treinar** ou **fine-tunar** um modelo nesses dados

Isso **não está implementado** no projeto atual. O que existe é:

- Usar o **FinBERT-PT-BR já treinado** para classificar as notícias que você for coletando.

Se a orientação for **obrigatoriamente** treinar/fine-tunar um modelo, aí sim falta uma **fase extra** no projeto:

1. Coletar dados (Scrapy) por muitos meses (e/ou usar base Santos).  
2. Rotular uma parte (ou usar rótulos existentes).  
3. Implementar um script de **treino/fine-tuning** (ex.: em cima do FinBERT) e rodar experimentos.  
4. Usar esse modelo treinado no lugar do FinBERT “de prateleira” no pipeline.

---

## 3. Resumo para falar com o professor

- **“Preciso coletar dados de muitos meses?”**  
  - Para **treinar/fine-tunar uma IA**: sim, e aí ainda falta implementar a parte de treino no projeto.  
  - Para **ter backtest e recomendações com histórico**: sim, você precisa de muitos meses de dados (base Santos ou meses de Scrapy); o projeto já está pronto para **usar** esses dados.

- **“A IA está treinada?”**  
  - A IA de sentimento (FinBERT-PT-BR) que usamos **já veio treinada** (Santos 2022). No código atual a gente **não treina** esse modelo, só o **utiliza** para classificar notícias.

- **“O projeto está pronto então?”**  
  - **Pronto** no sentido de: pipeline completo (coleta → sentimento → recomendação → backtest → interface), usando um modelo **pré-treinado**.  
  - **Não está pronto** no sentido de: “treinar uma IA com dados de muitos meses” — isso seria uma **etapa adicional** (coleta + rotulação + script de treino/fine-tuning), se o professor exigir isso.

Se quiser, no próximo passo podemos esboçar **como** seria esse script de treino/fine-tuning (e onde encaixar “coletar dados de muitos meses” exatamente) para você alinhar com o professor.
