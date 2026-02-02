# Checklist: O que falta para profissionalizar o projeto (nível USP)

Este documento lista **todas as lacunas e melhorias** necessárias para elevar o projeto de Iniciação Científica ao padrão profissional esperado em projetos do ICMC/USP.

---

## 1. Documentação

| Item | Status | Observação |
|------|--------|------------|
| README.md profissional | ✅ Criado | Descrição, instalação, uso, citação |
| Proposta de pesquisa no repositório | ✅ Incluído | `docs/Proposta_Pesquisa_IC_2025.pdf` |
| Documentação de arquitetura | ✅ Criado | `docs/ARCHITETURA.md` |
| Guia de instalação detalhado | ✅ Criado | `docs/INSTALACAO.md` |
| Instruções de citação (CITACAO.md) | ✅ Criado | `docs/CITACAO.md` |
| Docstrings em todas as funções públicas | ✅ Feito | Padrão Google em main, analisar_noticias, associar_tickers, criar_estrategia, config |
| Comentários em código complexo | ✅ Parcial | Pipelines e helpers documentados |
| Diagrama de fluxo de dados | ⬜ Sugerido | Mermaid ou figura em `docs/` |
| Relatório de experimentos (template) | ✅ Criado | `docs/RELATORIO_EXPERIMENTOS.md` |

---

## 2. Código e configuração

| Item | Status | Observação |
|------|--------|------------|
| Paths absolutos removidos | ✅ Corrigido | Uso de `config.py` com caminhos relativos |
| requirements.txt apenas com dependências | ✅ Corrigido | Comandos pip removidos |
| .gitignore completo | ✅ Criado | __pycache__, .env, dados sensíveis, etc. |
| Variáveis de ambiente para secrets | ✅ Criado | `.env.example` (MongoDB, HF) |
| Logging estruturado (em vez de apenas print) | ✅ Feito | `logging` em main, analisar_noticias, associar_tickers, criar_estrategia |
| Tratamento de exceções consistente | ✅ Parcial | Try/except com logger em scripts principais |
| Type hints em funções principais | ✅ Feito | main, analisar_noticias, associar_tickers, config, scripts/avaliacao_metricas |
| Testes unitários | ✅ Criado | pytest em `tests/` (test_config, test_analisar_noticias) |
| Formatação automática (Black/Ruff) | ⬜ Sugerido | pre-commit ou CI |

---

## 3. Dados e reprodutibilidade

| Item | Status | Observação |
|------|--------|------------|
| Especificação do schema da base (Santos 2022) | ✅ Criado | `docs/DADOS_SCHEMA.md` |
| Script de download/preparação de dados | ⬜ Pendente | Reproduzir ambiente de dados |
| Versionamento de modelos (FinBERT-PT-BR) | ✅ Feito | `config.FINBERT_MODEL_NAME` |
| Seeds para reprodutibilidade | ✅ Feito | `config.RANDOM_SEED` + numpy/torch em analisar_noticias |
| Dados de exemplo (sample) no repo | ⬜ Sugerido | Pequeno JSON/CSV para testes |

---

## 4. Pipeline científico

| Item | Status | Observação |
|------|--------|------------|
| Baseline (Regressão Logística / Random Forest) | ⬜ Conforme proposta | Implementar e documentar |
| Métricas financeiras (Sharpe, drawdown, retorno) | ✅ Criado | `scripts/avaliacao_metricas.py` |
| Comparação com Selic e benchmark passivo | ⬜ Pendente | Script de comparação (usar avaliacao_metricas) |
| Ambiente de RL (Q-Learning, DQN, PPO) | ⬜ Conforme cronograma | Estrutura e experimentos |
| Registro de resultados (tabelas/figuras) | ⬜ Pendente | Pasta `results/` ou `experimentos/` |

---

## 5. Infraestrutura e boas práticas

| Item | Status | Observação |
|------|--------|------------|
| Estrutura de pastas clara | ✅ Parcial | `docs/`, `tests/`, `scripts/` criados |
| CI (GitHub Actions) opcional | ⬜ Sugerido | Lint + testes em push |
| Docker opcional | ⬜ Sugerido | Para ambiente reprodutível |
| Changelog (CHANGELOG.md) | ✅ Criado | `CHANGELOG.md` |
| LICENSE no repositório | ✅ Criado | MIT — `LICENSE` |

---

## 6. Divulgação e entrega (conforme proposta)

| Item | Status | Observação |
|------|--------|------------|
| Vídeo explicativo (YouTube) | ⬜ Cronograma | Planejamento em docs |
| Relatório final (template/seções) | ✅ Template | `docs/RELATORIO_EXPERIMENTOS.md` + CHANGELOG |
| Simulação em corretora (validação) | ⬜ Cronograma | Documentar procedimento |

---

## 7. Referências e ética

| Item | Status | Observação |
|------|--------|------------|
| Citação do FinBERT-PT-BR (Santos 2022) | ✅ Documentado | Em README e CITACAO |
| Citação da base de dados utilizada | ⬜ Incluir | No relatório e no código |
| Uso de dados públicos / termos de uso | ⬜ Verificar | Scrapy: respeitar robots.txt e termos |

---

## Resumo de prioridades

1. **Imediato:** Docstrings, logging, type hints, .env.example, testes básicos.
2. **Curto prazo:** Métricas financeiras, baseline, seeds, schema de dados.
3. **Médio prazo:** Ambiente RL, comparação com Selic, resultados registrados.
4. **Entrega:** Relatório final, vídeo, citações e LICENSE.

---

*Documento gerado para acompanhamento do projeto de IC — ICMC/USP, 2025.*
