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
    year=st.session_state.get("year_preference", "Todos")
    cities=st.session_state.get("city_preference", list(MUNICIPIOS.values()))
    if year!="Todos" and "ano" in df:
        df=df[df.ano==int(year)]
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

def sidebar_filters():
    """Filtros globais com caixas de seleção de municípios."""
    years=["Todos",*range(2020,2026)]
    cities=list(MUNICIPIOS.values())
    st.session_state.setdefault("year_preference","Todos")
    st.session_state.setdefault("city_preference",cities.copy())
    st.session_state["city_preference"]=[c for c in cities if c in st.session_state["city_preference"]]

    def sync_year():
        st.session_state["year_preference"]=st.session_state["_year_widget"]

    def sync_city(city):
        selected=set(st.session_state["city_preference"])
        if st.session_state["_city_"+city]:
            selected.add(city)
        else:
            selected.discard(city)
        st.session_state["city_preference"]=[c for c in cities if c in selected]

    def set_all(value):
        st.session_state["city_preference"]=cities.copy() if value else []
        for city in cities:
            st.session_state["_city_"+city]=value

    st.session_state["_year_widget"]=st.session_state["year_preference"]

    with st.sidebar:
        logo=Path(__file__).resolve().parents[1]/"assets"/"LogoPET-Saude.jpeg"
        if logo.is_file():
            st.image(str(logo),use_container_width=True)
        st.markdown("### PET-Saúde — Informação e Saúde Digital")
        st.caption("TCC Engenharia de Software")
        st.divider()
        st.caption("Fonte: SISCAN/DATASUS · 2020–2025")

    # Filtros compartilhados no topo, fora da sidebar.
    with st.container():
        left,right=st.columns([1,3],gap="small")
        with left:
            st.selectbox("Ano",years,key="_year_widget",on_change=sync_year)
        with right:
            selected=st.session_state["city_preference"]
            with st.expander(f"Municípios da 10ª CRS ({len(selected)}/{len(cities)})",expanded=False):
                left,right=st.columns(2)
                with left:
                    st.button("Todos",key="city_all",use_container_width=True,on_click=set_all,args=(True,))
                with right:
                    st.button("Limpar",key="city_none",use_container_width=True,on_click=set_all,args=(False,))
                for city in cities:
                    key="_city_"+city
                    if key not in st.session_state:
                        st.session_state[key]=city in selected
                    st.checkbox(city,key=key,on_change=sync_city,args=(city,))
