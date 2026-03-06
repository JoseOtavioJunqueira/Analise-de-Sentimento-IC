"""
Interface Streamlit do projeto: status, dados, recomendações, backtest e testes.
Execute na raiz do projeto: streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Garante que a raiz do projeto está no path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (
    ARQUIVO_JSON_MAPEADAS,
    ARQUIVO_JSON_NOTICIAS,
    ARQUIVO_JSON_SENTIMENTO,
    ARQUIVO_STATUS,
    ARQUIVO_ULTIMA_RECOMENDACAO,
    ARQUIVO_ULTIMO_BACKTEST_JSON,
    ARQUIVO_RESULTADOS_BACKTEST,
)

st.set_page_config(
    page_title="Análise de Sentimento — Mercado Financeiro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Título e descrição ---
st.title("📈 Análise de Sentimento — Mercado Financeiro")
st.markdown("""
**Projeto de IC — ICMC/USP.**  
Sistema que coleta notícias financeiras, classifica o sentimento (positivo/negativo/neutro) com IA (FinBERT-PT-BR)  
e gera recomendações de investimento (quando, onde, por quê) visando lucro.
""")
st.divider()

# --- Sidebar: navegação e status rápido ---
with st.sidebar:
    st.header("Status da última execução")
    status = {}
    if os.path.exists(ARQUIVO_STATUS):
        try:
            with open(ARQUIVO_STATUS, "r", encoding="utf-8") as f:
                status = json.load(f)
        except Exception:
            pass
    ultima_coleta = status.get("ultima_coleta", "—")
    ultima_analise = status.get("ultima_analise", "—")
    ultima_recomendacao = status.get("ultima_recomendacao", "—")
    ultimo_backtest = status.get("ultimo_backtest", "—")
    st.metric("Última coleta (Scrapy)", ultima_coleta[:19] if isinstance(ultima_coleta, str) and len(ultima_coleta) > 19 else ultima_coleta)
    st.metric("Última análise (sentimento)", ultima_analise[:19] if isinstance(ultima_analise, str) and len(ultima_analise) > 19 else ultima_analise)
    st.metric("Última recomendação", ultima_recomendacao[:19] if isinstance(ultima_recomendacao, str) and len(ultima_recomendacao) > 19 else ultima_recomendacao)
    st.metric("Último backtest", ultimo_backtest[:19] if isinstance(ultimo_backtest, str) and len(ultimo_backtest) > 19 else ultimo_backtest)
    st.divider()
    st.caption("Rotina diária: `python rodar_todo_dia.py` (na raiz do projeto)")

# --- Abas principais ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "O que o projeto faz",
    "Status e dados coletados",
    "Recomendações atuais",
    "Backtest (lucro / métricas)",
    "Testes do projeto",
    "Como rodar e deixar online",
])

# --- Tab 1: O que o projeto faz ---
with tab1:
    st.header("O que o projeto faz")
    st.markdown("""
    1. **Scrapy** — Puxa notícias dos portais (Infomoney, Valor, Exame, Bloomberg) e salva em `financial_news.json`.
    2. **IA (FinBERT-PT-BR)** — Classifica cada notícia em **positivo**, **negativo** ou **neutro** (análise de sentimento).
    3. **Associar tickers** — Identifica quais ativos (PETR4, VALE3, etc.) são citados em cada notícia → `noticias_mapeadas.json`.
    4. **Recomendação** — Gera sinais compra/venda/segurar por ativo (**IA**: Random Forest ou agente RL Q-Learning, nunca regra fixa), com **quando**, **onde** e **por quê** (notícias que motivaram).
    5. **Backtest** — Simula se a estratégia teria dado lucro no passado (retorno %, Sharpe ratio, drawdown), usando o mesmo modelo ou RL quando disponível.
    """)
    st.subheader("Fluxo de dados")
    st.code("""
[Portais] → Scrapy → financial_news.json
    → analisar_noticias.py (FinBERT) → noticias_com_sentimento.json
    → associar_tickers.py → noticias_mapeadas.json
    → recomendacao.py → ultima_recomendacao.json (investir? onde? quando? por quê?)
    → criar_estrategia.py → backtest (retorno, Sharpe, drawdown) + resultados_backtest_v1.html
    """, language="text")
    st.caption("Documentação completa: docs/VISAO_E_ETAPAS.md")

# --- Tab 2: Status e dados coletados ---
with tab2:
    st.header("Status e dados coletados")
    col1, col2, col3 = st.columns(3)
    with col1:
        n_noticias_brutas = 0
        if os.path.exists(ARQUIVO_JSON_NOTICIAS):
            try:
                with open(ARQUIVO_JSON_NOTICIAS, "r", encoding="utf-8") as f:
                    raw = f.read()
                # Conta objetos no JSON (aproximado)
                n_noticias_brutas = raw.count('"title"') if raw.strip() and raw.strip() != "[]" else 0
            except Exception:
                pass
        st.metric("Notícias brutas (Scrapy)", n_noticias_brutas)
    with col2:
        n_sentimento = 0
        if os.path.exists(ARQUIVO_JSON_SENTIMENTO):
            try:
                df = pd.read_json(ARQUIVO_JSON_SENTIMENTO)
                n_sentimento = len(df)
            except Exception:
                pass
        st.metric("Notícias com sentimento", n_sentimento)
    with col3:
        n_mapeadas = 0
        if os.path.exists(ARQUIVO_JSON_MAPEADAS):
            try:
                df = pd.read_json(ARQUIVO_JSON_MAPEADAS)
                n_mapeadas = len(df)
            except Exception:
                pass
        st.metric("Notícias mapeadas (tickers)", n_mapeadas)

    st.subheader("Amostra: notícias com sentimento")
    if os.path.exists(ARQUIVO_JSON_SENTIMENTO):
        try:
            df = pd.read_json(ARQUIVO_JSON_SENTIMENTO)
            if not df.empty:
                cols_show = [c for c in ["title", "date", "data_normalizada", "source", "sentimento_previsto"] if c in df.columns]
                if cols_show:
                    st.dataframe(df[cols_show].head(50), use_container_width=True)
            else:
                st.info("Nenhuma notícia com sentimento ainda. Execute a rotina: python main.py")
        except Exception as e:
            st.warning(f"Erro ao carregar: {e}")
    else:
        st.info("Arquivo de notícias com sentimento não encontrado. Execute: python main.py e analisar_noticias.py")

# --- Tab 3: Recomendações atuais ---
with tab3:
    st.header("Recomendações atuais")
    st.markdown("**Investir? Onde? Quando? Por quanto tempo? Por quê?**")
    if os.path.exists(ARQUIVO_ULTIMA_RECOMENDACAO):
        try:
            with open(ARQUIVO_ULTIMA_RECOMENDACAO, "r", encoding="utf-8") as f:
                rec = json.load(f)
            st.metric("Data da recomendação", rec.get("quando", "—"))
            st.metric("Por quanto tempo", rec.get("por_quanto_tempo", "—"))
            st.write("**Resumo:**", rec.get("resumo", "—"))
            if rec.get("erro"):
                st.warning("Recomendação gerada com restrições (ex.: sem dados suficientes).")
            st.subheader("Ações por ativo")
            investir = rec.get("investir", [])
            if investir:
                df_rec = pd.DataFrame(investir)
                st.dataframe(df_rec, use_container_width=True)
                st.subheader("Onde atuar (comprar ou vender)")
                st.write(", ".join(rec.get("onde", [])) or "Nenhum ativo com sinal forte.")
                st.subheader("Por quê — notícias que motivaram cada ativo")
                por_que = rec.get("por_que", {})
                for ticker, noticias in por_que.items():
                    with st.expander(f"**{ticker}** — {len(noticias)} notícia(s)"):
                        for n in noticias:
                            st.markdown(f"- **{n.get('titulo', '')}** — {n.get('sentimento', '')}")
                            if n.get("url"):
                                st.caption(n["url"])
            else:
                st.info("Nenhuma ação recomendada para a última data disponível.")
        except Exception as e:
            st.error(f"Erro ao carregar recomendação: {e}")
    else:
        st.info("Nenhuma recomendação gerada ainda. Execute: python recomendacao.py (ou python main.py após associar_tickers.py).")

# --- Tab 4: Backtest (lucro / métricas) ---
with tab4:
    st.header("Backtest — Deu lucro? Métricas da estratégia")
    if os.path.exists(ARQUIVO_ULTIMO_BACKTEST_JSON):
        try:
            with open(ARQUIVO_ULTIMO_BACKTEST_JSON, "r", encoding="utf-8") as f:
                bt = json.load(f)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Retorno total (%)", f"{bt.get('retorno_total_pct', 0):.2f}%")
            c2.metric("Sharpe ratio", f"{bt.get('sharpe_ratio', 0):.2f}")
            c3.metric("Max drawdown (%)", f"{bt.get('max_drawdown_pct', 0):.2f}%")
            c4.metric("Win rate (%)", f"{bt.get('win_rate_pct', 0):.2f}%")
            c5.metric("Total de trades", bt.get("total_trades", 0))
            st.caption(f"Período: {bt.get('inicio', '')} a {bt.get('fim', '')} | Gerado em {bt.get('data_geracao', '')}")
            html_path = bt.get("arquivo_html", ARQUIVO_RESULTADOS_BACKTEST)
            if os.path.exists(html_path):
                st.subheader("Relatório HTML completo (VectorBT)")
                st.caption(f"Arquivo: {html_path}")
                try:
                    with open(html_path, "r", encoding="utf-8") as f:
                        html = f.read()
                    if len(html) < 2_000_000:  # evita travar com HTML muito grande
                        st.components.v1.html(html, height=600, scrolling=True)
                    else:
                        st.info("Relatório muito grande. Abra o arquivo no navegador.")
                except Exception as e:
                    st.warning(f"Não foi possível exibir o HTML: {e}. Abra o arquivo manualmente.")
            else:
                st.caption("Arquivo HTML do backtest não encontrado. Execute: python criar_estrategia.py")
        except Exception as e:
            st.error(f"Erro ao carregar backtest: {e}")
    else:
        st.info("Backtest ainda não executado. Execute: python criar_estrategia.py (requer noticias_mapeadas.json).")

# --- Tab 5: Testes do projeto ---
with tab5:
    st.header("Testes do projeto (pytest)")
    st.markdown("Testes automatizados: config, normalização de datas, deduplicação.")
    if st.button("Executar testes agora (pytest)"):
        with st.spinner("Executando pytest..."):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-v", "--tb=short"],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                st.code(result.stdout + "\n" + result.stderr, language="text")
                if result.returncode == 0:
                    st.success("Todos os testes passaram.")
                else:
                    st.warning("Alguns testes falharam.")
            except subprocess.TimeoutExpired:
                st.error("Testes expiraram (timeout).")
            except FileNotFoundError:
                st.warning("pytest não encontrado. Instale: pip install pytest")
            except Exception as e:
                st.error(str(e))
    st.caption("Ou na raiz do projeto: pytest")

# --- Tab 6: Como rodar e deixar online ---
with tab6:
    st.header("Como rodar e deixar a interface online")
    st.markdown("""
    **1. Rotina de coleta e análise (na máquina onde vai rodar):**
    ```bash
    cd /caminho/para/Analise-de-Sentimento-IC
    python main.py
    ```
    (Opcional: agende com **cron** ou **Agendador de Tarefas** para rodar todo dia.)

    **2. Associar notícias a tickers (uma vez ou quando tiver mapeamento novo):**
    ```bash
    python associar_tickers.py
    ```

    **3. Gerar recomendação (ou deixar main.py fazer após a análise):**
    ```bash
    python recomendacao.py
    ```

    **4. Backtest (quando quiser ver métricas de lucro):**
    ```bash
    python criar_estrategia.py
    ```

    **5. Subir a interface Streamlit para acesso na rede:**
    ```bash
    streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
    ```
    - Acesse de outro PC na mesma rede: `http://IP_DA_MAQUINA:8501`
    - Para manter rodando em segundo plano (Linux): use `nohup` ou um serviço systemd.
    """)
    st.caption("Documentação: docs/INSTALACAO.md e docs/VISAO_E_ETAPAS.md")

st.divider()
st.caption("Projeto de IC — ICMC/USP | Análise de Sentimento em Investimentos Financeiros")
