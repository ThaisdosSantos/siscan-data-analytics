"""Outubro Rosa (Q2): análise anual por município e faixa etária da Gold canônica.

A fonte Q02-outubroRosa tem quatro CSVs por ano que representam recortes
repetidos. A Gold usa um arquivo representativo por município/ano (moda).
Não há interpretação mensal válida nem junção com a fonte geral de Q1.
"""
import copy

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.theme import (
    apply_custom_css, page_header, display_table, fmt_num, NAVY,
)
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import (
    filtered, require, sidebar_filters, years_label,
)

st.set_page_config(page_title="Outubro Rosa | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
st.markdown("""
<style>
.pet-hero {margin-bottom:0!important}
.or-section-title {
    margin:30px 0 17px;padding:9px 0 12px;
    border-bottom:2px solid #D8E5EF;
    font:750 clamp(21px,2vw,26px)/1.35 Manrope,Arial,sans-serif;
    color:#1A3B5C;
}
.or-section-index {color:#006C9A;margin-right:10px}
@media(max-width:768px) {
    .or-section-title {margin:24px 0 13px;font-size:21px}
}
</style>
""", unsafe_allow_html=True)


def section(index, title):
    st.markdown(
        '<h2 class="or-section-title"><span class="or-section-index">'
        + index + '</span>' + title + '</h2>',
        unsafe_allow_html=True,
    )


GRUPOS = {
    "<= 24 anos": "<25 anos",
    "25 a 64 anos": "25–64 anos",
    ">= 65 anos": "≥65 anos",
}
ORDEM = ["<25 anos", "25–64 anos", "≥65 anos"]
CORES = {"<25 anos": "#169B62", "25–64 anos": "#1757A6", "≥65 anos": "#E85D2A"}


def download_plot(fig, nome, altura=450, largura=1400):
    """Gráfico interativo e cópia independente para exportação PNG."""
    fig.update_layout(
        template="plotly_white", height=altura,
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=NAVY, size=13),
        margin=dict(l=75, r=145, t=45, b=70),
        legend_title_text="",
    )
    fig.update_yaxes(gridcolor="#E4EBF1", rangemode="tozero")
    imagem = copy.deepcopy(fig)
    imagem.update_layout(
        width=largura,
        height=max(altura + 100, 650),
        title=dict(text=nome.replace("_", " ").replace(".png", "").title(),
                   x=0.5, font=dict(size=22, color=NAVY)),
        margin=dict(l=110, r=210, t=105, b=100),
    )
    chart_with_right_click_download(
        fig, filename=nome, height=altura,
        min_chart_width=870, export_fig=imagem,
    )


page_header(
    "Campanha · Outubro Rosa",
    "Perfil dos exames registrados no Outubro Rosa",
    "Apresenta a evolução anual dos registros associados à campanha, "
    "a distribuição por faixa etária e as diferenças entre municípios "
    "no período selecionado.",
)

st.markdown(
    '<div style="margin:15px 0 19px;padding:12px 16px;background:#EEF5FA;'
    'border-left:4px solid #006C9A;border-radius:8px;color:#1A3B5C;'
    'line-height:1.6;font-size:.91rem;">'
    '<strong>Fonte:</strong> SISCAN/DATASUS · Gold '
    '<code>fato_outubro_rosa_campanha_anual</code>. '
    'A fonte é consolidada por <strong>ano</strong>, sem informações '
    'mensais independentes que permitam comparar setembro e outubro.'
    '</div>',
    unsafe_allow_html=True,
)

dados = filtered("outubro_anual")
NECESSARIAS = [
    "municipio", "ano", "faixa_etaria", "grupo_etario_3",
    "quantidade_exames",
]
if require(dados, NECESSARIAS):
    dados = dados.copy()
    dados["quantidade_exames"] = pd.to_numeric(
        dados["quantidade_exames"], errors="coerce"
    )
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados["grupo"] = dados["grupo_etario_3"].astype(str).str.strip().map(GRUPOS)
    dados = dados.dropna(subset=["municipio", "ano", "grupo", "quantidade_exames"])
    dados = dados.loc[dados["quantidade_exames"] >= 0].copy()
    dados["ano"] = dados["ano"].astype(int)

    if dados.empty:
        st.info("Não há exames registrados para os filtros selecionados.")
        st.stop()

    # Uma linha por município × ano × faixa etária; somente a métrica
    # atômica é aditiva. Total/grupo na Gold são colunas repetidas.
    total = float(dados["quantidade_exames"].sum())
    por_grupo = (
        dados.groupby("grupo")["quantidade_exames"]
        .sum().reindex(ORDEM, fill_value=0)
    )
    alvo = float(por_grupo.loc["25–64 anos"])
    percentual_alvo = 100 * alvo / total if total > 0 else float("nan")
    cidades = dados["municipio"].nunique()
    anos = sorted(dados["ano"].unique().tolist())
    periodo = years_label()

    section("01", "Panorama dos registros da campanha")
    k1, k2, k3 = st.columns(3)
    k1.metric("Exames registrados", fmt_num(total))
    k2.metric("Exames de 25–64 anos", fmt_num(alvo))
    k3.metric("Participação de 25–64 anos", (
        f"{percentual_alvo:.2f}%" if pd.notna(percentual_alvo) else "N/D"
    ))
    st.caption(
        f"Recorte: {periodo} · {cidades} município(s). "
        "Os indicadores somam uma única observação representativa "
        "por município, ano e faixa etária."
    )
    with st.expander("ℹ️ Como interpretar os indicadores", expanded=False):
        st.markdown(
            "**Exames registrados:** total do recorte anual de Outubro Rosa "
            "presente na Gold. **Exames de 25–64 anos:** quantidade no grupo "
            "etário de referência. **Participação de 25–64 anos:** "
            "exames desse grupo ÷ total de exames do recorte × 100. "
            "Os registros não representam mulheres distintas."
        )

    section("02", "Evolução anual dos exames")
    st.markdown(
        "Acompanha **quantos exames foram registrados em cada ano** do recorte "
        "e como se distribuem entre os grupos etários."
    )
    anual = (
        dados.groupby(["ano", "grupo"], as_index=False)["quantidade_exames"]
        .sum(min_count=1)
    )
    somas_ano = anual.groupby("ano")["quantidade_exames"].sum()
    anual["participacao_pct"] = (
        anual["quantidade_exames"]
        .div(anual["ano"].map(somas_ano).where(
            anual["ano"].map(somas_ano) > 0
        )).mul(100)
    )
    with st.expander("ℹ️ Como interpretar a evolução anual", expanded=False):
        st.markdown(
            "**Eixo horizontal:** anos selecionados. **Eixo vertical:** "
            "quantidade de exames. Cada cor identifica um grupo etário. "
            "A altura da barra é o total anual; passe o mouse sobre um "
            "segmento para consultar sua quantidade e participação. "
            "Não é possível deduzir a produção de cada mês a partir "
            "desta tabela anual."
        )
    grafico_anual = px.bar(
        anual, x="ano", y="quantidade_exames", color="grupo",
        barmode="stack", color_discrete_map=CORES,
        category_orders={"grupo": ORDEM, "ano": anos},
        custom_data=["participacao_pct"],
        labels={"ano": "Ano", "quantidade_exames": "Exames",
                "grupo": "Grupo etário"},
    )
    grafico_anual.update_xaxes(type="category")
    grafico_anual.update_traces(
        hovertemplate="Ano: %{x}<br>Exames: %{y:,.0f}"
        "<br>Participação no ano: %{customdata[0]:.2f}%"
        "<extra>%{fullData.name}</extra>",
    )
    download_plot(
        grafico_anual, "outubro_rosa_evolucao_anual.png", altura=470,
    )

    section("03", "Composição etária da campanha")
    st.markdown(
        "Compara a **participação dos grupos etários** nos registros anuais, "
        "com destaque para a faixa de 25–64 anos."
    )
    tipo = st.selectbox(
        "Visualizar distribuição etária",
        ["Participação (%)", "Quantidade de exames"],
        key="outubro_anual_medida_etaria",
    )
    percentual = tipo == "Participação (%)"
    coluna = "participacao_pct" if percentual else "quantidade_exames"
    with st.expander("ℹ️ Como interpretar a composição etária", expanded=False):
        st.markdown(
            "**Participação (%):** cada barra representa 100% dos exames do ano. "
            "Os segmentos mostram a parcela de cada grupo etário; por exemplo, "
            "80% significa 80 em cada 100 exames registrados. "
            "**Quantidade:** mostra o número absoluto de exames de cada grupo. "
            "As proporções são calculadas sobre o total de cada ano, "
            "não pela média de percentuais municipais."
        )
    composicao = px.bar(
        anual, x="ano", y=coluna, color="grupo", barmode="stack",
        color_discrete_map=CORES,
        category_orders={"grupo": ORDEM, "ano": anos},
        custom_data=["quantidade_exames", "participacao_pct"],
        labels={"ano": "Ano", "grupo": "Grupo etário",
                "participacao_pct": "Participação (%)",
                "quantidade_exames": "Exames"},
    )
    composicao.update_xaxes(type="category")
    composicao.update_traces(
        hovertemplate="Ano: %{x}<br>Exames: %{customdata[0]:,.0f}"
        "<br>Participação: %{customdata[1]:.2f}%"
        "<extra>%{fullData.name}</extra>"
    )
    if percentual:
        composicao.update_yaxes(range=[0, 100], ticksuffix="%", tickformat=".0f")
    download_plot(composicao, "outubro_rosa_composicao_etaria_anual.png", altura=470)

    section("04", "Comparação entre municípios")
    st.markdown(
        "Compara o **volume de exames registrados** por município nos anos "
        "selecionados. A participação de 25–64 anos também é apresentada "
        "para facilitar a análise do público-alvo."
    )
    municipal = (
        dados.groupby(["municipio", "grupo"], as_index=False)["quantidade_exames"]
        .sum(min_count=1)
    )
    totais_mun = municipal.groupby("municipio")[
        "quantidade_exames"
    ].sum().rename("Total de exames")
    qtd_alvo_mun = (
        municipal.loc[municipal["grupo"] == "25–64 anos"]
        .set_index("municipio")["quantidade_exames"]
        .rename("Exames de 25–64 anos")
    )
    municipal_resumo = pd.concat([totais_mun, qtd_alvo_mun], axis=1).fillna(0)
    municipal_resumo["Participação de 25–64 anos (%)"] = (
        municipal_resumo["Exames de 25–64 anos"]
        .div(municipal_resumo["Total de exames"].where(
            municipal_resumo["Total de exames"] > 0
        )).mul(100)
    )
    modo_ordem = st.selectbox(
        "Ordenar municípios por",
        ["Maior para menor", "A–Z"],
        key="outubro_anual_ordem_municipal",
    )
    if modo_ordem == "Maior para menor":
        municipal_resumo = municipal_resumo.sort_values(
            ["Total de exames"], ascending=False,
        )
    else:
        municipal_resumo = municipal_resumo.sort_index(key=lambda idx: idx.str.casefold())
    ranking = municipal_resumo.reset_index().rename(columns={"municipio": "Município"})
    with st.expander("ℹ️ Como interpretar a comparação municipal", expanded=False):
        st.markdown(
            "**Cada barra:** número de exames registrados no município durante "
            "os anos selecionados. Barras maiores representam mais exames, "
            "não necessariamente maior cobertura populacional. "
            "A participação etária é calculada em relação ao total "
            "do próprio município."
        )
    fig_municipal = px.bar(
        ranking, x="Total de exames", y="Município",
        orientation="h", color_discrete_sequence=["#006C9A"],
        custom_data=["Exames de 25–64 anos", "Participação de 25–64 anos (%)"],
    )
    fig_municipal.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(ranking["Município"].tolist())),
        automargin=True,
    )
    fig_municipal.update_traces(
        hovertemplate="%{y}<br>Exames: %{x:,.0f}"
        "<br>25–64 anos: %{customdata[0]:,.0f}"
        "<br>Participação de 25–64: %{customdata[1]:.2f}%<extra></extra>",
    )
    download_plot(
        fig_municipal, "outubro_rosa_comparacao_municipios.png",
        altura=max(530, 42 * len(ranking) + 125),
    )

    st.markdown("### Distribuição etária por município")
    st.markdown(
        "Mostra o percentual de cada grupo etário **dentro do próprio município**, "
        "considerando os anos selecionados."
    )
    municipal["participacao_pct"] = (
        municipal["quantidade_exames"]
        .div(municipal["municipio"].map(totais_mun).where(
            municipal["municipio"].map(totais_mun) > 0
        )).mul(100)
    )
    distrib_mun = px.bar(
        municipal, x="municipio", y="participacao_pct", color="grupo",
        barmode="stack", color_discrete_map=CORES,
        category_orders={
            "grupo": ORDEM,
            "municipio": ranking["Município"].tolist(),
        },
        custom_data=["quantidade_exames"],
        labels={"municipio": "Município", "participacao_pct": "Participação (%)"},
    )
    distrib_mun.update_traces(
        hovertemplate="%{x}<br>Exames: %{customdata[0]:,.0f}"
        "<br>Participação: %{y:.2f}%<extra>%{fullData.name}</extra>",
    )
    distrib_mun.update_xaxes(tickangle=-65, tickfont=dict(size=12), automargin=True)
    distrib_mun.update_yaxes(range=[0, 100], ticksuffix="%")
    distrib_mun.update_layout(margin=dict(l=75, r=130, t=40, b=220))
    download_plot(distrib_mun, "outubro_rosa_distribuicao_etaria_municipal.png",
                  altura=650, largura=1650)

    section("05", "Dados detalhados da campanha")
    st.markdown(
        "Consulte os registros que compõem as visualizações, por **município, "
        "ano e faixa etária**, incluindo a competência do arquivo representativo "
        "selecionado na Gold."
    )
    with st.expander("ℹ️ Como a Gold consolida os arquivos", expanded=False):
        st.markdown(
            "Para cada município e ano, a Gold considera o **total mais frequente "
            "(moda)** entre os quatro arquivos de setembro a dezembro. "
            "Em caso de empate, escolhe o maior total; depois seleciona "
            "o arquivo de menor mês correspondente. **O mês escolhido serve "
            "para rastreabilidade, não para análise mensal.** "
            "Os totais repetidos em cada faixa etária não são somados."
        )

    colunas_detalhe = [
        "municipio", "ano", "faixa_etaria", "grupo",
        "quantidade_exames",
    ]
    if "mes_arquivo_representativo" in dados.columns:
        colunas_detalhe.append("mes_arquivo_representativo")
    detalhamento = dados[colunas_detalhe].rename(columns={
        "municipio": "Município",
        "ano": "Ano",
        "faixa_etaria": "Faixa etária",
        "grupo": "Grupo etário",
        "quantidade_exames": "Exames",
        "mes_arquivo_representativo": "Mês do arquivo representativo",
    }).sort_values(["Município", "Ano", "Faixa etária"])
    st.download_button(
        "⬇️ Exportar CSV detalhado",
        detalhamento.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="siscan_outubro_rosa_campanha_anual.csv",
        mime="text/csv", key="outubro_campanha_anual_download",
    )
    with st.expander("Ver dados detalhados da campanha", expanded=False):
        display_table(detalhamento, integer_columns=["Exames", "Ano"])

    st.caption(
        "Nota metodológica: esta página descreve o recorte anual disponibilizado "
        "na Gold. A fonte não permite inferir aumento de coletas em outubro "
        "nem medir efeito causal da campanha."
    )
