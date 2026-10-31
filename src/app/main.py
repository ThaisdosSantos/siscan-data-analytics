"""Dashboard executivo SISCAN 10ª CRS — leitura exclusiva das tabelas Gold."""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from utils.theme import apply_custom_css, style_chart, fmt_num, fmt_pct, pct, OCEAN, SKY, ORANGE, NAVY
from utils.data_loader import MUNICIPIOS, filtered, require, sidebar_filters, selected_years, years_label, year_month_index

st.set_page_config(page_title="SISCAN | Painel Analítico 10ª CRS", page_icon="🩺",
                   layout="wide", initial_sidebar_state="expanded")
apply_custom_css()
sidebar_filters()

logo = Path(__file__).parent / "assets" / "LogoPET-Saude.jpeg"
head, mark = st.columns([7, 1], vertical_alignment="center")
with head:
    st.markdown('<h1 style="font-size:1.75rem;margin:0">SISCAN — Painel Analítico 10ª CRS</h1>',
                unsafe_allow_html=True)
    st.caption("Exames citopatológicos do colo do útero · 2020–2025 · SISCAN/DATASUS")
with mark:
    if logo.is_file():
        st.image(str(logo), use_container_width=True)

# Os filtros globais (ano e municípios) permanecem na barra lateral.
# Filtros rápidos abaixo refinam apenas os gráficos da página principal e
# a taxa de alteração; a Gold não dispõe de cruzamento idade x competência.
col_city, col_age = st.columns([1.4, 1])
with col_city:
    city_focus = st.selectbox("Visualização territorial", ["Todos os municípios", *MUNICIPIOS.values()],
                              help="Refina somente os gráficos desta página.")
with col_age:
    age_focus = st.selectbox("Faixa etária · taxa de alteração",
                             ["Todas as idades", "25–64 anos", "Menores de 25", "65 anos ou mais"],
                             help="Filtro aplicável apenas ao indicador de exames alterados; não à série temporal.")

st.caption(f"**Anos selecionados:** {years_label()}")
df = filtered("temporal")
if not require(df, ["municipio", "ano", "mes", "quantidade"]):
    st.stop()

alt = filtered("alterados")
alt_ready = not alt.empty and {"quantidade_alterados", "total_exames_validos", "faixa_etaria"}.issubset(alt.columns)

def age_start(label):
    text = str(label).lower().strip()
    import re
    if "ate" in text or "até" in text:
        return 0
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else None

def in_age_group(label, selection):
    age = age_start(label)
    if age is None:
        return selection == "Todas as idades"
    return (selection == "Todas as idades"
            or selection == "25–64 anos" and 25 <= age <= 64
            or selection == "Menores de 25" and age < 25
            or selection == "65 anos ou mais" and age >= 65)

if alt_ready and age_focus != "Todas as idades":
    alt = alt[alt.faixa_etaria.map(lambda v: in_age_group(v, age_focus))]

nmonths = df[["ano", "mes"]].drop_duplicates().shape[0]
total = df.quantidade.sum(min_count=1)
num_cities = df.municipio.nunique()
if alt_ready:
    altered = alt.quantidade_alterados.sum(min_count=1)
    denominator = alt.total_exames_validos.sum(min_count=1)
    altered_pct = fmt_pct(pct(altered, denominator)) if pd.notna(denominator) else "N/D"
else:
    altered_pct = "N/D"

st.markdown('<div class="pet-section-label">VISÃO EXECUTIVA</div>', unsafe_allow_html=True)
k1,k2,k3,k4=st.columns(4, gap="small")
with k1:
    st.metric("Exames registrados", fmt_num(total))
with k2:
    st.metric("Municípios com registros", f"{num_cities} de 11")
with k3:
    st.metric("Meses com registros", f"{nmonths} de 72",
              help="Agosto de 2022 não está disponível na Gold temporal.")
with k4:
    st.metric("Exames alterados (%)", altered_pct,
              help="Estimativa operacional: denominador inclui exames sem exclusão de rejeitados/insatisfatórios por faixa etária.")
st.caption("⚠️ **Auditoria temporal:** agosto/2022 ausente da série Gold. "
           "A taxa de alteração é uma estimativa operacional, não um indicador clínico validado.")
if age_focus != "Todas as idades":
    st.caption("O filtro de faixa etária afeta apenas a taxa de alteração; a Gold temporal não oferece cruzamento por idade.")

data = df.copy()
if city_focus != "Todos os municípios":
    data = data[data.municipio == city_focus]

monthly = data.groupby(["ano", "mes"], as_index=False).quantidade.sum(min_count=1)
monthly["data"] = pd.to_datetime(dict(year=monthly.ano, month=monthly.mes, day=1))
monthly = monthly.sort_values("data")
by_city = data.groupby("municipio", as_index=False).quantidade.sum(min_count=1)
by_city = by_city.sort_values("quantidade", ascending=True)

left, right = st.columns([3,2], gap="medium")
with left:
    st.markdown("#### Evolução mensal de exames")
    if monthly.empty:
        st.info("Sem exames para o município selecionado.")
    else:
        fig=px.line(monthly, x="data", y="quantidade", markers=True,
                    color_discrete_sequence=[OCEAN],
                    labels={"data":"Competência","quantidade":"Exames"})
        # Lacunas de competências não devem ser apresentadas como um zero.
        full_index = year_month_index()
        wide=monthly.set_index("data").reindex(full_index)
        fig=px.line(x=wide.index, y=wide.quantidade, markers=True,
                    labels={"x":"Competência","y":"Exames"},
                    color_discrete_sequence=[OCEAN])
        fig.update_traces(connectgaps=False, hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>")
        fig.update_layout(showlegend=False, height=365)
        st.plotly_chart(style_chart(fig, height=365), use_container_width=True)
with right:
    st.markdown("#### Volume por município")
    if by_city.empty:
        st.info("Nenhuma observação disponível.")
    else:
        fig=px.bar(by_city, x="quantidade", y="municipio", orientation="h",
                   color_discrete_sequence=[SKY],
                   labels={"quantidade":"Exames","municipio":""})
        fig.update_traces(hovertemplate="%{y}<br>%{x:,.0f} exames<extra></extra>")
        fig.update_layout(showlegend=False, height=365, margin=dict(l=10,r=15,t=12,b=25))
        st.plotly_chart(style_chart(fig,height=365),use_container_width=True)

st.caption("Fonte: Databricks · camada Gold, somente leitura. "
           "Os volumes representam exames registrados, não mulheres únicas ou cobertura populacional.")
