"""Dashboard executivo SISCAN 10ª CRS — leitura exclusiva das tabelas Gold."""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from utils.theme import apply_custom_css, style_chart, fmt_num, fmt_pct, pct, OCEAN, SKY, ORANGE, NAVY
from utils.data_loader import MUNICIPIOS, filtered, require, sidebar_filters

st.set_page_config(page_title="SISCAN | Painel Analítico 10ª CRS", page_icon="🩺",
                   layout="wide", initial_sidebar_state="expanded")
apply_custom_css()
sidebar_filters()

st.markdown('<h1 style="font-size:1.75rem;margin:0">SISCAN — Painel Analítico 10ª CRS</h1>', unsafe_allow_html=True)
st.caption("10ª Coordenadoria Regional de Saúde do Rio Grande do Sul · Exames citopatológicos do colo do útero")
selected_year = st.session_state.get("year_preference", "Todos")
period = "2020–2025" if selected_year == "Todos" else str(selected_year)
selected_cities = st.session_state.get("city_preference", list(MUNICIPIOS.values()))
st.caption(f"**Recorte ativo:** {period} · {len(selected_cities)} municípios selecionados")

df = filtered("temporal")
if not require(df, ["municipio", "ano", "mes", "quantidade"]):
    st.stop()

alt = filtered("alterados")
alt_ready = not alt.empty and {"quantidade_alterados", "total_exames_validos", "faixa_etaria"}.issubset(alt.columns)

nmonths = df[["ano", "mes"]].drop_duplicates().shape[0]
expected_months = 72 if selected_year == "Todos" else 12
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
    st.metric("Meses com registros", f"{nmonths} de {expected_months}",
              help="Quantidade de meses com registros em relação ao período selecionado.")
with k4:
    st.metric("Exames alterados — estimativa (%)", altered_pct,
              help="Estimativa operacional: denominador inclui exames sem exclusão de rejeitados/insatisfatórios por faixa etária.")
st.caption("**Como é calculada a estimativa de alteração:** exames alterados ÷ total de exames "
           "do denominador disponível na Gold × 100. Esse denominador não exclui de forma "
           "verificável rejeitados e insatisfatórios por faixa etária.")
if selected_year == "Todos" or selected_year == 2022:
    st.warning("**Disponibilidade temporal:** agosto de 2022 não consta na série de exames do SISCAN utilizada.")
st.info(f"**Resumo do recorte:** {fmt_num(total)} exames registrados em {num_cities} municípios; "
        f"registros em {nmonths} dos {expected_months} meses previstos.")
data = df.copy()

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
        # Lacunas de competências não devem ser apresentadas como um zero.
        full_index=pd.date_range("2020-01-01", "2025-12-01", freq="MS")
        if st.session_state.get("year_preference", "Todos") != "Todos":
            year=int(st.session_state["year_preference"])
            full_index=pd.date_range(f"{year}-01-01", f"{year}-12-01",freq="MS")
        wide=monthly.set_index("data").reindex(full_index)
        fig=px.line(x=wide.index, y=wide.quantidade, markers=True,
                    labels={"x":"Competência","y":"Exames"},
                    color_discrete_sequence=[OCEAN])
        fig.update_traces(connectgaps=False, hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>")
        meses_pt = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
        marcacoes = full_index[::2]
        fig.update_xaxes(
            tickmode="array",
            tickvals=marcacoes,
            ticktext=[f"{meses_pt[d.month - 1]}/{str(d.year)[2:]}" for d in marcacoes]
        )
        fig.update_yaxes(tickformat=",d")
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

with st.expander("Sobre os dados e limitações", expanded=False):
    st.write("Fonte: SISCAN/DATASUS, dados consultados na camada Gold do Databricks (2020–2025).")
    st.write("Os volumes representam exames, não mulheres únicas nem cobertura populacional.")
    st.write("Agosto de 2022 está ausente na série histórica; a ausência não deve ser tratada como zero.")
    st.write("A taxa de alteração exibida é uma estimativa operacional, sujeita à limitação do denominador disponível.")
