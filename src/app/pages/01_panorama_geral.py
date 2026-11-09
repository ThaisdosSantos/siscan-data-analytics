"""Panorama territorial e temporal de exames citopatológicos registrados."""
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.theme import apply_custom_css, page_header, display_chart, display_table, export_table, fmt_num, fmt_pct, pct, OCEAN
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, require, sidebar_filters, MUNICIPIOS, selected_years, years_label, year_month_index

st.set_page_config(page_title="Panorama geral | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
page_header("Panorama geral", "Volume de exames por competência e município",
            "Exames citopatológicos registrados na 10ª CRS do Rio Grande do Sul.")

df = filtered("temporal")
if require(df, ["municipio", "ano", "mes", "quantidade"]):
    years = selected_years()
    places = st.session_state.get("city_preference", list(MUNICIPIOS.values()))
    period = years_label(years)
    total = df.quantidade.sum(min_count=1)
    monthly = (df.groupby(["ano", "mes"], as_index=False)
               .quantidade.sum(min_count=1).sort_values(["ano", "mes"]))
    monthly["data"] = pd.to_datetime(dict(year=monthly.ano, month=monthly.mes, day=1))
    months_count = len(monthly)
    expected = 12 * len(years)
    bycity = (df.groupby("municipio", as_index=False).quantidade.sum(min_count=1)
              .sort_values("quantidade", ascending=False))
    top = bycity.iloc[0] if not bycity.empty else None

    col_total, col_media, col_municipio = st.columns(3)
    with col_total:
        st.metric("Total de exames registrados", fmt_num(total))
        st.caption("Volume de exames, não de pessoas distintas.")
    with col_media:
        st.metric("Média por mês com registro", fmt_num(monthly.quantidade.mean()))
        st.caption(f"Calculada sobre **{months_count} de {expected} meses** disponíveis no recorte.")
    with col_municipio:
        st.metric("Maior participação no total selecionado",
                  fmt_pct(pct(top.quantidade, total)) if top is not None else "N/D")
        if top is not None:
            st.caption(f"**{top.municipio}** · percentual dos exames dos municípios selecionados em {period}.")

    # Constrói a série mensal completa antes de plotar: ausência permanece NaN.
    complete = year_month_index(years)
    selected_dates = pd.DatetimeIndex(
        [date for date in complete if date.year in years]
    )
    series = monthly.set_index("data").reindex(complete)
    missing = selected_dates[series.loc[selected_dates, "quantidade"].isna()]
    if len(missing):
        months_pt = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                     "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        missing_label = ", ".join(f"{months_pt[d.month - 1]}/{d.year}" for d in missing)
        st.warning(f"**Disponibilidade temporal:** {months_count} de {expected} meses com registros. "
                   f"Sem dados em **{missing_label}**.")
    else:
        st.caption(f"Disponibilidade temporal: **{months_count} de {expected} meses** com registros.")

    st.subheader("Evolução mensal")
    fig = px.line(x=complete, y=series["quantidade"], markers=True,
                  labels={"x": "Competência", "y": "Exames registrados"},
                  color_discrete_sequence=[OCEAN])
    fig.update_traces(connectgaps=False,
                      hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>")
    axis_dates = complete[::max(1, len(complete)//12)]
    short_pt = ["jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"]
    fig.update_xaxes(tickmode="array", tickvals=axis_dates,
                     ticktext=[f"{short_pt[d.month-1]}/{str(d.year)[2:]}" for d in axis_dates])
    fig.update_yaxes(tickformat=",d")
    display_chart(fig, filename="panorama_evolucao_mensal.png")

    st.subheader("Volume de exames por município")
    bars = bycity.sort_values("quantidade", ascending=True)
    fig = px.bar(bars, x="quantidade", y="municipio", orientation="h",
                 color_discrete_sequence=[OCEAN],
                 labels={"quantidade":"Exames registrados", "municipio":"Município"},
                 text="quantidade")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside",
                      cliponaxis=False,
                      hovertemplate="%{y}<br>%{x:,.0f} exames<extra></extra>")
    fig.update_xaxes(tickformat=",d", range=[0, max(1, bars.quantidade.max())*1.22])
    display_chart(fig, filename="panorama_volume_municipio.png")

    st.subheader("Evolução anual de exames por município")
    st.caption(
        "Quantidade de exames citopatológicos registrados por município e ano. "
        "Cada gráfico apresenta a evolução do seu município; anos sem registros "
        "permanecem sem ponto, em vez de serem interpretados como zero."
    )
    annual = (
        df.dropna(subset=["municipio", "ano"])
        .groupby(["municipio", "ano"], as_index=False)["quantidade"]
        .sum(min_count=1)
    )
    if not annual.empty:
        st.markdown("""
            <style>
            /* Somente o seletor de ordenação das facetas do panorama geral. */
            .st-key-panorama_sort_panel [data-testid="stSelectbox"] label p {
                color: #1A3B5C !important;
                font-weight: 700 !important;
                font-size: 0.88rem !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] > div {
                background-color: #FFFFFF !important;
                border: 1.5px solid #8FAFC5 !important;
                border-radius: 9px !important;
                min-height: 43px !important;
                box-shadow: 0 2px 7px rgba(26,59,92,0.07) !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] > div:hover {
                border-color: #006C9A !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] > div:focus-within {
                border-color: #006C9A !important;
                box-shadow: 0 0 0 2px rgba(0,108,154,0.18) !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] * {
                color: #1A3B5C !important;
            }
            .st-key-panorama_sort_panel [data-baseweb="select"] svg {
                fill: #006C9A !important;
            }
            </style>
        """, unsafe_allow_html=True)
        with st.container(key="panorama_sort_panel"):
            order = st.selectbox(
                "Ordenar por",
                ["A–Z", "Maior para menor"],
                key="sort_facetas_panorama",
            )
        municipalities = sorted(annual["municipio"].unique())
        if order == "Maior para menor":
            totals = annual.groupby("municipio")["quantidade"].sum(min_count=1)
            municipalities.sort(
                key=lambda city: (
                    -totals.loc[city] if pd.notna(totals.loc[city]) else float("inf"),
                    city.casefold(),
                )
            )

        # Grade completa apenas para manter os anos sem registros como lacunas.
        years_axis = sorted(years)
        grid = pd.MultiIndex.from_product(
            [municipalities, years_axis], names=["municipio", "ano"]
        )
        annual = annual.set_index(["municipio", "ano"]).reindex(grid).reset_index()
        annual["ano_rotulo"] = annual["ano"].astype(int).astype(str)

        fig = px.line(
            annual,
            x="ano_rotulo",
            y="quantidade",
            facet_col="municipio",
            facet_col_wrap=3,
            facet_col_spacing=0.045,
            facet_row_spacing=0.085,
            category_orders={
                "municipio": municipalities,
                "ano_rotulo": [str(year) for year in years_axis],
            },
            markers=True,
            color_discrete_sequence=[OCEAN],
            labels={
                "ano_rotulo": "Ano",
                "quantidade": "Exames registrados",
                "municipio": "Município",
            },
        )
        fig.for_each_annotation(
            lambda annotation: annotation.update(
                text=annotation.text.split("=", 1)[-1],
                font=dict(size=12, color="#1A3B5C"),
            )
        )
        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(size=7),
            connectgaps=False,
            hovertemplate="Ano: %{x}<br>Exames registrados: %{y:,.0f}<extra></extra>",
        )
        fig.update_xaxes(
            matches=None, showticklabels=True, title_text=None,
            type="category", categoryorder="array",
            categoryarray=[str(year) for year in years_axis],
        )
        fig.update_yaxes(
            matches=None, showticklabels=True, title_text=None,
            rangemode="tozero", tickformat=",d",
            gridcolor="#E9EDF1", zeroline=False,
        )
        # Um título por eixo para o conjunto completo de facetas.
        # Os valores e os anos continuam visíveis em cada município.
        fig.add_annotation(
            x=-0.065, y=0.5, xref="paper", yref="paper",
            text="Exames registrados", textangle=-90, showarrow=False,
            font=dict(family="Arial", size=13, color="#1A3B5C"),
            xanchor="center", yanchor="middle",
        )
        fig.add_annotation(
            x=0.5, y=-0.025, xref="paper", yref="paper",
            text="Anos", showarrow=False,
            font=dict(family="Arial", size=13, color="#1A3B5C"),
            xanchor="center", yanchor="top",
        )
        fig.update_layout(
            height=max(480, 285 * ((len(municipalities) + 2) // 3)),
            showlegend=False,
            margin=dict(l=95, r=15, t=55, b=105),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            font=dict(color="#1A3B5C", size=11),
        )
        st.caption("No celular, deslize o gráfico para os lados. No computador, clique com o botão direito para baixar em PNG.")
        chart_with_right_click_download(
            fig, filename="panorama_exames_anuais_municipios.png",
            height=fig.layout.height, min_chart_width=820
        )

    # ------------------------------------------------------------------
    # Cruzamento ano × ano: variação percentual (Δ%) por município.
    # Δ% = (exames do ano − exames do ano anterior) ÷ exames do ano
    # anterior × 100. Calculado apenas entre anos consecutivos presentes
    # no recorte; anos sem registro não geram variação (evita interpretar
    # dado ausente como crescimento ou queda).
    # ------------------------------------------------------------------
    st.subheader("Variação anual de exames por município (ano a ano)")
    st.caption(
        "Cruzamento ano × ano: compara o total de exames de cada município "
        "com o ano anterior. Valores positivos indicam expansão na oferta de "
        "exames; negativos, retração. Variação de volume não equivale à "
        "cobertura populacional."
    )

    var_ano = (
        df.dropna(subset=["municipio", "ano"])
        .groupby(["municipio", "ano"], as_index=False)["quantidade"]
        .sum(min_count=1)
    )
    var_ano["ano"] = pd.to_numeric(var_ano["ano"], errors="coerce")
    var_ano = var_ano.dropna(subset=["municipio", "ano", "quantidade"])
    var_ano["ano"] = var_ano["ano"].astype(int)
    var_ano = var_ano.sort_values(["municipio", "ano"]).reset_index(drop=True)

    var_ano["ano_anterior"] = var_ano.groupby("municipio", sort=False)["ano"].shift(1)
    var_ano["quantidade_anterior"] = var_ano.groupby("municipio", sort=False)["quantidade"].shift(1)
    consecutivos = var_ano["ano"].sub(var_ano["ano_anterior"]).eq(1)
    var_ano["variacao_pct"] = (
        (var_ano["quantidade"] - var_ano["quantidade_anterior"])
        .div(var_ano["quantidade_anterior"].where(var_ano["quantidade_anterior"].gt(0)))
        .mul(100)
        .where(consecutivos)
    )
    var_ano["transicao"] = [
        f"{int(a)}→{int(b)}" if cons else None
        for a, b, cons in zip(var_ano["ano_anterior"], var_ano["ano"], consecutivos)
    ]

    def fmt_delta(v):
        return "N/D" if pd.isna(v) else f"{v:+.2f}%".replace(".", ",")

    if not var_ano["variacao_pct"].notna().any():
        st.info(
            "Selecione pelo menos dois anos consecutivos nos filtros para "
            "calcular a variação anual por município."
        )
    else:
        # Matriz município × transição, com gradiente centrado em zero.
        pivo_var = var_ano.pivot_table(
            index="municipio", columns="transicao",
            values="variacao_pct", aggfunc="mean",
        )
        pivo_var = pivo_var[
            sorted(pivo_var.columns, key=lambda c: int(str(c).split("→")[1]))
        ]
        vmax_var = float(pivo_var.abs().max().max())
        st.markdown("#### Variação anual (%) por município e transição")
        st.dataframe(
            pivo_var.style
            .format(fmt_delta, na_rep="—")
            .background_gradient(cmap="RdYlGn", axis=None, vmin=-vmax_var, vmax=vmax_var),
            use_container_width=True,
        )
        st.caption(
            "Δ% = (exames do ano − exames do ano anterior) ÷ exames do ano "
            "anterior × 100. Verde = alta; vermelho = queda; — = transição "
            "sem os dois anos presentes no recorte."
        )
        if any("2022" in str(c) for c in pivo_var.columns):
            st.caption(
                "⚠️ agosto/2022 não existe na fonte do SISCAN: o total de 2022 "
                "refere-se a 11 meses de registro, o que tende a subestimar a "
                "variação 2021→2022 e a superestimar a 2022→2023."
            )

        # Ranking da transição mais recente do recorte selecionado.
        ultima_var = pivo_var.columns[-1]
        ranking_var = var_ano.loc[var_ano["transicao"].eq(ultima_var)].copy()
        ranking_var = ranking_var.sort_values("variacao_pct", ascending=False)
        st.markdown(f"#### Ranking de variação na transição {ultima_var}")
        st.caption("Do maior crescimento ao maior recuo no volume anual de exames.")
        ranking_plot = ranking_var.sort_values("variacao_pct")
        fig_var = px.bar(
            ranking_plot, x="variacao_pct", y="municipio", orientation="h",
            color="variacao_pct", color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            labels={
                "variacao_pct": "Variação anual (%)",
                "municipio": "Município",
            },
        )
        fig_var.update_layout(separators=",.")
        fig_var.update_traces(
            texttemplate="%{x:+.2f}%",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>" + ultima_var + ": %{x:+.2f}%<extra></extra>"
            ),
        )
        lim_inf = min(float(ranking_plot["variacao_pct"].min()) * 1.28, 0)
        lim_sup = max(float(ranking_plot["variacao_pct"].max()) * 1.28, 1)
        fig_var.update_xaxes(
            zeroline=True, zerolinecolor="#1A3B5C", zerolinewidth=1.4,
            ticksuffix="%", range=[lim_inf, lim_sup],
        )
        display_chart(fig_var, filename="panorama_variacao_anual_municipios.png")

        with st.expander("Ver dados detalhados da variação anual", expanded=False):
            detalhe_var = (
                var_ano.loc[var_ano["variacao_pct"].notna(), [
                    "municipio", "transicao", "ano_anterior",
                    "quantidade_anterior", "ano", "quantidade",
                    "variacao_pct",
                ]]
                .sort_values(["municipio", "ano"])
            )
            export_table(detalhe_var, "siscan_variacao_anual_municipios.csv")

    detail = df[["municipio", "ano", "mes", "quantidade"]].copy()
    detail["mes"] = detail["mes"].astype(int).map({
        i+1: month for i, month in enumerate(
            ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    })
    detail = detail.rename(columns={
        "municipio":"Município", "ano":"Ano", "mes":"Mês", "quantidade":"Exames registrados"
    })
    with st.expander("Ver dados detalhados de exames registrados", expanded=False):
        display_table(detail, integer_columns=['Ano', 'Exames registrados'])
        st.download_button(
            "⬇️ Exportar dados filtrados (CSV)",
            detail.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name="siscan_panorama.csv",
            mime="text/csv",
        )
    st.caption("**Como interpretar:** maior volume não significa necessariamente maior cobertura "
               "populacional ou melhor desempenho. A participação municipal usa como denominador "
               "o total de exames dos municípios selecionados.")
