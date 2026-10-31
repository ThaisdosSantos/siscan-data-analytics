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
    """Identidade Lovable: sidebar escura, hero em gradiente e cartões claros."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
    html,body,[data-testid="stAppViewContainer"] {font-family:'Manrope',system-ui,sans-serif;}
    .pet-hero-title,h1,h2,h3 {font-family:'Fraunces',Georgia,serif;}
    :root {--navy:#1A3B5C;--ocean:#006C9A;--sky:#4A9FD8;
           --orange:#EE5325;--gray:#D9D9D9;--light:#F4F6F8;}
    html,body,[data-testid="stAppViewContainer"] {background:#fff;color:#1A3B5C;}
    .block-container {padding:1.25rem 2.1rem 3rem;max-width:1480px;}
    h1,h2,h3,h4 {color:var(--navy)!important;letter-spacing:-.015em;}
    h2,h3 {font-weight:730!important;}
    .pet-hero {background:radial-gradient(120% 140% at 100% 0%,#006C9A 0%,#1A3B5C 66%);
        border-radius:19px;padding:36px 40px 74px;color:white;
        box-shadow:0 16px 36px -22px rgba(26,59,92,.35);margin:0 0 -43px;}
    .pet-hero-kicker {font-weight:750;letter-spacing:.22em;color:#89c8ee;
        font-size:.71rem;text-transform:uppercase;margin:0 0 13px;}
    .pet-hero-title {color:#fff!important;font-size:clamp(1.8rem,3.4vw,3rem);
        font-weight:760;line-height:1.13;letter-spacing:-.035em;margin:0 0 12px;}
    .pet-hero-desc {color:#d7e7f4;font-size:.95rem;line-height:1.5;max-width:740px;}
    .pet-kicker {color:var(--orange);font-size:.73rem;font-weight:780;
                 letter-spacing:.13em;text-transform:uppercase;}
    .pet-note,.pet-highlight {background:#F4F6F8;border-radius:14px;padding:16px 20px;
        border-left:4px solid var(--orange);line-height:1.6;margin:12px 0 20px;}
    .pet-section-label {color:var(--ocean);font-size:.73rem;font-weight:780;letter-spacing:.12em;}
    [data-testid="stSidebar"] {background:#1A3B5C!important;border-right:0!important;color:#e8f3fa;}
    [data-testid="stSidebar"] * {color:#e8f3fa;}
    [data-testid="stSidebar"] [data-testid="stImage"] {background:white;padding:8px;
         border-radius:14px;margin:4px auto 16px;max-width:220px;}
    [data-testid="stSidebar"] [data-testid="stExpander"] {background:#244d70;
        border:1px solid #38617d;border-radius:12px;}
    [data-testid="stSidebar"] [data-testid="stCheckbox"] {padding:1px 0;}
    [data-testid="stSidebar"] button {background:#244d70;color:#fff;border:1px solid #456b87;}
    [data-testid="stSidebar"] button:hover {background:#006C9A;color:white;border-color:#4A9FD8;}
    [data-testid="stSidebarNav"] a {border-radius:11px;padding:.56rem .75rem;}
    [data-testid="stSidebarNav"] a[aria-current="page"] {background:#006C9A!important;}
    [data-testid="stSidebarNav"] a:hover {background:#244d70;}
    [data-testid="stSidebar"] hr {border-color:#456b87;}
    div[data-testid="stMetric"] {background:white;border:1px solid #dfe6ec;
        border-radius:16px;padding:18px 20px;min-height:120px;
        box-shadow:0 1px 2px rgba(26,59,92,.04),0 15px 32px -24px rgba(26,59,92,.3);}
    div[data-testid="stMetricLabel"] {font-weight:700;color:#50667b;font-size:.85rem;}
    div[data-testid="stMetricValue"] {color:#1A3B5C;font-weight:760;}
    [data-testid="stPlotlyChart"] {background:#fff;border:1px solid #e5eaf0;
        padding:12px;border-radius:16px;box-shadow:0 12px 28px -24px rgba(26,59,92,.24);}
    [data-testid="stDataFrame"] {border:1px solid #dfe6ec;border-radius:13px;}
    [data-testid="stExpander"] {border-radius:12px;border-color:#dfe6ec;}
    .stButton button[kind="primary"] {background:#EE5325;color:white;border-color:#EE5325;}
    .stDownloadButton button {background:#EE5325!important;color:white!important;
        border:0!important;border-radius:20px!important;}
    @media(max-width:900px) {
      .block-container {padding:1rem .85rem 2rem;}
      .pet-hero {padding:24px 22px 60px;border-radius:13px;}
    }
    </style>""", unsafe_allow_html=True)


def page_header(kicker, title, description=""):
    """Hero do Lovable implementado em HTML/CSS, sem dependências React."""
    st.markdown(
        '<header class="pet-hero"><p class="pet-hero-kicker">'
        + html.escape(str(kicker)) + '</p><h1 class="pet-hero-title">'
        + html.escape(str(title)) + '</h1><div class="pet-hero-desc">'
        + html.escape(str(description)) + '</div></header>',
        unsafe_allow_html=True
    )


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
