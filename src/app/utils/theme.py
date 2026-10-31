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
LIGHT_BG = "#F4F6F8"
PALETTE = [OCEAN, SKY, ORANGE, NAVY]

def apply_custom_css():
    st.markdown("""
    <style>
    h1,h2,h3 {color:#1A3B5C;}
    .block-container {padding-top:1.6rem; max-width:1450px;}
    div[data-testid="stMetric"] {background:#F4F6F8;padding:1rem;border-radius:12px;
       border-left:4px solid #006C9A; min-height:112px;}
    div[data-testid="stMetricLabel"] {color:#1A3B5C;}
    .stButton button[kind="primary"] {background:#EE5325;border-color:#EE5325;}
    div[data-testid="stSidebar"] {border-right:1px solid #D9D9D9;}
    </style>""", unsafe_allow_html=True)

def style_chart(fig, height=430, percent=False):
    fig.update_layout(
        template="plotly_white", font=dict(family="Arial", color=NAVY),
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
