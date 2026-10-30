# Dashboard SISCAN — 10ª CRS (2020–2025)

Aplicativo Streamlit de consulta **somente leitura** às tabelas analíticas Gold do TCC.

## Execução

A partir da raiz do repositório:

```bash
python -m pip install -r src/app/requirements.txt
streamlit run src/app/main.py
```

## Fontes de dados

Escolha **CSV local** na barra lateral e coloque os arquivos CSV exportados da Gold em `data/3_gold/` (ou `data/gold/`), com os seguintes nomes:

- `fato_exames_temporais_territoriais.csv`
- `fato_analise_outubro_rosa.csv`
- `fato_conformidade_faixa_etaria.csv`
- `fato_adequabilidade_amostras.csv`
- `fato_exames_alterados.csv`

Para utilizar **Databricks SQL**, configure `.streamlit/secrets.toml` na raiz da aplicação (não versionar; nunca publique credenciais):

```toml
DATABRICKS_SERVER_HOSTNAME = "dbc-....cloud.databricks.com"
DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/..."
DATABRICKS_TOKEN = "..."
DATABRICKS_CATALOG = "tcc-analise-siscan-10crs"
```

Também são aceitas variáveis de ambiente com os mesmos nomes. A conexão requer um SQL Warehouse funcional e permissões de leitura no Unity Catalog.

## Observações metodológicas

- Todas as páginas calculam indicadores agregados com as quantidades base.
- Participação territorial se refere aos exames registrados; não equivale à cobertura da população.
- Análise Outubro Rosa é descritiva, não causal.
- A taxa de alterações é **operacional**, pois o denominador Gold não exclui amostras rejeitadas/insatisfatórias por faixa etária.
- Valores ausentes não são substituídos por zeros.
- As páginas não modificam tabelas Bronze, Silver ou Gold.
- O arquivo da identidade visual `src/app/assets/LogoPET-Saude.jpeg` deve ser incluído pela equipe, caso autorizado.

## Estrutura

`main.py` — início e filtros compartilhados. `pages/` — cinco análises. `utils/data_loader.py` — acesso à Gold e cache. `utils/theme.py` — estilos e apresentação.
