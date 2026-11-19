"""Visão Executiva do SISCAN para a 10ª CRS.

Apresenta a produção registrada, a disponibilidade temporal, a estimativa
operacional de exames alterados e um diagrama territorial esquemático.
Os registros representam exames, não mulheres distintas.
"""

import html
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_download import chart_with_right_click_download
from utils.data_loader import (
    MUNICIPIOS, filtered, require, selected_years, sidebar_filters, year_month_index,
)
from utils.theme import (
    NAVY, OCEAN, ORANGE, active_scope_html, apply_custom_css, fmt_num, fmt_pct, pct,
)

COLUNAS_TEMPORAL = ("municipio", "ano", "mes", "quantidade")
COLUNAS_ALTERADOS = {"quantidade_alterados", "total_exames_validos"}
DISTANCIA_CONEXAO = 34
# Coordenadas esquemáticas, não geográficas.
TERRITORIOS = (
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
)
ATALHOS = (
    ("Panorama geral", "Volume por competência e município",
     "pages/01_panorama_geral.py", "exec-nav-panorama"),
    ("Exames alterados", "Resultados e categorias citopatológicas",
     "pages/05_exames_alterados.py", "exec-nav-alterados"),
    ("Outubro Rosa", "Produção e sazonalidade dos exames",
     "pages/02_outubro_rosa.py", "exec-nav-outubro"),
)


ESTILOS_EXECUTIVOS = """
<style>
.exec-hero{background:linear-gradient(110deg,#1A3B5C,#006C9A);
    border-radius:17px;padding:32px 34px 68px;color:white;margin-bottom:-43px;}
.exec-kicker{font-size:.69rem;letter-spacing:.2em;color:#a8d5eb;font-weight:800}
.exec-title{font-family:Fraunces,Georgia,serif;font-size:clamp(1.7rem,3.2vw,2.9rem);
    font-weight:650;line-height:1.13;margin:10px 0;color:#fff!important;max-width:770px}
.exec-title em{font-style:italic;color:#c0d9eb;}
.exec-sub{font-family:Manrope,Arial,sans-serif;font-size:1.15rem;line-height:1.65;color:#FFFFFF;margin:15px 0 17px;max-width:920px;font-weight:500}
@media(max-width:768px){.exec-sub{font-size:1rem;line-height:1.55}}
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
/* Nota da série temporal: contraste suficiente sem competir com o gráfico. */
.st-key-exec-month-card .exec-month-note {
    font-family:Manrope,Arial,sans-serif!important;
    font-size:.9rem!important;line-height:1.55!important;
    color:#40566B!important;font-weight:400!important;
    padding:0 0 12px;margin:0;
    background:transparent;border:0;
    overflow-wrap:break-word;
}
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

/* Hierarquia e responsividade da Visão Executiva. */
.exec-hero {
  position:relative;
  background:radial-gradient(125% 155% at 100% 0%,#006C9A 0%,#1A3B5C 72%)!important;
  border-radius:20px!important;
  padding:38px 40px 34px!important;
  margin:14px 0 22px!important;
  min-height:0!important;
  box-shadow:0 15px 32px -25px rgba(26,59,92,.44);
}
.exec-kicker {
  font-family:Manrope,Arial,sans-serif!important;
  font-size:.73rem!important;
  font-weight:800!important;
  letter-spacing:.17em!important;
  line-height:1.5!important;
  color:#a8d5eb!important;
}
.exec-title {
  max-width:900px!important;
  font-family:Manrope,Arial,sans-serif!important;
  font-size:clamp(2rem,3.25vw,2.85rem)!important;
  font-weight:800!important;
  line-height:1.19!important;
  letter-spacing:-.035em!important;
  margin:17px 0 18px!important;
  color:#fff!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
}
.exec-title em {
  font-family:inherit!important;
  font-style:normal!important;
  font-weight:800!important;
  color:#b5dcef!important;
}
.exec-sub {
  max-width:920px!important;
  font:500 clamp(.98rem,1.2vw,1.12rem)/1.65 Manrope,Arial,sans-serif!important;
  margin:0 0 18px!important;
  color:#f5faff!important;
  overflow-wrap:normal!important;
}
.exec-hero .pet-active-scope {
  margin-top:18px!important;
  gap:9px!important;
  flex-wrap:wrap!important;
}
.exec-hero .pet-scope-label {
  font-size:.74rem!important;
  letter-spacing:.13em!important;
}
.exec-hero .pet-scope-chip {
  background:rgba(255,255,255,.15)!important;
  font-size:.85rem!important;
  padding:7px 12px!important;
}
.exec-metric,.exec-metric.blue,.exec-metric.orange {
  min-height:132px!important;
  height:auto!important;
  padding:20px 17px!important;
  border-radius:13px!important;
  box-shadow:0 8px 22px -17px rgba(26,59,92,.4)!important;
}
.exec-metric-label {
  padding-right:19px!important;
  font:800 .69rem/1.5 Manrope,Arial,sans-serif!important;
  letter-spacing:.035em!important;
}
.exec-metric-value {
  font:800 clamp(1.48rem,2vw,1.95rem)/1.2 Manrope,Arial,sans-serif!important;
  margin:12px 0 4px!important;
  letter-spacing:-.025em!important;
}
.exec-card-title,.exec-links strong {
  font-family:Manrope,Arial,sans-serif!important;
  font-weight:800!important;
  letter-spacing:-.025em!important;
}
.exec-card-title {font-size:1.15rem!important;}
@media(max-width:1100px) {
  .exec-hero {padding:29px 30px 27px!important;margin-top:10px!important;}
  .exec-title {font-size:clamp(1.85rem,3.4vw,2.5rem)!important;}
}
@media(max-width:768px) {
  .exec-hero {padding:25px 21px!important;border-radius:16px!important;margin:8px 0 18px!important;}
  .exec-title {font-size:clamp(1.65rem,5.3vw,2.25rem)!important;line-height:1.22!important;}
  .exec-sub {font-size:.98rem!important;line-height:1.58!important;}
  .exec-metric {min-height:118px!important;padding:17px 15px!important;}
}
@media(max-width:480px) {
  .exec-hero {padding:22px 17px!important;border-radius:14px!important;}
  .exec-title {font-size:1.65rem!important;}
  .exec-hero .pet-active-scope {gap:7px!important;}
  .exec-hero .pet-scope-label {flex-basis:100%!important;}
  .exec-metric-value {font-size:1.55rem!important;}
}
</style>
"""


ESTILOS_ATALHOS = """
<style>
.exec-explore-heading{margin:26px 0 7px;color:#1A3B5C;font-size:1.2rem;font-weight:750;font-family:Manrope,Arial,sans-serif;}
.exec-explore-desc{color:#60758a;font-size:.84rem;margin:0 0 15px;}
[data-testid="stMain"] :is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados){
  position:relative!important;background:#fff!important;
  border:1px solid #d7dde3!important;border-radius:13px!important;
  padding:0!important;min-height:78px!important;
  box-shadow:0 3px 9px rgba(26,59,92,.07)!important;
  transition:border-color .15s,box-shadow .15s,transform .15s;
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados):hover{
  border-color:#EE5325!important;
  box-shadow:0 7px 20px rgba(26,59,92,.13)!important;
  transform:translateY(-1px);
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados)::after{
  content:"→";position:absolute;right:16px;top:50%;
  transform:translateY(-50%);color:#EE5325;
  font-size:1.35rem;font-weight:500;pointer-events:none;
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"]{
  width:100%!important;
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"] a{
  display:flex!important;flex-direction:column!important;align-items:flex-start!important;
  justify-content:center!important;gap:2px!important;
  width:100%!important;min-height:76px!important;box-sizing:border-box!important;
  padding:15px 35px 15px 16px!important;border-radius:12px!important;
  background:transparent!important;border:0!important;text-decoration:none!important;
  cursor:pointer!important;
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"] a,
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"] a p{
  font-family:Fraunces,Georgia,serif!important;font-size:1rem!important;font-weight:650!important;
  line-height:1.3!important;color:#1A3B5C!important;text-align:left!important;margin:0!important;
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"] a::after{
  content:var(--exec-nav-subtitle);display:block;white-space:normal;
  font-family:Manrope,Arial,sans-serif;color:#72879d!important;font-size:.76rem!important;
  font-weight:400;line-height:1.35;text-align:left;
}
:is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"] a:focus-visible{
  outline:2px solid #EE5325!important;outline-offset:-3px!important;
}
@media(max-width:768px){
  :is(.st-key-exec-nav-panorama,.st-key-exec-nav-outubro,.st-key-exec-nav-alterados) [data-testid="stPageLink"] a{
    padding:14px 35px 14px 14px!important;min-height:75px!important;
  }
}
"""
# Os subtítulos são gerados a partir da mesma definição usada para os atalhos.
ESTILOS_ATALHOS += "\n".join(
    f".st-key-{key} {{ --exec-nav-subtitle: {json.dumps(subtitle, ensure_ascii=False)}; }}"
    for _, subtitle, _, key in ATALHOS
) + "\n</style>"


def agregar_mensal(df: pd.DataFrame) -> pd.Series:
    """Soma exames por competência, preservando totais ausentes.

    Args:
        df: Fato temporal Gold já filtrado por ano e município.

    Returns:
        Série de quantidades indexada pelo primeiro dia de cada mês.
    """
    mensal = (
        df.groupby(["ano", "mes"], as_index=False)["quantidade"]
        .sum(min_count=1)
    )
    mensal["data"] = pd.to_datetime(
        dict(year=mensal["ano"], month=mensal["mes"], day=1)
    )
    return mensal.set_index("data")["quantidade"].sort_index()


def preparar_serie_mensal(
    mensal: pd.Series, anos: list[int]
) -> tuple[pd.Series, pd.DatetimeIndex, int]:
    """Completa o calendário visual sem criar exames ou contar anos não ativos.

    Returns:
        Série com lacunas, competências ausentes nos anos selecionados
        e quantidade de competências com valores observados.
    """
    if not anos:
        return mensal.iloc[0:0].copy(), pd.DatetimeIndex([]), 0
    calendario = year_month_index(anos)
    selecionadas = calendario[calendario.year.isin(anos)]
    serie = mensal.reindex(calendario).where(calendario.year.isin(anos))
    observadas = serie.reindex(selecionadas).notna()
    ausentes = selecionadas[~observadas.to_numpy()]
    return serie, ausentes, int(observadas.sum())


def calcular_proporcao_alterados(alt: pd.DataFrame) -> str:
    """Formata a proporção operacional de alterados para todas as idades.

    Usa a razão dos totais Gold, sem calcular médias de percentuais.
    Retorna N/D quando os campos ou o denominador não estão disponíveis.
    """
    if alt.empty or not COLUNAS_ALTERADOS.issubset(alt.columns):
        return "N/D"
    alterados = alt["quantidade_alterados"].sum(min_count=1)
    validos = alt["total_exames_validos"].sum(min_count=1)
    if pd.isna(alterados) or pd.isna(validos) or validos <= 0:
        return "N/D"
    return fmt_pct(pct(alterados, validos))


def agregar_municipios(df: pd.DataFrame) -> pd.Series:
    """Retorna o volume observado por município, sem imputar ausências."""
    return df.groupby("municipio")["quantidade"].sum(min_count=1).sort_index()


def construir_indicadores(
    df: pd.DataFrame, alt: pd.DataFrame, meses: int, anos: list[int]
) -> list[tuple[str, str, str]]:
    """Monta os quatro indicadores do recorte executivo."""
    total = df["quantidade"].sum(min_count=1)
    municipios = df.loc[df["quantidade"].notna(), "municipio"].nunique()
    return [
        ("EXAMES REGISTRADOS", fmt_num(total) if pd.notna(total) else "N/D", "blue"),
        ("MUNICÍPIOS COM REGISTROS", f"{municipios} de {len(MUNICIPIOS)}", ""),
        ("MESES COM REGISTROS", f"{meses} de {12 * len(anos)}", ""),
        ("EXAMES ALTERADOS", calcular_proporcao_alterados(alt), "orange"),
    ]


def configurar_pagina() -> None:
    """Aplica os estilos exclusivos da visão executiva."""
    st.markdown(ESTILOS_EXECUTIVOS, unsafe_allow_html=True)


def renderizar_cabecalho() -> None:
    """Exibe o cabeçalho e os filtros ativos no recorte analítico."""
    st.markdown(
        """
<div class="exec-hero">
  <div class="exec-kicker">VISÃO EXECUTIVA · 10ª CRS · RS</div>
  <h1 class="exec-title">Rastreamento do câncer do colo do útero,
  <em>território a território.</em></h1>
  <div class="exec-sub">Apresenta um panorama dos exames citopatológicos registrados nos municípios da 10ª CRS, com indicadores de volume, distribuição territorial, evolução mensal e proporção de resultados alterados. Os dados acompanham os anos e municípios selecionados nos filtros.</div>
""" + active_scope_html() + "</div>",
        unsafe_allow_html=True,
    )


def renderizar_indicadores(
    kpis: list[tuple[str, str, str]], ausentes: pd.DatetimeIndex
) -> None:
    """Exibe cartões e ajuda contextual sobre a disponibilidade temporal."""
    explicacao = (
        "Competências sem registros: " + ", ".join(ausentes.strftime("%m/%Y"))
        if len(ausentes) else "Todas as competências selecionadas possuem registros."
    )
    for col, (label, value, color) in zip(st.columns(4, gap="small"), kpis):
        with col:
            desc = (
                '<div class="exec-metric-desc" '
                'title="Inclui todas as idades disponíveis na Gold">'
                'Estimativa operacional</div>'
                if color == "orange" else ""
            )
            hint = ""
            if label == "MESES COM REGISTROS":
                explanation = explicacao
                hint = ('<details class="exec-metric-help"><summary aria-label="Explicação sobre os meses" title="Entenda os meses">!</summary>'
                        '<div class="exec-metric-tip">' + html.escape(explanation) + '</div></details>')
            st.markdown(
                '<div class="exec-metric ' + color + '"><div class="exec-metric-label">'
                + html.escape(label) + '</div>' + hint
                + '<div class="exec-metric-value">' + html.escape(value)
                + '</div>' + desc + '</div>',
                unsafe_allow_html=True,
            )


def construir_diagrama_territorial(
    totais: pd.Series, selecionados: set[str]
) -> go.Figure:
    """Constrói a rede esquemática com bolhas proporcionais ao volume.

    As posições e arestas são fixas e não representam distâncias reais.
    Municípios fora da seleção ficam esmaecidos; ausências não são
    apresentadas como contagens observadas iguais a zero.
    """
    fig = go.Figure()
    xs, ys = [], []
    for i, (_, ax, ay) in enumerate(TERRITORIOS):
        for _, bx, by in TERRITORIOS[i + 1:]:
            if ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5 < DISTANCIA_CONEXAO:
                xs.extend([ax, bx, None])
                ys.extend([ay, by, None])
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", showlegend=False, hoverinfo="skip",
        line=dict(color="#d7e0e8", width=1.0),
    ))

    max_vol = max(1.0, float(totais.max())) if totais.notna().any() else 1.0
    for municipality, x, y in TERRITORIOS:
        volume = totais.get(municipality, float("nan"))
        enabled = municipality in selecionados
        observado = enabled and pd.notna(volume)
        tamanho = max(0.0, float(volume)) if observado else 0.0
        radius = 2.5 + (tamanho / max_vol) ** 0.5 * 11
        size = radius * 6.2
        valor_exibido = (
            f"{fmt_num(volume)} exames" if observado
            else "Sem registros" if enabled else "Fora do recorte"
        )
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(
                size=size,
                color="rgba(0,108,154,0.25)" if enabled else "rgba(160,175,190,0.20)",
                line=dict(color=OCEAN if enabled else "#b9c4cf", width=1.2),
            ),
            customdata=[[municipality, valor_exibido]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(size=6, color=ORANGE if enabled else "#9daeba"),
            hoverinfo="skip", showlegend=False,
        ))

    fig.update_xaxes(visible=False, range=[-9, 109], fixedrange=True,
                     constrain="domain")
    # Preserva a orientação do diagrama, com a origem no canto superior esquerdo.
    fig.update_yaxes(visible=False, range=[109, -9], fixedrange=True,
                     scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=330, margin=dict(l=3, r=3, t=5, b=5),
        plot_bgcolor="#f4f6f8", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_color=NAVY),
    )
    return fig


def construir_grafico_mensal(
    serie: pd.Series, ausentes: pd.DatetimeIndex
) -> go.Figure:
    """Mantém a lacuna na linha e um fundo de área contínuo em ausência isolada."""
    fig = go.Figure()
    # Mantém o NaN de uma competência ausente isolada dentro do mesmo trace:
    # o preenchimento do Plotly passa por ela, mas connectgaps=False interrompe
    # a linha e não cria ponto, valor ou tooltip. Lacunas maiores e anos fora
    # do recorte continuam separando os trechos, inclusive no preenchimento.
    isoladas = (
        serie.isna() & serie.index.isin(ausentes)
        & serie.shift(1).notna() & serie.shift(-1).notna()
    )
    separadores = serie.isna() & ~isoladas
    for _, trecho in serie[~separadores].groupby(separadores.cumsum()[~separadores]):
        observados = int(trecho.notna().sum())
        if not observados:
            continue
        fig.add_trace(go.Scatter(
            x=trecho.index, y=trecho, mode="lines+markers" if observados > 1 else "markers",
            line=dict(color=OCEAN, width=2),
            marker=dict(size=4, color=OCEAN, line=dict(color="white", width=0.5)),
            fill="tozeroy" if observados > 1 else "none",
            fillcolor="rgba(0,108,154,.08)",
            connectgaps=False,
            hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>",
        ))

    agosto = pd.Timestamp("2022-08-01")
    # A lacuna natural entre os trechos e o rótulo no eixo sinalizam
    # a ausência, sem linhas verticais ou sobreposições decorativas.
    destaque = agosto if agosto in ausentes else (ausentes[0] if len(ausentes) == 1 else None)
    fig.update_layout(height=370, showlegend=False,
                      margin=dict(l=70, r=18, t=22, b=32),
                      plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                      hovermode="closest", hoverdistance=20,
                      hoverlabel=dict(bgcolor="white", bordercolor="#D5E3ED",
                                      font=dict(color=NAVY)),
                      modebar=dict(bgcolor="rgba(255,255,255,0)",
                                   color="#72879D", activecolor=OCEAN))
    fig.update_yaxes(
        gridcolor="#e9eff3", rangemode="tozero", tickformat=",.0f",
        zeroline=True, zerolinecolor="#CBD5E1", zerolinewidth=1,
        tickfont=dict(size=11, color=NAVY), automargin=True,
        title_text="Exames", title_standoff=10,
        ticks="outside", ticklen=5, tickcolor="#D5E3ED",
    )
    fig.update_xaxes(
        showgrid=False, tickformat="%m/%Y", nticks=6,
        showline=True, linecolor="#CBD5E1", linewidth=1,
        ticks="outside", ticklen=5, tickcolor="#D5E3ED",
        tickfont=dict(size=10, color="#64748B"), automargin=True,
    )
    if destaque is not None and len(serie.index):
        # Preserva as referências anuais e acrescenta a competência ausente,
        # sem substituir janeiro/2023 nem qualquer outro rótulo regular.
        datas_eixo = serie.index[::max(1, (len(serie.index) + 5) // 6)].tolist()
        if destaque not in datas_eixo:
            datas_eixo.append(destaque)
            datas_eixo.sort()
        # Todas as datas têm a mesma cor, tamanho e peso tipográfico.
        rotulos = [data.strftime("%m/%Y") for data in datas_eixo]
        fig.update_xaxes(
            tickmode="array", tickvals=datas_eixo, ticktext=rotulos,
            tickfont=dict(size=10, color="#64748B"),
            automargin=True,
        )
    if len(serie.index):
        fig.update_xaxes(range=[
            serie.index.min() - pd.Timedelta(days=24),
            serie.index.max() + pd.Timedelta(days=24),
        ])
    return fig


def renderizar_graficos(
    df: pd.DataFrame, serie: pd.Series, ausentes: pd.DatetimeIndex
) -> None:
    """Exibe os dois gráficos executivos com as exportações originais."""
    st.markdown('<div style="height:22px" aria-hidden="true"></div>', unsafe_allow_html=True)

    left, right = st.columns([1, 1.45], gap="medium")
    with left:
        with st.container(border=True, key="exec-bubble-card"):
            st.markdown('<div class="exec-card-title">Visualização territorial</div>'
                        '<div class="exec-card-sub">Bolhas proporcionais ao volume de exames</div>',
                        unsafe_allow_html=True)
            selecionados = set(
                st.session_state.get("city_preference", list(MUNICIPIOS.values()))
            )
            fig = construir_diagrama_territorial(agregar_municipios(df), selecionados)
            chart_with_right_click_download(fig, filename="visao_executiva_territorial.png", height=fig.layout.height)
            st.caption("Passe o mouse sobre uma bolha para consultar o município.")

    with right:
        with st.container(border=True, key="exec-month-card"):
            st.markdown('<div class="exec-card-title">Evolução mensal de exames</div>'
                        '<div class="exec-card-sub">Competência × exames registrados</div>',
                        unsafe_allow_html=True)
            fig = construir_grafico_mensal(serie, ausentes)
            chart_with_right_click_download(
                fig, filename="visao_executiva_evolucao_mensal.png",
                height=fig.layout.height, compact_modebar=True, bottom_space=4,
            )
            if len(ausentes):
                competencias = ", ".join(ausentes.strftime("%m/%Y"))
                st.markdown(
                    '<div class="exec-month-note" role="note">'
                    f'{html.escape(competencias)} — sem dados na base. '
                    'A lacuna não representa zero exames.</div>',
                    unsafe_allow_html=True,
                )


def renderizar_atalhos() -> None:
    """Exibe os atalhos existentes e navega sem alterar os filtros ativos."""
    st.markdown(ESTILOS_ATALHOS, unsafe_allow_html=True)
    st.markdown(
        '<div class="exec-explore-heading">Explore as análises</div>'
        '<p class="exec-explore-desc">Aprofunde os indicadores por município, '
        'período e resultado citopatológico.</p>',
        unsafe_allow_html=True,
    )
    for col, (title, _, page, key) in zip(st.columns(3, gap="medium"), ATALHOS):
        with col:
            with st.container(key=key):
                # O link nativo ocupa o card inteiro e usa o roteador compartilhado.
                st.page_link(page, label=title, use_container_width=True)


def main() -> None:
    """Orquestra a visão executiva a partir das fontes Gold filtradas."""
    configurar_pagina()
    renderizar_cabecalho()

    df = filtered("temporal")
    if not require(df, COLUNAS_TEMPORAL):
        return

    alt = filtered("alterados")
    anos = selected_years()
    serie, ausentes, meses = preparar_serie_mensal(agregar_mensal(df), anos)
    kpis = construir_indicadores(df, alt, meses, anos)

    renderizar_indicadores(kpis, ausentes)
    renderizar_graficos(df, serie, ausentes)
    renderizar_atalhos()


def executar_aplicacao() -> None:
    """Mantém o menu, o tema e os filtros no ponto de entrada da aplicação.

    O roteador nativo preserva o contexto compartilhado entre páginas.
    Cada guia renderiza apenas seu conteúdo analítico.
    """
    st.set_page_config(
        page_icon="🩺", layout="wide", initial_sidebar_state="expanded",
    )
    paginas = {
        "main.py": st.Page(main, title="Visão executiva", default=True),
        "pages/01_panorama_geral.py": st.Page(
            "pages/01_panorama_geral.py", title="Panorama geral",
            url_path="panorama_geral",
        ),
        "pages/03_faixa_etaria.py": st.Page(
            "pages/03_faixa_etaria.py", title="Faixa etária",
            url_path="faixa_etaria",
        ),
        "pages/02_outubro_rosa.py": st.Page(
            "pages/02_outubro_rosa.py", title="Outubro Rosa",
            url_path="outubro_rosa",
        ),
        "pages/04_adequabilidade.py": st.Page(
            "pages/04_adequabilidade.py", title="Adequabilidade",
            url_path="adequabilidade",
        ),
        "pages/05_exames_alterados.py": st.Page(
            "pages/05_exames_alterados.py", title="Exames alterados",
            url_path="exames_alterados",
        ),
    }
    pagina = st.navigation(list(paginas.values()), position="hidden")
    with st.sidebar:
        apply_custom_css()
    sidebar_filters(paginas)
    pagina.run()


if __name__ == "__main__":
    executar_aplicacao()
