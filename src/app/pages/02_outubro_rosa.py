"""Comparação descritiva Setembro–Outubro, sem inferência causal."""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css, page_header, style_chart, display_table, fmt_num, fmt_pct, ORANGE, OCEAN, SKY, NAVY
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, require, sidebar_filters, years_label

st.set_page_config(page_title="Outubro Rosa | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
page_header("Campanha · Outubro Rosa", "Outubro em destaque: o que muda nos registros?")
st.caption(
    "Comparação descritiva dos exames registrados. Novembro e dezembro mostram o "
    "comportamento após outubro; diferenças mensais não comprovam efeito causal da campanha."
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
            f"(**{formatted_variation}**). A comparação não permite atribuir a mudança à campanha."
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
    chart_with_right_click_download(fig, filename="outubro_rosa_setembro_dezembro.png", height=fig.layout.height)

    city = octdf.groupby("municipio", as_index=False)[
        ["exames_mes", "exames_referencia_setembro"]
    ].sum(min_count=1)
    city["diferenca_exames"] = city["exames_mes"] - city["exames_referencia_setembro"]
    city["variacao_pct"] = (
        city["diferenca_exames"] /
        city["exames_referencia_setembro"].where(city["exames_referencia_setembro"] > 0)
        * 100
    )
    plot_city = city.dropna(subset=["variacao_pct"]).sort_values("variacao_pct")
    if not plot_city.empty:
        plot_city = plot_city.copy()
        plot_city["direcao"] = plot_city["variacao_pct"].map(
            lambda value: "Redução" if value < 0 else "Aumento ou estabilidade"
        )
        fig = px.bar(
            plot_city, y="municipio", x="variacao_pct", orientation="h",
            color="direcao",
            color_discrete_map={"Redução":NAVY, "Aumento ou estabilidade":ORANGE},
            custom_data=["exames_referencia_setembro", "exames_mes", "diferenca_exames"],
            labels={"municipio":"Município","variacao_pct":"Variação (%)"},
            title=f"Variação outubro × setembro por município · {period}"
        )
        fig.update_traces(
            hovertemplate=(
                "%{y}<br>Variação: %{x:+.2f}%"
                "<br>Setembro: %{customdata[0]:,.0f} exames"
                "<br>Outubro: %{customdata[1]:,.0f} exames"
                "<br>Diferença: %{customdata[2]:+.0f} exames<extra></extra>"
            )
        )
        fig.update_xaxes(tickformat=".2f", ticksuffix="%")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_chart(fig), use_container_width=True)
    st.caption(
        "Percentuais calculados sobre bases pequenas podem ser elevados mesmo "
        "quando a diferença absoluta é pequena. Não representam, por si só, "
        "maior efetividade da campanha."
    )

    table = city.rename(columns={
        "municipio":"Município",
        "exames_referencia_setembro":"Exames em setembro",
        "exames_mes":"Exames em outubro",
        "diferenca_exames":"Diferença (exames)",
        "variacao_pct":"Variação (%)"
    })
    st.markdown(f"#### Dados municipais · {len(table)} municípios")
    display_table(table, percent_columns=["Variação (%)"],
                  integer_columns=["Exames em setembro", "Exames em outubro", "Diferença (exames)"])
    st.download_button(
        "⬇️ Exportar CSV", table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="siscan_outubro_rosa.csv", mime="text/csv"
    )
