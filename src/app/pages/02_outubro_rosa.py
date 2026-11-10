"""Comparação descritiva Setembro–Outubro, sem inferência causal."""
import copy
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css, page_header, style_chart, display_table, fmt_num, fmt_pct, ORANGE, OCEAN, SKY, NAVY
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, require, sidebar_filters, years_label, MUNICIPIOS

st.set_page_config(page_title="Outubro Rosa | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
page_header(
    "Campanha · Outubro Rosa",
    "Outubro em destaque: o que muda nos registros?",
    "Compara os registros de setembro e outubro, acompanha a produção nos "
    "meses seguintes e apresenta o perfil sazonal dos exames nos municípios "
    "selecionados, sem atribuir causalidade à campanha.",
)
st.markdown(
    '<div style="margin:14px 0 19px;padding:11px 15px;'
    'background:#EEF5FA;border-left:4px solid #006C9A;'
    'border-radius:8px;color:#1A3B5C;line-height:1.5;">'
    '<strong>Fonte dos dados:</strong> SISCAN/DATASUS · '
    'tabelas Gold <code>fato_analise_outubro_rosa</code> e '
    '<code>fato_exames_temporais_territoriais</code>. '
    'A comparação é descritiva e não comprova efeito causal da campanha.'
    '</div>',
    unsafe_allow_html=True,
)
df = filtered("outubro")
if require(df, ["ano", "mes", "municipio", "exames_mes", "exames_referencia_setembro"]):
    selected_cities = st.session_state.get("city_preference", [])
    period = years_label()

    octdf = df.loc[df["mes"] == 10].copy()
    if octdf.empty:
        st.info("Não há registros de outubro para os filtros selecionados.")
        st.stop()

    sept = octdf["exames_referencia_setembro"].sum(min_count=1)
    octval = octdf["exames_mes"].sum(min_count=1)
    diff = octval - sept
    variation = ((octval - sept) / sept * 100) if pd.notna(sept) and sept > 0 else float("nan")
    formatted_variation = (
        ("+" if variation > 0 else "") + fmt_pct(variation)
        if pd.notna(variation) else "N/D"
    )
    col_sept, col_oct, col_var = st.columns(3)
    col_sept.metric("Exames em setembro", fmt_num(sept) if pd.notna(sept) else "N/D")
    col_oct.metric("Exames em outubro", fmt_num(octval) if pd.notna(octval) else "N/D")
    col_var.metric("Variação em relação a setembro", formatted_variation,
                   help="(Exames de outubro − exames de setembro) / exames de setembro × 100")

    if pd.notna(diff) and pd.notna(variation):
        direction = "a mais" if diff > 0 else ("a menos" if diff < 0 else "de diferença")
        st.info(
            f"Em outubro de {period}, foram registrados **{fmt_num(octval)} exames**, "
            f"**{fmt_num(abs(diff))} {direction}** que em setembro "
            f"(**{formatted_variation}**)."
        )

    st.subheader("Produção de exames de setembro a dezembro")
    st.markdown(
        "Mostra **quantos exames foram registrados em cada competência mensal**, "
        "de setembro a dezembro, para comparar os volumes entre os meses "
        "e observar sua evolução nos anos selecionados."
    )
    with st.expander("ℹ️ Como interpretar este gráfico", expanded=False):
        st.markdown(
            "**Como ler:** cada grupo de barras corresponde a um ano. "
            "As cores representam os meses: **setembro (azul-claro), "
            "outubro (laranja), novembro (verde) e dezembro (azul-escuro)**. "
            "Quanto mais alta a barra, maior a quantidade de exames registrada "
            "naquele mês. Compare as quatro barras do mesmo ano para identificar "
            "aumentos ou reduções.\n\n"
            "**O que significa o mês:** no SISCAN, a competência do exame "
            "é determinada pela **data do resultado laboratorial**, que pode "
            "ser posterior à coleta. Portanto, exames contabilizados em "
            "novembro ou dezembro **podem ter sido coletados em outubro ou "
            "em outros meses**.\n\n"
            "**Limitação:** o gráfico mostra registros de exames, não quantas "
            "mulheres realizaram a coleta em cada mês. Por isso, um aumento "
            "após outubro não comprova, isoladamente, efeito da campanha "
            "Outubro Rosa."
        )
    plot = df.groupby(["ano", "mes"], as_index=False)["exames_mes"].sum(min_count=1)
    ref = octdf.groupby("ano", as_index=False)["exames_referencia_setembro"].sum(min_count=1)
    ref["mes"] = 9
    ref = ref.rename(columns={"exames_referencia_setembro": "exames_mes"})
    plot = pd.concat([plot, ref], ignore_index=True)
    month_names = {9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
    plot = plot.loc[plot["mes"].isin(month_names)].copy()
    plot["periodo"] = plot["mes"].map(month_names)
    fig = px.bar(
        plot, x="ano", y="exames_mes", color="periodo", barmode="group",
        color_discrete_map={"Setembro":SKY,"Outubro":ORANGE,"Novembro":"#218B65","Dezembro":NAVY},
        category_orders={"periodo":list(month_names.values())},
        labels={"ano":"Ano","exames_mes":"Exames","periodo":"Mês"},
        title=f"Exames de setembro a dezembro · {period}"
    )
    fig.update_xaxes(type="category")
    fig.update_traces(hovertemplate="Ano: %{x}<br>Exames: %{y:,.0f}<extra>%{fullData.name}</extra>")
    st.caption("Clique com o botão direito no gráfico para baixar em PNG.")
    fig = style_chart(fig)
    # A versão exportada mostra valores absolutos; no site, preservamos
    # o gráfico original e seus tooltips sem rótulos sobrepostos.
    export_fig = copy.deepcopy(fig)
    export_fig.update_traces(
        texttemplate="%{y:,.0f}", textposition="outside",
        textfont=dict(size=13, color="#1A3B5C"),
        cliponaxis=False,
    )
    export_fig.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(color="#1A3B5C", size=13),
        title=dict(font=dict(size=22, color="#1A3B5C")),
        uniformtext=dict(minsize=10, mode="show"),
        margin=dict(l=100, r=185, t=100, b=90),
    )
    export_fig.update_yaxes(rangemode="tozero")
    chart_with_right_click_download(
        fig, filename="outubro_rosa_setembro_dezembro.png",
        height=fig.layout.height, export_fig=export_fig,
    )

    city = octdf.groupby("municipio", as_index=False)[
        ["exames_mes", "exames_referencia_setembro"]
    ].sum(min_count=1)
    city["diferenca_exames"] = city["exames_mes"] - city["exames_referencia_setembro"]
    city["variacao_pct"] = (
        city["diferenca_exames"] /
        city["exames_referencia_setembro"].where(city["exames_referencia_setembro"] > 0)
        * 100
    )
    st.subheader("Variação de outubro em relação a setembro por município")
    st.markdown(
        "Mostra a **variação percentual dos exames de outubro em relação a setembro** "
        "para cada município, distinguindo aumentos e reduções."
    )
    with st.expander("ℹ️ Como interpretar a variação municipal", expanded=False):
        st.markdown(
            "**Variação (%) = (exames de outubro − exames de setembro) "
            "÷ exames de setembro × 100.** Para cada município, a base é setembro "
            "do mesmo ano, ou a soma dos setembros dos anos selecionados quando "
            "o recorte contém mais de um ano. **Barras verdes à direita de 0%** "
            "representam aumento e **vermelhas à esquerda**, redução. "
            "O ponto 0% significa ausência de mudança. "
            "Passe o mouse para conferir as quantidades e a diferença absoluta. "
            "Percentuais elevados podem decorrer de bases pequenas; "
            "o gráfico não mede a efetividade causal da campanha."
        )
    plot_city = city.dropna(subset=["variacao_pct"]).sort_values("variacao_pct")
    if not plot_city.empty:
        plot_city = plot_city.copy()
        plot_city["direcao"] = plot_city["variacao_pct"].map(
            lambda value: "Redução" if value < 0 else "Aumento ou estabilidade"
        )
        # Texto já formatado evita variações de precisão entre versões do Plotly.
        # Quantidades permanecem inteiras, percentuais exibem exatamente 2 casas.
        plot_city["variacao_formatada"] = plot_city["variacao_pct"].map(
            lambda value: f"{value:+.2f}%" if pd.notna(value) else "N/D"
        )
        fig = px.bar(
            plot_city, y="municipio", x="variacao_pct", orientation="h",
            color="direcao",
            color_discrete_map={"Redução":"#A83A20", "Aumento ou estabilidade":"#218B65"},
            custom_data=["exames_referencia_setembro", "exames_mes", "diferenca_exames", "variacao_formatada"],
            labels={"municipio":"Município","variacao_pct":"Variação (%)"},
            title=f"Variação outubro × setembro por município · {period}"
        )
        fig.update_traces(
            hovertemplate=(
                "%{y}<br>Variação: %{customdata[3]}"
                "<br>Setembro: %{customdata[0]:,.0f} exames"
                "<br>Outubro: %{customdata[1]:,.0f} exames"
                "<br>Diferença: %{customdata[2]:+.0f} exames<extra></extra>"
            )
        )
        # O zero separa visualmente queda (esquerda, vermelho) e aumento
        # (direita, verde); a referência permanece visível na exportação PNG.
        fig.update_xaxes(
            tickformat=".2f", ticksuffix="%",
            zeroline=True, zerolinecolor="#1A3B5C", zerolinewidth=2,
        )
        fig.add_vline(x=0, line_width=2, line_color="#1A3B5C")
        fig.update_layout(showlegend=False, margin=dict(t=90))
        # Exportação: rótulos numéricos no PNG (o tooltip não existe em imagem).
        # Mantém o gráfico interativo sem rótulos para não poluir a tela.
        export_fig = copy.deepcopy(fig)
        # Strings prontas evitam exibir toda a precisão decimal no PNG.
        # As reduções são rotuladas dentro da barra para não cobrir a cidade.
        for trace in export_fig.data:
            # Recupera os valores do DataFrame, não de trace.x: no Plotly 6
            # o eixo numérico pode ser serializado como estrutura binária.
            values = plot_city.loc[
                plot_city["direcao"] == trace.name, "variacao_pct"
            ]
            trace.text = [
                f"{value:.2f}%" if pd.notna(value) else "—"
                for value in values
            ]
            is_reduction = trace.name == "Redução"
            trace.update(
                texttemplate="%{text}",
                textposition="inside" if is_reduction else "outside",
                textfont=dict(size=14, color="#FFFFFF" if is_reduction else NAVY),
                insidetextanchor="middle",
                cliponaxis=False,
            )
        export_fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=240, r=150, t=90, b=75),
        )
        chart_with_right_click_download(
            style_chart(fig),
            filename="outubro_rosa_variacao_municipal.png",
            height=430,
            export_fig=export_fig,
        )
    st.caption(
        "Verde: aumento · Vermelho: redução · Linha vertical: 0% (sem variação)."
    )

    # Índice sazonal (base = média das competências disponíveis).
    # A fonte permanece a fato_exames_temporais_territoriais da Gold.
    # Não preencher competências ausentes com zero.
    temporal = filtered("temporal")
    if {"ano", "mes", "quantidade"}.issubset(temporal.columns) and not temporal.empty:
        st.subheader("Índice Sazonal Regional por Mês")
        st.markdown(
            "Compara a **produção média de cada mês** à média mensal dos "
            "municípios selecionados. A linha de referência **100** representa "
            "a média do recorte."
        )
        with st.expander("ℹ️ Como interpretar o índice sazonal regional", expanded=False):
            st.markdown(
                "**Índice sazonal = média de exames do mês ÷ média mensal geral "
                "do recorte × 100.** Um índice de **120** indica volume médio "
                "**20% acima** da média; **80** indica **20% abaixo**. "
                "A linha tracejada marca a referência 100. "
                "As cores indicam **janelas temporais fixas** descritas na análise "
                "histórica do notebook Gold: maio–setembro (janela fraca), "
                "janeiro–abril e outubro (neutros) e novembro–dezembro (pico). "
                "Essas categorias identificam grupos de meses da análise histórica; "
                "**não são limites numéricos aplicados ao índice atual**. "
                "Os intervalos da legenda mostram os menores e maiores índices "
                "observados em cada grupo no recorte filtrado. "
                "Meses sem registros não entram como zero. "
                "O índice resume padrões de registros, sem demonstrar suas causas."
            )
        mensal = (
            temporal.dropna(subset=["ano", "mes", "quantidade"])
            .groupby(["ano", "mes"], as_index=False)["quantidade"]
            .sum(min_count=1)
        )
        mensal = mensal.loc[mensal["mes"].between(1, 12)]
        media_base = mensal["quantidade"].mean()
        if pd.notna(media_base) and media_base > 0:
            indice = (
                mensal.groupby("mes", as_index=False)["quantidade"]
                .mean()
                .rename(columns={"quantidade": "media_mes"})
            )
            indice["indice_sazonal"] = indice["media_mes"].div(media_base).mul(100)
            # Classificação temporal fixa documentada nas células 7.4 e 7.5
            # do notebook 03_gold_analytics_siscan. As cores representam
            # janelas de meses, NÃO intervalos numéricos do índice.
            indice["mes"] = indice["mes"].astype(int)
            indice["janela_sazonal"] = indice["mes"].map(
                lambda mes: (
                    "Janela fraca (mai–set)" if 5 <= mes <= 9
                    else "Pico sazonal (nov–dez)" if mes in (11, 12)
                    else "Neutro (demais meses)"
                )
            )
            janelas = [
                "Janela fraca (mai–set)",
                "Neutro (demais meses)",
                "Pico sazonal (nov–dez)",
            ]
            cores_janelas = {
                "Janela fraca (mai–set)": OCEAN,
                "Neutro (demais meses)": ORANGE,
                "Pico sazonal (nov–dez)": NAVY,
            }
            # Intervalos observados (mínimo e máximo) em cada janela.
            # Não são limites de classificação; os meses permanecem fixos
            # conforme as células 7.4 e 7.5 do notebook.
            intervalos = (
                indice.groupby("janela_sazonal")["indice_sazonal"]
                .agg(["min", "max"])
            )
            rotulos = {
                janela: (
                    f"{janela} · {intervalos.loc[janela, 'min']:.2f}"
                    f"–{intervalos.loc[janela, 'max']:.2f}"
                )
                for janela in janelas if janela in intervalos.index
            }
            indice["janela_rotulo"] = indice["janela_sazonal"].map(rotulos)
            rotulos_ordem = [rotulos[janela] for janela in janelas if janela in rotulos]
            cores_rotulos = {
                rotulos[janela]: cores_janelas[janela] for janela in rotulos
            }
            selected = st.session_state.get("city_preference", list(MUNICIPIOS.values()))
            base_label = (
                "Média 10ª CRS = 100"
                if set(selected) == set(MUNICIPIOS.values())
                else "Média dos municípios selecionados = 100"
            )
            st.caption(
                f"Base: {base_label}. Meses sem registros não são contados como zero. "
                "As cores representam janelas históricas fixas, não faixas "
                "de valores do índice."
            )
            fig_sazonal = px.bar(
                indice, x="mes", y="indice_sazonal", color="janela_rotulo",
                category_orders={
                    "mes": list(range(1, 13)),
                    "janela_rotulo": rotulos_ordem,
                },
                color_discrete_map=cores_rotulos,
                labels={
                    "mes": "Mês",
                    "indice_sazonal": "Índice sazonal regional",
                    "janela_rotulo": "Janela sazonal · intervalo observado",
                },
                custom_data=["media_mes"],
            )
            fig_sazonal.update_traces(
                hovertemplate=(
                    "Mês: %{x}<br>Índice sazonal: %{y:.2f}"
                    "<br>Média de exames: %{customdata[0]:,.1f}<extra></extra>"
                )
            )
            fig_sazonal.update_xaxes(
                type="category",
                categoryorder="array",
                categoryarray=list(range(1, 13)),
                title_text="Mês",
                tickfont=dict(size=12, color=NAVY),
                showgrid=False,
            )
            fig_sazonal.update_yaxes(
                rangemode="tozero", tickformat=".0f",
                title_text="Índice sazonal regional",
                gridcolor="#E4EBF1",
                tickfont=dict(size=12, color=NAVY),
            )
            fig_sazonal.update_layout(
                showlegend=True,
                legend=dict(
                    title_text="Janela sazonal · intervalo observado",
                    orientation="v",
                    x=1.02, xanchor="left", y=1, yanchor="top",
                    font=dict(size=12, color=NAVY),
                    bgcolor="rgba(255,255,255,0)",
                    itemsizing="constant",
                ),
                bargap=0.12,
                margin=dict(l=70, r=195, t=30, b=60),
                font=dict(color=NAVY),
            )
            # Linha base sem anotação sobreposta às barras.
            fig_sazonal.add_hline(
                y=100, line_dash="dash", line_color=NAVY,
                line_width=1.5,
            )
            export_sazonal = copy.deepcopy(fig_sazonal)
            export_sazonal.update_traces(
                texttemplate="%{y:.2f}", textposition="outside",
                textfont=dict(size=14, color=NAVY),
                cliponaxis=False,
            )
            export_sazonal.update_layout(
                title=dict(
                    text=f"Índice Sazonal Regional por Mês · {period}",
                    x=0.5, xanchor="center",
                    font=dict(family="Arial", size=22, color=NAVY),
                ),
                paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                margin=dict(l=95, r=255, t=110, b=80),
                legend=dict(
                    title_text="Janela sazonal · intervalo observado",
                    orientation="v",
                    x=1.02, xanchor="left", y=1, yanchor="top",
                    font=dict(size=16, color=NAVY),
                    bgcolor="rgba(255,255,255,0)",
                    itemsizing="constant",
                ),
            )
            chart_with_right_click_download(
                style_chart(fig_sazonal),
                filename="outubro_rosa_indice_sazonal_regional.png",
                height=430,
                export_fig=export_sazonal,
            )
        else:
            st.info("Não há dados suficientes para exibir o índice sazonal neste recorte.")
    else:
        st.info("O índice sazonal não está disponível para os filtros selecionados.")

    # Tabela sazonal por município: usa SOMENTE o volume mensal da Gold.
    # Média-base própria = média das competências disponíveis do município.
    # Não transformar meses sem registro em zero (ex.: agosto/2022).
    if (
        not temporal.empty
        and {"municipio", "ano", "mes", "quantidade"}.issubset(temporal.columns)
    ):
        st.markdown("#### Índice Sazonal por Município e Mês")
        st.markdown(
            "Mostra em quais meses cada município registra **mais ou menos exames "
            "em relação à sua própria média**, permitindo comparar padrões sazonais "
            "sem confundir diferenças de porte populacional."
        )
        with st.expander("ℹ️ Como interpretar o índice sazonal municipal", expanded=False):
            st.markdown(
                "Cada **linha** corresponde a um município e cada **coluna** "
                "a um mês. **Base 100** é a média das competências disponíveis "
                "do próprio município nos anos selecionados. "
                "**Índice municipal = média de exames no mês ÷ média mensal "
                "do município × 100.** Valores acima de 100 indicam volume "
                "superior à sua média; abaixo de 100, inferior. "
                "Como as bases são municipais, **100 não representa a mesma "
                "quantidade absoluta de exames em cidades diferentes**. "
                "Competências ausentes não são consideradas zero; agosto/2022, "
                "por exemplo, não deve ser tratado como ausência de produção."
            )
        sazonal_muni = (
            temporal.dropna(subset=["municipio", "ano", "mes", "quantidade"])
            .loc[lambda d: d["mes"].between(1, 12)]
            .groupby(["municipio", "ano", "mes"], as_index=False)["quantidade"]
            .sum(min_count=1)
        )
        if not sazonal_muni.empty:
            # Cada competência (ano/mês) é uma observação da média-base,
            # independentemente de quantos anos foram selecionados.
            bases_municipais = sazonal_muni.groupby("municipio")["quantidade"].mean()
            media_meses = sazonal_muni.groupby(["municipio", "mes"])["quantidade"].mean()
            indice_municipal = (
                media_meses.div(
                    bases_municipais.reindex(media_meses.index.get_level_values("municipio")).to_numpy()
                ).mul(100)
            )
            indice_municipal = indice_municipal.where(
                bases_municipais.reindex(media_meses.index.get_level_values("municipio")).to_numpy() > 0
            )
            tabela_sazonal = indice_municipal.unstack("mes")
            tabela_sazonal = tabela_sazonal.reindex(columns=range(1, 13))
            meses_colunas = {
                1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
                5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
                9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
            }
            tabela_sazonal = tabela_sazonal.rename(columns=meses_colunas)
            tabela_sazonal = (
                tabela_sazonal.sort_index(key=lambda idx: idx.str.casefold())
                .rename_axis("Município")
                .reset_index()
            )
            display_table(tabela_sazonal)
            st.download_button(
                "⬇️ Exportar índice sazonal por município (CSV)",
                data=tabela_sazonal.to_csv(
                    index=False, sep=";", decimal=",", float_format="%.2f"
                ).encode("utf-8-sig"),
                file_name="siscan_indice_sazonal_municipio_mes.csv",
                mime="text/csv",
                key="exportar_indice_sazonal_municipio",
            )
            # Medidas descritivas complementares: não modificam o índice sazonal.
            # Cada observação é uma competência (município × ano × mês) da Gold.
            with st.expander("Ver estatísticas mensais por município", expanded=False):
                st.markdown(
                    "Consulte a **quantidade de exames registrada em cada mês** "
                    "usando média, mediana ou moda entre os anos selecionados. "
                    "Essas medidas são complementares: **o índice sazonal acima "
                    "continua calculado pela média**."
                )
                medida_estatistica = st.selectbox(
                    "Medida estatística",
                    options=["Média", "Mediana", "Moda"],
                    index=0,
                    key="medida_estatistica_mensal_outubro",
                )

                def moda_unica(valores):
                    """Retorna a moda apenas se houver repetição e uma vencedora única."""
                    contagens = valores.dropna().value_counts()
                    if contagens.empty or int(contagens.iloc[0]) < 2:
                        return float("nan")
                    if int((contagens == contagens.iloc[0]).sum()) != 1:
                        return float("nan")
                    return float(contagens.index[0])

                agrupado_estatistico = sazonal_muni.groupby(
                    ["municipio", "mes"]
                )["quantidade"]
                if medida_estatistica == "Média":
                    valores_estatisticos = agrupado_estatistico.mean()
                elif medida_estatistica == "Mediana":
                    valores_estatisticos = agrupado_estatistico.median()
                else:
                    valores_estatisticos = agrupado_estatistico.agg(moda_unica)

                tabela_estatisticas = (
                    valores_estatisticos.unstack("mes")
                    .reindex(columns=range(1, 13))
                    .rename(columns=meses_colunas)
                    .sort_index(key=lambda nomes: nomes.str.casefold())
                    .rename_axis("Município")
                    .reset_index()
                )
                st.caption(
                    f"Valores em **quantidade de exames**, não em percentual. "
                    f"Medida exibida: **{medida_estatistica.lower()}**. "
                    "Meses sem registros são excluídos do cálculo, não tratados como zero."
                )
                with st.expander("ℹ️ Como interpretar média, mediana e moda", expanded=False):
                    st.markdown(
                        "**Média:** soma dos exames registrados naquele mês "
                        "nos anos disponíveis, dividida pelo número de observações. "
                        "É sensível a valores muito altos ou baixos.\n\n"
                        "**Mediana:** valor central das quantidades ordenadas; "
                        "com quantidade par de observações, é a média dos dois "
                        "valores centrais. É menos sensível a valores extremos.\n\n"
                        "**Moda:** quantidade de exames que se repete com maior "
                        "frequência naquele mês entre os anos disponíveis. "
                        "Mostra **N/D** quando todos os valores são diferentes "
                        "ou quando há empate entre as frequências máximas; "
                        "não é escolhida uma moda arbitrária.\n\n"
                        "Cada município usa somente os registros dos anos "
                        "selecionados. Essas medidas descrevem a produção "
                        "**em números de exames**, não são versões alternativas "
                        "do índice sazonal e não representam mulheres distintas."
                    )
                display_table(tabela_estatisticas)
                st.download_button(
                    "⬇️ Exportar estatísticas mensais (CSV)",
                    data=tabela_estatisticas.to_csv(
                        index=False, sep=";", decimal=".", float_format="%.2f",
                        na_rep="N/D",
                    ).encode("utf-8-sig"),
                    file_name=(
                        "siscan_estatisticas_mensais_"
                        + {"Média": "media", "Mediana": "mediana", "Moda": "moda"}[
                            medida_estatistica
                        ]
                        + ".csv"
                    ),
                    mime="text/csv",
                    key="exportar_estatisticas_mensais_outubro",
                )
        else:
            st.info("Não há competências disponíveis para a tabela sazonal neste recorte.")

    table = city.rename(columns={
        "municipio":"Município",
        "exames_referencia_setembro":"Exames em setembro",
        "exames_mes":"Exames em outubro",
        "diferenca_exames":"Diferença (exames)",
        "variacao_pct":"Variação (%)"
    })
    st.markdown(f"#### Dados municipais · {len(table)} municípios")
    st.markdown(
        "Detalha os **exames registrados em setembro e outubro**, a diferença "
        "absoluta e a variação percentual por município no recorte selecionado."
    )
    with st.expander("ℹ️ Como interpretar a tabela municipal", expanded=False):
        st.markdown(
            "**Diferença (exames) = outubro − setembro.** "
            "**Variação (%) = diferença ÷ exames de setembro × 100.** "
            "Valores positivos representam mais registros em outubro; negativos, "
            "menos registros. Quando setembro não apresenta base positiva, "
            "a variação percentual não pode ser calculada. "
            "Os valores são quantidades de exames, e não pessoas distintas."
        )
    display_table(table, percent_columns=["Variação (%)"],
                  integer_columns=["Exames em setembro", "Exames em outubro", "Diferença (exames)"])
    st.download_button(
        "⬇️ Exportar CSV", table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="siscan_outubro_rosa.csv", mime="text/csv"
    )
