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
/* Painel de interpretação: mesma leitura e hierarquia da página Faixa Etária. */
.st-key-outubro_variacao_explicacao [data-testid="stExpander"] summary {
    font-family:Manrope,Arial,sans-serif!important;
    font-size:0.92rem!important;
    font-weight:700!important;
    color:#1A3B5C!important;
}
.st-key-outubro_variacao_explicacao [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    font-family:Manrope,Arial,sans-serif!important;
    font-size:0.95rem!important;
    line-height:1.65!important;
    font-weight:500!important;
    color:#1A3B5C!important;
}
@media(max-width:768px) {
    .st-key-outubro_variacao_explicacao [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
        font-size:0.9rem!important;
        line-height:1.55!important;
    }
}
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



def download_plot(fig, nome, altura=450, largura=1400, margem_superior=45):
    """Gráfico interativo e cópia independente para exportação PNG."""
    fig.update_layout(
        template="plotly_white", height=altura,
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=NAVY, size=13),
        margin=dict(l=75, r=145, t=margem_superior, b=70),
        legend_title_text="",
    )
    fig.update_yaxes(gridcolor="#E4EBF1", rangemode="tozero")
    imagem = copy.deepcopy(fig)
    imagem.update_layout(
        width=largura,
        height=max(altura + 100, 650),
        title=dict(text=nome.replace("_", " ").replace(".png", "").title(),
                   x=0.5, font=dict(size=22, color=NAVY)),
        margin=dict(l=110, r=210, t=max(105, margem_superior + 35), b=100),
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
chart_help(
    "**Variação (%) = (Outubro − Setembro) ÷ Setembro × 100.** "
    "Ao selecionar vários anos, o indicador combina os registros de "
    "setembro e outubro dos anos selecionados. Se setembro for zero "
    "ou algum dos meses estiver ausente, o percentual não é calculável."
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

section("02", "Produção mensal por grupo etário — 10ª CRS")
st.markdown(
    "Quantidade de exames por **mês, ano e grupo etário** nos 11 municípios "
    "da região. O gráfico acompanha os anos selecionados."
)
chart_help(
    "**Cada barra** corresponde a um mês de um ano selecionado; os segmentos "
    "representam exames de menores de 25 anos, de 25 a 64 anos e de 65 anos "
    "ou mais. A altura total é a soma dos três grupos. "
    "A tabela Gold é **regional** (sem município) e exclui registros de "
    "idade ignorada; portanto, não permite recorte municipal."
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
    colunas_necessarias_or = {
        "ano", "mes_num", "grupo_etario", "quantidade_exames"
    }
    if not mensal_etario_or.empty and colunas_necessarias_or.issubset(
        mensal_etario_or.columns
    ):
        mensal_etario_or = mensal_etario_or.copy()
        mensal_etario_or["ano"] = pd.to_numeric(
            mensal_etario_or["ano"], errors="coerce"
        )
        mensal_etario_or["mes_num"] = pd.to_numeric(
            mensal_etario_or["mes_num"], errors="coerce"
        )
        mensal_etario_or["quantidade_exames"] = pd.to_numeric(
            mensal_etario_or["quantidade_exames"], errors="coerce"
        )
        grupo_label_or = {
            "<25 anos": "<25 anos",
            "25-64 anos": "25–64 anos",
            ">=65 anos": "≥65 anos",
        }
        mensal_etario_or["Grupo"] = (
            mensal_etario_or["grupo_etario"].astype(str).str.strip()
            .map(grupo_label_or)
        )
        mensal_etario_or = mensal_etario_or.loc[
            mensal_etario_or["ano"].isin(data_loader.selected_years())
            & mensal_etario_or["mes_num"].isin([9, 10, 11, 12])
            & mensal_etario_or["Grupo"].notna()
        ].dropna(subset=["ano", "mes_num", "quantidade_exames"])
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
            mensal_etario_or["Competência"] = (
                mensal_etario_or["mes_num"].astype(int).map({
                    9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
                })
                + "/" + mensal_etario_or["ano"].astype(int).astype(str)
            )
            ordem_competencias_or = [
                f"{mes}/{ano}"
                for ano in sorted(mensal_etario_or["ano"].unique())
                for mes in ["Set", "Out", "Nov", "Dez"]
                if f"{mes}/{ano}" in set(mensal_etario_or["Competência"])
            ]
            ordem_grupos_mensal_or = [
                "<25 anos", "25–64 anos", "≥65 anos"
            ]
            fig_mes_idade_or = px.bar(
                mensal_etario_or,
                x="Competência", y="quantidade_exames",
                color="Grupo", barmode="stack",
                category_orders={
                    "Competência": ordem_competencias_or,
                    "Grupo": ordem_grupos_mensal_or,
                },
                color_discrete_map={
                    "<25 anos": "#169B62",
                    "25–64 anos": "#1757A6",
                    "≥65 anos": "#E85D2A",
                },
                labels={
                    "Competência": "Mês / ano",
                    "quantidade_exames": "Exames registrados",
                },
            )
            fig_mes_idade_or.update_traces(
                hovertemplate="%{x}<br>Grupo: %{fullData.name}"
                "<br>Exames: %{y:,.0f}<extra></extra>"
            )
            fig_mes_idade_or.update_xaxes(
                type="category", categoryorder="array",
                categoryarray=ordem_competencias_or,
                tickangle=-45,
            )
            fig_mes_idade_or.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            )
            download_plot(
                fig_mes_idade_or,
                "outubro_rosa_producao_mensal_por_grupo_etario.png",
                altura=520, largura=max(1500, len(ordem_competencias_or) * 100),
            )
            tabela_mensal_or = (
                mensal_etario_or.pivot(
                    index="Competência", columns="Grupo",
                    values="quantidade_exames"
                )
                .reindex(
                    index=ordem_competencias_or,
                    columns=ordem_grupos_mensal_or,
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
            st.caption(
                "Fonte: gold.fato_outubro_rosa_mensal_grupo_etario. "
                "Valores regionais; diferenças pontuais frente à Gold "
                "geral podem decorrer de idade ignorada."
            )
    elif mensal_etario_or.empty:
        st.info("Não há registros acessíveis na Gold mensal por grupo etário.")
    else:
        st.warning(
            "A Gold mensal por grupo etário não possui todas as colunas "
            "necessárias para o gráfico."
        )

section("03", "Estimativa mensal por município (IPF)")
st.markdown(
    "Estimativa da **quantidade de exames por município e mês**, "
    "de setembro a dezembro dos anos selecionados. "
    "O cruzamento é reconstruído por IPF a partir de totais marginais do SISCAN."
)
with st.expander("ℹ️ Como interpretar a estimativa IPF", expanded=False):
    st.markdown(
        "**Cada ponto ou barra representa uma estimativa**, não a contagem "
        "mensal observada daquele município. O IPF distribui os totais "
        "mensais regionais entre os municípios segundo seus perfis etários "
        "consolidados. **Os filtros de anos e municípios são aplicados**, "
        "mas a distribuição pressupõe um padrão sazonal semelhante entre "
        "os municípios. O arredondamento pode gerar pequenas diferenças "
        "em relação aos totais mensais regionais."
    )
st.warning(
    "**Estimativa estatística (IPF) — não são exames municipais mensais "
    "observados no SISCAN.** Não utilize o gráfico para afirmar o número "
    "exato de exames realizado em cada município ou o efeito da campanha.",
    icon="⚠️",
)
try:
    ipf_or = data_loader.load_table(
        "outubro_ipf_municipio_mes", data_loader.selected_source()
    )
except (ValueError, data_loader.GoldConsultaIndisponivel):
    ipf_or = pd.DataFrame()
    st.info(
        "A tabela Gold de estimativas IPF ainda não está acessível neste "
        "ambiente. Confirme a conexão e o carregamento do novo commit."
    )

campos_ipf_or = {
    "municipio", "ano", "mes_num", "quantidade_exames_estimada",
    "fl_estimativa",
}
if not ipf_or.empty and not campos_ipf_or.issubset(ipf_or.columns):
    st.error(
        "A tabela IPF não possui as colunas esperadas: município, ano, "
        "mes_num, quantidade_exames_estimada e fl_estimativa."
    )
elif not ipf_or.empty:
    ipf_or = ipf_or.copy()
    municipios_ipf_or = st.session_state.get(
        "city_preference", list(data_loader.MUNICIPIOS.values())
    )
    ipf_or["ano"] = pd.to_numeric(ipf_or["ano"], errors="coerce")
    ipf_or["mes_num"] = pd.to_numeric(ipf_or["mes_num"], errors="coerce")
    ipf_or["quantidade_exames_estimada"] = pd.to_numeric(
        ipf_or["quantidade_exames_estimada"], errors="coerce"
    )
    # O contrato da Gold estabelece fl_estimativa=True em todas as linhas.
    flags_estimativa_or = (
        ipf_or["fl_estimativa"].astype(str).str.lower().isin(["true", "1"])
    )
    if not flags_estimativa_or.all():
        st.error(
            "A origem IPF apresenta registros sem identificação de "
            "estimativa. Revise a Gold antes de exibir o gráfico."
        )
    else:
        ipf_or = ipf_or.loc[
            ipf_or["municipio"].isin(municipios_ipf_or)
            & ipf_or["ano"].isin(data_loader.selected_years())
            & ipf_or["mes_num"].isin([9, 10, 11, 12])
        ].dropna(
            subset=["municipio", "ano", "mes_num",
                    "quantidade_exames_estimada"]
        ).copy()
        if ipf_or.empty:
            st.info(
                "Sem estimativas IPF para os anos e municípios selecionados."
            )
        elif ipf_or.duplicated(["municipio", "ano", "mes_num"]).any():
            st.error(
                "Foram encontradas competências municipais duplicadas na "
                "tabela IPF. Verifique a chave município × ano × mês."
            )
        else:
            ipf_or["Mês / ano"] = (
                ipf_or["mes_num"].astype(int).map({
                    9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
                }) + "/" + ipf_or["ano"].astype(int).astype(str)
            )
            ordem_comp_ipf = [
                f"{mes}/{ano}"
                for ano in sorted(ipf_or["ano"].unique())
                for mes in ["Set", "Out", "Nov", "Dez"]
                if f"{mes}/{ano}" in set(ipf_or["Mês / ano"])
            ]
            st.caption(
                f"Recorte IPF: {ipf_or['municipio'].nunique()} município(s) "
                f"e {len(ordem_comp_ipf)} competência(s) selecionada(s)."
            )
            tipo_ipf_or = st.radio(
                "Visualização",
                ["Comparar IPF × registrado", "Por município"],
                key="outubro_rosa_ipf_visualizacao",
                horizontal=True,
            )
            if tipo_ipf_or == "Por município":
                with st.container(key="outubro_ipf_sort_panel"):
                    ordenar_ipf = st.selectbox(
                        "Ordenar por", ["A–Z", "Maior para menor"],
                        key="outubro_rosa_ipf_ordenacao",
                        help="Maior para menor considera a soma estimada "
                             "nas competências selecionadas.",
                    )
                totais_mun_ipf = ipf_or.groupby(
                    "municipio"
                )["quantidade_exames_estimada"].sum()
                municipios_ord_ipf = sorted(
                    totais_mun_ipf.index.tolist(), key=str.casefold
                )
                if ordenar_ipf == "Maior para menor":
                    municipios_ord_ipf.sort(
                        key=lambda nome: (
                            -float(totais_mun_ipf.loc[nome]),
                            nome.casefold(),
                        )
                    )
                # Quatro séries mensais por município; eixo X compacto (anos),
                # evitando 24 rótulos de competência por painel.
                ipf_linhas = ipf_or.copy()
                ipf_linhas["Ano (rótulo)"] = (
                    ipf_linhas["ano"].astype(int).astype(str)
                )
                ipf_linhas["Mês"] = ipf_linhas["mes_num"].astype(int).map(MESES)
                anos_eixo_ipf = [
                    str(ano) for ano in sorted(ipf_linhas["ano"].unique())
                ]
                fig_ipf = px.line(
                    ipf_linhas.sort_values(["ano", "mes_num"]),
                    x="Ano (rótulo)", y="quantidade_exames_estimada",
                    color="Mês", facet_col="municipio", facet_col_wrap=2,
                    markers=True,
                    category_orders={
                        "municipio": municipios_ord_ipf,
                        "Ano (rótulo)": anos_eixo_ipf,
                        "Mês": ORDEM_MESES,
                    },
                    color_discrete_map=CORES_MESES,
                    custom_data=["Mês"],
                    labels={
                        "Ano (rótulo)": "Ano",
                        "quantidade_exames_estimada": "Exames estimados (IPF)",
                    },
                    facet_col_spacing=0.08,
                    facet_row_spacing=0.11,
                )
                fig_ipf.for_each_annotation(
                    lambda anotacao: anotacao.update(
                        text=anotacao.text.split("=", 1)[-1],
                        font=dict(size=14, color=NAVY),
                    )
                )
                fig_ipf.update_traces(
                    line=dict(width=2.5),
                    marker=dict(size=8),
                    connectgaps=False,
                    hovertemplate=(
                        "Ano: %{x}<br>Mês: %{customdata[0]}"
                        "<br>Estimativa IPF: %{y:,.0f} exames"
                        "<extra></extra>"
                    ),
                )
                fig_ipf.update_yaxes(
                    matches=None, rangemode="tozero",
                    tickformat=",d", title_text=None,
                    gridcolor="#E4EBF1",
                )
                fig_ipf.update_xaxes(
                    matches=None, showticklabels=True,
                    type="category", categoryorder="array",
                    categoryarray=anos_eixo_ipf,
                    tickangle=0, title_text=None,
                    gridcolor="#EEF2F7",
                )
                fig_ipf.update_layout(
                    legend=dict(
                        title_text="Mês",
                        orientation="h",
                        x=0, y=1.035, yanchor="bottom",
                    ),
                    margin=dict(l=80, r=35, t=125, b=75),
                )
                altura_ipf_or = max(
                    500, 360 * ((len(municipios_ord_ipf) + 1) // 2) + 130
                )
                largura_ipf_or = 1600
                st.caption(
                    "**Leitura:** cada linha corresponde a um mês "
                    "(setembro a dezembro) ao longo dos anos selecionados; "
                    "cada painel representa um município. "
                    "As escalas verticais são independentes."
                )
            else:
                # Comparar modelos é mais informativo do que repetir o gráfico
                # de produção observada usando uma fonte estimada.
                observado_ipf = (
                    dados.groupby(["ano", "mes"], as_index=False)["quantidade"]
                    .sum(min_count=1)
                    .rename(columns={
                        "mes": "mes_num",
                        "quantidade": "Exames observados",
                    })
                )
                estimado_ipf = (
                    ipf_or.groupby(["ano", "mes_num"], as_index=False)[
                        "quantidade_exames_estimada"
                    ].sum(min_count=1)
                    .rename(columns={
                        "quantidade_exames_estimada": "Exames estimados (IPF)"
                    })
                )
                comparacao_ipf = estimado_ipf.merge(
                    observado_ipf, on=["ano", "mes_num"], how="inner",
                    validate="one_to_one",
                ).sort_values(["ano", "mes_num"])
                if comparacao_ipf.empty:
                    st.info(
                        "Não há competências comuns para comparar estimativas "
                        "IPF com registros observados no recorte selecionado."
                    )
                    fig_ipf = None
                else:
                    comparacao_ipf["Diferença (IPF − observado)"] = (
                        comparacao_ipf["Exames estimados (IPF)"]
                        - comparacao_ipf["Exames observados"]
                    )
                    comparacao_ipf["Diferença (%)"] = (
                        comparacao_ipf["Diferença (IPF − observado)"]
                        .div(
                            comparacao_ipf["Exames observados"].where(
                                comparacao_ipf["Exames observados"] > 0
                            )
                        ) * 100
                    )
                    comparacao_ipf["Ano"] = (
                        comparacao_ipf["ano"].astype(int).astype(str)
                    )
                    comparacao_ipf["Mês"] = (
                        comparacao_ipf["mes_num"].astype(int).map(MESES)
                    )
                    anos_eixo_ipf = sorted(
                        comparacao_ipf["Ano"].unique().tolist()
                    )
                    total_obs_ipf = comparacao_ipf["Exames observados"].sum()
                    total_est_ipf = comparacao_ipf["Exames estimados (IPF)"].sum()
                    diferenca_total_ipf = total_est_ipf - total_obs_ipf
                    met1, met2, met3 = st.columns(3)
                    met1.metric(
                        "Registrados (SISCAN)", fmt_num(total_obs_ipf)
                    )
                    met2.metric(
                        "Estimados (IPF)", fmt_num(total_est_ipf)
                    )
                    met3.metric(
                        "Diferença acumulada (IPF − registrado)",
                        f"{diferenca_total_ipf:+,.0f}".replace(",", "."),
                    )
                    st.caption(
                        "Comparação restrita às competências existentes nas "
                        "duas fontes. A diferença acumulada pode ocultar "
                        "desvios positivos e negativos em meses distintos."
                    )
                    fig_ipf = px.bar(
                        comparacao_ipf,
                        x="Ano", y="Diferença (IPF − observado)",
                        color="Mês", barmode="group",
                        category_orders={
                            "Ano": anos_eixo_ipf,
                            "Mês": ORDEM_MESES,
                        },
                        color_discrete_map=CORES_MESES,
                        custom_data=[
                            "Exames observados", "Exames estimados (IPF)",
                            "Diferença (%)",
                        ],
                        labels={
                            "Diferença (IPF − observado)":
                                "Diferença de exames (IPF − registrado)",
                        },
                    )
                    fig_ipf.update_traces(
                        hovertemplate=(
                            "Ano: %{x}<br>Mês: %{fullData.name}"
                            "<br>Registrados: %{customdata[0]:,.0f}"
                            "<br>Estimados IPF: %{customdata[1]:,.0f}"
                            "<br>Diferença: %{y:+,.0f} exames"
                            "<br>Desvio: %{customdata[2]:+.2f}%"
                            "<extra></extra>"
                        ),
                    )
                    fig_ipf.update_xaxes(
                        categoryorder="array",
                        categoryarray=anos_eixo_ipf, title_text="Ano",
                    )
                    fig_ipf.update_yaxes(
                        tickformat=",d", zeroline=True,
                        zerolinecolor=NAVY, zerolinewidth=2,
                        title_text="Diferença de exames (IPF − registrado)",
                    )
                    fig_ipf.update_layout(
                        bargap=0.25, bargroupgap=0.06,
                        legend=dict(
                            title_text="Mês", orientation="h",
                            x=0, y=1.04, yanchor="bottom",
                        ),
                        margin=dict(l=80, r=40, t=105, b=75),
                    )
                    altura_ipf_or = 520
                    largura_ipf_or = 1500
                    st.caption(
                        "**Leitura:** barras acima de zero indicam "
                        "superestimação pelo IPF; abaixo de zero, "
                        "subestimação. Os dados registrados são a "
                        "referência para produção municipal observada."
                    )
                    tabela_comparacao_ipf = comparacao_ipf[[
                        "Ano", "Mês", "Exames observados",
                        "Exames estimados (IPF)",
                        "Diferença (IPF − observado)", "Diferença (%)",
                    ]]
                    with st.expander(
                        "Ver comparação entre estimativas e registros",
                        expanded=False,
                    ):
                        display_table(tabela_comparacao_ipf)
            if fig_ipf is not None:
                download_plot(
                    fig_ipf,
                    "outubro_rosa_comparacao_ipf_observado.png",
                    altura=altura_ipf_or, largura=largura_ipf_or,
                    margem_superior=125,
                )
            tabela_ipf_or = ipf_or[[
                "municipio", "ano", "mes_num",
                "quantidade_exames_estimada"
            ]].sort_values(["municipio", "ano", "mes_num"]).rename(
                columns={
                    "municipio": "Município",
                    "ano": "Ano",
                    "mes_num": "Mês",
                    "quantidade_exames_estimada": "Exames estimados (IPF)",
                }
            )
            with st.expander(
                "Ver tabela de estimativas por município e mês",
                expanded=False,
            ):
                display_table(
                    tabela_ipf_or,
                    integer_columns=["Ano", "Mês", "Exames estimados (IPF)"],
                )
            st.download_button(
                "⬇️ Exportar estimativas IPF (CSV)",
                tabela_ipf_or.to_csv(
                    index=False, sep=";", encoding="utf-8-sig",
                ).encode("utf-8-sig"),
                file_name="outubro_rosa_estimativas_ipf_municipio_mes.csv",
                mime="text/csv",
                key="outubro_rosa_ipf_export_csv",
            )
            st.caption(
                "Fonte: Gold fato_outubro_rosa_estimativa_ipf_municipio_mes. "
                "IPF com margens por município × idade e competência × idade. "
                "Valores modelados; não equivalem à produção mensal observada."
            )

section("04", "Comparação anual: setembro × outubro")
st.markdown(
    "Evolução da **variação percentual de setembro para outubro** em cada ano, "
    "sem misturar os totais de anos distintos."
)
chart_help(
    "Cada barra representa a diferença percentual entre outubro "
    "e setembro **do mesmo ano**. Verde: aumento ou estabilidade; "
    "vermelho: redução. Anos com meses ausentes ou setembro igual "
    "a zero não recebem percentual."
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
    download_plot(fig_ano, "outubro_rosa_variacao_anual_setembro_outubro.png", altura=420)

section("05", "Variação acumulada de setembro para outubro por município (%)")
st.markdown(
    "Variação percentual entre os totais acumulados de setembro e outubro "
    "nos anos selecionados, por município."
)

# Primeiro formar os pares setembro–outubro de CADA município e ano.
# Somar os meses antes de parear incluiria anos presentes em apenas um
# dos meses e distorceria a comparação acumulada.
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
pares_municipais["Variação (%)"] = [
    variacao_percentual(row["Outubro"], row["Setembro"])
    for _, row in pares_municipais.iterrows()
]
# Mesmo padrão da página Faixa Etária: descrição curta acima e
# explicação metodológica única no painel recolhível.
with st.container(key="outubro_variacao_explicacao"):
    with st.expander("ℹ️ Como interpretar o gráfico", expanded=False):
        st.markdown(
            "**Cada barra** mostra a variação percentual dos exames de "
            "outubro em relação a setembro para um município. "
            "**Cálculo:** (total de outubro − total de setembro) ÷ "
            "total de setembro × 100. Primeiro somamos os exames "
            "dos anos selecionados; **não calculamos a média anual**. "
            "Apenas anos com registros nos dois meses entram nas somas. "
            "**Exemplo:** setembro = 1.000 e outubro = 1.300 exames "
            "resultam em **+30.00% (300 exames a mais)**. "
            "Valores negativos indicam redução. "
            "O gráfico descreve a produção registrada e "
            "**não comprova efeito da campanha Outubro Rosa**."
        )

with st.container(key="outubro_variacao_sort_panel"):
    ordenacao = st.selectbox(
        "Ordenar por", ["A–Z", "Maior para menor"],
        index=0, key="outubro_rosa_ordenacao",
        help="Maior para menor considera a variação percentual acumulada "
             "de outubro em relação a setembro.",
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
        "<br>Variação acumulada: %{customdata[3]}"
        "<br>Anos com ambos os meses: %{customdata[4]}"
        "<extra></extra>"
    )
    fig_mun.update_layout(showlegend=False)
    download_plot(
        fig_mun, "outubro_rosa_variacao_acumulada_pares_completos.png",
        altura=max(500, 43 * len(municipios_validos) + 130),
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

section("06", "Matriz de produção: município × mês")
st.markdown(
    "Visualize a quantidade de exames em cada município nos meses de "
    "setembro a dezembro, somando apenas os anos selecionados."
)
chart_help(
    "Cada célula é a soma dos exames de um município em um mês "
    "considerando os anos selecionados. Células sem dados permanecem "
    "em branco — não são interpretadas como zero."
)
matriz = (
    dados.groupby(["municipio", "mes"])["quantidade"].sum(min_count=1)
    .unstack("mes")
    .reindex(columns=list(MESES))
    .rename(columns=MESES)
)
matriz.index.name = "Município"
with st.container(key="outubro_matriz_sort_panel"):
    ordem_matriz = st.selectbox(
        "Ordenar por", ["A–Z", "Maior para menor"],
        index=0, key="outubro_rosa_ordenacao_matriz",
        help="Maior para menor usa a soma de exames de setembro a dezembro no recorte.",
    )
if ordem_matriz == "Maior para menor":
    # min_count=1 preserva ausência de dados, sem converter em zero.
    totais_matriz = matriz.sum(axis=1, min_count=1)
    ordem_matriz_nomes = sorted(
        matriz.index,
        key=lambda nome: (
            -float(totais_matriz.loc[nome])
            if pd.notna(totais_matriz.loc[nome]) else float("inf"),
            nome.casefold(),
        ),
    )
    matriz = matriz.reindex(ordem_matriz_nomes)
else:
    matriz = matriz.sort_index(key=lambda nomes: nomes.str.casefold())
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
    download_plot(
        fig_heatmap, "outubro_rosa_matriz_municipio_mes.png",
        altura=max(490, 37 * len(matriz) + 120), largura=1550,
    )

section("07", "Perfil etário dos exames: município × grupo etário")
st.markdown(
    "Distribuição percentual dos exames registrados entre **setembro e dezembro "
    "de 2020–2025**, por município e grupo etário. "
    "A fonte é consolidada para todo o período, sem detalhamento anual."
)
with st.expander("ℹ️ Como interpretar o gráfico", expanded=False):
    st.markdown(
        "O gráfico mostra a **distribuição percentual dos exames por faixa "
        "etária em cada município**, considerando setembro a dezembro de "
        "2020–2025.\n\n"
        "Cada barra representa 100% dos exames com idade identificada, "
        "distribuídos em três grupos: **<25, 25–64 e ≥65 anos**.\n\n"
        "Os percentuais permitem comparar o perfil etário entre municípios. "
        "**Os dados estão consolidados para todo o período**, sem separação "
        "por ano ou mês."
    )

anos_totais_q02 = set(range(2020, 2026))
anos_ativos_q02 = set(data_loader.selected_years())
if anos_ativos_q02 != anos_totais_q02:
    st.info(
        "Este cruzamento está disponível somente para o período completo "
        "**2020–2025**. A tabela Gold consolidada não possui coluna de ano; "
        "para visualizar o gráfico, selecione todos os anos no filtro lateral. "
        "O filtro de municípios continua sendo respeitado."
    )
else:
    try:
        # Usa o mesmo filtro municipal aplicado às demais páginas.
        # A tabela consolidada não possui ano, então a restrição de anos
        # completos permanece acima, sem modificar os percentuais.
        perfil_or = filtered("outubro_grupo_etario")
    except ValueError as exc:
        # Deploy do Streamlit pode servir temporariamente uma versão antiga
        # do carregador, sem o alias novo em TABLES.
        if "Tabela não permitida" not in str(exc):
            raise
        st.warning(
            "A versão do carregador de dados ainda não reconhece a tabela "
            "do novo cruzamento etário. Atualize ou reinicie o aplicativo "
            "no Streamlit Cloud para carregar o código mais recente."
        )
        perfil_or = pd.DataFrame()
    except data_loader.GoldConsultaIndisponivel as exc:
        st.warning(
            "Não foi possível consultar a tabela Gold "
            "`fato_outubro_rosa_grupo_etario`. "
            "Verifique a conexão, as permissões e a disponibilidade "
            "da tabela no Databricks."
        )
        perfil_or = pd.DataFrame()

    colunas_or = {"municipio", "grupo_etario", "quantidade_exames"}
    if perfil_or.empty:
        st.info(
            "O gráfico ficará disponível quando a fonte Gold do "
            "perfil etário consolidado estiver acessível."
        )
    elif not colunas_or.issubset(perfil_or.columns):
        st.warning(
            "A tabela Gold do perfil etário não possui todas as colunas "
            "esperadas: município, grupo_etario e quantidade_exames."
        )
    else:
        # filtered() já aplica city_preference (filtros confirmados).
        # A Gold consolidada utiliza chaves de grupo próprias, sem mês/ano.
        nome_grupo_or = {
            "<25 anos": "<25 anos",
            "25-64 anos": "25–64 anos",
            ">=65 anos": "≥65 anos",
        }
        perfil_or["Grupo"] = (
            perfil_or["grupo_etario"].astype(str).str.strip()
            .map(nome_grupo_or)
        )
        perfil_or["quantidade_exames"] = pd.to_numeric(
            perfil_or["quantidade_exames"], errors="coerce"
        )
        perfil_or = perfil_or.dropna(
            subset=["municipio", "Grupo", "quantidade_exames"]
        )
        if perfil_or.empty:
            st.info("Não há dados etários válidos para os municípios selecionados.")
        elif perfil_or.duplicated(["municipio", "Grupo"]).any():
            st.error(
                "A Gold possui grupos etários duplicados por município. "
                "Verifique a integridade de "
                "`fato_outubro_rosa_grupo_etario`."
            )
        else:
            st.caption(
                f"Municípios no gráfico: {perfil_or['municipio'].nunique()} "
                "selecionado(s). Para alterar, marque os municípios na "
                "barra lateral e clique em **Aplicar filtros**."
            )
            total_por_municipio_or = perfil_or.groupby("municipio")[
                "quantidade_exames"
            ].transform("sum")
            perfil_or["Participação (%)"] = (
                perfil_or["quantidade_exames"]
                .div(total_por_municipio_or.where(total_por_municipio_or > 0))
                .mul(100)
            )
            perfil_or = perfil_or.dropna(subset=["Participação (%)"])
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
            ordem_grupos_or = ["<25 anos", "25–64 anos", "≥65 anos"]
            fig_etario_or = px.bar(
                perfil_or, y="municipio", x="Participação (%)",
                color="Grupo", orientation="h", barmode="stack",
                color_discrete_map={
                    "<25 anos": "#169B62",
                    "25–64 anos": "#1757A6",
                    "≥65 anos": "#E85D2A",
                },
                category_orders={
                    "municipio": municipios_etarios_or,
                    "Grupo": ordem_grupos_or,
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
                            x=0, y=1.02, yanchor="bottom"),
                margin=dict(l=140, r=35, t=90, b=65),
            )
            download_plot(
                fig_etario_or,
                "outubro_rosa_perfil_etario_consolidado_municipio.png",
                altura=max(520, 43 * len(municipios_etarios_or) + 155),
                largura=1600,
            )
            tabela_etaria_or = (
                perfil_or.pivot(
                    index="municipio", columns="Grupo",
                    values="quantidade_exames"
                ).reindex(
                    index=municipios_etarios_or,
                    columns=ordem_grupos_or,
                )
            )
            tabela_etaria_or.index.name = "Município"
            with st.expander(
                "Ver tabela de exames por município e grupo etário",
                expanded=False,
            ):
                display_table(tabela_etaria_or.reset_index())
            st.caption(
                "Fonte: Gold Q02 consolidada, setembro–dezembro de "
                "2020–2025. O total exclui 1 exame de idade ignorada "
                "registrado em Quaraí."
            )

section("08", "Dados mensais detalhados")
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
