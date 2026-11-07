import copy
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,page_header,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,format_percent_chart,OCEAN,SKY,ORANGE,NAVY
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered,require,sidebar_filters
st.set_page_config(page_title="Exames alterados | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
page_header("Resultados", "Exames citopatológicos alterados")
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
    st.caption(
        "Três grupos definidos pela coluna grupo_etario_3 da Gold. "
        "Proporção = soma de exames alterados ÷ soma de exames válidos × 100; "
        "não é a média de percentuais das faixas detalhadas."
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
                "<25 anos": SKY, "25–64 anos": OCEAN, "≥65 anos": ORANGE,
            },
            custom_data=["quantidade_alterados", "total_exames_validos"],
            labels={"grupo_3": "Grupo etário", "proporcao_pct": "Proporção (%)"},
        )
        macro_fig.update_layout(
            showlegend=False,
            bargap=0.48,  # barras mais estreitas e com espaçamento confortável
            margin=dict(l=65, r=25, t=20, b=65),
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
        # Ocupa cerca de 2/3 do conteúdo no desktop e a largura
        # disponível no celular; não afeta os demais gráficos.
        _, chart_col, _ = st.columns([1, 4, 1], gap="small")
        with chart_col:
            chart_with_right_click_download(
                macro_fig, filename="exames_alterados_grupos_etarios.png",
                height=380, export_fig=macro_export,
            )

    # Facetas exclusivamente para a população-alvo (25–64 anos).
    # A coluna grupo_etario_3 vem da Gold e preserva a granularidade
    # município × ano × faixa detalhada. Nunca somar o total de outros grupos.
    # Ausências continuam NaN, não são substituídas por zero.
    st.markdown("### Evolução anual de exames alterados por município · 25–64 anos")
    st.caption(
        "Quantidade anual de exames citopatológicos alterados somente na "
        "faixa-alvo de 25 a 64 anos, conforme grupo_etario_3 da Gold. "
        "Cada município utiliza escala vertical própria; compare os valores "
        "absolutos nos eixos ou ao passar o mouse."
    )
    if "ano" not in df.columns:
        st.info("O gráfico anual requer a coluna 'ano' na tabela Gold de exames alterados.")
    else:
        yearly = (
            df.loc[df["grupo_3"].eq("25–64 anos")]
            .dropna(subset=["ano"])
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
            # Ordena somente os exames alterados de 25–64 anos.
            # Conserva municípios sem registros como facetas vazias, sem imputar zero.
            from utils.data_loader import MUNICIPIOS
            selected = st.session_state.get(
                "city_preference", list(MUNICIPIOS.values())
            )
            municipalities = sorted(city for city in selected if city in MUNICIPIOS.values())
            if sort_mode == "Maior para menor":
                totals_by_city = (
                    yearly.groupby("municipio")["quantidade_alterados"]
                    .sum(min_count=1)
                )
                municipalities.sort(
                    key=lambda city: (
                        -totals_by_city.loc[city]
                        if city in totals_by_city.index and pd.notna(totals_by_city.loc[city])
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
                hovertemplate="Ano: %{x}<br>Exames alterados (25–64 anos): %{y:,.0f}<extra></extra>",
            )
            # Preserva a identificação da medida sem repetir o título em cada
            # subplot, evitando sobreposição com as escalas dos municípios.
            fig_yearly.update_yaxes(
                matches=None, showticklabels=True, title_text=None,
                rangemode="tozero", gridcolor="#E9EDF1", zeroline=False
            )
            fig_yearly.add_annotation(
                x=-0.065, y=0.5, xref="paper", yref="paper",
                text="Exames alterados (25–64 anos)", textangle=-90, showarrow=False,
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
                fig_yearly, filename="exames_alterados_anuais_municipios_25_64_anos.png",
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
        st.caption("Proporção de exames alterados em cada grupo etário (%) · — indica ausência de dados.")
        fig=px.imshow(
            heat, aspect="auto", color_continuous_scale="Blues",
            labels={"x":"Grupo etário","y":"Município","color":"%"},
            title="Matriz territorial de proporção de exames alterados por grupo etário",
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
