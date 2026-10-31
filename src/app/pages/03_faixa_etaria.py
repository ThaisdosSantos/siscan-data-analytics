"""Distribuição descritiva dos exames segundo grupos etários da Gold."""
import pandas as pd
import plotly.express as px
import streamlit as st
from utils.theme import apply_custom_css, display_chart, fmt_num, fmt_pct, pct, OCEAN, SKY, ORANGE
from utils.data_loader import filtered, require, sidebar_filters, MUNICIPIOS

st.set_page_config(page_title="Faixa etária | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
st.title("03 · Distribuição dos exames por faixa etária")
st.caption("Composição etária dos exames registrados na 10ª Coordenadoria Regional de Saúde do RS.")
df = filtered("etaria")
if require(df, ["municipio", "grupo_etario_diretriz", "quantidade_exames"]):
    year = st.session_state.get("year_preference", "Todos")
    period = "2020–2025" if year == "Todos" else str(year)
    selected = st.session_state.get("city_preference", list(MUNICIPIOS.values()))

    # Não atribuir registros de categoria desconhecida a alguma faixa etária conhecida.
    def classify(value):
        label = str(value).casefold().strip()
        if "25 a 64" in label or "25–64" in label or "25-64" in label:
            return "25–64 anos"
        if "<25" in label or "menor" in label or "abaixo de 25" in label:
            return "Menores de 25 anos"
        if "65 anos" in label or ">=65" in label or "≥65" in label:
            return "65 anos ou mais"
        return "Não classificado"

    order = ["25–64 anos", "Menores de 25 anos", "65 anos ou mais", "Não classificado"]
    colors = {"25–64 anos":OCEAN, "Menores de 25 anos":SKY,
              "65 anos ou mais":ORANGE, "Não classificado":"#87929E"}
    data = df.copy()
    data["grupo"] = data["grupo_etario_diretriz"].map(classify)
    data["quantidade_exames"] = pd.to_numeric(data["quantidade_exames"], errors="coerce")
    data = data[data["quantidade_exames"].notna()]
    sums = data.groupby("grupo")["quantidade_exames"].sum().reindex(order, fill_value=0)
    total = sums.sum()
    st.caption(f"**Recorte ativo:** {period} · {len(selected)} municípios selecionados · "
               f"**{fmt_num(total)} exames** classificados ou não classificados nesta análise.")

    if sums["Não classificado"] > 0:
        st.warning(f"Há **{fmt_num(sums['Não classificado'])} exames** em categorias etárias "
                   "não reconhecidas. Eles permanecem no denominador e são exibidos separadamente.")

    st.caption("**Os percentuais representam a proporção de exames neste conjunto, "
               "não a proporção de mulheres atendidas nem a cobertura populacional.**")

    cols = st.columns(3)
    for col, label in zip(cols, order[:3]):
        with col:
            st.metric(f"Exames: {label}", fmt_pct(pct(sums[label], total)))
            st.caption(f"{fmt_num(sums[label])} de {fmt_num(total)} exames analisados")

    with st.expander("Como são calculados os percentuais?", expanded=False):
        st.write("Percentual da faixa = número de exames classificados na faixa ÷ "
                 "total de exames presentes nesta análise × 100.")
        st.write("Os grupos são 25–64 anos, menores de 25 e 65 anos ou mais, "
                 "conforme os rótulos da Gold. Categorias não reconhecidas são "
                 "mantidas em 'Não classificado', sem serem redistribuídas.")
        st.write("Os dados são agregados por exames, não por pessoas únicas. "
                 "Essa classificação não determina adequação individual do rastreamento.")
        st.write("O universo desta tabela Gold pode diferir do total de outras páginas; "
                 "não se pressupõe igualdade entre tabelas distintas.")

    agg = (data.groupby(["municipio", "grupo"], as_index=False)["quantidade_exames"].sum())
    base = agg.groupby("municipio")["quantidade_exames"].transform("sum")
    agg["percentual"] = 100 * agg["quantidade_exames"] / base.where(base.gt(0))
    sort_by = st.selectbox("Ordenar municípios por", ["Nome (A–Z)", "Participação de 25–64 anos (%)"],
                           help="Ordenação descritiva, não é classificação de desempenho.")
    if sort_by == "Nome (A–Z)":
        cities = sorted(agg.municipio.unique())
    else:
        ranked = agg[agg.grupo == "25–64 anos"].set_index("municipio")["percentual"]
        cities = sorted(agg.municipio.unique(), key=lambda city: (-ranked.get(city, 0), city))

    st.subheader("Composição dos exames por município")
    fig = px.bar(agg, x="percentual", y="municipio", orientation="h", color="grupo",
                 category_orders={"grupo":order, "municipio":list(reversed(cities))},
                 color_discrete_map=colors, custom_data=["quantidade_exames"],
                 labels={"municipio":"Município", "percentual":"Participação (%)", "grupo":"Faixa etária"})
    fig.update_layout(barmode="stack", height=max(440, len(cities)*38+110), legend_title_text="")
    fig.update_xaxes(range=[0,100], ticksuffix="%")
    fig.update_traces(hovertemplate="%{y}<br>%{fullData.name}<br>"
                                  "%{x:.2f}% · %{customdata[0]:,.0f} exames<extra></extra>")
    display_chart(fig)
    st.caption("Cada barra corresponde a 100% dos exames da própria cidade; "
               "as barras não comparam volumes absolutos entre municípios.")

    if "ano" in data.columns and data.ano.nunique() > 1:
        st.subheader("Evolução anual da composição etária")
        annual = data.groupby(["ano", "grupo"], as_index=False)["quantidade_exames"].sum()
        base_annual = annual.groupby("ano")["quantidade_exames"].transform("sum")
        annual["percentual"] = annual.quantidade_exames / base_annual.where(base_annual.gt(0))*100
        fig = px.bar(annual, x="ano", y="percentual", color="grupo", barmode="stack",
                     category_orders={"grupo":order}, color_discrete_map=colors,
                     custom_data=["quantidade_exames"],
                     labels={"ano":"Ano", "percentual":"Participação (%)", "grupo":"Faixa etária"})
        fig.update_xaxes(type="category")
        fig.update_yaxes(range=[0,100], ticksuffix="%")
        fig.update_traces(hovertemplate="%{fullData.name}<br>%{y:.2f}%"
                                      "<br>%{customdata[0]:,.0f} exames<extra></extra>")
        display_chart(fig)
        st.caption("Variações anuais devem ser interpretadas considerando diferenças "
                   "na disponibilidade e classificação dos dados de cada ano.")

    st.subheader("Distribuição por município — percentual dentro de cada município")
    table = agg.rename(columns={"municipio":"Município", "grupo":"Faixa etária",
                                "quantidade_exames":"Exames registrados", "percentual":"Participação (%)"})
    table["Faixa etária"] = pd.Categorical(table["Faixa etária"], categories=order, ordered=True)
    table = table.sort_values(["Município", "Faixa etária"])
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={"Participação (%)":st.column_config.NumberColumn("Participação (%)",format="%.2f")})
    st.download_button("⬇️ Exportar dados filtrados (CSV)",
                       table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="siscan_faixa_etaria.csv", mime="text/csv")
