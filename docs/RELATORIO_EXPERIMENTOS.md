# Template: Relatório de Experimentos

Use este template para registrar resultados de experimentos (baseline, métricas financeiras, comparação com Selic, etc.) de forma reprodutível.

---

## Experimento: [Nome curto]

- **Data:** YYYY-MM-DD
- **Objetivo:** [Uma linha]
- **Configuração:** [Seeds, modelo, período de dados, etc.]

### Métricas

| Métrica            | Valor  | Observação     |
|--------------------|--------|----------------|
| Retorno total (%)  |        |                |
| Sharpe ratio       |        |                |
| Max drawdown (%)   |        |                |
| Win rate (%)       |        |                |
| Total de trades    |        |                |

### Comparação com benchmark

| Benchmark   | Retorno (%) | Período |
|-------------|-------------|---------|
| Estratégia  |             |         |
| Selic       |             |         |
| ETF passivo |             |         |

### Reprodutibilidade

- **Seed:** 42 (config.RANDOM_SEED)
- **Modelo:** FinBERT-PT-BR (lucas-leme/FinBERT-PT-BR)
- **Arquivos de entrada:** [listar JSONs ou datas]

### Observações e limitações

[Texto livre]

---

## Histórico de experimentos

| Data       | Nome              | Retorno (%) | Sharpe | Observação |
|------------|-------------------|-------------|--------|------------|
| YYYY-MM-DD | [nome]            |             |        |            |

---

*Documento de apoio ao projeto de IC — ICMC/USP, 2025.*
