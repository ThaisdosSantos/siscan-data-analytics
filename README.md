# SISCAN Data Analytics

Plataforma analítica para exploração de exames citopatológicos do colo do útero nos 11 municípios da 10ª Coordenadoria Regional de Saúde do Rio Grande do Sul (10ª CRS), entre 2020 e 2025.

**[Acessar o dashboard](https://siscan-data-analytics-rmvxtnyhxnphdaygum54uy.streamlit.app/)**

## Funcionalidades

- Visão executiva e distribuição territorial dos exames.
- Evolução mensal e anual da produção, com comparação entre municípios.
- Perfil etário e razão de exames na população feminina de 25 a 64 anos.
- Adequabilidade das amostras e análise dos resultados citopatológicos alterados.
- Comparação da produção no período do Outubro Rosa.

O dashboard oferece filtros por município e ano, gráficos interativos e exportação de gráficos (PNG) e tabelas (CSV).

## Arquitetura e tecnologias

```text
SISCAN / DATASUS (CSV) + IBGE / SIDRA
              ↓
       Bronze → Silver → Gold
              ↓
     Databricks SQL → Streamlit
```

| Camada | Responsabilidade |
| --- | --- |
| Bronze | Ingestão e preservação dos dados brutos. |
| Silver | Limpeza, padronização e validação dos registros. |
| Gold | Consolidação das tabelas e indicadores analíticos. |

**Stack:** Python, PySpark, Databricks, Delta Lake, Pandas, Plotly e Streamlit.

## Estrutura do repositório

| Diretório | Conteúdo |
| --- | --- |
| [notebooks/](notebooks/) | Ingestão, transformação, integração do IBGE, auditoria e execução no Databricks. |
| [src/app/](src/app/) | Dashboard, páginas analíticas e módulos compartilhados. |
| [data/](data/) | Estrutura de diretórios para as camadas de dados. |
| [config/](config/) | Configurações do projeto. |

## Execução

Requisitos: Python 3.11 recomendado, acesso a um SQL Warehouse e às tabelas Gold no Unity Catalog.

```bash
git clone https://github.com/ThaisdosSantos/siscan-data-analytics.git
cd siscan-data-analytics
python -m venv .venv
source .venv/bin/activate
python -m pip install -r src/app/requirements.txt
```

Na raiz do repositório, crie `.streamlit/secrets.toml` com suas credenciais do Databricks (ou configure as variáveis de ambiente equivalentes):

```toml
DATABRICKS_SERVER_HOSTNAME = "seu-workspace.cloud.databricks.com"
DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/seu-warehouse"
DATABRICKS_TOKEN = "seu-token"
DATABRICKS_CATALOG = "tcc-analise-siscan-10crs"
```

```bash
streamlit run src/app/main.py
```

Nunca versione credenciais. A aplicação realiza consultas somente leitura à Gold.

Para reconstruir as tabelas principais no Databricks, disponibilize o dataset no volume Bronze conforme o notebook 01 e execute os notebooks na ordem **01 → 02 → 06 → 03 → 05**. O notebook 04 permite iniciar o dashboard no Databricks. As tabelas complementares de perfil etário do Outubro Rosa devem estar disponíveis na Gold, pois não são reconstruídas pelo notebook 03.

## Fontes e limitações

- [SISCAN/DATASUS](https://datasus.saude.gov.br/informacoes-de-saude-tabnet/): exames registrados, não mulheres distintas.
- [IBGE/SIDRA — Censo 2022, tabela 9514](https://sidra.ibge.gov.br/tabela/9514): denominador populacional fixo para a razão anual de exames.
- Agosto de 2022 não possui registros na série temporal analisada; competências ausentes não equivalem a zero.
- A proporção de alterados por idade é uma estimativa operacional, pois as exclusões de amostras insatisfatórias e rejeitadas são distribuídas proporcionalmente por faixa etária.
- As análises são descritivas e não demonstram impacto causal da campanha Outubro Rosa.

A verificação automatizada de sintaxe da aplicação é realizada pelo [GitHub Actions](.github/workflows/streamlit-syntax.yml).
