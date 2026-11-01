"""Visão executiva SISCAN — painel PET-Saúde, dados Gold."""
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.theme import apply_custom_css, fmt_num, fmt_pct, pct, OCEAN, NAVY, ORANGE
from utils.data_loader import (
    MUNICIPIOS, filtered, require, sidebar_filters,
    selected_years, years_label, year_month_index,
)

st.set_page_config(page_title="Visão executiva | SISCAN", page_icon="🩺",
                   layout="wide", initial_sidebar_state="expanded")
apply_custom_css()
sidebar_filters()

st.markdown("""
<style>
.exec-hero{background:linear-gradient(110deg,#1A3B5C,#006C9A);
    border-radius:17px;padding:32px 34px 68px;color:white;margin-bottom:-43px;}
.exec-kicker{font-size:.69rem;letter-spacing:.2em;color:#a8d5eb;font-weight:800}
.exec-title{font-family:Fraunces,Georgia,serif;font-size:clamp(1.7rem,3.2vw,2.9rem);
    font-weight:650;line-height:1.13;margin:10px 0;color:#fff!important;max-width:770px}
.exec-title em{font-style:italic;color:#c0d9eb;}
.exec-sub{font-size:.82rem;color:#d8e7ef;margin:12px 0 17px}
.exec-pill{display:inline-block;border:1px solid #547e9d;border-radius:20px;
    padding:5px 12px;font-size:.7rem;color:#f3f8fb}
.exec-metric{background:#fff;border:1px solid #dae4ec;border-radius:12px;
    height:124px;box-sizing:border-box;padding:20px 17px;box-shadow:0 6px 18px -12px #193c5d33;}
.exec-metric.blue{background:#fff;color:#1A3B5C;border-color:#dae4ec}
.exec-metric.orange{background:#fff;color:#1A3B5C;border-color:#dae4ec}
.exec-metric-label{font-size:.67rem;font-weight:800;letter-spacing:.04em;color:#59728a}
.exec-metric.blue .exec-metric-label,.exec-metric.orange .exec-metric-label{color:#59728a}
.exec-metric-value{font-family:Fraunces,Georgia,serif;font-size:clamp(1.35rem,2vw,2.1rem);
    font-weight:650;margin:7px 0;color:#1A3B5C}
.exec-metric.blue .exec-metric-value,.exec-metric.orange .exec-metric-value{color:#1A3B5C}
.exec-metric-desc{font-size:.68rem;color:#72879d}
.exec-warning{border:1px solid #f6a381;border-left:4px solid #EE5325;border-radius:11px;
    padding:13px 16px;margin:17px 0;background:#fff;color:#1A3B5C;font-size:.78rem}
.exec-card-title{font-family:Fraunces,Georgia,serif;color:#1A3B5C;font-size:1.2rem;margin:0;font-weight:650}
.exec-card-sub{font-size:.75rem;color:#8499ad;margin:3px 0 0}
.exec-card{background:#fff;border:1px solid #dfe6ed;border-radius:14px;
    padding:18px 16px 14px;box-shadow:0 6px 20px -17px #1a3b5c55;}
.exec-links{display:block;border:1px solid #dbe4ec;border-radius:13px;
    padding:16px 16px;background:white;min-height:78px}
.exec-links strong{display:block;color:#1A3B5C;font-family:Fraunces,Georgia,serif}
.exec-links small{display:block;color:#72879d;font-size:.7rem;margin-top:3px}
.st-key-exec-bubble-card [data-testid="stPlotlyChart"],
.st-key-exec-month-card [data-testid="stPlotlyChart"]{border:none!important;
    box-shadow:none!important;background:transparent!important;padding:0!important}
.st-key-exec-bubble-card,.st-key-exec-month-card{border-radius:14px!important;background:white!important}
@media(max-width:850px){
  .exec-hero{padding:24px 18px 48px;margin-bottom:0;}
  .exec-metric{height:124px;}
}
@media(max-width:600px){
  .exec-title{font-size:clamp(1.55rem,6vw,2.1rem);}
  .exec-hero{padding:20px 16px 28px;}
  .exec-metric{height:auto;min-height:112px;padding:16px;}
  .exec-card-title{font-size:1.05rem;}
  .exec-warning{padding:11px 12px;}
  .exec-links{min-height:76px;}
}


.st-key-exec-ranking-card [data-testid="stPlotlyChart"]{
  border:none!important;box-shadow:none!important;padding:0!important;background:transparent!important;
}
.st-key-exec-ranking-card {border-radius:14px!important;background:white!important;}
@media (max-width:768px) {
  .st-key-exec-ranking-card,.st-key-exec-month-card {min-width:0;}
}
/* Ajuda compacta dentro dos KPIs, sem botões adicionais abaixo. */
.exec-metric {position:relative;overflow:visible;}
.exec-metric-help {position:absolute;right:12px;top:12px;z-index:10;}
.exec-metric-help summary {list-style:none;cursor:pointer;display:grid;place-items:center;
  width:21px;height:21px;border-radius:50%;border:1px solid #90a7b9;
  color:#43647f;font:bold 13px Arial,sans-serif;background:#f3f7fa;}
.exec-metric-help summary::-webkit-details-marker {display:none;}
.exec-metric-help summary:focus-visible {outline:2px solid #006C9A;outline-offset:3px;}
.exec-metric-tip {position:absolute;right:0;top:28px;width:min(255px,70vw);
  padding:11px 13px;border:1px solid #d8e3eb;border-radius:9px;
  background:#fff;color:#1A3B5C;font:500 .77rem/1.55 Manrope,Arial,sans-serif;
  box-shadow:0 8px 24px rgba(26,59,92,.2);z-index:20;}
/* Cartões executivos: fundo branco e traço de destaque lateral. */
.exec-metric,.exec-metric.blue,.exec-metric.orange{
  background:#fff!important;color:#1A3B5C!important;
  border:1px solid #e2e8ee!important;border-left:5px solid #006C9A!important;
  border-radius:10px;height:124px;box-sizing:border-box;
  box-shadow:0 3px 12px rgba(26,59,92,.07);
}
.exec-metric.orange{border-left-color:#EE5325!important;}
.exec-metric .exec-metric-label,.exec-metric.blue .exec-metric-label,
.exec-metric.orange .exec-metric-label{color:#60758a!important;}
.exec-metric .exec-metric-value,.exec-metric.blue .exec-metric-value,
.exec-metric.orange .exec-metric-value{color:#1A3B5C!important;}
.exec-metric-desc,.exec-metric.orange .exec-metric-desc{color:#8192a5!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="exec-hero">
  <div class="exec-kicker">VISÃO EXECUTIVA · 10ª CRS · RS</div>
  <h1 class="exec-title">Rastreamento do câncer do colo do útero,
  <em>território a território.</em></h1>
  <div class="exec-sub">Exames citopatológicos do colo do útero · 2020–2025 · SISCAN/DATASUS</div>
  <span class="exec-pill">Recorte ativo: """ + html.escape(years_label()) +
  """ · """ + str(len(st.session_state.get("city_preference", list(MUNICIPIOS.values())))) +
  """ de 11 municípios</span>
</div>
""", unsafe_allow_html=True)

df = filtered("temporal")
if not require(df, ["municipio", "ano", "mes", "quantidade"]):
    st.stop()

alt = filtered("alterados")
months = df[["ano", "mes"]].drop_duplicates().shape[0]
total = df["quantidade"].sum(min_count=1)
num_cities = df["municipio"].nunique()
if not alt.empty and {"quantidade_alterados", "total_exames_validos"}.issubset(alt.columns):
    altered = alt["quantidade_alterados"].sum(min_count=1)
    denominator = alt["total_exames_validos"].sum(min_count=1)
    altered_pct = fmt_pct(pct(altered, denominator))
else:
    altered_pct = "N/D"

kpis = [
    ("EXAMES REGISTRADOS", fmt_num(total), "blue"),
    ("MUNICÍPIOS COM REGISTROS", f"{num_cities} de 11", ""),
    ("MESES COM REGISTROS", f"{months} de {12 * len(selected_years())}", ""),
    ("EXAMES ALTERADOS", altered_pct, "orange"),
]
for col, (label, value, color) in zip(st.columns(4, gap="small"), kpis):
    with col:
        desc = '<div class="exec-metric-desc">Estimativa operacional</div>' if color == "orange" else ""
        hint = ""
        if label == "MESES COM REGISTROS":
            explanation = "Competência 08/2022 sem registros"
            hint = ('<details class="exec-metric-help"><summary aria-label="Explicação sobre os meses" title="Entenda os meses">!</summary>'
                    '<div class="exec-metric-tip">' + html.escape(explanation) + '</div></details>')
        st.markdown(
            '<div class="exec-metric ' + color + '"><div class="exec-metric-label">'
            + html.escape(label) + '</div>' + hint
            + '<div class="exec-metric-value">' + html.escape(value)
            + '</div>' + desc + '</div>',
            unsafe_allow_html=True,
        )

# Ausência de registro não é equivalente a zero.
calendar = pd.DatetimeIndex([d for d in year_month_index() if d.year in selected_years()])
monthly = df.groupby(["ano", "mes"], as_index=False)["quantidade"].sum(min_count=1)
monthly["data"] = pd.to_datetime(dict(year=monthly["ano"], month=monthly["mes"], day=1))
series = monthly.set_index("data")["quantidade"].reindex(calendar)
missing = [d.strftime("%m/%Y") for d in calendar if pd.isna(series.loc[d])]
audit = ("Competências sem registros: " + ", ".join(missing) + ". " if missing else "")
st.markdown(
    '<div class="exec-warning">⚠️ <b>Auditoria temporal:</b> '
    + html.escape(audit)
    + 'Os ' + html.escape(fmt_num(total)) + ' exames são procedimentos registrados em '
    + str(months) + ' competências, não mulheres únicas rastreadas. '
    + 'A taxa de alteração é uma estimativa operacional, não um indicador clínico validado.</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div style="margin:20px 0 12px;color:#1A3B5C;font-weight:750;font-size:1.1rem">'
    'Panorama executivo do período</div>',
    unsafe_allow_html=True,
)
city = (df.groupby("municipio", as_index=False)["quantidade"]
        .sum(min_count=1).sort_values("quantidade", ascending=True))
left, right = st.columns([3, 2], gap="medium")
with left:
    with st.container(border=True, key="exec-month-card"):
        st.markdown('<div class="exec-card-title">Evolução mensal de exames</div>'
                    '<div class="exec-card-sub">Competência × exames registrados</div>',
                    unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(
            x=calendar, y=series, mode="lines",
            line=dict(color=OCEAN, width=2.3),
            fill="tozeroy", fillcolor="rgba(0,108,154,.09)",
            connectgaps=False,
            hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>",
        ))
        fig.update_layout(height=445, showlegend=False,
                          margin=dict(l=15, r=12, t=25, b=22),
                          plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color=NAVY))
        fig.update_yaxes(gridcolor="#e9eff3", rangemode="tozero")
        fig.update_xaxes(showgrid=False, tickformat="%m/%Y", nticks=7)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with right:
    with st.container(border=True, key="exec-ranking-card"):
        st.markdown('<div class="exec-card-title">Volume por município</div>'
                    '<div class="exec-card-sub">11 municípios da 10ª CRS · exames registrados</div>',
                    unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=city["quantidade"], y=city["municipio"], orientation="h",
            marker=dict(color=OCEAN),
            hovertemplate="%{y}<br>%{x:,.0f} exames<extra></extra>",
        ))
        fig.update_layout(height=445, showlegend=False,
                          margin=dict(l=8, r=18, t=25, b=22),
                          plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color=NAVY, size=10), bargap=.28)
        fig.update_yaxes(automargin=True, showgrid=False, title=None)
        fig.update_xaxes(gridcolor="#e9eff3", title=None, rangemode="tozero")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
