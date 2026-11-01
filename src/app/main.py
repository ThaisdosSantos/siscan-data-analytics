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
            explanation = "Agosto/2022 está ausente"
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
    + 'A taxa de alteração é uma estimativa operacional, não um indicador clínico validado.</div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1, 1.45], gap="medium")
with left:
    with st.container(border=True, key="exec-bubble-card"):
        st.markdown('<div class="exec-card-title">Visualização territorial</div>'
                    '<div class="exec-card-sub">Bolhas proporcionais ao volume de exames</div>',
                    unsafe_allow_html=True)
        city = (df.groupby("municipio", as_index=False)["quantidade"]
                .sum(min_count=1).sort_values("municipio"))
        # Coordenadas fixas e regra de conexões do diagrama territorial.
        # Uma aresta existe para cada par com distância euclidiana < 34.
        # São posições visuais, não coordenadas geográficas.
        territories = [
            ("Uruguaiana", 12, 46),
            ("Alegrete", 42, 40),
            ("Sant'Ana do Livramento", 50, 84),
            ("São Gabriel", 82, 44),
            ("Itaqui", 20, 16),
            ("Rosário do Sul", 66, 62),
            ("Quaraí", 26, 76),
            ("Manoel Viana", 54, 18),
            ("Barra do Quaraí", 6, 70),
            ("Santa Margarida do Sul", 90, 66),
            ("Maçambará", 34, 8),
        ]
        totals = city.set_index("municipio")["quantidade"]
        visible = set(totals.index)
        selected = set(st.session_state.get("city_preference", list(MUNICIPIOS.values())))
        fig = go.Figure()

        # A rede é independente da seleção; apenas a cor indica desativação.
        xs, ys = [], []
        for i, (_, ax, ay) in enumerate(territories):
            for _, bx, by in territories[i + 1:]:
                if ((ax - bx)**2 + (ay - by)**2)**0.5 < 34:
                    xs.extend([ax, bx, None])
                    ys.extend([ay, by, None])
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", showlegend=False, hoverinfo="skip",
            line=dict(color="#d7e0e8", width=1.0),
        ))

        # O tamanho reflete os volumes da Gold. Círculos desativados ficam esmaecidos.
        max_vol = max(1, float(totals.max()) if not totals.empty else 1)
        for municipality, x, y in territories:
            volume = float(totals.loc[municipality]) if municipality in visible else 0.0
            enabled = municipality in selected
            radius = 2.5 + (volume / max_vol)**0.5 * 11
            size = radius * 6.2
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode="markers",
                marker=dict(
                    size=size,
                    color="rgba(0,108,154,0.25)" if enabled else "rgba(160,175,190,0.20)",
                    line=dict(color=OCEAN if enabled else "#b9c4cf", width=1.2),
                ),
                customdata=[[municipality, volume]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} exames<extra></extra>",
                showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode="markers",
                marker=dict(size=6, color=ORANGE if enabled else "#9daeba"),
                hoverinfo="skip", showlegend=False,
            ))

        fig.update_xaxes(visible=False, range=[-9, 109], fixedrange=True,
                         constrain="domain")
        # SVG original usa origem no canto superior esquerdo.
        fig.update_yaxes(visible=False, range=[109, -9], fixedrange=True,
                         scaleanchor="x", scaleratio=1)
        fig.update_layout(
            height=330, margin=dict(l=3, r=3, t=5, b=5),
            plot_bgcolor="#f4f6f8", paper_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(bgcolor="white", font_color=NAVY),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Passe o mouse sobre uma bolha para consultar o município.")

with right:
    with st.container(border=True, key="exec-month-card"):
        st.markdown('<div class="exec-card-title">Evolução mensal de exames</div>'
                    '<div class="exec-card-sub">Competência × exames registrados</div>',
                    unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(
            x=calendar, y=series, mode="lines",
            line=dict(color=OCEAN, width=2),
            fill="tozeroy", fillcolor="rgba(0,108,154,.08)",
            connectgaps=False,
            hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>",
        ))
        fig.update_layout(height=370, showlegend=False,
                          margin=dict(l=14,r=10,t=22,b=20),
                          plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(gridcolor="#e9eff3", rangemode="tozero")
        fig.update_xaxes(showgrid=False, tickformat="%m/%Y", nticks=7)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# Três cartões de navegação completos: link nativo sobre toda a área do cartão.
st.markdown("""
<style>
.exec-nav-subtitle{color:#72879d;font-size:.76rem;margin-top:1px;pointer-events:none;line-height:1.35;}
.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados{
  position:relative;background:#fff;border:1px solid #d7dde3;border-radius:13px;
  padding:15px 16px;min-height:78px;box-shadow:0 3px 9px rgba(26,59,92,.07);
  transition:border-color .15s,box-shadow .15s,transform .15s;
}
.st-key-exec-nav-panorama:hover,.st-key-exec-nav-outubro:hover,.st-key-exec-nav-alterados:hover{
  border-color:#EE5325;box-shadow:0 7px 20px rgba(26,59,92,.13);transform:translateY(-1px);
}
.st-key-exec-nav-panorama [data-testid="stPageLink"] a,
.st-key-exec-nav-outubro [data-testid="stPageLink"] a,
.st-key-exec-nav-alterados [data-testid="stPageLink"] a{
  position:static!important;display:block!important;color:#1A3B5C!important;
  text-decoration:none!important;font-family:Fraunces,Georgia,serif;
  font-size:1rem;font-weight:650;line-height:1.3;
  padding:0!important;margin:0!important;background:transparent!important;
}
.st-key-exec-nav-panorama [data-testid="stPageLink"] a::after,
.st-key-exec-nav-outubro [data-testid="stPageLink"] a::after,
.st-key-exec-nav-alterados [data-testid="stPageLink"] a::after {
  content:"";position:absolute;inset:0;z-index:2;cursor:pointer;
}
.st-key-exec-nav-panorama::after,.st-key-exec-nav-outubro::after,
.st-key-exec-nav-alterados::after{
  content:"→";position:absolute;right:16px;top:50%;
  transform:translateY(-50%);color:#EE5325;font-size:1.35rem;
  font-weight:500;pointer-events:none;
}
.st-key-exec-nav-panorama [data-testid="stPageLink"] a,
.st-key-exec-nav-outubro [data-testid="stPageLink"] a,
.st-key-exec-nav-alterados [data-testid="stPageLink"] a {
  padding-right:35px!important;
}
.st-key-exec-nav-panorama [data-testid="stPageLink"],
.st-key-exec-nav-outubro [data-testid="stPageLink"],
.st-key-exec-nav-alterados [data-testid="stPageLink"] {margin:0!important;}
.st-key-exec-nav-panorama .stCaptionContainer,
.st-key-exec-nav-outubro .stCaptionContainer,
.st-key-exec-nav-alterados .stCaptionContainer{margin-top:2px!important;}
</style>
""", unsafe_allow_html=True)
nav = [
    ("Panorama geral", "Volume por competência e município",
     "pages/01_panorama_geral.py", "exec-nav-panorama"),
    ("Outubro Rosa", "Setembro × outubro e meses seguintes",
     "pages/02_outubro_rosa.py", "exec-nav-outubro"),
    ("Exames alterados", "Pico de alterações por faixa etária",
     "pages/05_exames_alterados.py", "exec-nav-alterados"),
]
for col, (title, subtitle, page, key) in zip(st.columns(3, gap="medium"), nav):
    with col:
        with st.container(key=key):
            st.page_link(page, label=title, use_container_width=True)
            st.markdown('<div class="exec-nav-subtitle">' + html.escape(subtitle)
                        + '</div>', unsafe_allow_html=True)

st.caption("Fonte: SISCAN/DATASUS · Databricks camada Gold. "
           "Volumes representam exames registrados, não mulheres únicas ou cobertura populacional. "
           "As bolhas e linhas são um diagrama ilustrativo, sem representar coordenadas ou conexões geográficas.")
