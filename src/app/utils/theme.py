"""Identidade visual PET-Saúde e funções comuns de apresentação."""
import html
import io
import streamlit as st
import plotly.express as px

NAVY = "#1A3B5C"
OCEAN = "#006C9A"
SKY = "#4A9FD8"
ORANGE = "#EE5325"
GRAY = "#D9D9D9"
LIGHT_BG = "#F6F8FA"
PALETTE = [OCEAN, SKY, ORANGE, NAVY]

def apply_custom_css():
    """Aparência unificada conforme paleta PET-Saúde."""
    st.markdown("""
    <style>
    :root {
      --pet-navy:#1A3B5C; --pet-ocean:#006C9A; --pet-sky:#4A9FD8;
      --pet-orange:#EE5325; --pet-gray:#D9D9D9; --pet-light:#F6F8FA;
    }
    .block-container {padding-top:1.15rem;max-width:1680px;padding-left:1.7rem;padding-right:1.7rem;}
    .pet-section-label {font-size:.72rem;font-weight:750;color:#006C9A;
        letter-spacing:.11em;margin:.5rem 0 .55rem;}
    @media(max-width:900px) {.block-container {padding-left:.8rem;padding-right:.8rem;}}
    h1,h2,h3,h4 {color:var(--pet-navy)!important;letter-spacing:-.02em;}
    a {color:var(--pet-ocean);}
    div[data-testid="stSidebar"] {
        background:linear-gradient(180deg,#FFFFFF 0%,#F6F8FA 100%);
        border-right:1px solid var(--pet-gray);
    }
    div[data-testid="stSidebar"] h3 {color:var(--pet-navy)!important;}
    div[data-testid="stMetric"] {
        background:var(--pet-light);padding:1rem 1.1rem;border-radius:13px;
        border:1px solid #E6ECF1;border-left:4px solid var(--pet-ocean);
        min-height:105px;
    }
    div[data-testid="stMetric"]:has([data-testid="stMetricLabel"] [title*="alterados"]) {border-left-color:#EE5325;}
    div[data-testid="stMetric"]:has([data-testid="stMetricLabel"] [title*="Meses"]) {border-left-color:#EE5325;}
    div[data-testid="stMetricLabel"] {color:var(--pet-navy);}
    div[data-testid="stMetricValue"] {color:var(--pet-navy);font-weight:650;}
    .stButton button[kind="primary"],.stDownloadButton button[kind="primary"] {
        background:var(--pet-orange);border-color:var(--pet-orange);color:#fff;
    }
    .stButton button:hover,.stDownloadButton button:hover {
        border-color:var(--pet-orange);color:var(--pet-orange);
    }
    [data-testid="stExpander"] {border-color:var(--pet-gray);border-radius:11px;}
    div[data-testid="stDataFrame"] {border:1px solid var(--pet-gray);border-radius:10px;}
    </style>""", unsafe_allow_html=True)

def style_chart(fig, height=430, percent=False):
    fig.update_layout(
        template="plotly_white", font=dict(family="Arial", color=NAVY),
        colorway=PALETTE,
        margin=dict(l=15,r=15,t=45,b=20), height=height,
        hoverlabel=dict(bgcolor="white",font_color=NAVY),
        legend_title_text="", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e9edf1")
    return fig

def format_percent_chart(fig, axis="y"):
    """Formata percentuais nos eixos e no tooltip sem arredondar os cálculos."""
    if axis == "y":
        fig.update_yaxes(tickformat=".2f", ticksuffix="%")
        fig.update_traces(hovertemplate="%{x}<br>%{y:.2f}%<extra>%{fullData.name}</extra>")
    elif axis == "x":
        fig.update_xaxes(tickformat=".2f", ticksuffix="%")
        fig.update_traces(hovertemplate="%{y}<br>%{x:.2f}%<extra>%{fullData.name}</extra>")
    return fig

def display_chart(fig):
    st.plotly_chart(style_chart(fig), use_container_width=True)

def metric_row(items):
    cols = st.columns(len(items))
    for col, (label,value) in zip(cols,items):
        col.metric(label,value)

def export_table(df, name):
    """Duas casas nas colunas percentuais; CSV preserva valores originais."""
    from pandas.api.types import is_numeric_dtype
    config = {}
    for column in df.columns:
        lower = column.lower()
        is_percentage = (
            lower in {"percentual", "taxa", "variacao_pct"}
            or lower.endswith(("_pct", "_percentual", "_percentual_pct"))
            or lower.startswith(("taxa_", "proporcao_"))
        )
        if is_percentage and is_numeric_dtype(df[column]):
            config[column] = st.column_config.NumberColumn(column, format="%.2f")
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=config)
    st.download_button("⬇️ Exportar CSV", df.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name=name, mime="text/csv", key="csv_"+name)

def fmt_num(v):
    return f"{int(v):,}".replace(",", ".")

def fmt_pct(v):
    if v is None or v != v: return "N/D"
    return f"{v:.2f}%".replace(".", ",")

def pct(n, d):
    return 100*n/d if d and d > 0 else float("nan")
