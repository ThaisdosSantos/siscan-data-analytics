"""Acesso somente leitura à Gold, com CSV local ou Databricks SQL."""
import os
import base64
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
 "cobertura":"fato_evolucao_cobertura_municipios",
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
                "exames_mes","exames_referencia_setembro","quantidade_alterados","total_exames_validos",
                "total_exames_25_64","mulheres_25_64_anos","taxa_cobertura_pct","meta_ans_pct"]:
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



def _initialize_filter_draft():
    """Restaura a seleção temporária ao alternar páginas."""
    years = list(range(2020, 2026))
    cities = list(MUNICIPIOS.values())
    st.session_state["years_preference"] = selected_years()
    st.session_state.setdefault("city_preference", cities.copy())
    st.session_state["city_preference"] = [
        c for c in cities if c in st.session_state["city_preference"]
    ]
    st.session_state.setdefault(
        "_draft_years", st.session_state["years_preference"].copy()
    )
    st.session_state.setdefault(
        "_draft_cities", st.session_state["city_preference"].copy()
    )
    # Chaves próprias dos widgets: sobrevivem à troca de página via cópia persistente.
    st.session_state.setdefault(
        "filter_draft_years", st.session_state["_draft_years"].copy()
    )
    for city in cities:
        st.session_state.setdefault(
            "filter_draft_city_" + city, city in st.session_state["_draft_cities"]
        )


@st.fragment
def _render_filter_controls():
    """Atualiza apenas a barra lateral durante a seleção, sem recalcular gráficos."""
    years = list(range(2020, 2026))
    cities = list(MUNICIPIOS.values())

    def current_years():
        return [int(y) for y in st.session_state.get("filter_draft_years", []) if int(y) in years]

    def current_cities():
        return [c for c in cities if st.session_state.get("filter_draft_city_" + c, False)]

    def keep_draft():
        st.session_state["_draft_years"] = current_years()
        st.session_state["_draft_cities"] = current_cities()

    def set_years(choose_all):
        chosen = years.copy() if choose_all else []
        st.session_state["filter_draft_years"] = chosen
        keep_draft()

    def toggle_city(city):
        key = "filter_draft_city_" + city
        st.session_state[key] = not st.session_state.get(key, False)
        keep_draft()

    def set_cities(choose_all):
        for city in cities:
            st.session_state["filter_draft_city_" + city] = bool(choose_all)
        keep_draft()

    # O CSS de cabeçalho acompanha a seleção em rascunho sem recarregar a página.
    draft_years = current_years()
    draft_cities = current_cities()
    period_summary = (
        "Período completo" if len(draft_years) == 6
        else "Nenhum ano" if not draft_years
        else "Período: " + ", ".join(map(str, draft_years))
    )
    city_summary = (
        "Todos os 11 municípios" if len(draft_cities) == 11
        else f"{len(draft_cities)} de 11 municípios"
    )
    def css_string(value):
        return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    st.markdown(
        "<style>"
        ".st-key-siscan_year_panel details>summary::after{content:'"
        + css_string(f"{len(draft_years)}/6") + "';}"
        ".st-key-siscan_city_panel details>summary::after{content:'"
        + css_string(f"{len(draft_cities)}/11") + "';}"
        ".st-key-siscan_year_panel details:not([open])>summary [data-testid='stMarkdownContainer']::after{content:'"
        + css_string(period_summary) + "';}"
        ".st-key-siscan_city_panel details:not([open])>summary [data-testid='stMarkdownContainer']::after{content:'"
        + css_string(city_summary) + "';}"
        "</style>",
        unsafe_allow_html=True,
    )

    with st.container(key="siscan_filter_panel"):
        st.markdown(
            '<div class="filter-panel-title">☷ &nbsp; FILTROS</div>',
            unsafe_allow_html=True,
        )
        with st.container(key="siscan_year_panel"):
            with st.expander(
                "Anos", expanded=False,
            ):
                n = len(draft_years)
                st.markdown(
                    '<div class="filter-progress" role="progressbar" '
                    f'aria-label="Anos selecionados" aria-valuenow="{n}" '
                    'aria-valuemin="0" aria-valuemax="6">'
                    f'<span style="width:{100*n/6:.2f}%"></span></div>',
                    unsafe_allow_html=True,
                )
                all_col, clear_col = st.columns(2, gap="small")
                with all_col:
                    st.button("Todos", key="filter_all_years", use_container_width=True,
                              on_click=set_years, args=(True,))
                with clear_col:
                    st.button("Limpar", key="filter_clear_years", use_container_width=True,
                              on_click=set_years, args=(False,))
                st.pills(
                    "Anos disponíveis", years, selection_mode="multi",
                    key="filter_draft_years", label_visibility="collapsed",
                    on_change=keep_draft,
                )
                chosen = current_years()
                period = years_label(chosen)
                st.markdown(
                    '<p class="filter-period-label">'
                    + ("Período completo" if len(chosen) == 6 else
                       "Nenhum ano" if not chosen else "Período: " + period)
                    + '</p>', unsafe_allow_html=True,
                )
        with st.container(key="siscan_city_panel"):
            with st.expander(
                "Municípios", expanded=False,
            ):
                n = len(draft_cities)
                st.markdown(
                    '<div class="filter-progress" role="progressbar" '
                    f'aria-label="Municípios selecionados" aria-valuenow="{n}" '
                    'aria-valuemin="0" aria-valuemax="11">'
                    f'<span style="width:{100*n/11:.2f}%"></span></div>',
                    unsafe_allow_html=True,
                )
                all_col, clear_col = st.columns(2, gap="small")
                with all_col:
                    st.button("Todos", key="filter_all_cities", use_container_width=True,
                              on_click=set_cities, args=(True,))
                with clear_col:
                    st.button("Limpar", key="filter_clear_cities", use_container_width=True,
                              on_click=set_cities, args=(False,))
                with st.container(height=255, border=False, key="siscan_city_scroll"):
                    for city in cities:
                        selected = st.session_state.get("filter_draft_city_" + city, False)
                        st.button(city, key="filter_city_button_" + city,
                                  type="primary" if selected else "secondary",
                                  use_container_width=True, on_click=toggle_city,
                                  args=(city,))
        applied_years = st.session_state["years_preference"]
        applied_cities = st.session_state["city_preference"]
        is_changed = current_years() != applied_years or current_cities() != applied_cities
        if is_changed:
            st.caption("Seleção alterada · confirme para atualizar os gráficos.")
            if st.button(
                "Aplicar filtros", type="primary", key="filter_apply",
                use_container_width=True,
            ):
                keep_draft()
                st.session_state["years_preference"] = current_years()
                st.session_state["city_preference"] = current_cities()
                st.rerun(scope="app")


def sidebar_filters():
    """Navegação global com filtros reativos locais e aplicação explícita."""
    _initialize_filter_draft()
    with st.sidebar:
        # A logo institucional fica em src/assets e é incorporada ao HTML,
        # sem depender de hospedagem externa ou da URL do repositório.
        logo_path = ROOT / "src" / "assets" / "LogoPET-Saude.jpeg"
        logo_base64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        st.markdown(
            '<div class="lovable-brand">'
            '<span class="lovable-mark">'
            '<img src="data:image/jpeg;base64,' + logo_base64 + '" '
            'alt="Logo PET-Saúde" loading="eager" />'
            '</span>'
            '<span><strong>SISCAN</strong><small>PET-Saúde · 10ª CRS</small></span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="lovable-label">EXPLORAR</div>',
                    unsafe_allow_html=True)
        for path, label, icon, nav_key in [
            ("main.py", "Visão executiva", ":material/speed:", None),
            ("pages/01_panorama_geral.py", "Panorama geral", None, "nav_panorama_icon"),
            ("pages/02_outubro_rosa.py", "Outubro Rosa", None, "nav_outubro_icon"),
            ("pages/03_faixa_etaria.py", "Faixa etária", ":material/group:", None),
            ("pages/04_adequabilidade.py", "Adequabilidade", ":material/science:", None),
            ("pages/05_exames_alterados.py", "Exames alterados", None, "nav_exames_icon"),
        ]:
            if nav_key:
                with st.container(key=nav_key):
                    st.page_link(path, label=label)
            else:
                st.page_link(path, label=label, icon=icon)
        st.divider()
        _render_filter_controls()
        st.markdown(
            '<div class="lovable-footer">Fonte: SISCAN/DATASUS · 2020–2025'
            '<br>TCC Engenharia de Software · Informação e Saúde Digital</div>',
            unsafe_allow_html=True,
        )
