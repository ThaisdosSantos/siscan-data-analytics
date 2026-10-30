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
    if not all([host,path,token]): return pd.DataFrame()
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
        st.warning(f"Não foi possível consultar {name}: {type(exc).__name__}. Verifique a configuração e a disponibilidade.")
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
    return st.session_state.get("source","CSV local")

def filtered(table_key):
    df=load_table(table_key,selected_source())
    if df.empty: return df
    year=st.session_state.get("ano_global","Todos")
    cities=st.session_state.get("municipios_global",list(MUNICIPIOS.values()))
    if year!="Todos" and "ano" in df: df=df[df.ano==int(year)]
    if "municipio" in df: df=df[df.municipio.isin(cities)]
    return df.copy()

def require(df,columns):
    if df.empty:
        st.info("Não há dados Gold disponíveis para os filtros selecionados. Configure a conexão Databricks SQL ou adicione os CSVs em data/3_gold/.")
        return False
    missing=[c for c in columns if c not in df]
    if missing:
        st.warning("Colunas ausentes na tabela Gold: "+", ".join(missing))
        return False
    return True

def sidebar_filters():
    """Recria controles em todas as páginas e preserva valores na navegação."""
    from pathlib import Path
    def keep(key):
        st.session_state["saved_"+key]=st.session_state[key]
    def restore(key,default):
        if key not in st.session_state:
            st.session_state[key]=st.session_state.get("saved_"+key,default)
    with st.sidebar:
        logo=Path(__file__).resolve().parents[1]/"assets"/"LogoPET-Saude.jpeg"
        if logo.is_file(): st.image(str(logo),use_container_width=True)
        st.markdown("### PET-Saúde — Informação e Saúde Digital")
        st.caption("TCC Engenharia de Software")
        st.divider()
        restore("source","CSV local")
        st.selectbox("Origem dos dados",["CSV local","Databricks SQL"],key="source",on_change=keep,args=("source",))
        restore("ano_global","Todos")
        st.selectbox("Ano",["Todos",*range(2020,2026)],key="ano_global",on_change=keep,args=("ano_global",))
        restore("municipios_global",list(MUNICIPIOS.values()))
        st.multiselect("Municípios da 10ª CRS",list(MUNICIPIOS.values()),key="municipios_global",
                       on_change=keep,args=("municipios_global",))
        st.caption("Fonte: SISCAN/DATASUS · 2020–2025")
