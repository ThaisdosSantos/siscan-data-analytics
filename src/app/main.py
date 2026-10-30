"""Página inicial e filtros globais do Dashboard SISCAN."""
from pathlib import Path
import streamlit as st
from utils.theme import apply_custom_css, metric_row, fmt_num
from utils.data_loader import MUNICIPIOS, filtered, require

st.set_page_config(page_title="SISCAN | 10ª CRS",page_icon="🩺",layout="wide",initial_sidebar_state="expanded")
apply_custom_css()
with st.sidebar:
    logo=Path(__file__).parent/"assets"/"LogoPET-Saude.jpeg"
    if logo.is_file(): st.image(str(logo),use_container_width=True)
    st.markdown("### PET-Saúde — Informação e Saúde Digital")
    st.caption("TCC Engenharia de Software")
    st.divider()
    st.selectbox("Origem dos dados",["CSV local","Databricks SQL"],key="source")
    st.selectbox("Ano",["Todos",*range(2020,2026)],key="ano_global")
    st.multiselect("Municípios da 10ª CRS",list(MUNICIPIOS.values()),
                   default=list(MUNICIPIOS.values()),key="municipios_global")
    st.caption("Fonte: SISCAN/DATASUS · 2020–2025")
st.title("Exames citopatológicos do colo do útero")
st.markdown("#### Painel analítico — 10ª Coordenadoria Regional de Saúde do Rio Grande do Sul")
st.write("Explore a distribuição municipal e temporal, a campanha Outubro Rosa, a faixa etária, a adequabilidade das amostras e os resultados alterados.")
df=filtered("temporal")
if require(df,["quantidade","municipio","ano","mes"]):
    st.subheader("Panorama do período selecionado")
    total=df.quantidade.sum(min_count=1)
    nmun=df.municipio.nunique()
    nmes=df[["ano","mes"]].drop_duplicates().shape[0]
    metric_row([("Exames registrados",fmt_num(total)),("Municípios com dados",str(nmun)),("Competências registradas",str(nmes))])
else:
    st.warning("A interface está pronta, mas o resumo numérico requer dados da camada Gold.")
st.subheader("Navegação")
pages=[
 ("Panorama geral","pages/01_panorama_geral.py","Evolução mensal e distribuição territorial."),
 ("Outubro Rosa","pages/02_outubro_rosa.py","Comparação setembro–dezembro."),
 ("Faixa etária","pages/03_faixa_etaria.py","Participação da população-alvo."),
 ("Adequabilidade","pages/04_adequabilidade.py","Qualidade das amostras."),
 ("Exames alterados","pages/05_exames_alterados.py","Proporção operacional de alterações.")
]
for title,path,desc in pages:
    a,b=st.columns([2,5])
    with a: st.page_link(path,label=title,icon="📊")
    with b: st.caption(desc)
st.caption("Indicadores descrevem exames registrados, não a cobertura populacional ou o número de mulheres distintas.")
