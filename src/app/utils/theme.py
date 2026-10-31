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
    """Estilo inspirado no protótipo siscan_streamlit.zip, com dados Gold preservados."""
    st.markdown("""
    <style>
    :root {--navy:#1A3B5C;--ocean:#006C9A;--sky:#4A9FD8;
           --orange:#EE5325;--gray:#D9D9D9;--light:#F4F6F8;}
    .block-container {padding-top:1.35rem;max-width:1510px;padding-left:2rem;padding-right:2rem;}
    h1,h2,h3,h4 {color:var(--navy)!important;letter-spacing:-.018em;}
    h1 {font-size:2rem!important;margin-bottom:.4rem!important;}
    h3 {font-size:1.2rem!important;}
    .pet-kicker {color:var(--orange);font-size:.79rem;font-weight:750;
                 letter-spacing:.12em;text-transform:uppercase;margin-bottom:.35rem;}
    .pet-note {background:var(--light);border-left:4px solid var(--orange);
               border-radius:10px;padding:13px 16px;color:var(--navy);
               margin:10px 0 18px;line-height:1.55;}
    .pet-highlight {background:var(--light);border-left:4px solid var(--orange);
                    border-radius:14px;padding:17px 20px;color:var(--navy);
                    font-size:1.06rem;margin:12px 0 20px;line-height:1.55;}
    .pet-section-label {color:var(--orange);font-weight:750;letter-spacing:.1em;font-size:.75rem;}
    [data-testid="stSidebar"] {background:#F4F6F8;border-right:1px solid var(--gray);}
    [data-testid="stSidebar"] [data-testid="stImage"] {max-width:195px;margin:0 auto;}
    [data-testid="stSidebar"] h3 {font-size:.94rem!important;}
    [data-testid="stSidebar"] .stCaption {font-size:.78rem;}
    [data-testid="stMetric"] {background:var(--light);border:1px solid var(--gray);
       border-left:4px solid var(--ocean);border-radius:14px;padding:14px 18px;min-height:112px;}
    [data-testid="stMetricLabel"] {color:var(--navy);font-weight:550;}
    [data-testid="stMetricValue"] {color:var(--navy);font-weight:700;}
    [data-testid="stExpander"] {border-color:var(--gray);border-radius:10px;}
    [data-testid="stDataFrame"] {border:1px solid var(--gray);border-radius:10px;}
    .stButton button[kind="primary"] {background:var(--ocean);border-color:var(--ocean);color:white;}
    @media(max-width:850px) {.block-container {padding-left:1rem;padding-right:1rem;}}
    </style>""", unsafe_allow_html=True)


def page_header(kicker, title, description=""):
    """Cabeçalho editorial do protótipo, usado pelas páginas reais."""
    st.markdown(f'<div class="pet-kicker">{html.escape(str(kicker))}</div>', unsafe_allow_html=True)
    st.title(title)
    if description:
        st.caption(description)


def note(message, highlight=False):
    css = "pet-highlight" if highlight else "pet-note"
    st.markdown(f'<div class="{css}">{html.escape(str(message))}</div>', unsafe_allow_html=True)


def style_chart(fig, height=430, percent=False):
    fig.update_layout(
        template="plotly_white", font=dict(family="Arial", color=NAVY),
        colorway=PALETTE,
        margin=dict(l=15,r=15,t=30,b=20), height=height,
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
