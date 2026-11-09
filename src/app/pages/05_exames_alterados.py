import copy
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,page_header,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,format_percent_chart,OCEAN,SKY,ORANGE,NAVY
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered,require,sidebar_filters,selected_years

# Cores com maior contraste entre os grupos etários (PET-Saúde).
BABY_BLUE = "#A9DDF4"   # <25 anos
ROYAL_BLUE = "#1757A6"  # 25–64 anos
st.set_page_config(page_title="Exames alterados | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
page_header(
    "Resultados",
    "Exames citopatológicos alterados",
    "Apresenta a quantidade e a proporção de exames citopatológicos com "
    "resultados alterados entre os exames válidos, considerando os municípios "
    "e anos selecionados. Permite comparar os grupos etários, acompanhar "
    "a evolução anual dos registros e identificar diferenças entre municípios. "
    "As proporções se referem a exames, não ao número de mulheres com alterações.",
)
df=filtered("alterados")
if require(df,["municipio","faixa_etaria","grupo_etario_3","quantidade_alterados","total_exames_validos"]):
    # A Gold classifica as idades sem perder o detalhamento quinquenal.
    # 'Até 9 anos' pertence a <=24, enquanto 'Ignorado' não tem idade conhecida.
    grupo_para_rotulo = {
        "<= 24 anos": "<25 anos",
        "25 a 64 anos": "25–64 anos",
        ">= 65 anos": "≥65 anos",
    }
    df = df.copy()
    df["grupo_3"] = df["grupo_etario_3"].astype("string").str.strip().map(grupo_para_rotulo)
    desconhecidos = df.loc[
        df["grupo_3"].isna() & df["grupo_etario_3"].ne("Ignorado"),
        "grupo_etario_3",
    ].dropna().unique().tolist()
    if desconhecidos:
        st.error("Categorias etárias inesperadas na Gold: " + ", ".join(map(str, desconhecidos)))
        st.stop()
    df = df.loc[df["grupo_3"].notna()].copy()
    if df.empty:
        st.info("Não há exames com faixa etária conhecida no recorte selecionado.")
        st.stop()
    num=df.quantidade_alterados.sum(min_count=1)
    den=df.total_exames_validos.sum(min_count=1)
    metric_row([("Exames alterados",fmt_num(num)),("Proporção operacional",fmt_pct(pct(num,den))),
                ("Exames no denominador disponível",fmt_num(den) if pd.notna(den) else "N/D")])
    st.markdown("### Proporção de exames alterados por grupo etário")
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
    ordem_grupos = ["<25 anos", "25–64 anos", "≥65 anos"]
    macro = df.groupby("grupo_3", as_index=False)[
        ["quantidade_alterados", "total_exames_validos"]
    ].sum(min_count=1)
    macro["proporcao_pct"] = (
        macro["quantidade_alterados"]
        .div(macro["total_exames_validos"].where(macro["total_exames_validos"] > 0))
        .mul(100)
    )
    macro["grupo_3"] = pd.Categorical(
        macro["grupo_3"], categories=ordem_grupos, ordered=True
    )
    macro = macro.sort_values("grupo_3").dropna(subset=["proporcao_pct"])
    if not macro.empty:
        macro_fig = px.bar(
            macro, x="grupo_3", y="proporcao_pct", color="grupo_3",
            category_orders={"grupo_3": ordem_grupos},
            color_discrete_map={
                "<25 anos": "#169B62", "25–64 anos": ROYAL_BLUE, "≥65 anos": ORANGE,
            },
            custom_data=["quantidade_alterados", "total_exames_validos"],
            labels={"grupo_3": "Grupo etário", "proporcao_pct": "Proporção (%)"},
        )
        macro_fig.update_layout(
            showlegend=False,
            bargap=0.54,  # barras proporcionais à área branca ampliada
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
        # Área branca ampliada (~83% no desktop) e centralizada com
        # margens laterais simétricas. Na tela estreita, ocupa a largura
        # disponível sem alterar os outros gráficos.
        _, chart_col, _ = st.columns([1, 10, 1], gap="small")
        with chart_col:
            chart_with_right_click_download(
                macro_fig, filename="exames_alterados_grupos_etarios.png",
                height=410, export_fig=macro_export,
            )

    # Evolução anual com linhas independentes para os três grupos etários.
    # Dois municípios por linha (até seis linhas), sem acumular grupos.
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
            lines_source["grupo_3"].isin(ordem_grupos)
            & (lines_source["quantidade_alterados"] >= 0)
        ].copy()
        if lines_source.empty:
            st.info("Não há exames alterados por município e grupo etário no período selecionado.")
        else:
            lines_yearly = (
                lines_source.groupby(
                    ["municipio", "ano", "grupo_3"], as_index=False
                )["quantidade_alterados"].sum(min_count=1)
            )
            lines_yearly["ano"] = lines_yearly["ano"].astype(int)
            lines_yearly["ano_label"] = lines_yearly["ano"].astype(str)
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
            # Ordenação independente das facetas gerais, com os mesmos rótulos
            # e estilo de seletor já usados na página.
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
            municipios_lines = sorted(
                lines_yearly["municipio"].unique(), key=lambda name: name.casefold()
            )
            if sort_grupos == "Maior para menor":
                totals_grupos = (
                    lines_yearly.groupby("municipio")["quantidade_alterados"]
                    .sum(min_count=1)
                )
                municipios_lines.sort(
                    key=lambda municipio: (
                        -float(totals_grupos.loc[municipio])
                        if pd.notna(totals_grupos.loc[municipio])
                        else float("inf"),
                        municipio.casefold(),
                    )
                )
            anos_lines = sorted(lines_yearly["ano"].unique().tolist())
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
                    "grupo_3": ordem_grupos,
                },
                color_discrete_map={
                    "<25 anos": "#169B62",
                    "25–64 anos": ROYAL_BLUE,
                    "≥65 anos": ORANGE,
                },
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
            # Há anos em que <25 e >=65 possuem ambos zero. Se o laranja
            # for desenhado por cima, esconderá a linha verde nesses anos.
            # Ordem de desenho: laranja atrás, azul no meio, verde por cima;
            # sem alterar valores nem imputar competências ausentes.
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
            # PNG sem tabelas: preservar a mesma grade de 11 gráficos.
            # Rótulos distintos para cada grupo, com espaço extra abaixo
            # da linha zero para não sobrepor números ao eixo dos anos.
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
            # Ajustar escalas de cada faceta separadamente para os valores
            # baixos (verde/laranja) não se confundirem com o eixo X.
            for pos, municipio in enumerate(municipios_lines):
                painel = lines_yearly.loc[
                    lines_yearly["municipio"].eq(municipio),
                    "quantidade_alterados",
                ]
                maximo = float(painel.max()) if not painel.empty else 0.0
                amplitude = max(maximo, 3.0)
                # plotly express com wrap=2 posiciona a primeira faceta
                # na última linha, da esquerda para a direita.
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
                "No celular, deslize o gráfico para os lados. "
                "O PNG mostra valores nas três linhas, sem tabelas."
            )
            chart_with_right_click_download(
                fig_lines,
                filename="exames_alterados_linhas_grupos_etarios_por_municipio.png",
                height=fig_lines.layout.height,
                min_chart_width=760,
                export_fig=export_lines,
            )

    # Série anual por município: utiliza as quantidades já existentes na Gold.
    # Ausências de ano são mantidas como lacunas, nunca convertidas em zero.
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
        yearly = (
            df.dropna(subset=["ano"])
            .groupby(["municipio", "ano"], as_index=False)["quantidade_alterados"]
            .sum(min_count=1)
        )
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
            # O ranking considera a soma dos exames alterados no recorte filtrado.
            # Empates mantêm os nomes dos municípios em ordem alfabética.
            municipalities = sorted(yearly["municipio"].unique())
            if sort_mode == "Maior para menor":
                totals_by_city = (
                    yearly.groupby("municipio")["quantidade_alterados"]
                    .sum(min_count=1)
                )
                municipalities.sort(
                    key=lambda city: (
                        -totals_by_city.loc[city] if pd.notna(totals_by_city.loc[city])
                        else float("inf"),
                        city.casefold(),
                    )
                )
            available_years = sorted(yearly["ano"].astype(int).unique())
            # Também exibe lacunas dos anos selecionados, sem criar contagens artificiais.
            from utils.data_loader import selected_years
            years = selected_years()
            axis_years = years if years else available_years
            idx = pd.MultiIndex.from_product(
                [municipalities, axis_years], names=["municipio", "ano"]
            )
            yearly = (
                yearly.set_index(["municipio", "ano"])
                .reindex(idx)
                .reset_index()
            )
            yearly["ano_label"] = yearly["ano"].astype(str)
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
            # Preserva a identificação da medida sem repetir o título em cada
            # subplot, evitando sobreposição com as escalas dos municípios.
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
            # Um único título horizontal para todo o conjunto de facetas.
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
            st.caption("No celular, deslize o gráfico para os lados. No computador, clique com o botão direito para baixar em PNG.")
            chart_with_right_click_download(
                fig_yearly, filename="exames_alterados_anuais_municipios.png",
                height=fig_yearly.layout.height, min_chart_width=820
            )
        else:
            st.info("Não há registros anuais de exames alterados para o recorte selecionado.")

    # Matriz com as três categorias já classificadas na Gold.
    # A taxa de cada célula é ponderada pelos exames válidos; nunca é
    # a média simples das taxas das faixas quinquenais.
    matrix = df.groupby(["municipio", "grupo_3"], as_index=False)[
        ["quantidade_alterados", "total_exames_validos"]
    ].sum(min_count=1)
    matrix["taxa"] = (
        matrix["quantidade_alterados"]
        .div(matrix["total_exames_validos"].where(matrix["total_exames_validos"] > 0))
        .mul(100)
    )
    heat = matrix.pivot(index="municipio", columns="grupo_3", values="taxa")
    heat = heat.reindex(columns=ordem_grupos)
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
        fig=px.imshow(
            heat, aspect="auto", color_continuous_scale="Blues",
            labels={"x":"Grupo etário","y":"Município","color":"%"},
            title=None,
        )
        fig.update_traces(
            xgap=3, ygap=3,
            hovertemplate="Grupo etário: %{x}<br>Município: %{y}<br>Proporção: %{z:.2f}%<extra></extra>",
        )
        fig.update_coloraxes(colorbar_tickformat=".2f", colorbar_ticksuffix="%")
        # Rótulos permanentes para leitura também em imagens estáticas.
        # Não converter dados ausentes em 0: exibir um travessão.
        valid_values = heat.stack().dropna()
        max_rate = float(valid_values.max()) if not valid_values.empty else 0.0
        for city in heat.index:
            for age in heat.columns:
                value = heat.at[city, age]
                has_value = pd.notna(value)
                label = f"{value:.2f}".replace(".", ",") if has_value else "—"
                # Texto claro em células escuras, azul-marinho nas demais.
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
        # Contraste dos rótulos dos eixos, sem negrito.
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
        # Apenas três colunas, sem a largura mínima exigida pela antiga matriz de 15 faixas.
        chart_with_right_click_download(
            fig, filename="matriz_territorial_exames_alterados.png",
            height=fig.layout.height, min_chart_width=0,
        )
    with st.expander("Ver dados detalhados de exames alterados", expanded=False):
        export_table(matrix, "siscan_exames_alterados.csv")

    # Novas métricas Q5: fatos de composição da Gold, separados do indicador canônico.
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
    if not cat_anual.empty and {
        "ano", "categoria", "quantidade_alterados"
    }.issubset(cat_anual.columns):
        cat_anual["quantidade_alterados"] = pd.to_numeric(
            cat_anual["quantidade_alterados"], errors="coerce"
        )
        por_cat_ano = (
            cat_anual.groupby(["ano", "categoria"], as_index=False)[
                "quantidade_alterados"
            ].sum(min_count=1).dropna(subset=["quantidade_alterados"])
        )
        if not por_cat_ano.empty:
            # Paleta PET-Saúde: uma cor fixa por categoria, inclusive quando
            # os filtros ocultam categorias em determinados anos.
            categorias_ordenadas = sorted(
                por_cat_ano["categoria"].dropna().unique(), key=str.casefold
            )
            cores_categorias = [
                "#006C9A", "#E85D2A", "#218B65", "#6B5FB5",
                "#D49B22", "#1A3B5C", "#C24B75", "#54A8C3",
            ]
            mapa_cores = {
                categoria: cores_categorias[i % len(cores_categorias)]
                for i, categoria in enumerate(categorias_ordenadas)
            }
            fig_cat = px.bar(
                por_cat_ano, x="ano", y="quantidade_alterados",
                color="categoria", barmode="stack",
                color_discrete_map=mapa_cores,
                category_orders={"categoria": categorias_ordenadas},
                labels={"ano": "Ano", "quantidade_alterados": "Exames por categoria",
                        "categoria": "Categoria citopatológica"},
            )
            fig_cat.update_traces(
                hovertemplate=(
                    "Ano: %{x}<br>Exames: %{y:,.0f}"
                    "<extra>%{fullData.name}</extra>"
                ),
                marker_line_color="#FFFFFF",
                marker_line_width=0.6,
            )
            fig_cat.update_xaxes(type="category", showgrid=False)
            fig_cat.update_yaxes(
                rangemode="tozero", tickformat=",d", gridcolor="#E4EBF1"
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
            export_cat.update_layout(
                title=dict(text="Exames alterados por categoria e ano", x=0.5),
                margin=dict(l=90, r=240, t=100, b=85),
            )
            chart_with_right_click_download(
                fig_cat, filename="alterados_categorias_ano.png",
                height=480, export_fig=export_cat,
            )
            with st.expander("Ver dados de categorias por ano", expanded=False):
                total_ano = por_cat_ano.groupby("ano")[
                    "quantidade_alterados"
                ].transform("sum")
                tabela_cat = por_cat_ano.assign(
                    participacao_pct=por_cat_ano["quantidade_alterados"].div(
                        total_ano.where(total_ano > 0)
                    ).mul(100)
                ).rename(columns={
                    "ano": "Ano", "categoria": "Categoria",
                    "quantidade_alterados": "Exames na categoria",
                    "participacao_pct": "Participação entre categorias (%)",
                })
                export_table(tabela_cat, "siscan_categoria_anual.csv")
        else:
            st.info("Não há registros por categoria nos filtros selecionados.")
    else:
        st.info("A tabela Gold de categorias anuais está vazia ou incompleta.")

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
    if selected_years() != list(range(2020, 2026)):
        st.info(
            "Este cruzamento foi consolidado na Gold para 2020–2025, sem "
            "detalhamento anual. Selecione todos os anos para visualizá-lo."
        )
    else:
        cat_faixa = filtered("categoria_faixa")
        if not cat_faixa.empty and {
            "categoria", "grupo_etario_3", "quantidade_alterados"
        }.issubset(cat_faixa.columns):
            cat_faixa["grupo_3"] = (
                cat_faixa["grupo_etario_3"].astype("string").str.strip()
                .map(grupo_para_rotulo)
            )
            cat_faixa["quantidade_alterados"] = pd.to_numeric(
                cat_faixa["quantidade_alterados"], errors="coerce"
            )
            comp = (
                cat_faixa.dropna(subset=["grupo_3", "quantidade_alterados"])
                .groupby(["categoria", "grupo_3"], as_index=False)[
                    "quantidade_alterados"
                ].sum(min_count=1)
            )
            if not comp.empty:
                base = comp.groupby("categoria")[
                    "quantidade_alterados"
                ].transform("sum")
                comp["participacao_pct"] = comp[
                    "quantidade_alterados"
                ].div(base.where(base > 0)).mul(100)
                comp = comp.dropna(subset=["participacao_pct"])
                if not comp.empty:
                    # Barras verticais 100% com rótulos quebrados em duas linhas.
                    # Mantém os nomes originais nos dados e no hover.
                    categorias_presentes = sorted(
                        comp["categoria"].unique(), key=str.casefold
                    )
                    def rotulo_categoria(nome):
                        palavras = str(nome).replace("_", " ").split()
                        linhas = []
                        atual = ""
                        for palavra in palavras:
                            candidato = (atual + " " + palavra).strip()
                            if atual and len(candidato) > 15:
                                linhas.append(atual)
                                atual = palavra
                            else:
                                atual = candidato
                        if atual:
                            linhas.append(atual)
                        return "<br>".join(linhas)

                    cores_faixa = {
                        "<25 anos": "#169B62",
                        "25–64 anos": ROYAL_BLUE,
                        "≥65 anos": "#E85D2A",
                    }
                    fig_faixas = px.bar(
                        comp, x="categoria", y="participacao_pct",
                        color="grupo_3", barmode="stack",
                        color_discrete_map=cores_faixa,
                        category_orders={
                            "grupo_3": ordem_grupos,
                            "categoria": categorias_presentes,
                        },
                        labels={
                            "categoria": "Categoria citopatológica",
                            "participacao_pct": "Participação (%)",
                            "grupo_3": "Grupo etário",
                        },
                        custom_data=["quantidade_alterados"],
                    )
                    fig_faixas.update_traces(
                        marker_line_color="#FFFFFF", marker_line_width=0.8,
                        hovertemplate=(
                            "Categoria: %{x}<br>Participação: %{y:.2f}%"
                            "<br>Exames: %{customdata[0]:,.0f}"
                            "<extra>%{fullData.name}</extra>"
                        ),
                    )
                    fig_faixas.update_yaxes(
                        range=[0, 100], ticksuffix="%", dtick=20,
                        gridcolor="#E4EBF1",
                        title_text="Participação dentro da categoria (%)",
                    )
                    fig_faixas.update_xaxes(
                        type="category", categoryorder="array",
                        categoryarray=categorias_presentes,
                        tickmode="array", tickvals=categorias_presentes,
                        ticktext=[rotulo_categoria(nome) for nome in categorias_presentes],
                        tickangle=0,
                        tickfont=dict(size=11, color=NAVY),
                        title_text=None, automargin=True,
                    )
                    fig_faixas.update_layout(
                        height=485, bargap=0.27,
                        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                        font=dict(color=NAVY),
                        legend=dict(
                            title_text="Grupo etário", orientation="h",
                            x=0.5, xanchor="center", y=1.11, yanchor="bottom",
                            font=dict(size=12, color=NAVY),
                        ),
                        margin=dict(l=75, r=25, t=95, b=115),
                    )
                    img_faixas = copy.deepcopy(fig_faixas)
                    img_faixas.update_layout(
                        title=dict(
                            text="Composição etária por categoria (2020–2025)",
                            x=0.5, font=dict(size=21, color=NAVY),
                        ),
                        width=1400, height=600,
                        margin=dict(l=95, r=60, t=125, b=145),
                    )
                    chart_with_right_click_download(
                        fig_faixas, filename="alterados_categorias_faixas.png",
                        height=485, min_chart_width=970, export_fig=img_faixas,
                    )
                    with st.expander("Ver dados de categorias por faixa etária"):
                        export_table(
                            comp.rename(columns={
                                "categoria": "Categoria", "grupo_3": "Grupo etário",
                                "quantidade_alterados": "Exames na categoria",
                                "participacao_pct": "Participação na categoria (%)",
                            }), "siscan_categoria_faixa_etaria.csv",
                        )
                else:
                    st.info("Não há categorias com registros para esta visualização.")
            else:
                st.info("Não há registros por categoria e faixa etária.")
        else:
            st.info("A tabela Gold de categorias por faixa etária está indisponível.")

