"""Panorama territorial e temporal de exames citopatológicos registrados.

Consome a Gold temporal filtrada e apresenta volumes, participação municipal
e variações anuais. Exames registrados não equivalem a pessoas distintas.
"""

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.chart_download import chart_with_right_click_download
from utils.data_loader import (
    filtered, require, selected_years, sidebar_filters, year_month_index, years_label,
)
from utils.theme import (
    OCEAN, apply_custom_css, display_chart, display_table, fmt_num, fmt_pct,
    page_header, pct,
)

MESES_PT = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)
MESES_ABREV = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
COMPETENCIA_AUSENTE = pd.Timestamp("2022-08-01")
COLUNAS_OBRIGATORIAS = ("municipio", "ano", "mes", "quantidade")
COR_AUMENTO = "#006C9A"
COR_REDUCAO = "#A83A20"


def configurar_pagina() -> None:
    """Configura os estilos locais, os filtros e o cabeçalho da página."""
    st.set_page_config(page_title="Panorama geral | SISCAN", layout="wide")
    apply_custom_css()
    st.markdown("""
    <style>
    /* O tema global usa margem negativa no hero para sobrepor cartões.
       Nesta página, o primeiro conteúdo é um título de seção, então
       removemos a sobreposição apenas no Panorama Geral. */
    .pet-hero {
        margin-bottom: 0 !important;
    }
    .pet-hero .pet-hero-desc {
        font-family: Manrope, Arial, sans-serif !important;
        font-size: 1.15rem !important;
        line-height: 1.65 !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
        max-width: 920px !important;
    }
    @media (max-width: 768px) {
        .pet-hero .pet-hero-desc {
            font-size: 1rem !important;
            line-height: 1.55 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    sidebar_filters()
    page_header(
        "",
        "Volume de exames por competência e município",
        "Apresenta a quantidade de exames citopatológicos registrados "
        "no período selecionado, sua evolução mensal e anual, a distribuição entre os "
        "municípios e as variações percentuais de um ano para o seguinte. "
        "Permite comparar os volumes de exames ao longo do tempo e identificar "
        "diferenças na produção registrada entre os municípios.",
    )

    st.markdown(
        """
        <style>
        .panorama-section-title {
          margin:30px 0 17px;padding:9px 0 12px;
          border-bottom:2px solid #D8E5EF;
          font:750 clamp(21px,2vw,26px)/1.35 Manrope,Arial,sans-serif;
          color:#1A3B5C;
        }
        .panorama-section-title .panorama-section-index {
          color:#006C9A;margin-right:10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def agregar_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Soma os exames por competência, preservando totais ausentes.

    Args:
        df: Registros temporais Gold filtrados por município e ano.

    Returns:
        Série mensal ordenada, com data no primeiro dia de cada mês.
    """
    mensal = (
        df.groupby(["ano", "mes"], as_index=False)["quantidade"]
        .sum(min_count=1)
        .sort_values(["ano", "mes"])
    )
    mensal["data"] = pd.to_datetime(
        dict(year=mensal["ano"], month=mensal["mes"], day=1)
    )
    return mensal


def agregar_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna o volume acumulado por município, em ordem decrescente."""
    return (
        df.groupby("municipio", as_index=False)["quantidade"]
        .sum(min_count=1)
        .sort_values("quantidade", ascending=False)
    )


def agregar_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Soma os exames por município e ano sem imputar zeros."""
    return (
        df.dropna(subset=["municipio", "ano"])
        .groupby(["municipio", "ano"], as_index=False)["quantidade"]
        .sum(min_count=1)
    )


def preparar_serie_mensal(
    monthly: pd.DataFrame, years: list[int]
) -> tuple[pd.DataFrame, pd.DatetimeIndex, pd.DatetimeIndex]:
    """Reindexa a série no calendário completo e identifica lacunas.

    Anos não selecionados interrompem a linha, mas não entram na
    contagem de competências ausentes do recorte.
    """
    complete = year_month_index(years)
    selected_dates = pd.DatetimeIndex(
        [date for date in complete if date.year in years]
    )
    series = monthly.set_index("data").reindex(complete)
    missing = selected_dates[series.loc[selected_dates, "quantidade"].isna()]
    return series, complete, missing


def calcular_variacao_anual(annual: pd.DataFrame) -> pd.DataFrame:
    """Calcula a variação percentual entre anos consecutivos.

    Args:
        annual: Totais observados por município e ano, sem grade artificial.

    Returns:
        Dados anuais com ano anterior, volume anterior, transição e variação.
        Comparações sem referência positiva ou não consecutivas ficam nulas.
    """
    var_ano = annual.copy()
    var_ano["ano"] = pd.to_numeric(var_ano["ano"], errors="coerce")
    var_ano = var_ano.dropna(subset=["municipio", "ano", "quantidade"])
    var_ano["ano"] = var_ano["ano"].astype(int)
    var_ano = var_ano.sort_values(["municipio", "ano"]).reset_index(drop=True)

    var_ano["ano_anterior"] = var_ano.groupby("municipio", sort=False)["ano"].shift(1)
    var_ano["quantidade_anterior"] = var_ano.groupby("municipio", sort=False)["quantidade"].shift(1)
    consecutivos = var_ano["ano"].sub(var_ano["ano_anterior"]).eq(1)
    var_ano["variacao_pct"] = (
        (var_ano["quantidade"] - var_ano["quantidade_anterior"])
        .div(var_ano["quantidade_anterior"].where(var_ano["quantidade_anterior"].gt(0)))
        .mul(100)
        .where(consecutivos)
    )
    var_ano["transicao"] = [
        f"{int(a)}→{int(b)}" if cons else None
        for a, b, cons in zip(var_ano["ano_anterior"], var_ano["ano"], consecutivos)
    ]
    return var_ano


def fmt_delta(valor: float) -> str:
    """Formata a diferença percentual com sinal e duas casas decimais."""
    return "—" if pd.isna(valor) else f"{valor:+.2f}%"


def renderizar_indicadores(
    df: pd.DataFrame, monthly: pd.DataFrame, bycity: pd.DataFrame, years: list[int]
) -> None:
    """Exibe volume total, média mensal e participação do município líder."""
    period = years_label(years)
    total = df.quantidade.sum(min_count=1)
    months_count = len(monthly)
    expected = 12 * len(years)
    top = bycity.iloc[0] if not bycity.empty else None

    st.markdown(
        '<h2 class="panorama-section-title"><span class="panorama-section-index">01</span>'
        'Panorama da produção de exames</h2>', unsafe_allow_html=True,
    )

    col_total, col_media, col_municipio = st.columns(3)
    with col_total:
        st.metric("Total de exames registrados", fmt_num(total))
        st.caption("Volume de exames, não de pessoas distintas.")
    with col_media:
        st.metric("Média por mês com registro", fmt_num(monthly.quantidade.mean()))
        st.caption(f"Calculada sobre **{months_count} de {expected} meses** disponíveis no recorte.")
    with col_municipio:
        st.metric("Maior participação no total selecionado",
                  fmt_pct(pct(top.quantidade, total)) if top is not None else "N/D")
        if top is not None:
            st.caption(f"**{top.municipio}** · percentual dos exames dos municípios selecionados em {period}.")


def renderizar_disponibilidade(
    missing: pd.DatetimeIndex, months_count: int, expected: int
) -> None:
    """Informa competências sem registros, sem tratá-las como zeros."""
    if len(missing):
        missing_label = ", ".join(f"{MESES_PT[d.month - 1].lower()}/{d.year}" for d in missing)
        st.warning(f"**Disponibilidade temporal:** {months_count} de {expected} meses com registros. "
                   f"Sem dados em **{missing_label}**.")
    else:
        st.caption(f"Disponibilidade temporal: **{months_count} de {expected} meses** com registros.")


def renderizar_evolucao_mensal(
    series: pd.DataFrame, complete: pd.DatetimeIndex, agosto_2022_ausente: bool
) -> None:
    """Renderiza a série regional e sinaliza a competência ausente de agosto/2022."""
    st.subheader("Evolução mensal")
    st.markdown(
        "Apresenta a **quantidade de exames registrada a cada mês** no recorte "
        "selecionado, permitindo observar aumentos, reduções e possíveis padrões ao longo do tempo."
    )
    with st.expander("ℹ️ Como interpretar a evolução mensal", expanded=False):
        st.markdown(
            "**Eixo horizontal:** meses e anos. **Eixo vertical:** quantidade de exames. "
            "Pontos mais altos indicam maior volume mensal; pontos mais baixos, menor volume. "
            "Meses sem dados aparecem como interrupções da linha, e **não como zero exames**. "
            "Os valores se referem a exames registrados, não a mulheres distintas. "
            "O gráfico permite observar padrões, mas não determinar suas causas."
        )
    fig = px.line(x=complete, y=series["quantidade"], markers=True,
                  labels={"x": "Competência", "y": "Exames registrados"},
                  color_discrete_sequence=[OCEAN])
    fig.update_traces(connectgaps=False,
                      hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>")
    axis_dates = complete[::max(1, len(complete)//12)]
    fig.update_xaxes(tickmode="array", tickvals=axis_dates,
                     ticktext=[f"{MESES_ABREV[d.month-1]}/{str(d.year)[2:]}" for d in axis_dates])
    fig.update_yaxes(tickformat=",d")
    if agosto_2022_ausente:
        competencia = COMPETENCIA_AUSENTE.isoformat()
        fig.add_shape(
            type="line", x0=competencia, x1=competencia,
            y0=0, y1=1, xref="x", yref="paper",
            line=dict(color="#B7791F", width=1.5, dash="dash"),
            layer="below",
        )
        fig.add_annotation(
            x=competencia, y=0.98, xref="x", yref="paper",
            text="Ago/2022<br>Sem dados",
            showarrow=False, xanchor="center", yanchor="top",
            font=dict(size=12, color="#854D0E"),
            bgcolor="#FFF7E6", bordercolor="#E5C78F", borderpad=5,
        )
        st.caption("⚠️ Agosto/2022: sem registros na base analisada. A interrupção da linha não representa zero exames.")
    display_chart(fig, filename="panorama_evolucao_mensal.png")


def renderizar_volume_municipal(bycity: pd.DataFrame) -> None:
    """Exibe o ranking territorial com ordenação e download do gráfico."""
    st.markdown(
        '<h2 class="panorama-section-title"><span class="panorama-section-index">02</span>'
        'Distribuição e evolução municipal</h2>', unsafe_allow_html=True,
    )

    st.subheader("Volume de exames por município")
    st.markdown(
        "Compara o **total de exames registrados em cada município** durante "
        "o período selecionado, destacando os maiores e menores volumes."
    )
    with st.expander("ℹ️ Como interpretar o volume municipal", expanded=False):
        st.markdown(
            "Cada barra representa um município; barras mais longas indicam "
            "mais exames acumulados no período. A comparação utiliza **quantidades absolutas**, "
            "não taxas populacionais. Municípios maiores podem apresentar volumes maiores "
            "sem que isso represente maior cobertura ou melhor desempenho no rastreamento."
        )
    with st.container(key="panorama_volume_sort_panel"):
        ordem_volume = st.selectbox(
            "Ordenar por",
            ["A–Z", "Maior para menor"],
            index=1,
            key="ordenacao_volume_municipios_panorama",
        )
    if ordem_volume == "A–Z":
        bars = bycity.sort_values(
            "municipio", key=lambda nomes: nomes.str.casefold(), kind="stable"
        )
    else:
        bars = bycity.sort_values(
            ["quantidade", "municipio"], ascending=[False, True], kind="stable"
        )
    # Em barras horizontais, a última categoria é exibida no topo.
    ordem_eixo = list(reversed(bars["municipio"].tolist()))
    fig = px.bar(bars, x="quantidade", y="municipio", orientation="h",
                 color_discrete_sequence=[OCEAN],
                 labels={"quantidade":"Exames registrados", "municipio":"Município"},
                 text="quantidade")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                      cliponaxis=False,
                      hovertemplate="%{y}<br>%{x:,.0f} exames<extra></extra>")
    fig.update_xaxes(tickformat=",d", range=[0, max(1, bars.quantidade.max())*1.22])
    fig.update_yaxes(categoryorder="array", categoryarray=ordem_eixo)
    display_chart(fig, filename="panorama_volume_municipio.png")


def renderizar_evolucao_anual(
    annual: pd.DataFrame, years: list[int], agosto_2022_ausente: bool
) -> None:
    """Exibe facetas anuais por município, com ordenação e eixos independentes.

    A grade usa os anos selecionados e mantém NaN onde não há registro.
    """
    st.subheader("Evolução anual de exames por município")
    st.markdown(
        "Mostra a **evolução anual do volume de exames em cada município**, "
        "em gráficos separados para facilitar a comparação de tendências."
    )
    with st.expander("ℹ️ Como interpretar a evolução anual", expanded=False):
        st.markdown(
            "**Eixo horizontal:** anos selecionados. **Eixo vertical:** quantidade anual "
            "de exames do município. Linhas ascendentes indicam aumento de registros; "
            "descendentes, redução. Anos sem registros não são tratados como zero. "
            "As diferenças percentuais entre anos consecutivos podem ser consultadas "
            "na seção **03 — Variação anual da produção**."
        )
        if agosto_2022_ausente:
            st.warning(
                "Agosto/2022 não possui registros no recorte: o total anual de 2022 "
                "pode ficar subestimado em comparações com outros anos."
            )
    if not annual.empty:
        st.markdown("""
            <style>
            /* Somente o seletor de ordenação das facetas do panorama geral. */
            .st-key-panorama_sort_panel [data-testid="stSelectbox"] label p {
                color: #1A3B5C !important;
                font-weight: 700 !important;
                font-size: 0.88rem !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] > div {
                background-color: #FFFFFF !important;
                border: 1.5px solid #8FAFC5 !important;
                border-radius: 9px !important;
                min-height: 43px !important;
                box-shadow: 0 2px 7px rgba(26,59,92,0.07) !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] > div:hover {
                border-color: #006C9A !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] > div:focus-within {
                border-color: #006C9A !important;
                box-shadow: 0 0 0 2px rgba(0,108,154,0.18) !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] * {
                color: #1A3B5C !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] svg {
                fill: #006C9A !important;
            }
            </style>
        """, unsafe_allow_html=True)
        with st.container(key="panorama_sort_panel"):
            order = st.selectbox(
                "Ordenar por",
                ["A–Z", "Maior para menor"],
                key="sort_facetas_panorama",
            )
        municipalities = sorted(annual["municipio"].unique())
        if order == "Maior para menor":
            totals = annual.groupby("municipio")["quantidade"].sum(min_count=1)
            municipalities.sort(
                key=lambda city: (
                    -totals.loc[city] if pd.notna(totals.loc[city]) else float("inf"),
                    city.casefold(),
                )
            )

        # A grade preserva anos ausentes como lacunas nas facetas.
        years_axis = sorted(years)
        grid = pd.MultiIndex.from_product(
            [municipalities, years_axis], names=["municipio", "ano"]
        )
        annual = annual.set_index(["municipio", "ano"]).reindex(grid).reset_index()
        annual["ano_rotulo"] = annual["ano"].astype(int).astype(str)

        fig = px.line(
            annual,
            x="ano_rotulo",
            y="quantidade",
            facet_col="municipio",
            facet_col_wrap=3,
            facet_col_spacing=0.045,
            facet_row_spacing=0.085,
            category_orders={
                "municipio": municipalities,
                "ano_rotulo": [str(year) for year in years_axis],
            },
            markers=True,
            color_discrete_sequence=[OCEAN],
            labels={
                "ano_rotulo": "Ano",
                "quantidade": "Exames registrados",
                "municipio": "Município",
            },
        )
        fig.for_each_annotation(
            lambda annotation: annotation.update(
                text=annotation.text.split("=", 1)[-1],
                font=dict(size=12, color="#1A3B5C"),
            )
        )
        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(size=7),
            connectgaps=False,
            hovertemplate="Ano: %{x}<br>Exames registrados: %{y:,.0f}<extra></extra>",
        )
        fig.update_xaxes(
            matches=None, showticklabels=True, title_text=None,
            type="category", categoryorder="array",
            categoryarray=[str(year) for year in years_axis],
        )
        fig.update_yaxes(
            matches=None, showticklabels=True, title_text=None,
            rangemode="tozero", tickformat=",d",
            gridcolor="#E9EDF1", zeroline=False,
        )
        fig.add_annotation(
            x=-0.065, y=0.5, xref="paper", yref="paper",
            text="Exames registrados", textangle=-90, showarrow=False,
            font=dict(family="Arial", size=13, color="#1A3B5C"),
            xanchor="center", yanchor="middle",
        )
        fig.add_annotation(
            x=0.5, y=-0.025, xref="paper", yref="paper",
            text="Anos", showarrow=False,
            font=dict(family="Arial", size=13, color="#1A3B5C"),
            xanchor="center", yanchor="top",
        )
        fig.update_layout(
            height=max(480, 285 * ((len(municipalities) + 2) // 3)),
            showlegend=False,
            margin=dict(l=95, r=15, t=55, b=105),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            font=dict(color="#1A3B5C", size=11),
        )
        st.caption(
            "No computador, passe o mouse sobre os pontos para consultar os valores. "
            "No celular, toque nos pontos e deslize o gráfico para os lados."
        )
        chart_with_right_click_download(
            fig, filename="panorama_exames_anuais_municipios.png",
            height=fig.layout.height, min_chart_width=820
        )


def construir_matriz_html(pivo_var: pd.DataFrame) -> str:
    """Gera a matriz acessível com classes de sinal e rótulos escapados."""
    cabecalhos_var = (
        '<th scope="col">Município</th>'
        + "".join(
            f'<th scope="col">{escape(str(col))}</th>'
            for col in pivo_var.columns
        )
    )
    linhas_var = []
    for municipio, valores in pivo_var.iterrows():
        celulas = []
        for valor in valores:
            if pd.isna(valor):
                classe = "sem-dado"
            elif valor > 0:
                classe = "aumento"
            elif valor < 0:
                classe = "reducao"
            else:
                classe = "estavel"
            celulas.append(
                f'<td class="{classe}">{fmt_delta(valor)}</td>'
            )
        linhas_var.append(
            '<tr><th scope="row">'
            + escape(str(municipio)) + '</th>'
            + "".join(celulas) + '</tr>'
        )
    tabela_var_html = (
        '<div class="pet-var-scroller" role="region" tabindex="0" '
        'aria-label="Matriz de variação anual de exames por município">'
        '<table class="pet-var-table"><thead><tr>'
        + cabecalhos_var + '</tr></thead><tbody>'
        + "".join(linhas_var) + '</tbody></table></div>'
    )
    return tabela_var_html


def renderizar_ranking_variacao(
    ranking_var: pd.DataFrame, transicao_atual: str
) -> None:
    """Renderiza uma transição anual, com os volumes no tooltip."""
    ranking_plot = ranking_var.sort_values("variacao_pct", ascending=True)
    ranking_plot["cor"] = ranking_plot["variacao_pct"].apply(
        lambda valor: "Aumento" if valor >= 0 else "Redução"
    )
    # Os rótulos pertencem ao DataFrame, pois cada cor gera um trace Plotly.
    ranking_plot["rotulo_variacao"] = ranking_plot["variacao_pct"].map(fmt_delta)
    fig_var = px.bar(
        ranking_plot,
        x="variacao_pct", y="municipio", orientation="h",
        color="cor",
        color_discrete_map={"Aumento": COR_AUMENTO, "Redução": COR_REDUCAO},
        text="rotulo_variacao",
        labels={"variacao_pct": "Variação anual (%)",
                "municipio": "Município"},
        category_orders={"municipio": ranking_plot["municipio"].tolist()},
        custom_data=["quantidade_anterior", "quantidade"],
    )
    fig_var.update_traces(
        texttemplate="%{text}", textposition="outside",
        textfont=dict(size=13, color="#1A3B5C"),
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>" + transicao_atual
            + "<br>Variação: %{x:+.2f}%"
            + "<br>Anterior: %{customdata[0]:,.0f} exames"
            + "<br>Atual: %{customdata[1]:,.0f} exames<extra></extra>"
        ),
    )
    minimo = min(float(ranking_plot["variacao_pct"].min()), 0)
    maximo = max(float(ranking_plot["variacao_pct"].max()), 0)
    margem = max(4, (maximo - minimo) * 0.22)
    fig_var.update_xaxes(
        title="Variação anual (%)",
        range=[minimo - margem, maximo + margem],
        ticksuffix="%", tickfont=dict(size=12, color="#334E68"),
        showgrid=True, gridcolor="#E8F0F6",
        zeroline=True, zerolinecolor="#7C8FA0", zerolinewidth=1.5,
    )
    fig_var.update_yaxes(
        title=None, tickfont=dict(size=13, color="#1A3B5C"),
        automargin=True,
    )
    fig_var.update_layout(
        height=max(440, 41 * len(ranking_plot) + 110),
        margin=dict(l=18, r=60, t=28, b=55),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        showlegend=False, font=dict(color="#1A3B5C", size=13),
        bargap=0.28,
    )
    display_chart(fig_var, filename=f"panorama_variacao_{transicao_atual.replace('→', '_')}.png")


def renderizar_variacao_anual(
    var_ano: pd.DataFrame, agosto_2022_ausente: bool
) -> None:
    """Exibe matriz, rankings independentes e dados de variação anual."""
    st.markdown(
        '<h2 class="panorama-section-title"><span class="panorama-section-index">03</span>'
        'Variação anual da produção</h2>', unsafe_allow_html=True,
    )

    st.subheader("Variação anual de exames por município (ano a ano)")
    st.caption(
        "Esta seção mostra quanto a quantidade de exames registrados aumentou "
        "ou diminuiu em cada município de um ano para o seguinte. "
        "O indicador representa mudança no volume de registros, não na "
        "quantidade de mulheres atendidas nem na cobertura do rastreamento."
    )

    if not var_ano["variacao_pct"].notna().any():
        st.info(
            "Selecione pelo menos dois anos consecutivos nos filtros para "
            "calcular a variação anual por município."
        )
    else:
        pivo_var = var_ano.pivot_table(
            index="municipio", columns="transicao",
            values="variacao_pct", aggfunc="mean",
        )
        pivo_var = pivo_var[
            sorted(pivo_var.columns, key=lambda c: int(str(c).split("→")[1]))
        ]
        st.markdown("#### Variação anual (%) por município e transição")
        st.markdown(
            "Compara a **variação percentual dos exames entre anos consecutivos** "
            "para cada município. Azul indica aumento e vermelho indica redução."
        )
        with st.expander("ℹ️ Como interpretar a matriz de variação", expanded=False):
            st.markdown(
                "Cada **linha** corresponde a um município e cada **coluna** a uma "
                "transição, como 2023→2024. **+20.00%** significa 20% mais exames "
                "que no ano anterior; **-20.00%**, 20% menos. O percentual toma "
                "como base o **primeiro ano** da comparação. O símbolo **—** "
                "representa comparação indisponível. O indicador mede registros "
                "de exames, não cobertura de mulheres rastreadas. "
                "**Cálculo:** (exames no ano atual − exames no ano anterior) "
                "÷ exames no ano anterior × 100. "
                "Azul indica aumento; vermelho, redução; valores próximos de zero "
                "indicam pouca mudança. A comparação exige anos consecutivos "
                "e um total de exames maior que zero no primeiro ano."
            )
        modo_ordem_var = st.selectbox(
            "Ordenar por",
            ["A–Z", "Maior para menor (última variação)"],
            index=0,
            key="ordenacao_matriz_variacao_panorama",
            help="A ordenação por variação considera a transição anual mais recente "
                 "disponível nos filtros; comparações indisponíveis ficam ao final.",
        )
        if modo_ordem_var == "A–Z":
            pivo_var = pivo_var.sort_index(key=lambda nomes: nomes.str.casefold())
        else:
            ultima_coluna_matriz = pivo_var.columns[-1]
            pivo_var = pivo_var.sort_values(
                by=ultima_coluna_matriz,
                ascending=False,
                na_position="last",
                kind="stable",
            )

        tabela_var_html = construir_matriz_html(pivo_var)
        st.markdown(
            """
            <style>
            .pet-var-scroller {
                width:100%; overflow-x:auto; border-radius:8px;
                box-shadow:0 2px 7px rgba(26,59,92,.09);
                margin:12px 0 17px; border:1px solid #E6EBF0;
            }
            .pet-var-table {
                width:100%; min-width:720px; border-collapse:separate;
                border-spacing:0; background:#FFFFFF; color:#1A3B5C;
                font:500 .88rem Manrope,Arial,sans-serif;
            }
            .pet-var-table thead th {
                background:#1A3B5C; color:#FFFFFF;
                padding:15px 14px; text-align:center; white-space:nowrap;
                font-size:.87rem; font-weight:750;
                border-right:1px solid rgba(255,255,255,.14);
                position:sticky; top:0; z-index:2;
            }
            .pet-var-table thead th:first-child {
                text-align:left; left:0; z-index:4; min-width:190px;
            }
            .pet-var-table tbody th {
                position:sticky; left:0; z-index:1;
                color:#1A3B5C; text-align:left; font-weight:750;
                padding:13px 14px; white-space:nowrap;
                background:#FFFFFF; border-bottom:1px solid #E7EBEF;
                border-right:1px solid #D8E5EF;
            }
            .pet-var-table tbody tr:nth-child(even) th {background:#F6F8FA;}
            .pet-var-table tbody tr:hover th {background:#ECF5FA;}
            .pet-var-table tbody td {
                padding:13px 14px; text-align:center; font-weight:700;
                white-space:nowrap; border-bottom:1px solid #E7EBEF;
                border-right:1px solid #FFFFFF;
                font-variant-numeric:tabular-nums;
            }
            .pet-var-table td.aumento {background:#E8F0F6;color:#143650;}
            .pet-var-table td.reducao {background:#FDE8E4;color:#A83A20;}
            .pet-var-table td.estavel {background:#F4F7FA;color:#334E68;}
            .pet-var-table td.sem-dado {background:#F1F5F9;color:#64748B;}
            .pet-var-table tbody tr:hover td {filter:brightness(.97);}
            @media(max-width:768px){
                .pet-var-table {font-size:.82rem;min-width:690px;}
                .pet-var-table thead th,.pet-var-table tbody td,
                .pet-var-table tbody th {padding:12px 10px;}
                .pet-var-table thead th:first-child {min-width:165px;}
            }
            </style>
            """ + tabela_var_html,
            unsafe_allow_html=True,
        )
        export_matriz_var = pivo_var.reset_index().rename(columns={"municipio": "Município"})
        st.download_button(
            "⬇️ Exportar matriz de variação anual (CSV)",
            data=export_matriz_var.to_csv(
                index=False, sep=";", decimal=".", float_format="%.2f"
            ).encode("utf-8-sig"),
            file_name="siscan_matriz_variacao_anual_municipios.csv",
            mime="text/csv",
            key="exportar_matriz_variacao_panorama",
        )
        if agosto_2022_ausente and any(
            "2022" in str(coluna) for coluna in pivo_var.columns
        ):
            st.caption(
                "⚠️ Agosto/2022 não possui registros no recorte. As transições "
                "que incluem 2022 podem ser afetadas por essa ausência."
            )

        st.markdown(
            "Visualize a **variação percentual por município** em cada "
            "comparação anual. **Azul, à direita do zero**, indica aumento; "
            "**vermelho, à esquerda**, indica redução."
        )
        with st.expander("ℹ️ Como interpretar o ranking", expanded=False):
            st.markdown(
                "Cada ranking compara o total de exames de **dois anos consecutivos**. "
                "Quanto maior a distância da barra ao zero, maior a variação. "
                "São **percentuais de mudança**, não quantidades absolutas. "
                "Passe o mouse sobre as barras para conferir os dois volumes. "
                "Na opção **Todas as transições**, cada período é apresentado "
                "separadamente; os percentuais não são somados nem calculados "
                "como uma média entre anos."
            )
        transicoes_disponiveis = list(pivo_var.columns)
        todas_transicoes = "Todas as transições"
        transicao_ranking = st.selectbox(
            "Comparar a transição anual",
            options=[todas_transicoes] + transicoes_disponiveis,
            index=1,
            key="transicao_ranking_panorama",
            help="Veja todos os rankings anuais ou escolha uma transição específica. "
                 "Cada comparação utiliza dois anos consecutivos com registros.",
        )
        modo_todas = transicao_ranking == todas_transicoes
        transicoes_ranking = (
            transicoes_disponiveis if modo_todas else [transicao_ranking]
        )
        if agosto_2022_ausente and any(
            "2022" in t for t in transicoes_ranking
        ):
            st.caption(
                "⚠️ As comparações que incluem 2022 podem ser afetadas "
                "pela ausência de registros de agosto/2022."
            )

        for transicao_atual in transicoes_ranking:
            ranking_var = var_ano.loc[
                var_ano["transicao"].eq(transicao_atual)
                & var_ano["variacao_pct"].notna()
            ].copy()
            st.markdown(f"#### Ranking de variação — {transicao_atual}")
            if ranking_var.empty:
                st.info("Não há valores calculáveis para esta transição no recorte.")
                continue
            renderizar_ranking_variacao(ranking_var, transicao_atual)

        with st.expander("Ver dados detalhados da variação anual", expanded=False):
            detalhe_var = var_ano.loc[
                var_ano["variacao_pct"].notna(), [
                    "municipio", "transicao", "ano_anterior",
                    "quantidade_anterior", "ano", "quantidade", "variacao_pct",
                ]
            ].copy()
            ordem_detalhe_var = st.selectbox(
                "Ordenar por",
                ["A–Z (município)", "Maior para menor (variação %)",
                 "Menor para maior (variação %)"],
                key="ordenacao_detalhe_variacao_panorama",
            )
            if ordem_detalhe_var == "A–Z (município)":
                detalhe_var = detalhe_var.sort_values(
                    ["municipio", "ano"], key=lambda serie: (
                        serie.str.casefold() if serie.name == "municipio" else serie
                    ), kind="stable",
                )
            else:
                detalhe_var = detalhe_var.sort_values(
                    ["variacao_pct", "municipio"],
                    ascending=[ordem_detalhe_var.startswith("Menor"), True],
                    kind="stable",
                )
            tabela_detalhe_var = detalhe_var.rename(columns={
                "municipio": "Município", "transicao": "Transição",
                "ano_anterior": "Ano anterior",
                "quantidade_anterior": "Exames no ano anterior",
                "ano": "Ano atual", "quantidade": "Exames no ano atual",
                "variacao_pct": "Variação anual (%)",
            })
            display_table(
                tabela_detalhe_var,
                integer_columns=["Ano anterior", "Exames no ano anterior",
                                 "Ano atual", "Exames no ano atual"],
                percent_columns=["Variação anual (%)"],
            )
            st.download_button(
                "⬇️ Exportar dados detalhados da variação anual (CSV)",
                data=tabela_detalhe_var.to_csv(
                    index=False, sep=";", decimal=".", float_format="%.2f"
                ).encode("utf-8-sig"),
                file_name="siscan_variacao_anual_municipios.csv",
                mime="text/csv",
                key="exportar_detalhe_variacao_panorama",
            )


def renderizar_detalhamento(df: pd.DataFrame) -> None:
    """Exibe a produção detalhada com ordenação e exportação CSV."""
    detail = df[["municipio", "ano", "mes", "quantidade"]].copy()
    detail["mes"] = detail["mes"].astype(int).map(dict(enumerate(MESES_PT, start=1)))
    detail = detail.rename(columns={
        "municipio":"Município", "ano":"Ano", "mes":"Mês", "quantidade":"Exames registrados"
    })
    with st.expander("Ver dados detalhados da produção", expanded=False):
        ordem_producao = st.selectbox(
            "Ordenar por",
            ["A–Z (município)", "Maior para menor (exames registrados)",
             "Menor para maior (exames registrados)"],
            key="ordenacao_detalhe_producao_panorama",
        )
        if ordem_producao == "A–Z (município)":
            detail = detail.sort_values(
                ["Município", "Ano"],
                key=lambda serie: (
                    serie.str.casefold() if serie.name == "Município" else serie
                ),
                kind="stable",
            )
        else:
            detail = detail.sort_values(
                ["Exames registrados", "Município"],
                ascending=[ordem_producao.startswith("Menor"), True],
                kind="stable",
            )
        display_table(detail, integer_columns=['Ano', 'Exames registrados'])
        st.download_button(
            "⬇️ Exportar dados filtrados (CSV)",
            detail.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name="siscan_panorama.csv",
            mime="text/csv",
        )
    st.caption("**Como interpretar:** maior volume não significa necessariamente maior cobertura "
               "populacional ou melhor desempenho. A participação municipal usa como denominador "
               "o total de exames dos municípios selecionados.")


def main() -> None:
    """Orquestra a página após validar a disponibilidade da Gold temporal."""
    configurar_pagina()
    df = filtered("temporal")
    if not require(df, COLUNAS_OBRIGATORIAS):
        return

    years = selected_years()
    monthly = agregar_mensal(df)
    bycity = agregar_municipios(df)
    annual = agregar_anual(df)
    series, complete, missing = preparar_serie_mensal(monthly, years)
    agosto_2022_ausente = COMPETENCIA_AUSENTE in missing

    renderizar_indicadores(df, monthly, bycity, years)
    renderizar_disponibilidade(missing, len(monthly), 12 * len(years))
    renderizar_evolucao_mensal(series, complete, agosto_2022_ausente)
    renderizar_volume_municipal(bycity)
    renderizar_evolucao_anual(annual, years, agosto_2022_ausente)
    renderizar_variacao_anual(calcular_variacao_anual(annual), agosto_2022_ausente)
    renderizar_detalhamento(df)


if __name__ == "__main__":
    main()
