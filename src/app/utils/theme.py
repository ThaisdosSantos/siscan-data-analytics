"""Identidade visual PET-Saúde e funções comuns de apresentação."""
import html
import io
import pandas as pd
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
    /* KPIs das páginas analíticas: mantém a identidade PET-Saúde.
       A Visão Executiva possui cartões HTML próprios e permanece branca. */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
      [data-testid="stMetric"] {background:#006C9A;border-color:#006C9A;}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
      [data-testid="stMetric"] {background:#EE5325;border-color:#EE5325;}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
      [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
      [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
      [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
      [data-testid="stMetric"] [data-testid="stMetricValue"] {color:white!important;}

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

    [data-testid="stSidebarNav"] {display:none!important;}
    [data-testid="stAppViewContainer"] {background:#f8fafb!important;}
    [data-testid="stSidebar"] {width:300px!important;min-width:300px!important;}
    .lovable-brand {display:flex;align-items:center;gap:12px;padding:14px 6px 22px;}
    .lovable-mark {display:grid;place-items:center;width:42px;height:42px;background:#ee5325;
      border-radius:12px;font-size:24px;color:white!important;}
    .lovable-brand strong {display:block;font-size:1.3rem;color:white;font-weight:800;}
    .lovable-brand small {display:block;color:#c3d7e6;font-size:.74rem;}
    .lovable-label {font-weight:800;color:#9cc5de!important;font-size:.68rem;letter-spacing:.15em;margin:14px 0 9px;}
    .lovable-footer {font-size:.72rem;line-height:1.8;color:#bad0df!important;border-top:1px solid #456b87;margin-top:20px;padding-top:18px;}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {padding:10px 13px;border-radius:10px;font-weight:650;text-decoration:none;}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {background:#285778;}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {background:#006c9a!important;}
    [data-testid="stSidebar"] [data-testid="stButton"] button {min-height:34px;border-radius:9px;font-size:.8rem;padding:4px;}
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {background:#006c9a!important;border-color:#4a9fd8!important;}
    .pet-hero {min-height:185px;padding-bottom:75px;}
    [data-testid="stMetricValue"] {font-size:1.85rem;}

    /* Responsividade compartilhada — desktop, tablet e smartphone. */
    *, *::before, *::after {box-sizing:border-box;}
    [data-testid="stAppViewContainer"], .block-container {min-width:0;}
    .block-container {width:100%;max-width:1480px;margin:0 auto;}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width:0;}
    [data-testid="stPlotlyChart"],[data-testid="stPlotlyChart"] > div {max-width:100%;min-width:0;}
    [data-testid="stImage"] img {max-width:100%;height:auto;}
    .pet-hero-title,.pet-hero-desc,.exec-title,.exec-sub {overflow-wrap:anywhere;}
    .pet-table-scroller,.q3-matrix-scroll {max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;}
    @media (max-width:1100px) {
      .block-container {padding:1.1rem 1.2rem 2rem;}
      [data-testid="stSidebar"] {width:min(300px,85vw)!important;min-width:0!important;}
    }
    @media (max-width:768px) {
      .block-container {padding:0.85rem 0.8rem 2rem;}
      .pet-hero {padding:23px 20px 42px;min-height:0;margin-bottom:0;}
      .pet-hero-title {font-size:clamp(1.55rem,6vw,2.2rem);}
      .pet-hero-desc {font-size:.84rem;}
      [data-testid="stMetric"] {min-height:100px;padding:14px 15px;}
      [data-testid="stMetricValue"] {font-size:clamp(1.35rem,5vw,1.85rem)!important;}
      [data-testid="stPlotlyChart"] {padding:5px;border-radius:12px;}
      .stDownloadButton button {max-width:100%;white-space:normal;}
      .pet-table th,.pet-table td,.q3-matrix th,.q3-matrix td {padding:10px 9px;}
    }
    @media (max-width:480px) {
      .block-container {padding:0.65rem 0.55rem 2rem;}
      .pet-hero {padding:18px 15px 28px;}
      .pet-hero-title {font-size:1.55rem;}
      [data-testid="stSidebar"] {width:min(300px,92vw)!important;}
      [data-testid="stSidebar"] [data-testid="stButton"] button {min-height:42px;}
      [data-testid="stPageLink"] a {overflow-wrap:anywhere;}
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


def display_table(df, *, percent_columns=None, integer_columns=None):
    """Tabela PET-Saúde: HTML acessível e responsivo, sem alterar os dados."""
    percent_columns = set(percent_columns or [])
    integer_columns = set(integer_columns or [])
    css = """
    <style>
    .pet-table-scroller{width:100%;overflow-x:auto;border-radius:8px;
      box-shadow:0 2px 7px rgba(26,59,92,.09);margin:12px 0 17px}
    table.pet-table{border-collapse:collapse;width:100%;background:#fff;color:#1A3B5C;
      font:500 .83rem Manrope,Arial,sans-serif}
    .pet-table th{background:#1A3B5C;color:#fff;padding:13px 12px;text-align:left;
      font-size:.76rem;line-height:1.35;font-weight:750;white-space:normal}
    .pet-table td{padding:13px 12px;border-bottom:1px solid #e7ebef;white-space:nowrap}
    .pet-table tbody tr:nth-child(even){background:#f6f8fa}
    .pet-table tbody tr:hover{background:#ecf5fa}
    .pet-table td:first-child{font-weight:700}
    .pet-table .pet-badge{display:inline-block;border-radius:5px;padding:5px 9px;
      font-size:.76rem;font-weight:750;white-space:normal}
    .pet-badge.ok{color:#385723;background:#e2f0d9}
    .pet-badge.low{color:#856404;background:#fff3cd}
    .pet-badge.bad{color:#b72323;background:#ffe6e6}
    .pet-badge.unknown{color:#4a5968;background:#e9edf1}
    </style>
    """
    def br_number(value, decimals):
        return f"{value:,.{decimals}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    def cell(value, column):
        if pd.isna(value):
            return "N/D"
        if isinstance(value, (bool,)):
            return "Sim" if value else "Não"
        if column in percent_columns and isinstance(value, (int, float)):
            return br_number(value, 2) + "%"
        if column in integer_columns and isinstance(value, (int, float)):
            return br_number(value, 0)
        if isinstance(value, (int, float)):
            return br_number(value, 2 if isinstance(value, float) and not value.is_integer() else 0)
        content = html.escape(str(value))
        if column.lower().startswith(("classificação", "classificacao", "alerta")):
            mode = "unknown"
            if "🟢" in content or "boa" in content.lower(): mode = "ok"
            elif "🟡" in content or "baixo" in content.lower(): mode = "low"
            elif "🔴" in content or "alto" in content.lower(): mode = "bad"
            return '<span class="pet-badge ' + mode + '">' + content + '</span>'
        return content
    header = "".join("<th scope='col'>" + html.escape(str(c)) + "</th>" for c in df.columns)
    rows = []
    for values in df.itertuples(index=False, name=None):
        rows.append("<tr>" + "".join("<td>" + cell(v, c) + "</td>"
                                   for c, v in zip(df.columns, values)) + "</tr>")
    if not rows:
        rows = ['<tr><td colspan="' + str(max(1,len(df.columns))) + '">Nenhum registro.</td></tr>']
    markup = ('<div class="pet-table-scroller" role="region" aria-label="Tabela de dados" tabindex="0">'
              '<table class="pet-table"><thead><tr>' + header + '</tr></thead><tbody>'
              + "".join(rows) + '</tbody></table></div>')
    st.markdown(css + markup, unsafe_allow_html=True)


def export_table(df, name):
    """Exibe tabela estilizada, mantendo exportação dos dados originais."""
    from pandas.api.types import is_numeric_dtype
    percentage = [
        c for c in df.columns if is_numeric_dtype(df[c]) and
        (c.lower() in {"percentual", "taxa", "variacao_pct"} or
         c.lower().endswith(("_pct", "_percentual", "_percentual_pct")) or
         c.lower().startswith(("taxa_", "proporcao_")))
    ]
    display_table(df, percent_columns=percentage)
    st.download_button("⬇️ Exportar CSV", df.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name=name, mime="text/csv", key="csv_" + name)

def fmt_num(v):
    return f"{int(v):,}".replace(",", ".")

def fmt_pct(v):
    if v is None or v != v: return "N/D"
    return f"{v:.2f}%".replace(".", ",")

def pct(n, d):
    return 100*n/d if d and d > 0 else float("nan")
