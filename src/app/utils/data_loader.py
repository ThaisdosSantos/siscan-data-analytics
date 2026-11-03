"""Acesso somente leitura à Gold, com CSV local ou Databricks SQL."""
import os
import re
import unicodedata
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
TABLES = {
 "temporal":"fato_exames_temporais_territoriais",
 "outubro":"fato_analise_outubro_rosa",
 "etaria":"fato_conformidade_faixa_etaria",
 "adequabilidade":"fato_adequabilidade_amostras",
 "alterados":"fato_exames_alterados",
}
MUNICIPIOS = {
 "430040":"Alegrete", "430187":"Barra do Quaraí", "431060":"Itaqui",
 "431171":"Maçambará", "431175":"Manoel Viana", "431530":"Quaraí",
 "431640":"Rosário do Sul", "431697":"Santa Margarida do Sul",
 "431710":"Sant'Ana do Livramento", "431830":"São Gabriel", "432240":"Uruguaiana"
}

def _config(key, default=None):
    try: return st.secrets.get(key, os.getenv(key, default))
    except (FileNotFoundError, KeyError): return os.getenv(key,default)

def _norm(value):
    text=unicodedata.normalize("NFKD",str(value)).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]","",text)

def _from_csv(name):
    roots=[ROOT/"data"/"3_gold",ROOT/"data"/"gold"]
    for folder in roots:
        f=folder/f"{name}.csv"
        if f.is_file():
            try: return pd.read_csv(f,sep=None,engine="python",encoding="utf-8-sig")
            except UnicodeDecodeError: return pd.read_csv(f,sep=None,engine="python",encoding="latin-1")
    return pd.DataFrame()

def _from_databricks(name):
    from databricks import sql
    host=_config("DATABRICKS_SERVER_HOSTNAME")
    path=_config("DATABRICKS_HTTP_PATH")
    token=_config("DATABRICKS_TOKEN")
    catalog=_config("DATABRICKS_CATALOG","tcc-analise-siscan-10crs")
    missing=[k for k,v in {
        "DATABRICKS_SERVER_HOSTNAME":host,
        "DATABRICKS_HTTP_PATH":path,
        "DATABRICKS_TOKEN":token,
    }.items() if not v]
    if missing:
        raise RuntimeError("Configuração Databricks incompleta: " + ", ".join(missing)
          + ". Configure esses valores nos Secrets do Streamlit Cloud ou em variáveis de ambiente.")
    with sql.connect(server_hostname=host.replace("https://",""),http_path=path,access_token=token) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{catalog}`.gold.`{name}`")
            return cursor.fetchall_arrow().to_pandas()

@st.cache_data(ttl=900,show_spinner=False)
def load_table(table_key, source="CSV local"):
    if table_key not in TABLES: raise ValueError("Tabela não permitida")
    name=TABLES[table_key]
    try:
        df=_from_databricks(name) if source=="Databricks SQL" else _from_csv(name)
    except Exception as exc:
        st.error(f"Falha ao consultar Gold: {type(exc).__name__}: {exc}")
        return pd.DataFrame()
    if df.empty: return df
    df.columns=[str(x).strip().lower() for x in df.columns]
    if "codigo_municipio" in df.columns:
        codes=df["codigo_municipio"].astype("string").str.extract(r"(\d{6,7})",expand=False).str[:6]
        df["codigo_municipio"]=codes
        df=df[df["codigo_municipio"].isin(MUNICIPIOS)].copy()
        df["municipio"]=df["codigo_municipio"].map(MUNICIPIOS)
    elif "municipio" in df:
        canonical={_norm(m):m for m in MUNICIPIOS.values()}
        df["municipio"]=df["municipio"].map(lambda x:canonical.get(_norm(x)))
        df=df[df["municipio"].notna()].copy()
    if "ano" in df:
        df["ano"]=pd.to_numeric(df["ano"],errors="coerce")
        df=df[df["ano"].between(2020,2025)].copy()
    if "mes" in df: df["mes"]=pd.to_numeric(df["mes"],errors="coerce")
    if "dt_competencia" in df: df["dt_competencia"]=pd.to_datetime(df["dt_competencia"],errors="coerce")
    for col in ["quantidade","quantidade_exames","quantidade_amostras",
                "exames_mes","exames_referencia_setembro","quantidade_alterados","total_exames_validos"]:
        if col in df: df[col]=pd.to_numeric(df[col],errors="coerce")
    return df

def selected_source():
    """Fonte persistente, independente da vida útil dos widgets multipágina."""
    return "Databricks SQL"

def filtered(table_key):
    df=load_table(table_key, selected_source())
    if df.empty:
        return df
    years=selected_years()
    cities=st.session_state.get("city_preference", list(MUNICIPIOS.values()))
    if not years or not cities:
        return df.iloc[0:0].copy()
    if "ano" in df:
        df=df[df.ano.isin(years)]
    if "municipio" in df:
        df=df[df.municipio.isin(cities)]
    return df.copy()

def require(df,columns):
    if df.empty:
        st.info("Não há registros para os filtros selecionados na fonte "
                + selected_source() + ". Verifique os dados e os filtros.")
        return False
    missing=[c for c in columns if c not in df]
    if missing:
        st.warning("Colunas ausentes na tabela Gold: "+", ".join(missing))
        return False
    return True

def selected_years():
    """Anos ativos para todas as páginas, inclusive após troca de página."""
    years = list(range(2020, 2026))
    saved = st.session_state.get("years_preference")
    if saved is None:
        old = st.session_state.get("year_preference", "Todos")
        saved = years if old == "Todos" else [int(old)]
    return [year for year in years if year in saved]


def years_label(years=None):
    """Representação fiel inclusive de anos não consecutivos."""
    years = selected_years() if years is None else years
    if not years:
        return "Nenhum ano"
    if years == list(range(min(years), max(years) + 1)):
        return str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
    return ", ".join(map(str, years))


def year_month_index(years=None):
    """Calendário com meses omitidos preservados como NaN."""
    years = selected_years() if years is None else years
    if not years:
        return pd.DatetimeIndex([])
    return pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-01", freq="MS")



def sidebar_filters():
    """Filtros globais: várias escolhas sem recarregar até confirmar o formulário."""
    years = list(range(2020, 2026))
    cities = list(MUNICIPIOS.values())
    st.session_state["years_preference"] = selected_years()
    st.session_state.setdefault("city_preference", cities.copy())
    st.session_state["city_preference"] = [
        city for city in cities if city in st.session_state["city_preference"]
    ]

    # Estado temporário dos widgets, separado do recorte aplicado nas tabelas Gold.
    # Quando o Streamlit recria os widgets após trocar de página,
    # os valores são recuperados das preferências persistentes.
    st.session_state.setdefault("filter_draft_years", selected_years())
    for city in cities:
        st.session_state.setdefault(
            "filter_draft_city_" + city, city in st.session_state["city_preference"]
        )

    def submit_filters(action="apply"):
        selected_years_draft = list(st.session_state.get("filter_draft_years", []))
        selected_cities_draft = [
            city for city in cities
            if st.session_state.get("filter_draft_city_" + city, False)
        ]
        if action == "all_years":
            selected_years_draft = years.copy()
        elif action == "clear_years":
            selected_years_draft = []
        elif action == "all_cities":
            selected_cities_draft = cities.copy()
        elif action == "clear_cities":
            selected_cities_draft = []

        # Atualização atômica: a página só consulta o novo recorte no envio.
        st.session_state["years_preference"] = [
            year for year in years if year in selected_years_draft
        ]
        st.session_state["city_preference"] = [
            city for city in cities if city in selected_cities_draft
        ]
        st.session_state["filter_draft_years"] = st.session_state["years_preference"].copy()
        for city in cities:
            st.session_state["filter_draft_city_" + city] = city in selected_cities_draft

    with st.sidebar:
        st.markdown(
            '<div class="lovable-brand"><span class="lovable-mark">✳</span>'
            '<span><strong>SISCAN</strong><small>PET-Saúde · 10ª CRS</small></span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="lovable-label">EXPLORAR</div>', unsafe_allow_html=True)
        for path, label, icon in [
            ("main.py", "Visão executiva", ":material/speed:"),
            ("pages/01_panorama_geral.py", "Panorama geral", ":material/bar_chart:"),
            ("pages/02_outubro_rosa.py", "Outubro Rosa", ":material/workspace_premium:"),
            ("pages/03_faixa_etaria.py", "Faixa etária", ":material/group:"),
            ("pages/04_adequabilidade.py", "Adequabilidade", ":material/science:"),
            ("pages/05_exames_alterados.py", "Exames alterados", ":material/ecg_heart:"),
        ]:
            st.page_link(path, label=label, icon=icon)

        st.divider()
        with st.container(key="siscan_filter_panel"):
            st.markdown(
                '<div class="filter-panel-title">☷ &nbsp; FILTROS</div>',
                unsafe_allow_html=True,
            )
            with st.form("siscan_filters_form", border=False):
                with st.expander(
                    f"Anos   ·   {len(selected_years())}/6",
                    expanded=False, icon=":material/calendar_month:",
                ):
                    st.caption("Selecione os anos e confirme ao final.")
                    st.pills(
                        "Anos disponíveis", years,
                        selection_mode="multi", key="filter_draft_years",
                        label_visibility="collapsed",
                    )
                    y_all, y_clear = st.columns(2, gap="small")
                    with y_all:
                        st.form_submit_button(
                            "Todos", use_container_width=True,
                            on_click=submit_filters, args=("all_years",),
                        )
                    with y_clear:
                        st.form_submit_button(
                            "Limpar", use_container_width=True,
                            on_click=submit_filters, args=("clear_years",),
                        )
                with st.expander(
                    f"Municípios   ·   {len(st.session_state['city_preference'])}/11",
                    expanded=False, icon=":material/location_on:",
                ):
                    st.caption("Marque os municípios antes de aplicar.")
                    c_all, c_clear = st.columns(2, gap="small")
                    with c_all:
                        st.form_submit_button(
                            "Todos", use_container_width=True,
                            on_click=submit_filters, args=("all_cities",),
                        )
                    with c_clear:
                        st.form_submit_button(
                            "Limpar", use_container_width=True,
                            on_click=submit_filters, args=("clear_cities",),
                        )
                    with st.container(height=255, border=False):
                        for city in cities:
                            st.checkbox(city, key="filter_draft_city_" + city)
                st.form_submit_button(
                    "Aplicar filtros", type="primary", use_container_width=True,
                    on_click=submit_filters,
                )
        st.markdown(
            '<div class="lovable-footer">Fonte: SISCAN/DATASUS · 2020–2025'
            '<br>TCC Engenharia de Software · Informação e Saúde Digital</div>',
            unsafe_allow_html=True,
        )
