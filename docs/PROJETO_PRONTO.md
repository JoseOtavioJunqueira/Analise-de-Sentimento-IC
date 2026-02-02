# O projeto está pronto?

## Resposta curta

**O pipeline está pronto.** O fluxo está completo: coleta → sentimento → mapeamento → recomendação → backtest → interface online. O que **não** está pronto (ou depende de você) é:

1. **Ter muitos meses de dados** — para o backtest e as recomendações serem confiáveis, você precisa de histórico (base Santos 2022 ou rodar o Scrapy por muitos meses). O código já usa esses dados quando existirem.
2. **“Treinar a IA”** — hoje usamos o **FinBERT-PT-BR já treinado** (Santos 2022); não há etapa de treino no código. Se o professor exigir que você **treine** ou **fine-tune** um modelo com dados coletados, isso seria uma fase extra (veja [DADOS_E_TREINAMENTO.md](DADOS_E_TREINAMENTO.md)).

Ou seja: **pronto** = pipeline completo e funcionando; **dados de muitos meses** = você acumula rodando o Scrapy (ou usando a base Santos); **treinar a IA** = só se o professor pedir, e aí entra outra etapa no projeto.

---

## O que está pronto (funcionando de ponta a ponta)

| Item | Status |
|------|--------|
| Scrapy puxa notícias e salva | ✅ |
| IA classifica positivo/negativo/neutro (FinBERT-PT-BR) | ✅ |
| Associar notícias a tickers (NER + mapa) | ✅ |
| Sinais de compra/venda por dia (regra + backtest) | ✅ |
| Recomendação estruturada (investir? onde? quando? por quê?) | ✅ |
| Interface Streamlit (status, dados, recomendações, backtest, testes) | ✅ |
| Rotina integrada (`main.py` → coleta + análise + recomendação) | ✅ |
| Documentação (README, instalação, arquitetura, citação, visão do projeto) | ✅ |
| Testes (pytest), config centralizado, logging, LICENSE | ✅ |

---

## O que é opcional ou fica para o cronograma

| Item | Observação |
|------|------------|
| **Horário (que hora do dia)** | Hoje é só por **dia**. “Que hora” exige dados intraday ou regra (ex.: abertura 10h). Não é bloqueante para o sistema funcionar. |
| **Baseline (Regressão Logística / Random Forest)** | Na proposta, para comparação científica. Não impede o sistema de rodar. |
| **Comparação com Selic** | Na proposta. Pode ser feita no relatório usando as métricas já geradas. |
| **RL (Q-Learning, DQN, PPO)** | Conforme cronograma da proposta; evolução futura. |
| **Vídeo (YouTube)** | Divulgação, conforme cronograma. |
| **Relatório final** | Entrega do IC; há template em `docs/RELATORIO_EXPERIMENTOS.md`. |
| **Diagrama de fluxo (Mermaid)** | Sugerido na doc; não obrigatório para rodar. |
| **CI (GitHub Actions), Docker** | Infra opcional. |

---

## Conclusão

- **Para rodar, coletar dados e analisar na interface:** o **pipeline** está pronto. Você ainda precisa **acumular dados** (muitos meses de coleta ou base Santos) para o backtest/recomendações serem significativos.
- **Para “treinar a IA”:** hoje a IA (FinBERT) é **pré-treinada**; não há treino no código. Se o professor exigir treino/fine-tuning com dados coletados, é uma fase extra — veja [DADOS_E_TREINAMENTO.md](DADOS_E_TREINAMENTO.md).
- **Para entregar o IC completo:** relatório final, vídeo e, se quiser, baseline/Selic/RL (cronograma).
- **Para “que hora”:** melhoria opcional (regra ou dados intraday).

Ou seja: **não falta nada crítico para o projeto estar pronto e em uso.** O resto é opcional ou parte da entrega formal do IC.
