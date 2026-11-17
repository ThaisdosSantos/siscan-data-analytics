"""Adequabilidade das amostras citopatológicas na 10ª CRS.

Apresenta contagens e proporções das categorias classificadas na Gold.
Amostras insatisfatórias e rejeitadas não são resultados citológicos
alterados; os registros não representam mulheres distintas.
"""

import copy
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, require
from utils.theme import (
    ORANGE,
    SKY,
    export_table,
    fmt_num,
    fmt_pct,
    metric_row,
    page_header,
    pct,
)

SATISFATORIA = "Satisfatória"
INSATISFATORIA = "Insatisfatória"
REJEITADA = "Rejeitada"
CATEGORIAS = (INSATISFATORIA, REJEITADA, SATISFATORIA)
CATEGORIAS_INADEQUADAS = (INSATISFATORIA, REJEITADA)
CORES_INADEQUADAS = {INSATISFATORIA: ORANGE, REJEITADA: SKY}
COLUNAS_OBRIGATORIAS = ("municipio", "ano", "categoria_adequabilidade", "quantidade_amostras")
COLUNAS_TOTAL = (*CATEGORIAS, "total")


def classificar_categoria(valor: object) -> str | None:
    """Normaliza os rótulos Gold, sem atribuir categoria a valores desconhecidos."""
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    categorias = {
        "satisfatoria": SATISFATORIA,
        "insatisfatoria": INSATISFATORIA,
        "rejeitada": REJEITADA,
    }
    return categorias.get(texto.strip().casefold())


def preparar_adequabilidade(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Seleciona registros classificados e valida suas quantidades.

    Args:
        df: Fato Gold filtrado por município e ano.

    Returns:
        Cópia dos registros classificados e número de linhas não reconhecidas.

    Raises:
        ValueError: Quando uma contagem classificada é ausente, negativa
            ou não inteira, ou quando município/ano é inválido.
    """
    dados = df.copy()
    dados["categoria"] = dados["categoria_adequabilidade"].map(classificar_categoria)
    desconhecidas = int(dados["categoria"].isna().sum())
    dados = dados.loc[dados["categoria"].notna()].copy()
    dados["quantidade_amostras"] = pd.to_numeric(
        dados["quantidade_amostras"], errors="coerce"
    )
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")

    quantidades = dados["quantidade_amostras"]
    anos = dados["ano"]
    if (
        quantidades.isna().any()
        or (quantidades < 0).any()
        or (quantidades % 1 != 0).any()
        or anos.isna().any()
        or (anos % 1 != 0).any()
        or dados["municipio"].isna().any()
        or dados["municipio"].astype(str).str.strip().eq("").any()
    ):
        raise ValueError(
            "A Gold de adequabilidade contém campos inválidos. "
            "Revise as quantidades, os anos e os municípios."
        )

    dados["ano"] = anos.astype(int)
    return dados, desconhecidas


def agregar_categorias(dados: pd.DataFrame) -> pd.Series:
    """Soma contagens classificadas, incluindo categorias sem registros como zero."""
    return (
        dados.groupby("categoria")["quantidade_amostras"]
        .sum(min_count=1)
        .reindex(CATEGORIAS, fill_value=0)
    )


def agregar_evolucao_anual(dados: pd.DataFrame) -> pd.DataFrame:
    """Retorna quantidades observadas de insatisfatórias e rejeitadas por ano."""
    return (
        dados.loc[dados["categoria"].isin(CATEGORIAS_INADEQUADAS)]
        .groupby(["ano", "categoria"], as_index=False)["quantidade_amostras"]
        .sum(min_count=1)
        .sort_values(["ano", "categoria"], kind="stable")
    )


def calcular_taxas(tabela: pd.DataFrame) -> pd.DataFrame:
    """Recalcula taxas sobre o total classificado, mantendo NaN para total zero."""
    resultado = tabela.copy()
    base = resultado["total"].where(resultado["total"].gt(0))
    resultado["taxa_insatisfatorias_pct"] = resultado[INSATISFATORIA].div(base).mul(100)
    resultado["taxa_rejeitadas_pct"] = resultado[REJEITADA].div(base).mul(100)
    return resultado


def agregar_municipios(dados: pd.DataFrame) -> pd.DataFrame:
    """Consolida contagens e taxas municipais no período selecionado.

    Uma categoria omitida na tabulação de um município com registros
    classificados contribui com zero; não são criados municípios sem dados.
    """
    contagens = (
        dados.groupby(["municipio", "categoria"])["quantidade_amostras"]
        .sum(min_count=1)
        .unstack("categoria", fill_value=0)
        .reindex(columns=CATEGORIAS, fill_value=0)
    )
    contagens["total"] = contagens[list(CATEGORIAS)].sum(axis=1)
    return calcular_taxas(contagens.reset_index())


def adicionar_totalizador(tabela: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta o total das contagens e recalcula as taxas regionais.

    Não soma nem calcula a média simples dos percentuais municipais.
    """
    totais = tabela[list(COLUNAS_TOTAL)].sum()
    linha_total = pd.DataFrame([{"municipio": "Total", **totais.to_dict()}])
    return pd.concat([tabela, calcular_taxas(linha_total)], ignore_index=True)


def configurar_pagina() -> None:
    """Configura os estilos e o cabeçalho específicos desta página."""
    page_header(
        "Qualidade da amostra",
        "Adequabilidade das amostras",
        "Apresenta a distribuição das amostras citopatológicas segundo sua "
        "adequabilidade, a evolução anual das amostras insatisfatórias e rejeitadas "
        "e a comparação dos resultados entre os municípios selecionados.",
    )
    st.markdown(
        """
        <style>
        .pet-hero {margin-bottom:0 !important;}
        .adequabilidade-section-title {
          margin:30px 0 17px; padding:9px 0 12px;
          border-bottom:2px solid #D8E5EF;
          font:750 clamp(21px,2vw,26px)/1.35 Manrope,Arial,sans-serif;
          color:#1A3B5C;
        }
        .adequabilidade-section-title .adequabilidade-section-index {
          color:#006C9A; margin-right:10px;
        }
        @media(max-width:768px) {
          .adequabilidade-section-title {margin-top:23px;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_perfil(dados: pd.DataFrame) -> None:
    """Exibe os indicadores regionais e a proporção de amostras inadequadas."""
    totais = agregar_categorias(dados)
    total = totais.sum(min_count=1)
    inadequadas = totais[list(CATEGORIAS_INADEQUADAS)].sum()
    st.markdown(
        '<h2 class="adequabilidade-section-title">'
        '<span class="adequabilidade-section-index">01</span>'
        'Perfil de adequabilidade das amostras</h2>',
        unsafe_allow_html=True,
    )
    metric_row([
        ("Amostras avaliadas", fmt_num(total)),
        ("Satisfatórias", fmt_pct(pct(totais[SATISFATORIA], total))),
        ("Insatisfatórias e rejeitadas", fmt_pct(pct(inadequadas, total))),
    ])
    renderizar_guia_categorias()


def renderizar_guia_categorias() -> None:
    """Apresenta as definições de adequabilidade e a referência metodológica."""
    with st.expander("ℹ️ Entenda as categorias de adequabilidade", expanded=False):
        st.markdown(
            """
        <style>
        .pet-adequacy-guide {
            margin:3px 0 0; padding:0; border:0;
            background:transparent; color:#1A3B5C;
            font-family:Manrope,Arial,sans-serif;
        }
        .pet-adequacy-guide-grid {
            display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px;
        }
        .pet-adequacy-guide-item {
            background:#FFFFFF; border:1px solid #E2EAF0;
            border-radius:9px; padding:14px 15px;
            line-height:1.55; font-size:.88rem;
        }
        .pet-adequacy-guide-item strong {display:block;margin-bottom:6px;font-size:.95rem;}
        .pet-adequacy-guide-item p {margin:0;}
        .pet-adequacy-guide-foot {
            margin:14px 0 0;font-size:.82rem;line-height:1.5;color:#334E68;
        }
        @media(max-width:800px){
            .pet-adequacy-guide-grid {grid-template-columns:1fr;}
            .pet-adequacy-guide {padding:15px;}
        }
        </style>
        <section class="pet-adequacy-guide" aria-label="Definições de adequabilidade">
          <div class="pet-adequacy-guide-grid">
            <div class="pet-adequacy-guide-item">
              <strong>✅ Satisfatória</strong>
              <p>O material permite a análise microscópica e a emissão de
              resultado citopatológico. Isso não significa, por si só,
              ausência de alterações nas células.</p>
            </div>
            <div class="pet-adequacy-guide-item">
              <strong>⚠️ Insatisfatória</strong>
              <p>O material foi recebido, mas não permite uma avaliação
              confiável, por exemplo, por ter poucas células ou excesso
              de sangue que prejudica a leitura.</p>
            </div>
            <div class="pet-adequacy-guide-item">
              <strong>❌ Rejeitada</strong>
              <p>A amostra não pode ser aceita para análise, por exemplo,
              devido a problemas de identificação, informações incompatíveis
              ou lâmina quebrada.</p>
            </div>
          </div>
          <p class="pet-adequacy-guide-foot"><strong>Importante:</strong>
          insatisfatória e rejeitada não são diagnósticos de câncer nem
          resultados citológicos alterados; indicam que não foi possível
          realizar uma avaliação adequada do material.
          <br><strong>Referência:</strong> INCA/Ministério da Saúde —
          Nomenclatura Brasileira para Laudos Citopatológicos Cervicais.</p>
        </section>
            """,
            unsafe_allow_html=True,
        )


def renderizar_evolucao_anual(dados: pd.DataFrame) -> None:
    """Exibe a evolução anual das amostras inadequadas em quantidade absoluta."""
    st.markdown(
        '<h2 class="adequabilidade-section-title">'
        '<span class="adequabilidade-section-index">02</span>'
        'Evolução anual da adequabilidade</h2>',
        unsafe_allow_html=True,
    )
    series = agregar_evolucao_anual(dados)
    if not series.empty:
        st.subheader("Evolução anual de amostras insatisfatórias e rejeitadas")
        st.markdown(
            "Mostra **quantas amostras insatisfatórias e rejeitadas foram registradas "
            "em cada ano**, permitindo acompanhar mudanças no volume dessas categorias."
        )
        with st.expander("ℹ️ Como interpretar a evolução anual da adequabilidade", expanded=False):
            st.markdown(
                "**Eixo horizontal:** anos selecionados. **Eixo vertical:** "
                "quantidade de amostras. A linha **laranja** representa "
                "amostras insatisfatórias e a linha **azul-claro**, rejeitadas. "
                "Cada ponto mostra o total registrado naquela categoria e ano. "
                "Uma linha ascendente indica aumento do **número absoluto** "
                "de amostras, não necessariamente piora proporcional da qualidade: "
                "o volume total de exames também pode ter mudado. "
                "Os resultados não indicam quantas mulheres distintas foram atendidas."
            )
        fig = px.line(
            series, x="ano", y="quantidade_amostras", color="categoria", markers=True,
            color_discrete_map=CORES_INADEQUADAS,
            title="Quantidade anual de amostras por categoria",
            labels={"quantidade_amostras": "Quantidade de amostras", "ano": "Ano", "categoria": ""},
        )
        fig.update_xaxes(type="category")
        fig.update_yaxes(tickformat=",d", rangemode="tozero")
        fig.update_traces(
            hovertemplate="Ano: %{x}<br>Quantidade: %{y:,.0f} amostras<extra>%{fullData.name}</extra>"
        )
        # Os rótulos de valores são exclusivos do PNG exportado.
        export_fig = copy.deepcopy(fig)
        for trace in export_fig.data:
            values = (
                series.loc[series["categoria"] == trace.name]
                .sort_values("ano")["quantidade_amostras"]
            )
            trace.update(
                mode="lines+markers+text",
                text=[f"{int(value):,}" if pd.notna(value) else "—" for value in values],
                textposition="top center" if trace.name == INSATISFATORIA else "bottom center",
                textfont=dict(size=16, color="#1A3B5C"),
            )
        export_fig.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            margin=dict(l=100, r=185, t=95, b=85),
        )
        export_fig.update_yaxes(rangemode="tozero")
        chart_with_right_click_download(
            fig,
            filename="adequabilidade_quantidade_anual_categorias.png",
            height=430,
            export_fig=export_fig,
        )


def renderizar_comparacao_municipal(dados: pd.DataFrame) -> None:
    """Exibe a tabela municipal com totalizador destacado e exportação CSV."""
    st.markdown(
        '<h2 class="adequabilidade-section-title">'
        '<span class="adequabilidade-section-index">03</span>'
        'Comparação municipal da adequabilidade</h2>',
        unsafe_allow_html=True,
    )
    st.subheader("Adequabilidade das amostras por município")
    st.markdown(
        "Compara a **quantidade e a proporção de amostras insatisfatórias e "
        "rejeitadas** entre os municípios do período selecionado."
    )
    with st.expander("ℹ️ Como interpretar a tabela municipal", expanded=False):
        st.markdown(
            "**Satisfatória, insatisfatória e rejeitada:** contagens de amostras "
            "em cada categoria. **Total:** soma dessas categorias no município. "
            "**Taxa de insatisfatórias (%):** quantidade insatisfatória ÷ total × 100. "
            "**Taxa de rejeitadas (%):** quantidade rejeitada ÷ total × 100. "
            "A última linha totaliza as quantidades e recalcula as taxas "
            "sobre o total selecionado, "
            "sem somar percentuais municipais. "
            "As taxas descrevem adequabilidade da amostra, não alterações citológicas."
        )
    table = adicionar_totalizador(agregar_municipios(dados))
    st.markdown(
        """
        <style>
        .pet-table tbody tr:last-child {
            background: #e7f1f8 !important;
            font-weight: 750;
            border-top: 2px solid #006C9A;
        }
        .pet-table tbody tr:last-child td {
            font-weight: 750;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    export_table(table, "siscan_adequabilidade.csv")


def main() -> None:
    """Orquestra as três seções após verificar a integridade dos dados Gold."""
    configurar_pagina()
    df = filtered("adequabilidade")
    if not require(df, COLUNAS_OBRIGATORIAS):
        return

    try:
        dados, desconhecidas = preparar_adequabilidade(df)
    except ValueError as exc:
        st.error(str(exc))
        return

    if desconhecidas:
        st.warning(
            f"Há {fmt_num(desconhecidas)} registros com categoria não reconhecida; "
            "eles não entram nos totais e percentuais classificados."
        )
    if dados.empty:
        st.info("Não há amostras classificadas para os filtros selecionados.")
        return

    renderizar_perfil(dados)
    renderizar_evolucao_anual(dados)
    renderizar_comparacao_municipal(dados)


if __name__ == "__main__":
    main()
