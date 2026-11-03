import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,page_header,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,format_percent_chart,OCEAN
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered,require,sidebar_filters
st.set_page_config(page_title="Exames alterados | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
page_header("Resultados", "Exames citopatológicos alterados")
df=filtered("alterados")
# Alinhamento metodológico (31/out/2026): 'Ignorado' e 'Até 9 anos' têm bases ínfimas
# (0 alterados sobre ~1-2 exames) e não compõem grupos da diretriz de rastreio.
# Excluídas das proporções (barra e matriz territorial); os dados permanecem íntegros
# na Gold e nos contadores globais. Mesma regra aplicada no dashboard AI/BI.
df=df[~df["faixa_etaria"].isin(["Ignorado","Até 9 anos"])]
if require(df,["municipio","faixa_etaria","quantidade_alterados","total_exames_validos"]):
    num=df.quantidade_alterados.sum(min_count=1)
    den=df.total_exames_validos.sum(min_count=1)
    metric_row([("Exames alterados",fmt_num(num)),("Proporção operacional",fmt_pct(pct(num,den))),
                ("Exames no denominador disponível",fmt_num(den) if pd.notna(den) else "N/D")])
    byage=df.groupby("faixa_etaria",as_index=False)[["quantidade_alterados","total_exames_validos"]].sum(min_count=1)
    byage["taxa"]=byage.quantidade_alterados.div(byage.total_exames_validos.where(byage.total_exames_validos>0)).mul(100)
    fig=px.bar(byage,x="faixa_etaria",y="taxa",color_discrete_sequence=[OCEAN],
               labels={"faixa_etaria":"Faixa etária","taxa":"Proporção (%)"},
               title="Exames alterados por faixa etária")
    fig.update_xaxes(tickangle=-45)
    display_chart(format_percent_chart(fig))
    # Série anual por município: utiliza as quantidades já existentes na Gold.
    # Ausências de ano são mantidas como lacunas, nunca convertidas em zero.
    st.markdown("### Evolução anual de exames alterados por município")
    st.caption(
        "Quantidade de exames citopatológicos alterados por município e ano. "
        "Cada painel usa sua própria escala vertical para facilitar a leitura; "
        "compare os valores absolutos pelos eixos e pelo cursor."
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
            st.caption("Clique com o botão direito no gráfico para baixar em PNG.")
            chart_with_right_click_download(
                fig_yearly, filename="exames_alterados_anuais_municipios.png",
                height=fig_yearly.layout.height, min_chart_width=820
            )
        else:
            st.info("Não há registros anuais de exames alterados para o recorte selecionado.")

    matrix=df.groupby(["municipio","faixa_etaria"],as_index=False)[["quantidade_alterados","total_exames_validos"]].sum(min_count=1)
    matrix["taxa"]=matrix.quantidade_alterados.div(matrix.total_exames_validos.where(matrix.total_exames_validos>0)).mul(100)
    heat=matrix.pivot(index="municipio",columns="faixa_etaria",values="taxa")
    if not heat.empty:
        st.caption("Valores nas células em (%) · — indica ausência de dados.")
        fig=px.imshow(
            heat, aspect="auto", color_continuous_scale="Blues",
            labels={"x":"Faixa etária","y":"Município","color":"%"},
            title="Matriz territorial de proporção operacional",
        )
        fig.update_traces(
            xgap=3, ygap=3,
            hovertemplate="Faixa etária: %{x}<br>Município: %{y}<br>Proporção: %{z:.2f}%<extra></extra>",
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
                    font=dict(size=10, color=font_color),
                    xanchor="center", yanchor="middle",
                    hovertext=None,
                )
        # Contraste dos rótulos dos eixos, sem negrito.
        fig.update_xaxes(
            tickfont=dict(color="#1A3B5C", size=12, family="Arial"),
            title_text="Faixa etária",
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
            height=max(500, 43 * len(heat.index) + 155),
            margin=dict(l=25, r=15, t=70, b=65),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#1A3B5C"),
        )
        # Usa a altura definida acima: display_chart aplica 430px a todos os gráficos.
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("Ver dados detalhados de exames alterados", expanded=False):
        export_table(matrix, "siscan_exames_alterados.csv")
