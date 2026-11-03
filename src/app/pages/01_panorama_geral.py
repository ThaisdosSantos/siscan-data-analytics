"""Panorama territorial e temporal de exames citopatológicos registrados."""
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.theme import apply_custom_css, page_header, display_chart, display_table, fmt_num, fmt_pct, pct, OCEAN
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
                   f"Sem dados em **{missing_label}**. A ausência não foi substituída por zero.")
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
    display_chart(fig)

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
    display_chart(fig)

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
        order = st.selectbox(
            "Ordenar gráficos dos municípios por",
            ["Ordem alfabética (A–Z)", "Maior para menor número de exames"],
            key="sort_facetas_panorama",
        )
        municipalities = sorted(annual["municipio"].unique())
        if order == "Maior para menor número de exames":
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
            matches=None, showticklabels=True, type="category",
            categoryorder="array",
            categoryarray=[str(year) for year in years_axis],
        )
        fig.update_yaxes(
            matches=None, showticklabels=True, rangemode="tozero",
            tickformat=",d", gridcolor="#E9EDF1", zeroline=False,
        )
        fig.update_layout(
            height=max(480, 285 * ((len(municipalities) + 2) // 3)),
            showlegend=False,
            margin=dict(l=25, r=15, t=55, b=35),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            font=dict(color="#1A3B5C", size=11),
        )
        st.plotly_chart(
            fig, use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )

    st.subheader("Dados detalhados")
    detail = df[["municipio", "ano", "mes", "quantidade"]].copy()
    detail["mes"] = detail["mes"].astype(int).map({
        i+1: month for i, month in enumerate(
            ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
    })
    detail = detail.rename(columns={
        "municipio":"Município", "ano":"Ano", "mes":"Mês", "quantidade":"Exames registrados"
    })
    display_table(detail, integer_columns=['Ano', 'Exames registrados'])
    st.download_button("⬇️ Exportar dados filtrados (CSV)",
                       detail.to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name="siscan_panorama.csv", mime="text/csv")
    st.caption("**Como interpretar:** maior volume não significa necessariamente maior cobertura "
               "populacional ou melhor desempenho. A participação municipal usa como denominador "
               "o total de exames dos municípios selecionados.")
