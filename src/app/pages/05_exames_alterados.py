"""Exames citopatológicos alterados na 10ª CRS.

Separa a proporção operacional de alterados entre exames válidos da
composição entre categorias citopatológicas. A alocação proporcional
das exclusões de adequabilidade por idade é uma estimativa da Gold.
"""

import copy

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, require, selected_years, sidebar_filters
from utils.theme import (
    NAVY, OCEAN, ORANGE, apply_custom_css, export_table, fmt_num, fmt_pct,
    metric_row, page_header, pct,
)

GRUPOS_ETARIOS = ("<25 anos", "25–64 anos", "≥65 anos")
ROTULOS_GRUPOS = {
    "<= 24 anos": "<25 anos",
    "25 a 64 anos": "25–64 anos",
    ">= 65 anos": "≥65 anos",
}
CORES_GRUPOS = {"<25 anos": "#169B62", "25–64 anos": "#1757A6", "≥65 anos": ORANGE}
CORES_CATEGORIAS = (
    "#006C9A", "#E85D2A", "#218B65", "#6B5FB5",
    "#D49B22", "#1A3B5C", "#C24B75", "#54A8C3",
)
ANOS_CONSOLIDADOS = tuple(range(2020, 2026))
LIMIAR_ROTULO_PCT = 6
COLUNAS_ALTERADOS = (
    "municipio", "faixa_etaria", "grupo_etario_3",
    "quantidade_alterados", "total_exames_validos",
)
COLUNAS_CATEGORIA_ANUAL = {"ano", "municipio", "categoria", "quantidade_alterados"}
COLUNAS_CATEGORIA_FAIXA = {"categoria", "grupo_etario_3", "quantidade_alterados"}


def preparar_alterados(df: pd.DataFrame) -> pd.DataFrame:
    """Classifica grupos etários sem atribuir idade aos registros ignorados.

    Args:
        df: Fato Gold de exames alterados no recorte ativo.

    Returns:
        Cópia dos registros com grupo etário reconhecido.

    Raises:
        ValueError: Quando a Gold contém rótulos etários inesperados.
    """
    dados = df.copy()
    grupos = dados["grupo_etario_3"].astype("string").str.strip()
    dados["grupo_3"] = grupos.map(ROTULOS_GRUPOS)
    desconhecidos = grupos.loc[
        dados["grupo_3"].isna() & grupos.ne("Ignorado")
    ].dropna().unique().tolist()
    if desconhecidos:
        raise ValueError(
            "Categorias etárias inesperadas na Gold: "
            + ", ".join(map(str, desconhecidos))
        )
    return dados.loc[dados["grupo_3"].notna()].copy()


def safe_percent(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Calcula percentuais sem atribuir zero a uma base ausente ou não positiva."""
    return numerator.div(denominator.where(denominator.gt(0))).mul(100)


def agregar_proporcao(
    df: pd.DataFrame, chaves: list[str], coluna: str = "proporcao_pct"
) -> pd.DataFrame:
    """Consolida numeradores e denominadores antes de calcular a proporção.

    O denominador de exames válidos é o estimado na Gold. Não utiliza
    médias de percentuais por faixa, município ou ano.
    """
    resultado = df.groupby(chaves, as_index=False)[
        ["quantidade_alterados", "total_exames_validos"]
    ].sum(min_count=1)
    resultado[coluna] = safe_percent(
        resultado["quantidade_alterados"], resultado["total_exames_validos"]
    )
    return resultado


def agregar_quantidades(df: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Soma os registros alterados pelas dimensões solicitadas."""
    return (
        df.groupby(chaves, as_index=False)["quantidade_alterados"]
        .sum(min_count=1)
    )


def preparar_composicao(df: pd.DataFrame, chaves: list[str], base: str) -> pd.DataFrame:
    """Consolida categorias e calcula participação dentro da dimensão base.

    Args:
        df: Fato Gold de composição citopatológica.
        chaves: Dimensões de agrupamento, incluindo a base.
        base: Campo que define o total de referência (ano, município ou categoria).

    Returns:
        Quantidades e participações entre registros classificados.
        Grupos com denominador zero conservam NaN nos percentuais.
    """
    dados = df.copy()
    dados["quantidade_alterados"] = pd.to_numeric(
        dados["quantidade_alterados"], errors="coerce"
    )
    dados_validos = dados.dropna(subset=[*chaves, "quantidade_alterados"])
    resultado = agregar_quantidades(dados_validos, chaves)
    denominador = resultado.groupby(base)["quantidade_alterados"].transform("sum")
    resultado["participacao_pct"] = safe_percent(
        resultado["quantidade_alterados"], denominador
    )
    return resultado


def preparar_rotulos_exportacao(dados: pd.DataFrame, percentual: bool) -> pd.DataFrame:
    """Acrescenta rótulos somente a segmentos suficientemente largos no PNG."""
    resultado = dados.copy()
    campo = "participacao_pct" if percentual else "quantidade_alterados"
    formatar = (
        (lambda valor: f"{valor:.2f}%")
        if percentual else (lambda valor: f"{valor:,.0f}".replace(",", "."))
    )
    mascara = resultado["participacao_pct"].ge(LIMIAR_ROTULO_PCT) & resultado[campo].notna()
    resultado["rotulo_exportacao"] = ""
    resultado.loc[mascara, "rotulo_exportacao"] = resultado.loc[mascara, campo].map(
        formatar
    )
    return resultado


def ordenar_municipios(
    dados: pd.DataFrame, modo: str, alfabetico_casefold: bool = True
) -> list[str]:
    """Ordena municípios alfabeticamente ou pelo volume acumulado de alterações."""
    nomes = dados["municipio"].unique().tolist()
    municipios = sorted(nomes, key=str.casefold) if alfabetico_casefold else sorted(nomes)
    if modo == "Maior para menor":
        totais = dados.groupby("municipio")["quantidade_alterados"].sum(min_count=1)
        municipios.sort(key=lambda nome: (
            -float(totais.loc[nome]) if pd.notna(totais.loc[nome]) else float("inf"),
            nome.casefold(),
        ))
    return municipios


def completar_grade_anual(
    dados: pd.DataFrame, municipios: list[str], anos: list[int],
    por_grupo: bool = False,
) -> pd.DataFrame:
    """Completa somente o calendário de exibição, deixando lacunas como NaN."""
    chaves = ["municipio", "ano"]
    dimensoes = [municipios, anos]
    if por_grupo:
        chaves.append("grupo_3")
        dimensoes.append(list(GRUPOS_ETARIOS))
    indice = pd.MultiIndex.from_product(dimensoes, names=chaves)
    resultado = dados.set_index(chaves).reindex(indice).reset_index()
    resultado["ano_label"] = resultado["ano"].astype(str)
    return resultado


def configurar_pagina() -> None:
    """Configura estilos locais, cabeçalho e filtros compartilhados."""
    st.set_page_config(page_title="Exames alterados | SISCAN", layout="wide")
    apply_custom_css()
    sidebar_filters()
    st.markdown("""
    <style>
    .pet-hero .pet-hero-desc {
        font-family: Manrope, Arial, sans-serif !important;
        font-size: 1.15rem !important;
        line-height: 1.65 !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
        max-width: 900px !important;
    }
    @media (max-width: 768px) {
        .pet-hero .pet-hero-desc {
            font-size: 1rem !important;
            line-height: 1.55 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
    /* O cabeçalho não deve sobrepor o primeiro título de seção. */
    .pet-hero {
        margin-bottom: 0 !important;
    }
    .q5-section-title {
        margin: 30px 0 17px;
        padding: 9px 0 12px;
        border-bottom: 2px solid #D8E5EF;
        font: 750 clamp(21px, 2vw, 26px)/1.35 Manrope, Arial, sans-serif;
        color: #1A3B5C;
    }
    .q5-section-title .q5-section-index {
        color: #006C9A;
        margin-right: 10px;
    }
    @media (max-width: 768px) {
        .q5-section-title {margin: 24px 0 13px; font-size: 21px;}
    }
    </style>
    """, unsafe_allow_html=True)

    page_header(
        "Resultados",
        "Exames citopatológicos alterados",
        "Apresenta a quantidade e a proporção de exames citopatológicos alterados "
        "entre os exames válidos, sua evolução anual e a distribuição por município, "
        "faixa etária e categoria citopatológica, conforme o recorte selecionado.",
    )


def renderizar_panorama(df: pd.DataFrame) -> None:
    """Exibe os totais e a proporção operacional dos exames de idade conhecida."""
    num = df["quantidade_alterados"].sum(min_count=1)
    den = df["total_exames_validos"].sum(min_count=1)
    st.markdown(
        '<h2 class="q5-section-title"><span class="q5-section-index">01</span>'
        'Panorama dos exames alterados</h2>',
        unsafe_allow_html=True,
    )
    metric_row([
        ("Exames alterados", fmt_num(num)),
        ("Proporção operacional", fmt_pct(pct(num, den)) if pd.notna(den) and den > 0 else "N/D"),
        ("Exames válidos (denominador)", fmt_num(den) if pd.notna(den) else "N/D"),
    ])
    with st.expander("ℹ️ Como é calculada a proporção operacional?", expanded=False):
        st.markdown(
            "**Fórmula:** (soma de exames alterados ÷ soma dos exames válidos) × 100. "
            "Somamos primeiro numeradores e denominadores dos municípios, anos e "
            "grupos selecionados; **não** calculamos a média simples de percentuais.\n\n"
            "**Base de comparação:** a Gold desconta amostras rejeitadas e "
            "insatisfatórias do total de exames. Como o SISCAN não disponibiliza "
            "o cruzamento de adequabilidade por faixa etária, essas exclusões são "
            "**distribuídas proporcionalmente por idade em cada município/ano**. "
            "Esse pressuposto torna o percentual uma **estimativa operacional**, "
            "não uma taxa clínica de risco, prevalência ou cobertura.\n\n"
            "**Limitações:** registros sem grupo etário identificável não entram "
            "nos cartões; exames não correspondem necessariamente a pessoas distintas."
        )


def renderizar_proporcao_etaria(df: pd.DataFrame) -> None:
    """Exibe proporções por grupo, usando os exames válidos do próprio grupo."""
    st.markdown("### Proporção operacional de exames alterados por grupo etário")
    st.markdown(
        "Compara a **proporção de exames citopatológicos alterados** nos grupos "
        "etários de menores de 25 anos, 25–64 anos e 65 anos ou mais."
    )
    with st.expander("ℹ️ Como interpretar a proporção por grupo etário", expanded=False):
        st.markdown(
            "**Eixo horizontal:** grupos etários. **Eixo vertical:** proporção de "
            "exames alterados (%). Cada barra mostra quantos exames tiveram "
            "resultado alterado em relação ao total de **exames válidos do próprio "
            "grupo**, e não ao total de todos os grupos. "
            "**Proporção (%) = exames alterados ÷ exames válidos × 100.** "
            "Uma barra mais alta indica maior proporção de resultados alterados "
            "naquele grupo, não necessariamente maior quantidade de exames. "
            "A medida se refere a exames, não a mulheres distintas."
        )
    macro = agregar_proporcao(df, ["grupo_3"])
    macro["grupo_3"] = pd.Categorical(
        macro["grupo_3"], categories=list(GRUPOS_ETARIOS), ordered=True
    )
    macro = macro.sort_values("grupo_3").dropna(subset=["proporcao_pct"])
    if not macro.empty:
        macro_fig = px.bar(
            macro, x="grupo_3", y="proporcao_pct", color="grupo_3",
            category_orders={"grupo_3": list(GRUPOS_ETARIOS)},
            color_discrete_map=CORES_GRUPOS,
            custom_data=["quantidade_alterados", "total_exames_validos"],
            labels={"grupo_3": "Grupo etário", "proporcao_pct": "Proporção (%)"},
        )
        macro_fig.update_layout(
            showlegend=False,
            bargap=0.54,
            margin=dict(l=90, r=90, t=30, b=70),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
        )
        macro_fig.update_yaxes(rangemode="tozero", ticksuffix="%", tickformat=".2f")
        macro_fig.update_traces(
            hovertemplate=(
                "Faixa: %{x}<br>Proporção: %{y:.2f}%"
                "<br>Exames alterados: %{customdata[0]:,.0f}"
                "<br>Exames válidos: %{customdata[1]:,.0f}<extra></extra>"
            )
        )
        macro_export = copy.deepcopy(macro_fig)
        macro_export.update_traces(
            texttemplate="%{y:.2f}%", textposition="outside",
            textfont=dict(size=15, color=NAVY), cliponaxis=False,
        )
        macro_export.update_layout(
            title=dict(
                text="Proporção de exames alterados por grupo etário",
                x=0.5, xanchor="center", font=dict(size=21, color=NAVY),
            ),
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            margin=dict(l=85, r=40, t=100, b=80),
        )
        _, chart_col, _ = st.columns([1, 10, 1], gap="small")
        with chart_col:
            chart_with_right_click_download(
                macro_fig, filename="exames_alterados_grupos_etarios.png",
                height=410, export_fig=macro_export,
            )


def renderizar_evolucao_municipal(df: pd.DataFrame) -> None:
    """Exibe facetas anuais por município, sem preencher ausências com zero."""
    st.markdown(
        '<h2 class="q5-section-title"><span class="q5-section-index">02</span>'
        'Evolução temporal dos exames alterados</h2>',
        unsafe_allow_html=True,
    )

    st.markdown("### Evolução anual de exames alterados por município")
    st.markdown(
        "Mostra a **evolução anual do total de exames alterados em cada município**, "
        "considerando os grupos etários disponíveis no recorte selecionado."
    )
    with st.expander("ℹ️ Como interpretar a evolução anual por município", expanded=False):
        st.markdown(
            "Cada painel representa um município. No **eixo horizontal** estão "
            "os anos e no **vertical**, a quantidade anual de exames alterados. "
            "Linhas ascendentes representam mais exames alterados registrados "
            "do que no ano anterior; descendentes, menos. "
            "Os valores são **contagens**, não proporções. "
            "Municípios com maior volume de exames podem registrar mais alterações "
            "sem apresentar maior percentual de resultados alterados. "
            "Anos sem registros aparecem como lacunas, e não como zero. "
            "Compare as proporções no gráfico etário ou na matriz territorial "
            "para avaliar diferenças relativas."
        )
    if "ano" not in df.columns:
        st.info("O gráfico anual requer a coluna 'ano' na tabela Gold de exames alterados.")
    else:
        yearly = agregar_quantidades(df.dropna(subset=["ano"]), ["municipio", "ano"])
        yearly["ano"] = yearly["ano"].astype(int)
        if not yearly.empty:
            st.markdown("""
                <style>
                /* Somente o seletor de ordenação das facetas de exames alterados. */
                .st-key-alterados_sort_panel [data-testid="stSelectbox"] label p {
                    color: #1A3B5C !important;
                    font-weight: 700 !important;
                    font-size: 0.88rem !important;
                }
                .st-key-alterados_sort_panel [data-baseweb="select"] > div {
                    background-color: #FFFFFF !important;
                    border: 1.5px solid #8FAFC5 !important;
                    border-radius: 9px !important;
                    min-height: 43px !important;
                    box-shadow: 0 2px 7px rgba(26,59,92,0.07) !important;
                }
                .st-key-alterados_sort_panel [data-baseweb="select"] > div:hover {
                    border-color: #006C9A !important;
                }
                .st-key-alterados_sort_panel [data-baseweb="select"] > div:focus-within {
                    border-color: #006C9A !important;
                    box-shadow: 0 0 0 2px rgba(0,108,154,0.18) !important;
                }
                .st-key-alterados_sort_panel [data-baseweb="select"] * {
                    color: #1A3B5C !important;
                }
                .st-key-alterados_sort_panel [data-baseweb="select"] svg {
                    fill: #006C9A !important;
                }
                </style>
            """, unsafe_allow_html=True)
            with st.container(key="alterados_sort_panel"):
                sort_mode = st.selectbox(
                    "Ordenar por",
                    options=[
                        "A–Z",
                        "Maior para menor",
                    ],
                    key="sort_facetas_alterados",
                )
            municipalities = ordenar_municipios(yearly, sort_mode, alfabetico_casefold=False)
            axis_years = selected_years() or sorted(yearly["ano"].astype(int).unique())
            yearly = completar_grade_anual(yearly, municipalities, axis_years)
            fig_yearly = px.line(
                yearly,
                x="ano_label",
                y="quantidade_alterados",
                facet_col="municipio",
                facet_col_wrap=3,
                facet_col_spacing=0.045,
                facet_row_spacing=0.085,
                category_orders={
                    "municipio": municipalities,
                    "ano_label": [str(y) for y in axis_years],
                },
                markers=True,
                color_discrete_sequence=[OCEAN],
                labels={
                    "ano_label": "Ano",
                    "quantidade_alterados": "Exames alterados",
                    "municipio": "Município",
                },
            )
            fig_yearly.for_each_annotation(
                lambda annotation: annotation.update(
                    text=annotation.text.split("=", 1)[-1],
                    font=dict(size=12, color="#1A3B5C"),
                )
            )
            fig_yearly.update_traces(
                line=dict(width=2.5),
                marker=dict(size=7),
                connectgaps=False,
                hovertemplate="Ano: %{x}<br>Exames alterados: %{y:,.0f}<extra></extra>",
            )
            fig_yearly.update_yaxes(
                matches=None, showticklabels=True, title_text=None,
                rangemode="tozero", gridcolor="#E9EDF1", zeroline=False
            )
            fig_yearly.add_annotation(
                x=-0.065, y=0.5, xref="paper", yref="paper",
                text="Exames alterados", textangle=-90, showarrow=False,
                font=dict(family="Arial", size=13, color="#1A3B5C"),
                xanchor="center", yanchor="middle",
            )
            fig_yearly.update_xaxes(
                matches=None, showticklabels=True, title_text=None,
                type="category", categoryorder="array",
                categoryarray=[str(y) for y in axis_years]
            )
            fig_yearly.add_annotation(
                x=0.5, y=-0.025, xref="paper", yref="paper",
                text="Anos", showarrow=False,
                font=dict(family="Arial", size=13, color="#1A3B5C"),
                xanchor="center", yanchor="top",
            )
            fig_yearly.update_layout(
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
                fig_yearly, filename="exames_alterados_anuais_municipios.png",
                height=fig_yearly.layout.height, min_chart_width=820
            )
        else:
            st.info("Não há registros anuais de exames alterados para o recorte selecionado.")


def renderizar_evolucao_por_grupo(df: pd.DataFrame) -> None:
    """Exibe linhas anuais por grupo etário e município com lacunas preservadas."""
    st.markdown("### Evolução anual de exames alterados por município e grupo etário")
    st.markdown(
        "Apresenta a **quantidade anual de exames alterados por município**, "
        "com linhas separadas para os três grupos etários no período selecionado."
    )
    with st.expander("ℹ️ Como interpretar a evolução anual por grupo etário", expanded=False):
        st.markdown(
            "Cada painel corresponde a um **município**. **Eixo horizontal:** "
            "anos selecionados. **Eixo vertical:** quantidade de exames alterados. "
            "As cores e os símbolos identificam os grupos **<25 anos**, "
            "**25–64 anos** e **≥65 anos**. Linhas ascendentes indicam aumento "
            "de registros alterados; descendentes, redução. "
            "**Este gráfico apresenta quantidades absolutas, não percentuais.** "
            "Um aumento pode acompanhar mudanças no volume total de exames; "
            "não significa, isoladamente, maior risco ou prevalência de alterações. "
            "Ausências de registros não devem ser interpretadas automaticamente como zero."
        )
    if "ano" not in df.columns:
        st.info("A evolução anual requer a coluna 'ano' na tabela Gold.")
    else:
        lines_source = df.copy()
        lines_source["ano"] = pd.to_numeric(lines_source["ano"], errors="coerce")
        lines_source["quantidade_alterados"] = pd.to_numeric(
            lines_source["quantidade_alterados"], errors="coerce"
        )
        lines_source = lines_source.dropna(
            subset=["municipio", "ano", "grupo_3", "quantidade_alterados"]
        )
        lines_source = lines_source.loc[
            lines_source["grupo_3"].isin(list(GRUPOS_ETARIOS))
            & (lines_source["quantidade_alterados"] >= 0)
        ].copy()
        if lines_source.empty:
            st.info("Não há exames alterados por município e grupo etário no período selecionado.")
        else:
            lines_yearly = agregar_quantidades(
                lines_source, ["municipio", "ano", "grupo_3"]
            )
            lines_yearly["ano"] = lines_yearly["ano"].astype(int)
            st.markdown("""
                <style>
                .st-key-alterados_sort_grupos_panel [data-testid="stSelectbox"] label p {
                    color: #1A3B5C !important;
                    font-weight: 700 !important;
                    font-size: 0.88rem !important;
                }
                .st-key-alterados_sort_grupos_panel [data-baseweb="select"] > div {
                    background: #FFFFFF !important;
                    border: 1.5px solid #8FAFC5 !important;
                    border-radius: 9px !important;
                    min-height: 43px !important;
                }
                .st-key-alterados_sort_grupos_panel [data-baseweb="select"] * {
                    color: #1A3B5C !important;
                }
                </style>
            """, unsafe_allow_html=True)
            with st.container(key="alterados_sort_grupos_panel"):
                sort_grupos = st.selectbox(
                    "Ordenar por",
                    options=["A–Z", "Maior para menor"],
                    key="sort_facetas_grupos_alterados",
                    help=(
                        "Maior para menor considera o total de exames alterados "
                        "dos três grupos no período e municípios selecionados."
                    ),
                )
            municipios_lines = ordenar_municipios(lines_yearly, sort_grupos)
            anos_lines = selected_years() or sorted(lines_yearly["ano"].unique().tolist())
            lines_yearly = completar_grade_anual(
                lines_yearly, municipios_lines, anos_lines, por_grupo=True
            )
            fig_lines = px.line(
                lines_yearly,
                x="ano_label",
                y="quantidade_alterados",
                color="grupo_3",
                facet_col="municipio",
                facet_col_wrap=2,
                facet_col_spacing=0.075,
                facet_row_spacing=0.075,
                category_orders={
                    "municipio": municipios_lines,
                    "ano_label": [str(ano) for ano in anos_lines],
                    "grupo_3": list(GRUPOS_ETARIOS),
                },
                color_discrete_map=CORES_GRUPOS,
                labels={
                    "ano_label": "Anos",
                    "quantidade_alterados": "Exames alterados",
                    "grupo_3": "Grupo etário",
                    "municipio": "Município",
                },
                markers=True,
            )
            fig_lines.for_each_annotation(
                lambda annotation: annotation.update(
                    text=annotation.text.split("=", 1)[-1],
                    font=dict(size=12, color=NAVY),
                )
            )
            fig_lines.update_traces(
                hovertemplate=(
                    "Ano: %{x}<br>Exames alterados: %{y:,.0f}"
                    "<extra>%{fullData.name}</extra>"
                ),
                line=dict(width=2.5),
                marker=dict(size=7),
                connectgaps=False,
            )
            # Desenha as séries coincidentes de zero em ordem de contraste.
            ordem_desenho = {"≥65 anos": 0, "25–64 anos": 1, "<25 anos": 2}
            fig_lines.data = tuple(
                sorted(
                    fig_lines.data,
                    key=lambda trace: ordem_desenho.get(trace.name, 3),
                )
            )
            for trace in fig_lines.data:
                grupo = trace.name
                trace.update(
                    legendrank={
                        "<25 anos": 1, "25–64 anos": 2, "≥65 anos": 3
                    }.get(grupo, 4),
                    line=dict(
                        width=4 if grupo == "≥65 anos" else 2.8,
                        dash="dot" if grupo == "≥65 anos" else "solid",
                    ),
                    marker=dict(
                        size=8,
                        symbol={
                            "<25 anos": "circle",
                            "25–64 anos": "diamond",
                            "≥65 anos": "square",
                        }.get(grupo, "circle"),
                    ),
                )
            fig_lines.update_xaxes(
                type="category",
                categoryorder="array",
                categoryarray=[str(ano) for ano in anos_lines],
                showticklabels=True,
                matches=None,
                title_text=None,
                showgrid=False,
                showline=False,
            )
            fig_lines.update_yaxes(
                matches=None,
                showticklabels=True,
                title_text=None,
                rangemode="tozero",
                tickformat=",.0f",
                gridcolor="#E9EDF1",
            )
            fig_lines.add_annotation(
                x=-0.065, y=0.5, xref="paper", yref="paper",
                text="Exames alterados", textangle=-90,
                showarrow=False, font=dict(size=13, color=NAVY),
            )
            fig_lines.add_annotation(
                x=0.5, y=-0.025, xref="paper", yref="paper",
                text="Anos", showarrow=False,
                font=dict(size=13, color=NAVY),
            )
            n_linhas = (len(municipios_lines) + 1) // 2
            fig_lines.update_layout(
                height=max(520, 360 * n_linhas),
                showlegend=True,
                legend=dict(
                    title_text="", orientation="h",
                    x=0.5, xanchor="center", y=1.06, yanchor="bottom",
                    font=dict(size=12, color=NAVY),
                ),
                margin=dict(l=95, r=25, t=115, b=95),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color=NAVY, size=11),
            )
            export_lines = copy.deepcopy(fig_lines)
            posicoes_texto = {
                "<25 anos": "top left",
                "25–64 anos": "top center",
                "≥65 anos": "bottom right",
            }
            for trace in export_lines.data:
                trace.update(
                    mode="lines+markers+text",
                    texttemplate="%{y:,.0f}",
                    textposition=posicoes_texto.get(trace.name, "top center"),
                    textfont=dict(size=12, color=trace.line.color or NAVY),
                    cliponaxis=False,
                )
            for pos, municipio in enumerate(municipios_lines):
                painel = lines_yearly.loc[
                    lines_yearly["municipio"].eq(municipio),
                    "quantidade_alterados",
                ]
                maximo = float(painel.max()) if painel.notna().any() else 0.0
                amplitude = max(maximo, 3.0)
                numero_eixo = (
                    (n_linhas - 1 - pos // 2) * 2 + pos % 2 + 1
                )
                eixo = "yaxis" if numero_eixo == 1 else f"yaxis{numero_eixo}"
                if eixo in export_lines.layout:
                    export_lines.layout[eixo].update(
                        range=[-amplitude * 0.19, amplitude * 1.20],
                        tickformat=",.0f",
                        automargin=True,
                    )
            export_lines.update_layout(
                title=dict(
                    text="Evolução anual de exames alterados por município e grupo etário",
                    x=0.5, xanchor="center",
                    font=dict(size=23, color=NAVY),
                ),
                height=max(950, 465 * n_linhas),
                width=1800,
                legend=dict(
                    title_text="", orientation="h",
                    x=0.5, xanchor="center",
                    y=-0.065, yanchor="top",
                    font=dict(size=15, color=NAVY),
                ),
                margin=dict(l=115, r=75, t=125, b=145),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color=NAVY, size=12),
            )
            st.caption(
                "No computador, passe o mouse sobre os pontos para consultar os valores. "
                "No celular, toque nos pontos e deslize o gráfico para os lados."
            )
            chart_with_right_click_download(
                fig_lines,
                filename="exames_alterados_linhas_grupos_etarios_por_municipio.png",
                height=fig_lines.layout.height,
                min_chart_width=760,
                export_fig=export_lines,
            )


def renderizar_detalhe_evolucao(df: pd.DataFrame) -> None:
    """Ativa a análise etária detalhada apenas sob demanda."""
    st.markdown(
        "Para uma leitura mais detalhada, abra a evolução anual separada por grupos etários."
    )
    if st.toggle(
        "Exibir evolução por município e grupo etário",
        value=False, key="q5_detalhe_evolucao",
    ):
        renderizar_evolucao_por_grupo(df)


def renderizar_matriz_territorial(df: pd.DataFrame) -> None:
    """Exibe a matriz das proporções operacionais por município e grupo."""
    st.markdown(
        '<h2 class="q5-section-title"><span class="q5-section-index">03</span>'
        'Comparação territorial das alterações</h2>',
        unsafe_allow_html=True,
    )
    matrix = agregar_proporcao(df, ["municipio", "grupo_3"], coluna="taxa")
    heat = matrix.pivot(index="municipio", columns="grupo_3", values="taxa")
    heat = heat.reindex(columns=list(GRUPOS_ETARIOS))
    if not heat.empty:
        st.markdown("### Matriz territorial de proporção de exames alterados por grupo etário")
        st.markdown(
            "Compara a **proporção de exames alterados por município e grupo etário**. "
            "Tons mais escuros indicam percentuais maiores no recorte selecionado."
        )
        with st.expander("ℹ️ Como interpretar a matriz territorial", expanded=False):
            st.markdown(
                "Cada **linha** corresponde a um município e cada **coluna**, "
                "a um grupo etário. A célula apresenta a **proporção (%) de exames "
                "alterados entre os exames válidos daquele município e grupo**. "
                "**Proporção (%) = exames alterados ÷ exames válidos × 100.** "
                "Quanto mais escura a célula, maior a proporção. "
                "O símbolo **—** indica comparação sem dado disponível; "
                "não equivale a 0%. Os percentuais usam os totais de exames "
                "válidos como denominador, e não devem ser interpretados "
                "como prevalência de doença ou número de mulheres afetadas."
            )
        fig = px.imshow(
            heat, aspect="auto", color_continuous_scale="Blues",
            labels={"x":"Grupo etário","y":"Município","color":"%"},
            title=None,
        )
        fig.update_traces(
            xgap=3, ygap=3,
            hovertemplate="Grupo etário: %{x}<br>Município: %{y}<br>Proporção: %{z:.2f}%<extra></extra>",
        )
        fig.update_coloraxes(colorbar_tickformat=".2f", colorbar_ticksuffix="%")
        valid_values = heat.stack().dropna()
        max_rate = float(valid_values.max()) if not valid_values.empty else 0.0
        for city in heat.index:
            for age in heat.columns:
                value = heat.at[city, age]
                has_value = pd.notna(value)
                label = f"{value:.2f}".replace(".", ",") if has_value else "—"
                font_color = (
                    "#FFFFFF" if has_value and max_rate > 0
                    and float(value) / max_rate >= 0.55 else "#1A3B5C"
                )
                fig.add_annotation(
                    x=age, y=city, text=label, showarrow=False,
                    font=dict(size=12, color=font_color),
                    xanchor="center", yanchor="middle",
                    hovertext=None,
                )
        fig.update_xaxes(
            tickfont=dict(color="#1A3B5C", size=12, family="Arial"),
            title_text="Grupo etário",
            title_font=dict(color="#1A3B5C", size=14, family="Arial"),
            title_standoff=16,
        )
        fig.update_yaxes(
            tickfont=dict(color="#1A3B5C", size=12, family="Arial"),
            title_text="Municípios",
            title_font=dict(color="#1A3B5C", size=14, family="Arial"),
            title_standoff=16,
        )
        fig.update_layout(
            template="plotly_white",
            height=max(480, 43 * len(heat.index) + 155),
            margin=dict(l=25, r=15, t=70, b=65),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#1A3B5C"),
        )
        chart_with_right_click_download(
            fig, filename="matriz_territorial_exames_alterados.png",
            height=fig.layout.height, min_chart_width=0,
        )
    with st.expander("Ver dados detalhados de exames alterados", expanded=False):
        export_table(matrix, "siscan_exames_alterados.csv")


def renderizar_grafico_categoria_anual(por_cat_ano: pd.DataFrame) -> None:
    """Exibe a composição anual na unidade escolhida e exporta os dados."""
    if not por_cat_ano.empty:
        categorias_ordenadas = sorted(
            por_cat_ano["categoria"].dropna().unique(), key=str.casefold
        )
        cores_categorias = CORES_CATEGORIAS
        mapa_cores = {
            categoria: cores_categorias[i % len(cores_categorias)]
            for i, categoria in enumerate(categorias_ordenadas)
        }
        visual_anual = st.selectbox(
            "Visualizar composição anual",
            ["Quantidade de exames", "Participação por categoria (%)"],
            key="q5_categoria_anual_visual",
        )
        percentual_anual = visual_anual == "Participação por categoria (%)"
        coluna_grafico_anual = (
            "participacao_pct" if percentual_anual else "quantidade_alterados"
        )
        por_cat_ano = preparar_rotulos_exportacao(por_cat_ano, percentual_anual)
        fig_cat = px.bar(
            por_cat_ano, x="ano", y=coluna_grafico_anual,
            color="categoria", barmode="stack",
            text="rotulo_exportacao",
            custom_data=["quantidade_alterados", "participacao_pct"],
            color_discrete_map=mapa_cores,
            category_orders={"categoria": categorias_ordenadas},
            labels={
                "ano": "Ano",
                "quantidade_alterados": "Exames por categoria",
                "participacao_pct": "Participação (%)",
                "categoria": "Categoria citopatológica",
            },
        )
        hover_anual = (
            "Ano: %{x}<br>Participação: %{y:.2f}%"
            "<extra>%{fullData.name}</extra>"
            if percentual_anual else
            "Ano: %{x}<br>Quantidade de exames: %{y:,.0f}"
            "<extra>%{fullData.name}</extra>"
        )
        fig_cat.update_traces(
            hovertemplate=hover_anual,
            marker_line_color="#FFFFFF",
            marker_line_width=0.6,
            textposition="none",
        )
        fig_cat.update_xaxes(type="category", showgrid=False)
        fig_cat.update_yaxes(
            rangemode="tozero",
            tickformat=".0f" if percentual_anual else ",d",
            ticksuffix="%" if percentual_anual else "",
            range=[0, 100] if percentual_anual else None,
            gridcolor="#E4EBF1",
        )
        fig_cat.update_layout(
            height=500, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font=dict(color=NAVY),
            legend=dict(
                title_text="Categoria citopatológica",
                x=1.02, xanchor="left", y=1, yanchor="top",
                font=dict(size=11, color=NAVY),
                bgcolor="rgba(255,255,255,0)",
            ),
            margin=dict(l=70, r=225, t=35, b=65),
        )
        export_cat = copy.deepcopy(fig_cat)
        export_cat.update_traces(
            textposition="inside",
            textfont=dict(size=13, color="#FFFFFF"),
            insidetextanchor="middle",
        )
        export_cat.update_layout(
            title=dict(
                text=("Composição percentual por categoria e ano"
                      if percentual_anual
                      else "Exames alterados por categoria e ano"),
                x=0.5,
            ),
            height=650, width=1600,
            margin=dict(l=90, r=265, t=110, b=90),
            uniformtext=dict(mode="hide", minsize=12),
        )
        chart_with_right_click_download(
            fig_cat, filename="alterados_categorias_ano.png",
            height=480, export_fig=export_cat,
        )
        with st.expander("Ver dados de categorias por ano", expanded=False):
            tabela_cat = por_cat_ano[
                ["ano", "categoria", "quantidade_alterados", "participacao_pct"]
            ].rename(columns={
                "ano": "Ano", "categoria": "Categoria",
                "quantidade_alterados": "Exames na categoria",
                "participacao_pct": "Participação entre categorias (%)",
            })
            export_table(tabela_cat, "siscan_categoria_anual.csv")
    else:
        st.info("Não há registros por categoria nos filtros selecionados.")


def renderizar_composicao_municipal(cat_anual: pd.DataFrame) -> None:
    """Exibe quantidades ou participação entre categorias dentro do município."""
    st.markdown("### Composição dos exames alterados por município e categoria")
    st.markdown(
        "Mostra **quantos exames alterados foram registrados em cada categoria** "
        "e **qual a participação de cada categoria no total de alterados** "
        "de cada município, conforme os filtros selecionados."
    )
    with st.expander("ℹ️ Como interpretar a composição por município", expanded=False):
        st.markdown(
            "**Como ler:** cada **linha** representa um município e cada "
            "**coluna**, uma categoria citopatológica. As cores mais escuras "
            "indicam valores maiores na medida escolhida.\n\n"
            "**Quantidade de exames:** mostra o número de registros daquela "
            "categoria no município, somando os anos selecionados. "
            "Exemplo: **70** significa 70 exames classificados nessa categoria.\n\n"
            "**Participação (%):** mostra quanto a categoria representa "
            "**entre todos os exames alterados do mesmo município**. "
            "É calculada por **exames da categoria ÷ total de exames alterados "
            "classificados no município × 100**. Exemplo: se 70 dos 100 exames "
            "alterados forem ASC-US, a célula exibirá **70.00%**. "
            "As participações das categorias de cada município somam 100% "
            "quando há registros.\n\n"
            "**Atenção:** o percentual **não** representa a proporção de "
            "alterações entre todos os exames válidos nem a porcentagem de "
            "mulheres com a alteração. **0** ou **0.00%** indica nenhum "
            "registro da categoria na grade consultada; **—** indica que "
            "o percentual não pôde ser calculado por falta de denominador. "
            "Os resultados citopatológicos não equivalem, por si só, "
            "a diagnósticos de câncer."
        )
    medida_municipal = st.selectbox(
        "Visualizar composição municipal",
        ["Participação (%)", "Quantidade de exames"],
        key="q5_categoria_municipal_visual",
    )
    st.caption(
        "**Leitura atual:** "
        + (
            "cada célula apresenta a **participação percentual** da categoria "
            "entre os exames alterados do município (total da linha = 100%, "
            "quando há registros)."
            if medida_municipal == "Participação (%)"
            else "cada célula apresenta a **quantidade de exames** da categoria "
            "registrada no município, nos anos selecionados."
        )
    )
    dados_municipais = preparar_composicao(cat_anual, ["municipio", "categoria"], "municipio")
    if not dados_municipais.empty:
        coluna_municipal = (
            "participacao_pct"
            if medida_municipal == "Participação (%)"
            else "quantidade_alterados"
        )
        nomes_municipios = sorted(
            dados_municipais["municipio"].unique(), key=str.casefold
        )
        categorias_municipais = sorted(
            dados_municipais["categoria"].unique(), key=str.casefold
        )
        quadro_municipal = dados_municipais.pivot(
            index="municipio", columns="categoria",
            values=coluna_municipal,
        ).reindex(
            index=nomes_municipios, columns=categorias_municipais
        )
        if quadro_municipal.notna().any().any():
            st.caption(
                "Para facilitar a leitura, a matriz utiliza células maiores. "
                "Em telas menores, deslize horizontalmente para ver todas "
                "as categorias; no PNG, todos os valores ficam visíveis."
            )
            grafico_municipal = px.imshow(
                quadro_municipal,
                aspect="auto",
                color_continuous_scale="Blues",
                labels={
                    "x": "Categoria citopatológica",
                    "y": "Município",
                    "color": (
                        "Participação (%)"
                        if coluna_municipal == "participacao_pct"
                        else "Exames alterados"
                    ),
                },
                title=None,
            )
            grafico_municipal.update_traces(
                xgap=4, ygap=4,
                hovertemplate=(
                    "Município: %{y}<br>Categoria: %{x}<br>"
                    + (
                        "Participação: %{z:.2f}%"
                        if coluna_municipal == "participacao_pct"
                        else "Exames: %{z:,.0f}"
                    )
                    + "<extra></extra>"
                ),
            )
            maior_valor = quadro_municipal.max().max()
            for municipio in nomes_municipios:
                for categoria in categorias_municipais:
                    valor = quadro_municipal.at[municipio, categoria]
                    valido = pd.notna(valor)
                    rotulo = (
                        (
                            f"{valor:.2f}%"
                            if coluna_municipal == "participacao_pct"
                            else f"{valor:,.0f}"
                        )
                        if valido else "—"
                    )
                    texto_claro = (
                        valido and pd.notna(maior_valor)
                        and float(maior_valor) > 0
                        and float(valor) / float(maior_valor) >= 0.55
                    )
                    grafico_municipal.add_annotation(
                        x=categoria, y=municipio,
                        text=rotulo, showarrow=False,
                        font=dict(
                            size=15, family="Arial",
                            color="#FFFFFF" if texto_claro else NAVY,
                        ),
                        xanchor="center", yanchor="middle",
                    )
            if coluna_municipal == "participacao_pct":
                grafico_municipal.update_coloraxes(
                    colorbar_tickformat=".2f",
                    colorbar_ticksuffix="%",
                )
            else:
                grafico_municipal.update_coloraxes(
                    colorbar_tickformat=",.0f",
                )
            grafico_municipal.update_xaxes(
                tickangle=-90,
                tickfont=dict(color=NAVY, size=16, family="Arial"),
                title_text="Categoria citopatológica",
                title_font=dict(color=NAVY, size=18, family="Arial"),
                title_standoff=35,
                automargin=True,
                showgrid=False,
            )
            grafico_municipal.update_yaxes(
                tickfont=dict(color=NAVY, size=17, family="Arial"),
                title_text="Municípios",
                title_font=dict(color=NAVY, size=18, family="Arial"),
                title_standoff=20,
                automargin=True,
                showgrid=False,
            )
            grafico_municipal.update_layout(
                template="plotly_white",
                height=max(825, 51 * len(nomes_municipios) + 255),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFFFFF",
                font=dict(color=NAVY, family="Arial"),
                margin=dict(l=65, r=65, t=35, b=245),
            )
            export_municipal = copy.deepcopy(grafico_municipal)
            export_municipal.update_layout(
                title=dict(
                    text="Composição de exames alterados por município",
                    x=0.5, font=dict(size=22, color=NAVY),
                ),
                width=1750,
                height=max(960, 51 * len(nomes_municipios) + 375),
                margin=dict(l=160, r=110, t=105, b=290),
            )
            chart_with_right_click_download(
                grafico_municipal,
                filename="alterados_composicao_municipio_categoria.png",
                height=grafico_municipal.layout.height,
                min_chart_width=1450,
                export_fig=export_municipal,
            )
        else:
            st.info("Não há valores calculáveis para a composição municipal.")
        with st.expander(
            "Ver dados por município e categoria", expanded=False
        ):
            detalhe_municipal = dados_municipais.rename(columns={
                "municipio": "Município",
                "categoria": "Categoria citopatológica",
                "quantidade_alterados": "Exames na categoria",
                "participacao_pct": "Participação (%)",
            }).sort_values(["Município", "Categoria citopatológica"])
            export_table(
                detalhe_municipal,
                "siscan_composicao_municipio_categoria.csv",
            )
    else:
        st.info("Não há registros por município e categoria neste recorte.")


def renderizar_categorias_anuais() -> None:
    """Consulta a composição anual e municipal na Gold de categorias."""
    st.markdown("### Composição dos exames alterados por categoria e ano")
    st.markdown(
        "Mostra as **quantidades de registros por categoria citopatológica** "
        "ao longo dos anos e municípios selecionados."
    )
    with st.expander("ℹ️ Como interpretar a composição anual", expanded=False):
        st.markdown(
            "Cada barra representa um ano e suas cores representam as categorias. "
            "A altura mostra **quantidades absolutas**, não taxas entre exames válidos. "
            "Na Gold, combinações não retornadas pelo TabNet são preenchidas com zero. "
            "**A soma das categorias pode diferir ligeiramente da métrica geral** "
            "de exames alterados em alguns pares município/ano; a métrica geral "
            "acima continua sendo a referência oficial deste dashboard."
        )
    cat_anual = filtered("categoria_anual")
    if not cat_anual.empty and COLUNAS_CATEGORIA_ANUAL.issubset(cat_anual.columns):
        por_cat_ano = preparar_composicao(cat_anual, ["ano", "categoria"], "ano")
        renderizar_grafico_categoria_anual(por_cat_ano)
        renderizar_composicao_municipal(cat_anual)
    else:
        st.info("A tabela Gold de categorias anuais está vazia ou incompleta.")


def renderizar_grafico_categoria_faixa(comp: pd.DataFrame) -> None:
    """Exibe composição etária de cada categoria e exporta o consolidado."""
    categorias_presentes = sorted(
        comp["categoria"].unique(), key=str.casefold
    )
    cores_faixa = {**CORES_GRUPOS, "≥65 anos": "#E85D2A"}
    comp = preparar_rotulos_exportacao(comp, percentual=True)
    fig_faixas = px.bar(
        comp, x="categoria", y="participacao_pct",
        color="grupo_3", barmode="stack",
        color_discrete_map=cores_faixa,
        category_orders={
            "grupo_3": list(GRUPOS_ETARIOS),
            "categoria": categorias_presentes,
        },
        labels={
            "categoria": "Categoria citopatológica",
            "participacao_pct": "Participação (%)",
            "grupo_3": "Grupo etário",
        },
        custom_data=["quantidade_alterados"],
        text="rotulo_exportacao",
    )
    fig_faixas.update_traces(
        marker_line_color="#FFFFFF", marker_line_width=0.8,
        textposition="none",
        hovertemplate=(
            "Categoria: %{x}<br>Participação: %{y:.2f}%"
            "<br>Exames: %{customdata[0]:,.0f}"
            "<extra>%{fullData.name}</extra>"
        ),
    )
    fig_faixas.update_yaxes(
        range=[0, 100], ticksuffix="%", dtick=20,
        gridcolor="#E4EBF1",
        title_text="Participação (%)",
    )
    fig_faixas.update_xaxes(
        type="category", categoryorder="array",
        categoryarray=categorias_presentes,
        tickmode="array", tickvals=categorias_presentes,
        ticktext=[
            str(nome).replace("_", " ")
            for nome in categorias_presentes
        ],
        tickangle=-90,
        tickfont=dict(size=16, color=NAVY, family="Arial"),
        title_text="Categoria citopatológica",
        title_font=dict(size=18, color=NAVY, family="Arial"),
        title_standoff=35, automargin=True,
    )
    fig_faixas.update_layout(
        height=710, bargap=0.24,
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(color=NAVY),
        legend=dict(
            title_text="Faixa etária", orientation="h",
            x=0.5, xanchor="center", y=1.12, yanchor="bottom",
            font=dict(size=14, color=NAVY),
            bgcolor="rgba(255,255,255,0)",
        ),
        margin=dict(l=85, r=50, t=120, b=300),
    )
    img_faixas = copy.deepcopy(fig_faixas)
    img_faixas.update_traces(
        textposition="inside",
        textfont=dict(color="#FFFFFF", size=13),
        insidetextanchor="middle",
    )
    img_faixas.update_layout(
        title=dict(
            text="Composição etária por categoria (2020–2025)",
            x=0.5, font=dict(size=21, color=NAVY),
        ),
        width=1650, height=870,
        legend=dict(
            title_text="Faixa etária", orientation="h",
            x=0.5, xanchor="center", y=1.10, yanchor="bottom",
            font=dict(size=16, color=NAVY),
        ),
        margin=dict(l=110, r=70, t=170, b=325),
        uniformtext=dict(mode="hide", minsize=12),
    )
    chart_with_right_click_download(
        fig_faixas, filename="alterados_categorias_faixas.png",
        height=710, min_chart_width=1450, export_fig=img_faixas,
    )
    with st.expander("Ver dados de categorias por faixa etária"):
        export_table(
            comp.rename(columns={
                "categoria": "Categoria", "grupo_3": "Grupo etário",
                "quantidade_alterados": "Exames na categoria",
                "participacao_pct": "Participação na categoria (%)",
            }), "siscan_categoria_faixa_etaria.csv",
        )


def renderizar_categorias_por_faixa() -> None:
    """Exibe a base consolidada apenas quando o período 2020–2025 está ativo."""
    st.markdown("### Distribuição etária dos exames alterados por categoria")
    st.markdown(
        "Compara a **distribuição dos registros de cada categoria** entre "
        "os grupos etários no consolidado de 2020–2025."
    )
    with st.expander("ℹ️ Como interpretar a distribuição por faixa etária", expanded=False):
        st.markdown(
            "Cada barra corresponde a uma categoria e os segmentos representam "
            "a participação de cada grupo etário **dentro daquela categoria**. "
            "A distribuição não mede o risco de alteração em cada faixa. "
            "**A Gold não possui ano nessa tabela:** o cruzamento representa "
            "todo o período 2020–2025, e não pode ser filtrado por ano."
        )
    if tuple(selected_years()) != ANOS_CONSOLIDADOS:
        st.info(
            "Este cruzamento foi consolidado na Gold para 2020–2025, sem "
            "detalhamento anual. Selecione todos os anos para visualizá-lo."
        )
    else:
        cat_faixa = filtered("categoria_faixa")
        if not cat_faixa.empty and COLUNAS_CATEGORIA_FAIXA.issubset(cat_faixa.columns):
            cat_faixa = cat_faixa.copy()
            cat_faixa["grupo_3"] = (
                cat_faixa["grupo_etario_3"].astype("string").str.strip().map(ROTULOS_GRUPOS)
            )
            comp = preparar_composicao(cat_faixa, ["categoria", "grupo_3"], "categoria")
            if comp.empty:
                st.info("Não há registros por categoria e faixa etária.")
                return
            comp = comp.dropna(subset=["participacao_pct"])
            if comp.empty:
                st.info("Não há categorias com registros para esta visualização.")
                return
            renderizar_grafico_categoria_faixa(comp)
        else:
            st.info("A tabela Gold de categorias por faixa etária está indisponível.")


def renderizar_composicao() -> None:
    """Apresenta análises de composição independentes da proporção operacional."""
    st.markdown(
        '<h2 class="q5-section-title"><span class="q5-section-index">04</span>'
        'Composição dos resultados citopatológicos</h2>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "As análises por categoria são complementares e não substituem a proporção "
        "operacional. Os gráficos detalhados ficam ocultos inicialmente para facilitar a navegação."
    )
    if st.toggle(
        "Exibir análises avançadas por categoria citopatológica",
        value=False, key="q5_detalhe_categorias",
    ):
        renderizar_categorias_anuais()
        renderizar_categorias_por_faixa()


def main() -> None:
    """Orquestra os blocos da página após validar a fonte operacional."""
    configurar_pagina()
    df = filtered("alterados")
    if not require(df, COLUNAS_ALTERADOS):
        return

    try:
        df = preparar_alterados(df)
    except ValueError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.info("Não há exames com faixa etária conhecida no recorte selecionado.")
        return

    renderizar_panorama(df)
    renderizar_proporcao_etaria(df)
    renderizar_evolucao_municipal(df)
    renderizar_detalhe_evolucao(df)
    renderizar_matriz_territorial(df)
    renderizar_composicao()


if __name__ == "__main__":
    main()
