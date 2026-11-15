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
.or-mini-note {font-size:.86rem; color:#526B81; margin:4px 0 16px}
.st-key-outubro_rosa_ordenacao [data-testid="stSelectbox"] {max-width:280px}

.or-section-title {
    margin:38px 0 13px;padding:8px 0 12px;
    border-bottom:1px solid #D8E5EF;
    font:750 clamp(20px,2vw,25px)/1.35 Manrope,Arial,sans-serif;
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
    .or-section-title {margin:27px 0 12px;font-size:20px}
}
</style>
""", unsafe_allow_html=True)


def section(index, title):
    st.markdown(
        '<h2 class="or-section-title"><span class="or-section-index">'
        + index + '</span>' + title + '</h2>',
        unsafe_allow_html=True,
    )



def download_plot(fig, nome, altura=450, largura=1400, margem_superior=45, margem_esquerda=75, margem_inferior=70, rotulos_exportacao=None, titulo_exportacao=None):
    """Gráfico interativo e cópia independente para exportação PNG."""
    fig.update_layout(
        template="plotly_white", height=altura,
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=NAVY, size=13),
        margin=dict(l=margem_esquerda, r=145, t=margem_superior, b=margem_inferior),
        legend_title_text="",
    )
    fig.update_yaxes(gridcolor="#E4EBF1", rangemode="tozero")
    imagem = copy.deepcopy(fig)
    # Os números de cada faixa aparecem apenas no PNG exportado.
    # Não modificamos o gráfico interativo nem reutilizamos o mesmo formato
    # para quantidades e percentuais.
    if rotulos_exportacao in {
        "percentual_vertical", "quantidade_vertical", "percentual_horizontal"
    }:
        # O grupo >=65 anos é a fatia SUPERIOR das colunas empilhadas:
        # nos meses com poucos exames, o rótulo interno fica cortado.
        # No PNG vertical, ele passa a ficar acima da barra, com cor
        # escura; os rótulos do grupo central continuam brancos.
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
        if rotulos_exportacao == "percentual_vertical":
            # Deixa espaço acima dos 100% para as etiquetas laranja,
            # mas não cria marcas percentuais acima de 100 no eixo.
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
        min_chart_width=0, export_fig=imagem,
    )


page_header(
    "Campanha · Outubro Rosa",
    "Outubro Rosa: produção e perfil etário dos exames",
    "Analisa a produção de exames citopatológicos nos municípios da "
    "10ª CRS, com destaque para a participação da população-alvo de "
    "25 a 64 anos e as diferenças entre períodos e municípios.",
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

section("01", "Produção mensal · setembro a dezembro")
st.markdown(
    "Compare os exames registrados em cada mês, por ano, considerando "
    "os municípios selecionados."
)
chart_help(
    "**Variação (%) = (Outubro − Setembro) ÷ Setembro × 100.** "
    "A variação reúne os totais dos meses disponíveis nos anos "
    "selecionados; ela não equivale à média das variações anuais. "
    "Se setembro for zero, o percentual não é calculável."
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
st.markdown(
    f'<p class="or-mini-note">Recorte aplicado: <strong>{periodo}</strong>'
    f' · {cidades} município(s) · produção registrada, não cobertura</p>',
    unsafe_allow_html=True,
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

st.markdown("### Comparação municipal · setembro × outubro")
st.markdown(
    "Veja quais municípios registraram aumento ou redução de exames em "
    "outubro, comparando apenas anos com setembro e outubro disponíveis."
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
            "**Variação (%) = (outubro − setembro) ÷ setembro × 100**. "
            "Primeiro são pareados setembro e outubro do mesmo ano; "
            "depois, são somados os exames dos anos selecionados. "
            "O resultado não é a média das variações anuais. "
            "Valores negativos indicam redução, sem atribuição "
            "de causalidade à campanha."
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

section("02", "Faixa etária · participação na população-alvo")
st.markdown(
    "Avalia a participação de exames realizados em mulheres de "
    "**25 a 64 anos** nos meses de setembro a dezembro dos anos "
    "selecionados. O cruzamento mensal é **regional (11 municípios)**."
)
chart_help(
    "**Exames e participação (25–64 anos):** consideram setembro a "
    "dezembro dos anos selecionados. A participação é a quantidade "
    "de exames desse grupo dividida pelo total com idade classificada.\n\n"
    "**Diferença outubro − setembro:** compara somente a participação "
    "do grupo de 25–64 anos nesses dois meses. "
    "Exemplo: de 80,00% para 80,50% = **+0,50 ponto percentual**; "
    "não significa 0,50% a mais de exames.\n\n"
    "**Por que pode diferir da seção 01?** Aqui são considerados "
    "apenas exames com idade classificada, de toda a 10ª CRS. "
    "A seção 01 utiliza os registros gerais e permite filtrar municípios."
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
            # O denominador usa apenas exames com idade classificável
            # na própria competência; não representa mulheres distintas.
            totais_comp_or = (
                mensal_etario_or.groupby(["ano", "mes_num"])[
                    "quantidade_exames"
                ].transform("sum")
            )
            mensal_etario_or["Participação (%)"] = (
                mensal_etario_or["quantidade_exames"]
                .div(totais_comp_or.where(totais_comp_or > 0))
                .mul(100)
            )
            total_class_or = mensal_etario_or["quantidade_exames"].sum()
            alvo_or = mensal_etario_or.loc[
                mensal_etario_or["Grupo"] == "25–64 anos", "quantidade_exames"
            ].sum()
            pct_alvo_or = (
                alvo_or / total_class_or * 100
                if total_class_or > 0 else float("nan")
            )
            sep_class_or = mensal_etario_or.loc[
                mensal_etario_or["mes_num"] == 9
            ]
            out_class_or = mensal_etario_or.loc[
                mensal_etario_or["mes_num"] == 10
            ]
            def _participacao_alvo_mes_or(tabela):
                total = tabela["quantidade_exames"].sum()
                alvo = tabela.loc[
                    tabela["Grupo"] == "25–64 anos", "quantidade_exames"
                ].sum()
                return (alvo / total * 100) if total > 0 else float("nan")

            p_sep_or = _participacao_alvo_mes_or(sep_class_or)
            p_out_or = _participacao_alvo_mes_or(out_class_or)
            delta_pp_or = p_out_or - p_sep_or
            st.caption(
                "**Meses considerados:** os dois primeiros indicadores "
                "incluem **setembro a dezembro** dos anos selecionados; "
                "o terceiro compara **outubro com setembro** desses anos. "
                "Os anos ativos já aparecem no filtro lateral."
            )
            kpi_alvo_a, kpi_alvo_b, kpi_alvo_c = st.columns(3)
            kpi_alvo_a.metric(
                "Exames de 25–64 anos (set.–dez.)", fmt_num(alvo_or)
            )
            kpi_alvo_b.metric(
                "Participação de 25–64 anos (set.–dez.)",
                f"{pct_alvo_or:.2f}%" if pd.notna(pct_alvo_or) else "N/D",
            )
            kpi_alvo_c.metric(
                "Diferença em pontos percentuais (out. − set.)",
                f"{delta_pp_or:+.2f}"
                if pd.notna(delta_pp_or) else "N/D",
                help="Pontos percentuais (p.p.) = participação percentual "
                     "de 25–64 anos em outubro menos a participação "
                     "em setembro, nos anos selecionados. Não é a "
                     "variação da quantidade de exames.",
            )
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
                str(a) for a in sorted(dados_grafico_etario_or["ano"].unique())
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
                    "Grupo": ordem_grupos_mensal_or,
                },
                color_discrete_map={
                    "<25 anos": "#169B62",
                    "25–64 anos": "#1757A6",
                    "≥65 anos": "#E85D2A",
                },
                custom_data=["quantidade_exames", "Participação (%)", "Ano"],
                labels={
                    "quantidade_exames": "Quantidade de exames",
                    "Participação (%)": "Participação dos exames (%)",
                },
            )
            # Cada ano deve aparecer ABAIXO dos quatro meses do seu painel.
            # Os títulos automáticos de facetagem são colocados em cima
            # pelo Plotly; reposicionamos no rodapé da respectiva linha.
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
            # Cada opção tem seu próprio eixo e limites. Isso evita
            # que a escala percentual de 0–100 seja mantida ao trocar
            # para a visualização de quantidades.
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
            # Um único título global para os eixos de todos os painéis.
            # Os meses e as escalas permanecem em cada ano, sem
            # repetir "Meses" ou a unidade em cada pequeno gráfico.
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
                margem_inferior=150,
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
    elif mensal_etario_or.empty:
        st.info("Não há registros acessíveis na Gold mensal por grupo etário.")
    else:
        st.warning(
            "A Gold mensal por grupo etário não possui todas as colunas "
            "necessárias para o gráfico."
        )

section("03", "Perfil etário municipal · consolidado 2020–2025")
st.markdown(
    "Mostra como os exames citopatológicos se distribuem entre os grupos "
    "etários em cada município, com destaque para a **população-alvo "
    "de 25 a 64 anos**. Os resultados reúnem os registros de "
    "**setembro a dezembro de 2020–2025**, sem distinção por ano ou mês."
)
with st.expander("ℹ️ Como interpretar o gráfico", expanded=False):
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
                            x=0, y=1.035, yanchor="bottom"),
                margin=dict(l=150, r=35, t=100, b=60),
                bargap=0.25,
            )
            download_plot(
                fig_etario_or,
                "outubro_rosa_perfil_etario_consolidado_municipio.png",
                altura=max(520, 43 * len(municipios_etarios_or) + 155),
                largura=1600,
                rotulos_exportacao="percentual_horizontal",
                titulo_exportacao=(
                    "Outubro Rosa — Perfil etário por município (%)"
                ),
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
                "Ver quantidades por município e grupo etário",
                expanded=False,
            ):
                display_table(tabela_etaria_or.reset_index())

section("04", "Dados para consulta e exportação")
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
st.download_button(
    "⬇️ Exportar dados mensais (CSV)",
    detalhes.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
    file_name="siscan_outubro_rosa_producao_mensal.csv",
    mime="text/csv", key="outubro_rosa_mensal_csv",
)
with st.expander("Ver tabela mensal detalhada", expanded=False):
    display_table(detalhes, integer_columns=["Ano", "Mês (número)", "Exames"])
st.caption(
    "Nota: a produção mensal geral é observada no SISCAN; as "
    "visualizações etárias utilizam bases específicas, conforme "
    "a granularidade disponível. Não se infere causalidade da campanha."
)
