"""Comparação descritiva Setembro–Outubro, sem inferência causal."""
import copy
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
            f"(**{formatted_variation}**)."
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
            color_discrete_map={"Redução":NAVY, "Aumento ou estabilidade":ORANGE},
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
        fig.update_xaxes(tickformat=".2f", ticksuffix="%")
        fig.update_layout(showlegend=False)
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
