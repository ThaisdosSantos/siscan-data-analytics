"""Outubro Rosa: cruzamentos mensais da Gold territorial, setembro a dezembro."""
import copy

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.theme import (
    apply_custom_css, page_header, display_table, fmt_num, NAVY,
)
from utils.chart_download import chart_with_right_click_download
from utils import data_loader
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
    "Outubro Rosa: produção mensal de exames",
    "Compara a produção registrada entre setembro e dezembro, por ano e "
    "município de residência, nos 11 municípios da 10ª CRS (2020–2025).",
)

st.markdown(
    '<div style="margin:13px 0 16px;padding:10px 15px;background:#EEF5FA;'
    'border-left:4px solid #006C9A;border-radius:8px;color:#1A3B5C;'
    'font-size:.91rem;line-height:1.5">'
    '<strong>Fonte:</strong> SISCAN/DATASUS · '
    '<strong>Gold:</strong> fato_exames_temporais_territoriais '
    '(competência mensal da base geral).</div>',
    unsafe_allow_html=True,
)
with st.expander("ℹ️ Fontes, recorte e limitações", expanded=False):
    st.markdown(
        "A comparação utiliza apenas a tabela Gold mensal "
        "**fato_exames_temporais_territoriais**, no recorte de setembro "
        "a dezembro. Os arquivos dedicados Q02-outubroRosa não são "
        "utilizados aqui porque os meses indicados nesses arquivos "
        "não constituem uma série mensal confiável. "
        "**Variações de registros não comprovam efeito causal da campanha** "
        "nem informam a quantidade de mulheres distintas examinadas. "
        "Os resultados referem-se à produção registrada, não à cobertura "
        "do rastreamento."
    )

MESES = {9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
ORDEM_MESES = list(MESES.values())
CORES_MESES = {
    "Setembro": "#419AD1", "Outubro": "#E85D2A",
    "Novembro": "#218B65", "Dezembro": "#1A3B5C",
}

dados = filtered("temporal")
if not require(dados, ["municipio", "ano", "mes", "quantidade"]):
    st.stop()

dados = dados[["municipio", "ano", "mes", "quantidade"]].copy()
for coluna in ["ano", "mes", "quantidade"]:
    dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
dados = dados.dropna(subset=["municipio", "ano", "mes", "quantidade"])
dados = dados.loc[dados["mes"].isin(MESES)].copy()
dados = dados.loc[dados["quantidade"] >= 0].copy()
if dados.empty:
    st.info("Não há registros mensais entre setembro e dezembro para os filtros selecionados.")
    st.stop()
dados["ano"] = dados["ano"].astype(int)
dados["mes"] = dados["mes"].astype(int)
dados["Mês"] = dados["mes"].map(MESES)

# A métrica é aditiva, a participação territorial e os indicadores derivados
# não são; um município×ano×mês corresponde a uma competência mensal.
mensal = (
    dados.groupby(["ano", "mes", "Mês"], as_index=False)["quantidade"]
    .sum(min_count=1)
)
mensal["ano_texto"] = mensal["ano"].astype(str)
anos = sorted(dados["ano"].unique().tolist())
periodo = years_label()
cidades = dados["municipio"].nunique()

def variacao_percentual(outubro, setembro):
    if pd.isna(setembro) or pd.isna(outubro) or setembro <= 0:
        return float("nan")
    return (outubro - setembro) / setembro * 100

def chart_help(message):
    with st.expander("ℹ️ Como interpretar", expanded=False):
        st.markdown(message)

section("01", "Produção mensal e comparação com setembro")
st.markdown(
    "Compara a **quantidade de exames registrados** nos quatro meses. "
    "Os totais consideram os anos e municípios selecionados."
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
st.caption(
    f"Recorte ativo: {periodo} · {cidades} município(s). "
    "A variação usa as somas dos meses disponíveis; não indica causalidade."
)
chart_help(
    "**Variação (%) = (Outubro − Setembro) ÷ Setembro × 100.** "
    "Ao selecionar vários anos, o indicador combina os registros de "
    "setembro e outubro dos anos selecionados. Se setembro for zero "
    "ou algum dos meses estiver ausente, o percentual não é calculável."
)
fig = px.bar(
    mensal, x="ano_texto", y="quantidade", color="Mês",
    barmode="group", color_discrete_map=CORES_MESES,
    category_orders={"Mês": ORDEM_MESES, "ano_texto": [str(a) for a in anos]},
    labels={"ano_texto": "Ano", "quantidade": "Exames registrados"},
)
fig.update_traces(
    hovertemplate="Ano: %{x}<br>Exames: %{y:,.0f}<extra>%{fullData.name}</extra>"
)
download_plot(fig, "outubro_rosa_producao_mensal_por_ano.png", altura=490, largura=1550)

section("02", "Comparação anual: setembro × outubro")
st.markdown(
    "Evolução da **variação percentual de setembro para outubro** em cada ano, "
    "sem misturar os totais de anos distintos."
)
por_ano = (
    mensal.loc[mensal["mes"].isin([9, 10])]
    .pivot(index="ano", columns="mes", values="quantidade")
    .reindex(index=anos, columns=[9, 10])
    .rename(columns={9: "Setembro", 10: "Outubro"})
)
por_ano["Variação (%)"] = [
    variacao_percentual(row["Outubro"], row["Setembro"])
    for _, row in por_ano.iterrows()
]
anual_grafico = por_ano.reset_index()
anual_grafico["Ano"] = anual_grafico["ano"].astype(str)
anual_valida = anual_grafico.dropna(subset=["Variação (%)"]).copy()
if anual_valida.empty:
    st.info("Sem pares setembro–outubro completos para a comparação anual.")
else:
    anual_valida["Situação"] = anual_valida["Variação (%)"].map(
        lambda v: "Redução" if v < 0 else "Aumento ou estabilidade"
    )
    fig_ano = px.bar(
        anual_valida, x="Ano", y="Variação (%)", color="Situação",
        color_discrete_map={
            "Redução": "#B53A27", "Aumento ou estabilidade": "#218B65",
        },
        custom_data=["Setembro", "Outubro"],
        category_orders={"Ano": [str(a) for a in anos]},
    )
    fig_ano.update_traces(
        hovertemplate="Ano: %{x}<br>Setembro: %{customdata[0]:,.0f}"
        "<br>Outubro: %{customdata[1]:,.0f}"
        "<br>Variação: %{y:+.2f}%<extra></extra>"
    )
    fig_ano.update_yaxes(
        ticksuffix="%", tickformat=".2f",
        zeroline=True, zerolinecolor=NAVY, zerolinewidth=2,
    )
    fig_ano.update_layout(showlegend=False)
    chart_help(
        "Cada barra representa a diferença percentual entre outubro "
        "e setembro **do mesmo ano**. Verde: aumento ou estabilidade; "
        "vermelho: redução. Anos com meses ausentes ou setembro igual "
        "a zero não recebem percentual."
    )
    download_plot(fig_ano, "outubro_rosa_variacao_anual_setembro_outubro.png", altura=420)

section("03", "Comparação entre municípios")
st.markdown(
    "Examina a **variação de setembro para outubro por município**. "
    "A ordenação pode seguir a maior variação ou a ordem alfabética."
)
pares_municipais = (
    dados.loc[dados["mes"].isin([9, 10])]
    .groupby(["municipio", "mes"])["quantidade"].sum(min_count=1)
    .unstack("mes")
    .reindex(columns=[9, 10])
    .rename(columns={9: "Setembro", 10: "Outubro"})
)
pares_municipais["Variação (%)"] = [
    variacao_percentual(row["Outubro"], row["Setembro"])
    for _, row in pares_municipais.iterrows()
]
pares_municipais = pares_municipais.reset_index().rename(
    columns={"municipio": "Município"}
)
ordenacao = st.selectbox(
    "Ordenar municípios", ["Maior variação", "A–Z"],
    key="outubro_rosa_ordenacao",
)
municipios_validos = pares_municipais.dropna(subset=["Variação (%)"]).copy()
if ordenacao == "Maior variação":
    municipios_validos = municipios_validos.sort_values(
        "Variação (%)", ascending=False
    )
else:
    municipios_validos = municipios_validos.sort_values(
        "Município", key=lambda s: s.str.casefold()
    )
if municipios_validos.empty:
    st.info("Nenhum município possui dados completos para essa comparação.")
else:
    municipios_validos["Situação"] = municipios_validos["Variação (%)"].map(
        lambda v: "Redução" if v < 0 else "Aumento ou estabilidade"
    )
    municipios_validos["Variação formatada"] = municipios_validos[
        "Variação (%)"
    ].map(lambda v: f"{v:+.2f}%")
    fig_mun = px.bar(
        municipios_validos, x="Variação (%)", y="Município",
        color="Situação", orientation="h",
        color_discrete_map={
            "Redução": "#B53A27", "Aumento ou estabilidade": "#218B65",
        },
        custom_data=["Setembro", "Outubro", "Variação formatada"],
    )
    fig_mun.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(municipios_validos["Município"].tolist())),
        automargin=True,
    )
    fig_mun.update_xaxes(
        ticksuffix="%", tickformat=".2f", zeroline=True,
        zerolinecolor=NAVY, zerolinewidth=2,
    )
    fig_mun.update_traces(
        hovertemplate="%{y}<br>Setembro: %{customdata[0]:,.0f}"
        "<br>Outubro: %{customdata[1]:,.0f}"
        "<br>Variação: %{customdata[2]}<extra></extra>"
    )
    fig_mun.update_layout(showlegend=False)
    chart_help(
        "Cada barra representa um município. Valores positivos indicam "
        "aumento dos registros em outubro; valores negativos, redução. "
        "O cálculo soma os meses nos anos selecionados **antes** de "
        "calcular a variação. Sem setembro válido, o percentual fica ausente."
    )
    download_plot(
        fig_mun, "outubro_rosa_variacao_por_municipio.png",
        altura=max(500, 43 * len(municipios_validos) + 130), largura=1600,
    )
sem_base = pares_municipais.loc[
    pares_municipais["Variação (%)"].isna(), "Município"
].tolist()
if sem_base:
    st.caption(
        "Sem variação calculável (mês ausente ou setembro igual a zero): "
        + ", ".join(sorted(sem_base)) + "."
    )

section("04", "Matriz de produção: município × mês")
st.markdown(
    "Visualize a quantidade de exames em cada município nos meses de "
    "setembro a dezembro, somando apenas os anos selecionados."
)
matriz = (
    dados.groupby(["municipio", "mes"])["quantidade"].sum(min_count=1)
    .unstack("mes")
    .reindex(columns=list(MESES))
    .rename(columns=MESES)
)
matriz.index.name = "Município"
matriz = matriz.sort_index(key=lambda s: s.str.casefold())
if matriz.empty:
    st.info("Não há dados para a matriz municipal.")
else:
    import plotly.graph_objects as go
    z = matriz.to_numpy(dtype=float)
    customtext = [
        [f"{v:,.0f}".replace(",", ".") if pd.notna(v) else "—" for v in row]
        for row in z
    ]
    fig_heatmap = go.Figure(go.Heatmap(
        x=ORDEM_MESES, y=matriz.index.tolist(), z=z,
        colorscale=[[0, "#F0F6FA"], [0.5, "#70B0D0"], [1, "#07527C"]],
        text=customtext, texttemplate="%{text}",
        textfont=dict(size=12),
        hovertemplate="Município: %{y}<br>Mês: %{x}"
        "<br>Exames: %{text}<extra></extra>",
        colorbar=dict(title="Exames"),
    ))
    fig_heatmap.update_yaxes(
        autorange="reversed", automargin=True,
    )
    fig_heatmap.update_layout(margin=dict(l=115, r=100, t=45, b=80))
    chart_help(
        "Cada célula é a soma dos exames de um município em um mês "
        "considerando os anos selecionados. Células sem dados permanecem "
        "em branco — não são interpretadas como zero."
    )
    download_plot(
        fig_heatmap, "outubro_rosa_matriz_municipio_mes.png",
        altura=max(490, 37 * len(matriz) + 120), largura=1550,
    )

# Cruzamentos Gold adicionais: caso as tabelas novas ainda não tenham sido
# materializadas, a página calcula o mesmo agregado a partir de fatos Gold
# já existentes. Nenhuma fonte Q02 com meses ambíguos é utilizada.
def gold_nova_ou_vazia(chave):
    try:
        bruto = data_loader.load_table(chave, data_loader.selected_source())
    except data_loader.GoldConsultaIndisponivel:
        return pd.DataFrame()
    if bruto.empty:
        return bruto
    if "ano" in bruto:
        bruto = bruto[bruto["ano"].isin(data_loader.selected_years())]
    if "municipio" in bruto:
        cidades_ativas = st.session_state.get(
            "city_preference", list(data_loader.MUNICIPIOS.values())
        )
        bruto = bruto[bruto["municipio"].isin(cidades_ativas)]
    return bruto.copy()

section("05", "Volume de setembro a dezembro por município × ano")
st.markdown(
    "Acompanhe a **produção registrada entre setembro e dezembro**, "
    "por município e ano. Esses registros abrangem a rotina geral do "
    "SISCAN; **não representam exclusivamente atendimentos da campanha**."
)
producao_gold = gold_nova_ou_vazia("outubro_producao_anual")
if not producao_gold.empty and {
    "municipio", "ano", "exames_set_dez", "meses_observados"
}.issubset(producao_gold.columns):
    producao_gold["exames_set_dez"] = pd.to_numeric(
        producao_gold["exames_set_dez"], errors="coerce"
    )
    producao_gold["meses_observados"] = pd.to_numeric(
        producao_gold["meses_observados"], errors="coerce"
    )
    producao_ano = producao_gold.loc[
        producao_gold["meses_observados"] == 4,
        ["municipio", "ano", "exames_set_dez"],
    ].rename(columns={
        "municipio": "Município", "ano": "Ano",
        "exames_set_dez": "Exames",
    })
else:
    # Mesmo cálculo, obtido da Gold mensal já consultada pela página.
    qt_meses = (dados.groupby(["municipio", "ano"], as_index=False)
                .agg(meses_observados=("mes", "nunique"),
                     total=("quantidade", "sum")))
    producao_ano = (
        qt_meses.loc[qt_meses["meses_observados"] == 4]
        .rename(columns={
            "municipio": "Município", "ano": "Ano", "total": "Exames"
        })[["Município", "Ano", "Exames"]]
    )
if producao_ano.empty:
    st.info("Não há anos com os quatro meses disponíveis para esse cruzamento.")
else:
    producao_ano["Ano"] = pd.to_numeric(
        producao_ano["Ano"], errors="coerce"
    ).astype(int)
    ano_cols = sorted(producao_ano["Ano"].unique().tolist())
    pivot_producao = (
        producao_ano.pivot_table(
            index="Município", columns="Ano",
            values="Exames", aggfunc="sum"
        ).reindex(columns=ano_cols)
    )
    pivot_producao.index.name = "Município"
    pivot_producao = pivot_producao.sort_index(
        key=lambda idx: idx.str.casefold()
    )
    with st.expander("ℹ️ Como interpretar o volume por município × ano", expanded=False):
        st.markdown(
            "Cada barra agrupa os exames registrados **de setembro a dezembro "
            "do mesmo ano** no município. Competências ausentes não são "
            "substituídas por zero: anos incompletos são omitidos dessa "
            "comparação. Trata-se do total da rotina mensal, não do volume "
            "exclusivo ou do efeito da campanha."
        )
    fig_volume = px.bar(
        producao_ano.assign(Ano=producao_ano["Ano"].astype(str)),
        x="Município", y="Exames", color="Ano",
        barmode="group",
        category_orders={"Município": pivot_producao.index.tolist(),
                         "Ano": [str(a) for a in ano_cols]},
        labels={"Exames": "Exames registrados (set–dez)"},
    )
    fig_volume.update_xaxes(tickangle=-55, automargin=True)
    fig_volume.update_traces(
        hovertemplate="Município: %{x}<br>Exames: %{y:,.0f}"
        "<extra>Ano %{fullData.name}</extra>"
    )
    fig_volume.update_layout(margin=dict(l=75, r=130, t=40, b=170))
    download_plot(
        fig_volume, "outubro_rosa_volume_set_dez_municipio_ano.png",
        altura=570, largura=1800
    )
    with st.expander("Tabela dinâmica — município × ano", expanded=False):
        display_table(pivot_producao.reset_index())
    st.download_button(
        "⬇️ Exportar volume por município e ano",
        pivot_producao.reset_index().to_csv(
            index=False, sep=";", decimal=","
        ).encode("utf-8-sig"),
        file_name="siscan_set_dez_municipio_ano.csv",
        mime="text/csv", key="outubro_rosa_volume_municipio_ano_csv",
    )

section("06", "Perfil etário geral — contexto anual (Q3)")
st.markdown(
    "O cruzamento **município × grupo etário** e a evolução da participação "
    "de **25–64 anos** são calculados com a Gold **Q3 anual geral**. "
    "**Não** representam o perfil etário exclusivo de setembro–dezembro "
    "ou da campanha Outubro Rosa."
)
perfil = gold_nova_ou_vazia("perfil_etario_geral_anual")
if not perfil.empty and {
    "municipio", "ano", "grupo_etario_diretriz", "quantidade_exames"
}.issubset(perfil.columns):
    perfil = perfil[[
        "municipio", "ano", "grupo_etario_diretriz", "quantidade_exames"
    ]].copy()
else:
    # Fonte anual geral Q3 já publicada na Gold.
    perfil = filtered("etaria")
    if not perfil.empty and {
        "municipio", "ano", "grupo_etario_diretriz", "quantidade_exames"
    }.issubset(perfil.columns):
        perfil = perfil[[
            "municipio", "ano", "grupo_etario_diretriz", "quantidade_exames"
        ]].copy()
    else:
        perfil = pd.DataFrame()
if perfil.empty:
    st.info("Perfil etário geral indisponível no recorte.")
else:
    perfil["quantidade_exames"] = pd.to_numeric(
        perfil["quantidade_exames"], errors="coerce"
    )
    perfil["ano"] = pd.to_numeric(perfil["ano"], errors="coerce")
    perfil["Grupo"] = perfil["grupo_etario_diretriz"].map({
        "<25 anos (Sobrerrastreamento)": "<25 anos",
        "25 a 64 anos (População-Alvo)": "25–64 anos",
        "65 anos ou mais (Sub-rastreamento)": "≥65 anos",
    })
    perfil = perfil.dropna(
        subset=["municipio", "ano", "Grupo", "quantidade_exames"]
    )
    perfil["ano"] = perfil["ano"].astype(int)
    ordem_grupos = ["<25 anos", "25–64 anos", "≥65 anos"]
    cores_grupos = {
        "<25 anos": "#169B62", "25–64 anos": "#1757A6",
        "≥65 anos": "#E85D2A",
    }
    if perfil.empty:
        st.info("Não há grupos etários classificáveis na fonte Q3.")
    else:
        st.markdown("### Município × grupo etário")
        perfil_mun = (
            perfil.groupby(["municipio", "Grupo"], as_index=False)[
                "quantidade_exames"
            ].sum(min_count=1)
        )
        total_mun = perfil_mun.groupby("municipio")[
            "quantidade_exames"
        ].transform("sum")
        perfil_mun["Participação (%)"] = (
            perfil_mun["quantidade_exames"] /
            total_mun.where(total_mun > 0) * 100
        )
        fig_etario_mun = px.bar(
            perfil_mun, x="municipio", y="Participação (%)",
            color="Grupo", barmode="stack",
            color_discrete_map=cores_grupos,
            category_orders={"Grupo": ordem_grupos},
            custom_data=["quantidade_exames"],
            labels={"municipio": "Município"},
        )
        fig_etario_mun.update_traces(
            hovertemplate="%{x}<br>Exames: %{customdata[0]:,.0f}"
            "<br>Participação: %{y:.2f}%"
            "<extra>%{fullData.name}</extra>"
        )
        fig_etario_mun.update_xaxes(tickangle=-55, automargin=True)
        fig_etario_mun.update_yaxes(range=[0, 100], ticksuffix="%")
        fig_etario_mun.update_layout(margin=dict(l=70, r=125, t=40, b=170))
        download_plot(
            fig_etario_mun, "outubro_rosa_contexto_q3_municipio_grupo.png",
            altura=585, largura=1700,
        )

        st.markdown("### Evolução anual da participação de 25–64 anos")
        por_ano_etario = (
            perfil.groupby(["ano", "Grupo"], as_index=False)[
                "quantidade_exames"
            ].sum(min_count=1)
        )
        total_ano_etario = (
            por_ano_etario.groupby("ano")["quantidade_exames"].sum()
        )
        alvo_ano = por_ano_etario.loc[
            por_ano_etario["Grupo"] == "25–64 anos"
        ].copy()
        alvo_ano["Participação (%)"] = (
            alvo_ano["quantidade_exames"] /
            alvo_ano["ano"].map(total_ano_etario).where(
                alvo_ano["ano"].map(total_ano_etario) > 0
            ) * 100
        )
        alvo_ano["Ano"] = alvo_ano["ano"].astype(str)
        with st.expander("ℹ️ Como interpretar a evolução do percentual-alvo", expanded=False):
            st.markdown(
                "O percentual anual é a **razão entre a soma dos exames "
                "de 25–64 anos e a soma de todos os exames com idade "
                "classificável no mesmo ano**. Não é média dos percentuais "
                "dos municípios. Esta tendência corresponde à Q3 anual "
                "geral: **não permite concluir se a campanha Outubro Rosa "
                "ficou mais focada na população-alvo**."
            )
        fig_alvo = px.line(
            alvo_ano.sort_values("ano"), x="Ano",
            y="Participação (%)", markers=True,
            color_discrete_sequence=["#1757A6"],
            custom_data=["quantidade_exames"],
        )
        fig_alvo.update_traces(
            hovertemplate="Ano: %{x}<br>25–64 anos: %{customdata[0]:,.0f}"
            "<br>Participação: %{y:.2f}%<extra></extra>"
        )
        fig_alvo.update_yaxes(ticksuffix="%", tickformat=".2f")
        download_plot(
            fig_alvo, "outubro_rosa_contexto_q3_alvo_por_ano.png",
            altura=420, largura=1500,
        )
        alvo_tabela = alvo_ano[[
            "ano", "quantidade_exames", "Participação (%)"
        ]].rename(columns={
            "ano": "Ano",
            "quantidade_exames": "Exames de 25–64 anos",
        })
        with st.expander("Detalhamento anual do grupo 25–64 anos", expanded=False):
            display_table(
                alvo_tabela,
                integer_columns=["Ano", "Exames de 25–64 anos"]
            )

section("07", "Dados mensais detalhados")
st.markdown(
    "Tabela consolidada por **município × ano × mês**, "
    "com a quantidade registrada em cada competência."
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
st.download_button(
    "⬇️ Exportar dados mensais (CSV)",
    detalhes.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
    file_name="siscan_outubro_rosa_producao_mensal.csv",
    mime="text/csv", key="outubro_rosa_mensal_csv",
)
with st.expander("Ver tabela mensal detalhada", expanded=False):
    display_table(detalhes, integer_columns=["Ano", "Mês (número)", "Exames"])
st.caption(
    "Nota metodológica: os cruzamentos desta página são análises "
    "descritivas da produção registrada na base geral do SISCAN, "
    "sem atribuição de causalidade ao Outubro Rosa."
)
