# Schema dos Dados

Especificação dos formatos de dados utilizados no projeto (JSON e colunas esperadas) para reprodutibilidade e integração.

---

## 1. Notícias brutas (saída do Scrapy)

**Arquivo:** `financial_scraper/financial_news.json`  
**Formato:** JSON array de objetos (um por notícia).

| Campo   | Tipo   | Obrigatório | Descrição                          |
|---------|--------|-------------|------------------------------------|
| title   | string | Sim         | Título da notícia                  |
| url     | string | Sim         | URL da página                      |
| date    | string/number | Não  | Data da publicação (ISO ou timestamp) |
| content | string | Não         | Corpo do texto                     |
| source  | string | Não         | Nome da fonte (ex: InfoMoney)      |

O Scrapy pode gerar múltiplos blocos `[...]` no mesmo arquivo; o pipeline de análise consolida todos.

---

## 2. Notícias com sentimento (saída do analisar_noticias.py)

**Arquivo:** `noticias_com_sentimento.json`  
**Formato:** JSON array de objetos.

Campos herdados da notícia bruta mais:

| Campo               | Tipo   | Descrição                                      |
|---------------------|--------|------------------------------------------------|
| texto_completo      | string | title + " " + content (para classificação)     |
| data_normalizada    | string | Data em ISO 8601 (normalizada por normalizar_data) |
| sentimento_previsto | string | "POSITIVE", "NEGATIVE" ou "NEUTRAL" (FinBERT-PT-BR) |

---

## 3. Notícias mapeadas (saída do associar_tickers.py)

**Arquivo:** `noticias_mapeadas.json`  
**Formato:** JSON array de objetos (apenas notícias com pelo menos um ticker mapeado).

Campos herdados de notícias com sentimento mais:

| Campo            | Tipo    | Descrição                                      |
|------------------|---------|------------------------------------------------|
| empresas_citadas | list    | Lista de nomes de empresas (NER spaCy ORG/MISC) |
| tickers_citados  | list    | Lista de tickers (ex: ["PETR4", "VALE3"])      |

---

## 4. Mapeamento empresa → ticker

**Arquivo:** `mapeamento_tickers.json`  
**Formato:** JSON object `{ "Nome da Empresa": "TICKER", ... }`.

- Chave: nome da empresa (como aparece em notícias ou NER).
- Valor: ticker na B3 (ex: "PETR4"). Use `null` para empresas que não devem gerar sinal.

Exemplo:
```json
{
  "Petrobras": "PETR4",
  "Vale": "VALE3",
  "Empresa sem ticker": null
}
```

---

## 5. Base de dados (Santos 2022)

A proposta do projeto referencia a base desenvolvida por **Lucas L. Santos (2022)** para notícias financeiras (2006–2022). A expansão é feita via Scrapy a partir de Infomoney, Valor Econômico e Exame. O schema das notícias coletadas segue o mesmo formato da tabela 1 (notícias brutas), podendo ser armazenado em MongoDB com os mesmos campos.

---

## Referências

- Proposta: [Proposta_Pesquisa_IC_2025.pdf](Proposta_Pesquisa_IC_2025.pdf)
- Santos (2022): [CITACAO.md](CITACAO.md)
