"""Outubro Rosa: produção e perfil etário dos exames registrados.

Consome três fatos Gold com granularidades distintas: produção territorial
mensal, perfil etário regional mensal e perfil municipal consolidado.
As comparações são descritivas e não identificam efeito causal da campanha.
"""

import base64
import copy
from typing import Literal

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import data_loader
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, require, sidebar_filters, years_label
from utils.theme import (
    NAVY,
    apply_custom_css,
    display_table,
    fmt_num,
    indicator_context,
    page_header,
)

MESES = {9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
ORDEM_MESES = list(MESES.values())
CORES_MESES = {
    "Setembro": "#419AD1", "Outubro": "#E85D2A",
    "Novembro": "#218B65", "Dezembro": "#1A3B5C",
}

COLUNAS_PRODUCAO = ("municipio", "ano", "mes", "quantidade")
COLUNAS_MENSAL_ETARIO = {"ano", "mes_num", "grupo_etario", "quantidade_exames"}
COLUNAS_PERFIL_ETARIO = {"municipio", "grupo_etario", "quantidade_exames"}
ANOS_CONSOLIDADOS = frozenset(range(2020, 2026))
MESES_ABREV = {9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
GRUPOS_ETARIOS = ("<25 anos", "25–64 anos", "≥65 anos")
GRUPO_ALVO = "25–64 anos"
ROTULOS_GRUPOS = {
    "<25 anos": "<25 anos",
    "25-64 anos": GRUPO_ALVO,
    ">=65 anos": "≥65 anos",
}
CORES_GRUPOS = {
    "<25 anos": "#169B62",
    GRUPO_ALVO: "#1757A6",
    "≥65 anos": "#E85D2A",
}
ModoRotulo = Literal["percentual_vertical", "quantidade_vertical", "percentual_horizontal"]


def configurar_pagina() -> None:
    """Configura o tema, os filtros e o cabeçalho do Outubro Rosa."""
    st.set_page_config(page_title="Outubro Rosa | SISCAN", layout="wide")
    apply_custom_css()
    sidebar_filters()
    st.markdown("""
    <style>
    .pet-hero {margin-bottom:0!important}
    .or-mini-note {font-size:.86rem; color:#526B81; margin:4px 0 16px}
    .st-key-outubro_rosa_ordenacao [data-testid="stSelectbox"] {max-width:280px}

    .or-section-title {
        margin:38px 0 13px;padding:8px 0 12px;
        border-bottom:1px solid #D8E5EF;
        font:750 clamp(20px,2vw,25px)/1.35 Manrope,Arial,sans-serif;
        color:#1A3B5C;
    }
    .or-section-index {color:#006C9A;margin-right:10px}
    /* Explicações da página Outubro Rosa — alinhadas à tipografia de Faixa Etária. */
    [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] {
        border:1px solid #D8E5EF!important;
        border-radius:10px!important;
        background:#FFFFFF!important;
        margin:8px 0 14px!important;
    }
    [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] summary {
        font-family:Manrope,Arial,sans-serif!important;
        font-size:.95rem!important;
        font-weight:700!important;
        line-height:1.45!important;
        color:#1A3B5C!important;
    }
    [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
        font-family:Manrope,Arial,sans-serif!important;
        font-size:.95rem!important;
        line-height:1.6!important;
        font-weight:500!important;
        color:#1A3B5C!important;
        margin:0 0 .65rem!important;
    }
    [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p:last-child {
        margin-bottom:0!important;
    }
    [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] strong {
        font-weight:750!important;
    }
    @media(max-width:768px) {
        [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] summary,
        [class*="st-key-outubro_ajuda_"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
            font-size:.9rem!important;
            line-height:1.55!important;
        }
    }
    @media(max-width:768px) {
        .or-section-title {margin:27px 0 12px;font-size:20px}
    }
    </style>
    """, unsafe_allow_html=True)

    page_header(
        "",
        "Outubro Rosa: produção e perfil etário dos exames",
        "Analisa a produção de exames citopatológicos, com destaque para a "
        "participação da população-alvo de 25 a 64 anos e as diferenças "
        "entre períodos e municípios.",
    )


def section(index: str, title: str) -> None:
    """Exibe o título numerado com a identidade visual desta página."""
    st.markdown(
        '<h2 class="or-section-title"><span class="or-section-index">'
        + index + '</span>' + title + '</h2>',
        unsafe_allow_html=True,
    )


def download_plot(
    fig: go.Figure,
    nome: str,
    altura: int = 450,
    largura: int = 1400,
    margem_superior: int = 45,
    margem_esquerda: int = 75,
    margem_inferior: int = 70,
    rotulos_exportacao: ModoRotulo | None = None,
    titulo_exportacao: str | None = None,
    min_chart_width: int = 0,
) -> None:
    """Apresenta a figura interativa e uma cópia independente para o PNG.

    Args:
        fig: Figura Plotly configurada pelo chamador.
        nome: Nome do arquivo PNG.
        altura: Altura da figura interativa em pixels.
        largura: Largura da imagem exportada em pixels.
        margem_superior: Margem superior da figura.
        margem_esquerda: Margem esquerda da figura.
        margem_inferior: Margem inferior da figura.
        rotulos_exportacao: Formato opcional de rótulos nas barras do PNG.
        titulo_exportacao: Título opcional exclusivo da imagem.
        min_chart_width: Largura mínima da figura interativa para rolagem.
    """
    fig.update_layout(
        template="plotly_white", height=altura,
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=NAVY, size=13),
        margin=dict(l=margem_esquerda, r=145, t=margem_superior, b=margem_inferior),
        legend_title_text="",
    )
    fig.update_yaxes(gridcolor="#E4EBF1", rangemode="tozero")
    imagem = copy.deepcopy(fig)
    # Os rótulos do PNG não alteram a figura interativa.
    if rotulos_exportacao in {
        "percentual_vertical", "quantidade_vertical", "percentual_horizontal"
    }:
        barras_verticais = rotulos_exportacao != "percentual_horizontal"
        percentual = rotulos_exportacao != "quantidade_vertical"
        for traco in imagem.data:
            nome_grupo = str(getattr(traco, "name", ""))
            grupo_superior = nome_grupo in {"≥65 anos", ">=65 anos"}
            texto_escuro = grupo_superior
            traco.update(
                texttemplate=(
                    "<b>%{x:.1f}%</b>"
                    if not barras_verticais
                    else ("<b>%{y:.1f}%</b>" if percentual
                          else "<b>%{y:,.0f}</b>")
                ),
                textposition=(
                    "outside" if grupo_superior and barras_verticais
                    else "inside"
                ),
                insidetextanchor="middle",
                textfont=dict(
                    family="Arial Black, Arial, sans-serif",
                    size=12 if grupo_superior else 13,
                    color=NAVY if texto_escuro else "#FFFFFF",
                ),
                cliponaxis=False,
                constraintext="none",
            )
        if rotulos_exportacao == "percentual_horizontal":
            for traco in imagem.data:
                if str(getattr(traco, "name", "")) != "<25 anos":
                    continue
                # Plotly 6 pode representar vetores como dtype e bdata.
                bruto_x = traco.x
                if isinstance(bruto_x, dict) and "bdata" in bruto_x:
                    valores = np.frombuffer(
                        base64.b64decode(bruto_x["bdata"]),
                        dtype=np.dtype(bruto_x["dtype"]),
                    ).tolist()
                else:
                    valores = list(bruto_x)
                municipios = list(traco.y)
                templates = []
                for valor, municipio in zip(valores, municipios):
                    try:
                        largura_faixa = float(valor)
                    except (TypeError, ValueError):
                        templates.append("<b>%{x:.1f}%</b>")
                        continue
                    # Desloca rótulos estreitos sem modificar os valores.
                    if 0 < largura_faixa < 4:
                        templates.append("")
                        imagem.add_annotation(
                            x=largura_faixa + 2.7,
                            y=str(municipio),
                            xref="x", yref="y",
                            text=f"<b>{largura_faixa:.1f}%</b>",
                            showarrow=False,
                            font=dict(
                                family="Arial Black, Arial, sans-serif",
                                size=13, color="#FFFFFF",
                            ),
                            align="center",
                            xanchor="center", yanchor="middle",
                        )
                    else:
                        templates.append("<b>%{x:.1f}%</b>")
                traco.update(texttemplate=templates)
        if rotulos_exportacao == "percentual_vertical":
            imagem.update_yaxes(
                range=[0, 113], tickvals=[0, 20, 40, 60, 80, 100],
            )
        imagem.update_layout(
            uniformtext_minsize=10, uniformtext_mode="show",
        )
    imagem.update_layout(
        width=largura,
        height=max(altura + 100, 650),
        title=dict(text=(titulo_exportacao or nome.replace("_", " ").replace(".png", "").title()),
                   x=0.5, font=dict(size=22, color=NAVY)),
        margin=dict(l=max(110, margem_esquerda + 35), r=210,
                    t=max(105, margem_superior + 35),
                    b=max(100, margem_inferior + 30)),
    )
    chart_with_right_click_download(
        fig, filename=nome, height=altura,
        min_chart_width=min_chart_width, export_fig=imagem,
    )


def chart_help(message: str, chave: str) -> None:
    """Exibe a orientação metodológica em painel recolhível."""
    with st.container(key=f"outubro_ajuda_{chave}"):
        with st.expander("ℹ️ Como interpretar", expanded=False):
            st.markdown(message)


def preparar_producao(dados: pd.DataFrame) -> pd.DataFrame:
    """Seleciona dados válidos de setembro a dezembro sem imputar ausências.

    Args:
        dados: Registros temporais Gold já filtrados por município e ano.

    Returns:
        Cópia com competência numérica, mês rotulado e quantidade não negativa.
    """
    dados = dados[["municipio", "ano", "mes", "quantidade"]].copy()
    for coluna in ["ano", "mes", "quantidade"]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    dados = dados.dropna(subset=["municipio", "ano", "mes", "quantidade"])
    dados = dados.loc[dados["mes"].isin(MESES)].copy()
    dados = dados.loc[dados["quantidade"] >= 0].copy()
    dados["ano"] = dados["ano"].astype(int)
    dados["mes"] = dados["mes"].astype(int)
    dados["Mês"] = dados["mes"].map(MESES)
    return dados


def agregar_producao_mensal(dados: pd.DataFrame) -> pd.DataFrame:
    """Consolida o volume por ano e mês, somando somente a quantidade."""
    mensal = (
        dados.groupby(["ano", "mes", "Mês"], as_index=False)["quantidade"]
        .sum(min_count=1)
    )
    mensal["ano_texto"] = mensal["ano"].astype(str)
    return mensal


def variacao_percentual(outubro: float, setembro: float) -> float:
    """Retorna a variação outubro/setembro; referência ausente ou zero gera NaN."""
    if pd.isna(setembro) or pd.isna(outubro) or setembro <= 0:
        return float("nan")
    return (outubro - setembro) / setembro * 100


def calcular_pares_municipais(dados: pd.DataFrame) -> pd.DataFrame:
    """Compara os totais de setembro e outubro de anos pareados.

    Args:
        dados: Produção mensal válida por município e competência.

    Returns:
        Totais pareados, número de anos, diferença absoluta e variação.
        A variação é a razão dos totais, não a média dos percentuais anuais.
    """
    pares_ano_municipio = (
        dados.loc[dados["mes"].isin([9, 10])]
        .groupby(["municipio", "ano", "mes"])["quantidade"]
        .sum(min_count=1)
        .unstack("mes")
        .reindex(columns=[9, 10])
        .rename(columns={9: "Setembro", 10: "Outubro"})
    )
    pares_completos = pares_ano_municipio.dropna(
        subset=["Setembro", "Outubro"]
    ).reset_index()
    pares_municipais = (
        pares_completos.groupby("municipio", as_index=False)
        .agg(
            Setembro=("Setembro", "sum"),
            Outubro=("Outubro", "sum"),
            Anos_pareados=("ano", "nunique"),
        )
        .rename(columns={
            "municipio": "Município",
            "Anos_pareados": "Anos pareados",
        })
    )
    pares_municipais["Diferença absoluta"] = (
        pares_municipais["Outubro"] - pares_municipais["Setembro"]
    )
    base = pares_municipais["Setembro"]
    pares_municipais["Variação (%)"] = (
        pares_municipais["Diferença absoluta"].div(base.where(base > 0)).mul(100)
    )
    return pares_municipais


def preparar_perfil_etario(
    tabela: pd.DataFrame, chaves: list[str]
) -> pd.DataFrame:
    """Normaliza os grupos etários e a quantidade sem alterar a fonte.

    Args:
        tabela: Fato Gold de perfil etário mensal ou consolidado.
        chaves: Dimensões obrigatórias específicas da granularidade.

    Returns:
        Cópia com rótulos padronizados e valores numéricos válidos.
    """
    perfil = tabela.copy()
    perfil["Grupo"] = (
        perfil["grupo_etario"].astype(str).str.strip().map(ROTULOS_GRUPOS)
    )
    perfil["quantidade_exames"] = pd.to_numeric(
        perfil["quantidade_exames"], errors="coerce"
    )
    return perfil.dropna(subset=[*chaves, "Grupo", "quantidade_exames"])


def preparar_perfil_mensal(
    tabela: pd.DataFrame, anos: list[int]
) -> pd.DataFrame:
    """Restringe o perfil regional aos anos selecionados e meses set–dez."""
    perfil = tabela.copy()
    for coluna in ("ano", "mes_num"):
        perfil[coluna] = pd.to_numeric(perfil[coluna], errors="coerce")
    perfil = preparar_perfil_etario(perfil, ["ano", "mes_num"])
    perfil = perfil.loc[
        perfil["ano"].isin(anos) & perfil["mes_num"].isin(MESES)
    ].copy()
    return perfil.astype({"ano": "int64", "mes_num": "int64"})


def calcular_participacao(
    perfil: pd.DataFrame, chaves: list[str]
) -> pd.DataFrame:
    """Calcula participação dentro da competência ou do município.

    Usa apenas exames classificáveis e mantém NaN quando não há
    denominador positivo. Não representa mulheres distintas.
    """
    resultado = perfil.copy()
    total = resultado.groupby(chaves)["quantidade_exames"].transform("sum")
    resultado["Participação (%)"] = (
        resultado["quantidade_exames"].div(total.where(total > 0)).mul(100)
    )
    return resultado


def participacao_alvo(tabela: pd.DataFrame) -> float:
    """Calcula a participação de 25–64 anos pela razão dos totais."""
    total = tabela["quantidade_exames"].sum()
    alvo = tabela.loc[tabela["Grupo"] == GRUPO_ALVO, "quantidade_exames"].sum()
    return float(alvo / total * 100) if total > 0 else float("nan")


def rotular_competencias(perfil: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta o rótulo mês/ano sem alterar os valores observados."""
    resultado = perfil.copy()
    resultado["Competência"] = (
        resultado["mes_num"].astype(int).map(MESES_ABREV)
        + "/" + resultado["ano"].astype(int).astype(str)
    )
    return resultado


def ordenar_competencias(perfil: pd.DataFrame) -> list[str]:
    """Retorna apenas competências observadas, em ordem cronológica."""
    observadas = set(perfil["Competência"])
    return [
        f"{mes}/{ano}"
        for ano in sorted(perfil["ano"].astype(int).unique())
        for mes in MESES_ABREV.values()
        if f"{mes}/{ano}" in observadas
    ]


def renderizar_producao_mensal(mensal: pd.DataFrame) -> None:
    """Exibe cartões e barras mensais para os municípios selecionados."""
    anos = sorted(mensal["ano"].unique().tolist())
    section("01", "Produção mensal · setembro a dezembro")
    st.markdown(
        "Compare os exames registrados em cada mês, por ano, considerando "
        "os municípios selecionados."
    )
    chart_help(
        "**Variação (%) = (Outubro − Setembro) ÷ Setembro × 100.** "
        "A variação reúne os totais dos meses disponíveis nos anos "
        "selecionados; ela não equivale à média das variações anuais. "
        "Se setembro for zero, o percentual não é calculável.",
        chave="producao",
    )
    totais_mes = (
        mensal.groupby("mes")["quantidade"].sum().reindex(MESES.keys())
    )
    setembro = totais_mes.get(9, float("nan"))
    outubro = totais_mes.get(10, float("nan"))
    diferenca = outubro - setembro if pd.notna(outubro) and pd.notna(setembro) else float("nan")
    variacao = variacao_percentual(outubro, setembro)
    c1, c2, c3 = st.columns(3)
    c1.metric("Exames em setembro", fmt_num(setembro) if pd.notna(setembro) else "N/D")
    c2.metric("Exames em outubro", fmt_num(outubro) if pd.notna(outubro) else "N/D")
    c3.metric(
        "Variação setembro → outubro",
        f"{variacao:+.2f}%" if pd.notna(variacao) else "N/D",
        delta=f"{diferenca:+,.0f} exames".replace(",", ".") if pd.notna(variacao) else None,
    )
    anos_set_or = set(mensal.loc[mensal["mes"] == 9, "ano"])
    anos_out_or = set(mensal.loc[mensal["mes"] == 10, "ano"])
    if anos_set_or != anos_out_or:
        st.warning(
            "Atenção: setembro e outubro não aparecem em todos os mesmos anos. "
            "Os cartões acima agregam meses disponíveis; a comparação municipal "
            "abaixo utiliza apenas pares completos do mesmo município e ano."
        )
    fig = px.bar(
        mensal, x="ano_texto", y="quantidade", color="Mês",
        barmode="group", color_discrete_map=CORES_MESES,
        category_orders={"Mês": ORDEM_MESES, "ano_texto": [str(a) for a in anos]},
        labels={"ano_texto": "Ano", "quantidade": "Exames registrados"},
    )
    fig.update_traces(
        hovertemplate="Ano: %{x}<br>Exames registrados: %{y:,.0f}"
        "<extra>%{fullData.name}</extra>"
    )
    fig.update_layout(
        bargap=0.23, bargroupgap=0.07,
        legend=dict(orientation="v", x=1.02, xanchor="left", y=1, yanchor="top"),
    )
    fig.update_xaxes(title_text="Ano", showgrid=False)
    fig.update_yaxes(title_text="Quantidade de exames", tickformat=",d")
    download_plot(fig, "outubro_rosa_producao_mensal_por_ano.png", altura=440, largura=1550, margem_superior=100)


def renderizar_comparacao_municipal(dados: pd.DataFrame) -> None:
    """Exibe a comparação acumulada usando somente pares completos."""
    st.markdown("### Comparação municipal · setembro × outubro")
    st.markdown(
        "Veja quais municípios registraram aumento ou redução de exames em "
        "outubro, comparando apenas anos com setembro e outubro disponíveis."
    )

    pares_municipais = calcular_pares_municipais(dados)

    with st.container(key="outubro_ajuda_variacao"):
        with st.expander("ℹ️ Como interpretar", expanded=False):
            st.markdown(
                "**Como interpretar:** este indicador compara o total de exames de "
                "setembro com o total de outubro nos anos selecionados. Para cada "
                "município, entram apenas os anos com registros nos dois meses.\n\n"
                "**Cálculo:** (total de outubro − total de setembro) ÷ "
                "total de setembro × 100.\n\n"
                "O resultado é a **variação percentual dos totais de setembro e outubro**, "
                "não a média simples das variações de cada ano. "
                "Valores positivos indicam aumento e negativos indicam redução "
                "na quantidade de exames. Essa comparação não demonstra que "
                "as mudanças foram causadas pela campanha Outubro Rosa."
            )

    with st.container(key="outubro_variacao_sort_panel"):
        ordenacao = st.selectbox(
            "Ordenar por", ["A–Z", "Maior para menor"],
            index=0, key="outubro_rosa_ordenacao",
            help="Maior para menor considera a variação percentual dos totais "
                 "de setembro e outubro nos anos pareados.",
        )
    municipios_validos = pares_municipais.dropna(
        subset=["Variação (%)"]
    ).copy()
    if ordenacao == "Maior para menor":
        municipios_validos = municipios_validos.sort_values(
            ["Variação (%)", "Município"], ascending=[False, True],
            kind="stable",
        )
    else:
        municipios_validos = municipios_validos.sort_values(
            "Município", key=lambda nomes: nomes.str.casefold(),
            kind="stable",
        )

    if municipios_validos.empty:
        st.info("Não há pares setembro–outubro com setembro maior que zero "
                "para os filtros selecionados.")
    else:
        municipios_validos["Situação"] = municipios_validos["Variação (%)"].map(
            lambda valor: "Redução" if valor < 0 else "Aumento ou estabilidade"
        )
        municipios_validos["Variação formatada"] = municipios_validos[
            "Variação (%)"
        ].map(lambda valor: f"{valor:+.2f}%")
        municipios_validos["Diferença formatada"] = municipios_validos[
            "Diferença absoluta"
        ].map(lambda valor: f"{valor:+,.0f}".replace(",", "."))
        municipios_validos["Setembro formatado"] = municipios_validos[
            "Setembro"
        ].map(lambda valor: f"{valor:,.0f}".replace(",", "."))
        municipios_validos["Outubro formatado"] = municipios_validos[
            "Outubro"
        ].map(lambda valor: f"{valor:,.0f}".replace(",", "."))

        fig_mun = px.bar(
            municipios_validos, x="Variação (%)", y="Município",
            color="Situação", orientation="h",
            color_discrete_map={
                "Redução": "#B53A27",
                "Aumento ou estabilidade": "#218B65",
            },
            custom_data=[
                "Setembro formatado", "Outubro formatado",
                "Diferença formatada", "Variação formatada", "Anos pareados",
            ],
        )
        fig_mun.update_yaxes(
            categoryorder="array",
            categoryarray=list(reversed(municipios_validos["Município"].tolist())),
            automargin=True,
        )
        fig_mun.update_xaxes(
            ticksuffix="%", tickformat=".2f",
            zeroline=True, zerolinecolor=NAVY, zerolinewidth=2,
        )
        fig_mun.update_traces(
            hovertemplate="<b>%{y}</b>"
            "<br>Setembro (acumulado): %{customdata[0]} exames"
            "<br>Outubro (acumulado): %{customdata[1]} exames"
            "<br>Diferença absoluta: %{customdata[2]} exames"
            "<br>Variação percentual dos totais de setembro e outubro: %{customdata[3]}"
            "<br>Anos com ambos os meses: %{customdata[4]}"
            "<extra></extra>"
        )
        fig_mun.update_layout(showlegend=False, bargap=0.32)
        download_plot(
            fig_mun, "outubro_rosa_variacao_acumulada_pares_completos.png",
            altura=max(460, 42 * len(municipios_validos) + 110),
            largura=1600,
        )

    municipios_ativos = set(dados["municipio"].unique())
    municipios_validos_set = set(municipios_validos["Município"])
    sem_base = sorted(municipios_ativos - municipios_validos_set)
    if sem_base:
        st.caption(
            "Sem percentual calculável (pares ausentes ou setembro acumulado "
            "igual a zero): " + ", ".join(sem_base) + "."
        )
    anos_selecionados = len(data_loader.selected_years())
    menos_anos = pares_municipais.loc[
        pares_municipais["Anos pareados"] < anos_selecionados
    ]
    if not menos_anos.empty:
        st.caption(
            "Disponibilidade: para alguns municípios, o cálculo utiliza "
            "menos anos que os selecionados porque faltam registros em "
            "setembro ou outubro. Confira a quantidade de anos no tooltip."
        )


def renderizar_indicadores_etarios(mensal_etario_or: pd.DataFrame) -> None:
    """Exibe produção-alvo, participação e diferença em pontos percentuais."""
    alvo_or = mensal_etario_or.loc[
        mensal_etario_or["Grupo"] == GRUPO_ALVO, "quantidade_exames"
    ].sum()
    pct_alvo_or = participacao_alvo(mensal_etario_or)
    sep_class_or = mensal_etario_or.loc[
        mensal_etario_or["mes_num"] == 9
    ]
    out_class_or = mensal_etario_or.loc[
        mensal_etario_or["mes_num"] == 10
    ]
    p_sep_or = participacao_alvo(sep_class_or)
    p_out_or = participacao_alvo(out_class_or)
    delta_pp_or = p_out_or - p_sep_or
    kpi_alvo_a, kpi_alvo_b, kpi_alvo_c = st.columns(3)
    kpi_alvo_a.metric(
        "Exames de 25–64 anos (set.–dez.)", fmt_num(alvo_or)
    )
    kpi_alvo_b.metric(
        "Participação de 25–64 anos (set.–dez.)",
        f"{pct_alvo_or:.2f}%" if pd.notna(pct_alvo_or) else "N/D",
    )
    kpi_alvo_c.metric(
        "Participação da população-alvo: outubro × setembro",
        f"{delta_pp_or:+.2f}"
        if pd.notna(delta_pp_or) else "N/D",
        help=(
            "A participação dos exames em mulheres de 25 a 64 anos "
            f"passou de {p_sep_or:.2f}% em setembro para "
            f"{p_out_or:.2f}% em outubro, considerando os anos "
            "selecionados. A diferença é medida em pontos "
            "percentuais, não representa a variação na quantidade "
            "de exames."
        ) if pd.notna(p_sep_or) and pd.notna(p_out_or)
        else "Não há dados suficientes de setembro e outubro "
             "para calcular a diferença de participação.",
    )


def renderizar_grafico_etario_mensal(mensal_etario_or: pd.DataFrame) -> None:
    """Exibe as facetas regionais por ano em quantidade ou participação."""
    modo_etario_or = st.radio(
        "Exibir no gráfico",
        ["Participação (%)", "Quantidade de exames"],
        key="outubro_rosa_modo_mensal_etario",
        horizontal=True,
    )
    dados_grafico_etario_or = mensal_etario_or.copy()
    dados_grafico_etario_or["Ano"] = (
        dados_grafico_etario_or["ano"].astype(int).astype(str)
    )
    dados_grafico_etario_or["Mês"] = (
        dados_grafico_etario_or["mes_num"].astype(int).map(MESES)
    )
    anos_grafico_or = [
        str(a) for a in sorted(dados_grafico_etario_or["ano"].astype(int).unique())
    ]
    campo_valor_or = (
        "Participação (%)" if modo_etario_or == "Participação (%)"
        else "quantidade_exames"
    )
    fig_mes_idade_or = px.bar(
        dados_grafico_etario_or,
        x="Mês", y=campo_valor_or,
        color="Grupo", barmode="stack",
        facet_col="Ano", facet_col_wrap=2,
        facet_col_spacing=0.10, facet_row_spacing=0.18,
        category_orders={
            "Ano": anos_grafico_or,
            "Mês": ORDEM_MESES,
            "Grupo": list(GRUPOS_ETARIOS),
        },
        color_discrete_map=CORES_GRUPOS,
        custom_data=["quantidade_exames", "Participação (%)", "Ano"],
        labels={
            "quantidade_exames": "Quantidade de exames",
            "Participação (%)": "Participação dos exames (%)",
        },
    )
    # Reposiciona os títulos das facetas abaixo dos meses de cada ano.
    dominios_y_etario_or = [
        list(getattr(fig_mes_idade_or.layout, chave).domain)
        for chave in fig_mes_idade_or.layout
        if chave.startswith("yaxis")
        and getattr(fig_mes_idade_or.layout, chave).domain is not None
    ]
    for anotacao in fig_mes_idade_or.layout.annotations:
        dominio_painel_or = min(
            dominios_y_etario_or,
            key=lambda d: abs(d[1] - float(anotacao.y)),
        )
        anotacao.update(
            text=anotacao.text.split("=", 1)[-1],
            y=dominio_painel_or[0] - 0.055,
            yanchor="top",
            font=dict(size=15, color=NAVY),
        )
    fig_mes_idade_or.update_traces(
        hovertemplate=(
            "%{x}/%{customdata[2]} — %{fullData.name}"
            "<br>Exames: %{customdata[0]:,.0f}"
            "<br>Participação: %{customdata[1]:.2f}%"
            "<extra></extra>"
        )
    )
    modo_percentual_or = modo_etario_or == "Participação (%)"
    fig_mes_idade_or.update_xaxes(
        categoryorder="array", categoryarray=ORDEM_MESES,
        tickangle=0, title_text=None, showgrid=False,
        showticklabels=True,
    )
    fig_mes_idade_or.update_yaxes(
        title_text=None, rangemode="tozero",
        ticksuffix="%" if modo_percentual_or else "",
        tickformat=".0f" if modo_percentual_or else ",d",
    )
    # A escala depende da unidade selecionada.
    if modo_percentual_or:
        fig_mes_idade_or.update_yaxes(range=[0, 100])
    else:
        max_mensal_or = (
            dados_grafico_etario_or.groupby(
                ["ano", "mes_num"]
            )["quantidade_exames"].sum(min_count=1).max()
        )
        fig_mes_idade_or.update_yaxes(
            range=[0, float(max_mensal_or) * 1.12]
            if pd.notna(max_mensal_or) and max_mensal_or > 0
            else None
        )
    fig_mes_idade_or.add_annotation(
        text="Meses/ano", x=0.5, y=-0.17,
        xref="paper", yref="paper",
        showarrow=False, font=dict(size=13, color=NAVY),
    )
    fig_mes_idade_or.add_annotation(
        text=("Participação dos exames (%)" if modo_percentual_or
              else "Quantidade de exames"),
        x=-0.09, y=0.5,
        xref="paper", yref="paper",
        textangle=-90, showarrow=False,
        font=dict(size=13, color=NAVY),
    )
    fig_mes_idade_or.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.035, x=0,
            title_text="Grupo etário",
        ),
        margin=dict(l=75, r=40, t=115, b=115),
        bargap=0.23,
    )
    altura_etario_or = max(
        590, 365 * ((len(anos_grafico_or) + 1) // 2) + 150
    )
    download_plot(
        fig_mes_idade_or,
        "outubro_rosa_perfil_mensal_grupo_etario.png",
        altura=altura_etario_or, largura=1600,
        margem_superior=125, margem_esquerda=120,
        margem_inferior=150, min_chart_width=740,
        rotulos_exportacao=(
            "percentual_vertical" if modo_percentual_or
            else "quantidade_vertical"
        ),
        titulo_exportacao=(
            "Outubro Rosa — Participação por grupo etário (%)"
            if modo_percentual_or
            else "Outubro Rosa — Exames por grupo etário (quantidade)"
        ),
    )
    st.caption(
        "Os meses aparecem no eixo horizontal e o ano fica "
        "abaixo de cada painel. Cada barra representa uma "
        "competência mês/ano; dados regionais com idade classificável."
    )


def renderizar_tabela_etaria_mensal(mensal_etario_or: pd.DataFrame) -> None:
    """Exibe e exporta as quantidades por competência e grupo etário."""
    tabela_mensal_or = (
        mensal_etario_or.pivot(
            index="Competência", columns="Grupo",
            values="quantidade_exames"
        )
        .reindex(
            index=ordenar_competencias(mensal_etario_or),
            columns=list(GRUPOS_ETARIOS),
        )
    )
    tabela_mensal_or["Total classificável"] = (
        tabela_mensal_or.sum(axis=1, min_count=1)
    )
    with st.expander(
        "Ver tabela mensal por grupo etário", expanded=False
    ):
        tabela_exibicao_or = tabela_mensal_or.reset_index().rename(
            columns={"Competência": "Mês / ano"}
        )
        display_table(tabela_exibicao_or)
        st.download_button(
            "⬇️ Exportar tabela mensal por grupo etário (CSV)",
            data=tabela_exibicao_or.to_csv(
                index=False, sep=";", decimal=".", float_format="%.2f"
            ).encode("utf-8-sig"),
            file_name="siscan_outubro_rosa_mensal_grupo_etario.csv",
            mime="text/csv",
            key="exportar_outubro_mensal_grupo_etario",
        )


def renderizar_perfil_mensal(periodo: str) -> None:
    """Consulta a base regional somente quando os 11 municípios estão ativos."""
    section("02", "Faixa etária · participação na população-alvo")
    st.markdown(
        f"Exames de **25 a 64 anos** entre setembro e dezembro de **{periodo}**."
    )
    st.caption(
        "ℹ️ **Limitação dos dados:** o cruzamento mensal por idade é regional "
        "(11 municípios juntos) e não permite análise individual por município."
    )
    chart_help(
        "**Exames (set.–dez.):** quantidade registrada na faixa de 25 a 64 anos.\n\n"
        "**Participação (set.–dez.):** percentual desses exames entre todos os "
        "exames com idade identificada.\n\n"
        "**Outubro × setembro:** diferença da participação entre os meses, "
        "em **pontos percentuais (p.p.)**, não variação na quantidade.\n\n"
        "**Base:** somente exames com idade classificável dos 11 municípios. "
        "O dado mensal por idade é regional, sem filtro individual por município; "
        "não representa mulheres distintas.",
        chave="etaria",
    )
    todos_municipios_or = set(data_loader.MUNICIPIOS.values())
    municipios_selecionados_or = set(
        st.session_state.get("city_preference", list(todos_municipios_or))
    )
    if municipios_selecionados_or != todos_municipios_or:
        st.info(
            "O cruzamento mensal por idade está disponível apenas para os "
            "**11 municípios juntos**. A Gold mensal não possui município; "
            "selecione todos os municípios no filtro lateral para visualizar "
            "o gráfico sem misturar recortes diferentes."
        )
    else:
        try:
            mensal_etario_or = data_loader.load_table(
                "outubro_mensal_grupo_etario", data_loader.selected_source()
            )
        except (ValueError, data_loader.GoldConsultaIndisponivel):
            st.warning(
                "A nova Gold mensal por faixa etária não está acessível. "
                "Confirme a publicação da tabela "
                "`fato_outubro_rosa_mensal_grupo_etario` e atualize o Streamlit."
            )
            mensal_etario_or = pd.DataFrame()

        if not mensal_etario_or.empty and COLUNAS_MENSAL_ETARIO.issubset(
            mensal_etario_or.columns
        ):
            mensal_etario_or = preparar_perfil_mensal(
                mensal_etario_or, data_loader.selected_years()
            )
            if mensal_etario_or.empty:
                st.info("Sem dados etários mensais para os anos selecionados.")
            elif mensal_etario_or.duplicated(
                ["ano", "mes_num", "Grupo"]
            ).any():
                st.error(
                    "A tabela Gold contém competências/grupos duplicados. "
                    "Revise a chave ano × mês × grupo antes de representar os valores."
                )
            else:
                mensal_etario_or = calcular_participacao(
                    rotular_competencias(mensal_etario_or), ["ano", "mes_num"]
                )
                renderizar_indicadores_etarios(mensal_etario_or)
                renderizar_grafico_etario_mensal(mensal_etario_or)
                renderizar_tabela_etaria_mensal(mensal_etario_or)
        elif mensal_etario_or.empty:
            st.info("Não há registros acessíveis na Gold mensal por grupo etário.")
        else:
            st.warning(
                "A Gold mensal por grupo etário não possui todas as colunas "
                "necessárias para o gráfico."
            )


def renderizar_tabela_etaria_municipal(
    perfil_or: pd.DataFrame, municipios_etarios_or: list[str]
) -> None:
    """Exibe e exporta as quantidades consolidadas por município e grupo."""
    tabela_etaria_or = (
        perfil_or.pivot(
            index="municipio", columns="Grupo",
            values="quantidade_exames"
        ).reindex(
            index=municipios_etarios_or,
            columns=list(GRUPOS_ETARIOS),
        )
    )
    tabela_etaria_or.index.name = "Município"
    with st.expander(
        "Ver quantidades por município e grupo etário",
        expanded=False,
    ):
        tabela_etaria_exportacao_or = tabela_etaria_or.reset_index()
        display_table(tabela_etaria_exportacao_or)
        st.download_button(
            "⬇️ Exportar quantidades por município e grupo etário (CSV)",
            data=tabela_etaria_exportacao_or.to_csv(
                index=False, sep=";", decimal=".", float_format="%.2f"
            ).encode("utf-8-sig"),
            file_name="siscan_outubro_rosa_municipio_grupo_etario.csv",
            mime="text/csv",
            key="exportar_outubro_municipio_grupo_etario",
        )


def renderizar_grafico_etario_municipal(perfil_or: pd.DataFrame) -> None:
    """Exibe a composição por município, com ordenação e exportação."""
    st.caption(
        f"Municípios no gráfico: {perfil_or['municipio'].nunique()}. "
        "Para alterar a seleção, utilize os filtros da barra lateral e clique em "
        "**Aplicar filtros**. Clique ou toque em um segmento da barra para "
        "consultar a quantidade de exames e a participação percentual."
    )
    perfil_or = calcular_participacao(perfil_or, ["municipio"]).dropna(
        subset=["Participação (%)"]
    )
    if perfil_or.empty:
        st.info("Não há municípios com total classificável maior que zero.")
        return
    totais_or = (
        perfil_or.groupby("municipio")["quantidade_exames"]
        .sum(min_count=1)
    )
    with st.container(key="outubro_perfil_etario_sort_panel"):
        ordem_etaria_or = st.selectbox(
            "Ordenar por", ["A–Z", "Maior para menor"],
            index=0, key="outubro_rosa_grupo_etario_sort",
            help="Maior para menor considera o total de exames "
                 "com idade classificável no município.",
        )
    municipios_etarios_or = sorted(
        totais_or.index.tolist(), key=lambda nome: nome.casefold()
    )
    if ordem_etaria_or == "Maior para menor":
        municipios_etarios_or.sort(
            key=lambda municipio: (
                -float(totais_or[municipio]),
                municipio.casefold(),
            )
        )
    fig_etario_or = px.bar(
        perfil_or, y="municipio", x="Participação (%)",
        color="Grupo", orientation="h", barmode="stack",
        color_discrete_map=CORES_GRUPOS,
        category_orders={
            "municipio": municipios_etarios_or,
            "Grupo": list(GRUPOS_ETARIOS),
        },
        custom_data=["quantidade_exames"],
        labels={"municipio": "Município"},
    )
    fig_etario_or.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(municipios_etarios_or)),
        automargin=True,
    )
    fig_etario_or.update_xaxes(
        range=[0, 100], ticksuffix="%",
        title_text="Participação dos exames (%)",
    )
    fig_etario_or.update_traces(
        hovertemplate="%{y}<br>Grupo: %{fullData.name}"
        "<br>Exames: %{customdata[0]:,.0f}"
        "<br>Participação: %{x:.2f}%<extra></extra>"
    )
    fig_etario_or.update_layout(
        legend=dict(title_text="Grupo etário", orientation="h",
                    x=0, y=1.035, yanchor="bottom"),
        margin=dict(l=150, r=35, t=100, b=60),
        bargap=0.25,
    )
    download_plot(
        fig_etario_or,
        "outubro_rosa_perfil_etario_consolidado_municipio.png",
        altura=max(520, 43 * len(municipios_etarios_or) + 155),
        largura=1600,
        min_chart_width=690,
        rotulos_exportacao="percentual_horizontal",
        titulo_exportacao=(
            "Outubro Rosa — Perfil etário por município (%)"
        ),
    )
    renderizar_tabela_etaria_municipal(perfil_or, municipios_etarios_or)


def renderizar_perfil_municipal() -> None:
    """Consulta a base consolidada apenas com o período completo 2020–2025."""
    section("03", "Perfil etário municipal · consolidado 2020–2025")
    indicator_context(
        "Base fixa · setembro–dezembro de 2020–2025",
        "A tabela Gold deste cruzamento não contém ano ou mês. Exige os seis anos "
        "selecionados e respeita o filtro de municípios; não representa somente outubro.",
    )
    st.markdown(
        "Mostra como os exames citopatológicos se distribuem entre os grupos "
        "etários em cada município, com destaque para a **população-alvo "
        "de 25 a 64 anos**. Os resultados reúnem os registros de "
        "**setembro a dezembro de 2020–2025**, sem distinção por ano ou mês."
    )
    with st.container(key="outubro_ajuda_perfil"):
        with st.expander("ℹ️ Como interpretar", expanded=False):
            st.markdown(
                "Cada barra representa **100% dos exames com idade identificada** "
                "em um município. As cores indicam a participação de **menores "
                "de 25 anos, 25–64 anos e 65 anos ou mais**. "
                "Quanto maior a parcela de 25–64 anos, maior a participação "
                "da população-alvo entre os exames registrados. "
                "O gráfico **não mede quantas mulheres distintas foram atendidas** "
                "nem permite avaliar exclusivamente o mês de outubro, pois "
                "os dados estão consolidados para todo o período."
            )

    anos_ativos_q02 = set(data_loader.selected_years())
    if anos_ativos_q02 != ANOS_CONSOLIDADOS:
        st.info(
            "Este cruzamento está disponível somente para o período completo "
            "**2020–2025**. A tabela Gold consolidada não possui coluna de ano; "
            "para visualizar o gráfico, selecione todos os anos no filtro lateral. "
            "O filtro de municípios continua sendo respeitado."
        )
    else:
        try:
            perfil_or = filtered("outubro_grupo_etario")
        except ValueError as exc:
            if "Tabela não permitida" not in str(exc):
                raise
            st.warning(
                "A versão do carregador de dados ainda não reconhece a tabela "
                "do novo cruzamento etário. Atualize ou reinicie o aplicativo "
                "no Streamlit Cloud para carregar o código mais recente."
            )
            perfil_or = pd.DataFrame()
        except data_loader.GoldConsultaIndisponivel:
            st.warning(
                "Não foi possível consultar a tabela Gold "
                "`fato_outubro_rosa_grupo_etario`. "
                "Verifique a conexão, as permissões e a disponibilidade "
                "da tabela no Databricks."
            )
            perfil_or = pd.DataFrame()

        if perfil_or.empty:
            st.info(
                "O gráfico ficará disponível quando a fonte Gold do "
                "perfil etário consolidado estiver acessível."
            )
        elif not COLUNAS_PERFIL_ETARIO.issubset(perfil_or.columns):
            st.warning(
                "A tabela Gold do perfil etário não possui todas as colunas "
                "esperadas: município, grupo_etario e quantidade_exames."
            )
        else:
            perfil_or = preparar_perfil_etario(perfil_or, ["municipio"])
            if perfil_or.empty:
                st.info("Não há dados etários válidos para os municípios selecionados.")
            elif perfil_or.duplicated(["municipio", "Grupo"]).any():
                st.error(
                    "A Gold possui grupos etários duplicados por município. "
                    "Verifique a integridade de "
                    "`fato_outubro_rosa_grupo_etario`."
                )
            else:
                renderizar_grafico_etario_municipal(perfil_or)


def renderizar_detalhamento(dados: pd.DataFrame, periodo: str) -> None:
    """Exibe os registros mensais observados e a exportação CSV."""
    section("04", "Dados para consulta e exportação")
    indicator_context(
        f"Dados mensais para exportação · {periodo}",
        "Exames observados entre setembro e dezembro dos anos e municípios selecionados.",
    )
    st.markdown(
        "Consulte os registros observados por município, ano e mês "
        "ou exporte os dados utilizados na análise de produção mensal."
    )
    detalhes = (
        dados.groupby(["municipio", "ano", "mes"], as_index=False)["quantidade"]
        .sum(min_count=1)
        .sort_values(["municipio", "ano", "mes"])
        .rename(columns={
            "municipio": "Município", "ano": "Ano",
            "mes": "Mês (número)", "quantidade": "Exames",
        })
    )
    detalhes["Mês"] = detalhes["Mês (número)"].map(MESES)
    detalhes = detalhes[["Município", "Ano", "Mês (número)", "Mês", "Exames"]]
    with st.expander("Ver tabela mensal detalhada", expanded=False):
        display_table(detalhes, integer_columns=["Ano", "Mês (número)", "Exames"])
        st.download_button(
            "⬇️ Exportar dados mensais (CSV)",
            data=detalhes.to_csv(
                index=False, sep=";", decimal=".", float_format="%.2f"
            ).encode("utf-8-sig"),
            file_name="siscan_outubro_rosa_producao_mensal.csv",
            mime="text/csv",
            key="outubro_rosa_mensal_csv",
        )
    st.caption(
        "Nota: a produção mensal geral é observada no SISCAN; as "
        "visualizações etárias utilizam bases específicas, conforme "
        "a granularidade disponível. Não se infere causalidade da campanha."
    )


def main() -> None:
    """Orquestra a página sem misturar as granularidades das fontes Gold."""
    configurar_pagina()
    dados = filtered("temporal")
    if not require(dados, COLUNAS_PRODUCAO):
        return

    dados = preparar_producao(dados)
    if dados.empty:
        st.info("Não há registros mensais entre setembro e dezembro para os filtros selecionados.")
        return

    periodo = years_label()
    renderizar_producao_mensal(agregar_producao_mensal(dados))
    renderizar_comparacao_municipal(dados)
    renderizar_perfil_mensal(periodo)
    renderizar_perfil_municipal()
    renderizar_detalhamento(dados, periodo)


if __name__ == "__main__":
    main()
