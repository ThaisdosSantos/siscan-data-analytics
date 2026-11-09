import copy
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,page_header,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,format_percent_chart,OCEAN,ORANGE,SKY
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered,require,sidebar_filters
st.set_page_config(page_title="Adequabilidade | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
page_header(
    "Qualidade da amostra",
    "Adequabilidade das amostras",
    "Apresenta a distribuição das amostras citopatológicas segundo sua "
    "adequabilidade, a evolução anual das amostras insatisfatórias e rejeitadas "
    "e a comparação dos resultados entre os municípios selecionados.",
)
df=filtered("adequabilidade")
if require(df,["municipio","ano","categoria_adequabilidade","quantidade_amostras"]):
    def cat(s):
        s=str(s).lower()
        if "insatisfat" in s:return "Insatisfatória"
        if "rejeitad" in s:return "Rejeitada"
        if "satisfat" in s:return "Satisfatória"
        return "Outra"
    df["categoria"]=df.categoria_adequabilidade.map(cat)
    g=df.groupby("categoria").quantidade_amostras.sum(min_count=1)
    tot=g.sum(min_count=1)
    ruim=g.get("Insatisfatória",0)+g.get("Rejeitada",0)
    st.markdown(
        "Os indicadores resumem a **quantidade de amostras registradas** e a "
        "**proporção de amostras satisfatórias, insatisfatórias ou rejeitadas** "
        "no recorte selecionado."
    )
    with st.expander("ℹ️ Como interpretar os indicadores de adequabilidade", expanded=False):
        st.markdown(
            "**Amostras avaliadas:** soma das quantidades registradas nas categorias "
            "de adequabilidade disponíveis. **Satisfatórias (%):** amostras "
            "classificadas como satisfatórias divididas pelo total. "
            "**Insatisfatórias e rejeitadas (%):** soma dessas duas categorias "
            "dividida pelo mesmo total. "
            "Uma amostra **insatisfatória** não oferece qualidade adequada "
            "para interpretação citopatológica; uma amostra **rejeitada** "
            "não é aceita para avaliação. Essas categorias não devem ser "
            "interpretadas como resultados citológicos alterados."
        )
    metric_row([("Amostras avaliadas",fmt_num(tot)),("Satisfatórias",fmt_pct(pct(g.get("Satisfatória",0),tot))),
                ("Insatisfatórias e rejeitadas",fmt_pct(pct(ruim,tot)))])
    series=df.groupby(["ano","categoria"],as_index=False).quantidade_amostras.sum(min_count=1)
    series=series[series.categoria.isin(["Insatisfatória","Rejeitada"])]
    if not series.empty:
        st.subheader("Evolução anual de amostras insatisfatórias e rejeitadas")
        st.markdown(
            "Mostra **quantas amostras insatisfatórias e rejeitadas foram registradas "
            "em cada ano**, permitindo acompanhar mudanças no volume dessas categorias."
        )
        with st.expander("ℹ️ Como interpretar a evolução anual da adequabilidade", expanded=False):
            st.markdown(
                "**Eixo horizontal:** anos selecionados. **Eixo vertical:** "
                "quantidade de amostras. A linha **laranja** representa "
                "amostras insatisfatórias e a linha **azul-claro**, rejeitadas. "
                "Cada ponto mostra o total registrado naquela categoria e ano. "
                "Uma linha ascendente indica aumento do **número absoluto** "
                "de amostras, não necessariamente piora proporcional da qualidade: "
                "o volume total de exames também pode ter mudado. "
                "Os resultados não indicam quantas mulheres distintas foram atendidas."
            )
        fig=px.line(
            series, x="ano", y="quantidade_amostras", color="categoria", markers=True,
            color_discrete_map={"Insatisfatória":ORANGE,"Rejeitada":SKY},
            title="Quantidade anual de amostras por categoria",
            labels={"quantidade_amostras":"Quantidade de amostras","ano":"Ano","categoria":""},
        )
        fig.update_xaxes(type="category")
        fig.update_yaxes(tickformat=",d", rangemode="tozero")
        fig.update_traces(
            hovertemplate="Ano: %{x}<br>Quantidade: %{y:,.0f} amostras<extra>%{fullData.name}</extra>"
        )
        # Na imagem PNG, mostra explicitamente os valores dos pontos.
        # Mantém a versão do site sem rótulos, com tooltip interativo.
        export_fig = copy.deepcopy(fig)
        for trace in export_fig.data:
            values = (
                series.loc[series["categoria"] == trace.name]
                .sort_values("ano")["quantidade_amostras"]
            )
            trace.update(
                mode="lines+markers+text",
                text=[f"{int(value):,}" if pd.notna(value) else "—" for value in values],
                textposition="top center" if trace.name == "Insatisfatória" else "bottom center",
                textfont=dict(size=16, color="#1A3B5C"),
            )
        export_fig.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            margin=dict(l=100, r=185, t=95, b=85),
        )
        export_fig.update_yaxes(rangemode="tozero")
        chart_with_right_click_download(
            fig,
            filename="adequabilidade_quantidade_anual_categorias.png",
            height=430,
            export_fig=export_fig,
        )
    bycity=df.groupby(["municipio","categoria"],as_index=False).quantidade_amostras.sum(min_count=1)
    pivot=bycity.pivot(index="municipio",columns="categoria",values="quantidade_amostras").fillna(0)
    for name in ["Satisfatória","Insatisfatória","Rejeitada"]:
        if name not in pivot:pivot[name]=0
    pivot["total"]=pivot[["Satisfatória","Insatisfatória","Rejeitada"]].sum(axis=1)
    pivot["taxa_insatisfatorias_pct"]=pivot["Insatisfatória"]/pivot.total.replace(0,float("nan"))*100
    pivot["taxa_rejeitadas_pct"]=pivot["Rejeitada"]/pivot.total.replace(0,float("nan"))*100
    st.subheader("Adequabilidade das amostras por município")
    st.markdown(
        "Compara a **quantidade e a proporção de amostras insatisfatórias e "
        "rejeitadas** entre os municípios do período selecionado."
    )
    with st.expander("ℹ️ Como interpretar a tabela municipal", expanded=False):
        st.markdown(
            "**Satisfatória, insatisfatória e rejeitada:** contagens de amostras "
            "em cada categoria. **Total:** soma dessas categorias no município. "
            "**Taxa de insatisfatórias (%):** quantidade insatisfatória ÷ total × 100. "
            "**Taxa de rejeitadas (%):** quantidade rejeitada ÷ total × 100. "
            "O **destaque exploratório** sinaliza municípios em que a soma das "
            "duas taxas ultrapassa o limiar escolhido; ele **não representa "
            "um parâmetro oficial de qualidade**. A última linha totaliza as "
            "quantidades e recalcula as taxas sobre o total selecionado, "
            "sem somar percentuais municipais. "
            "As taxas descrevem adequabilidade da amostra, não alterações citológicas."
        )
    limiar=st.number_input("Limiar exploratório para destaque (%); não é um limite oficial",min_value=0.0,max_value=100.0,value=5.0,step=0.5)
    pivot["alerta_exploratorio"]=pivot.taxa_insatisfatorias_pct.add(pivot.taxa_rejeitadas_pct).gt(limiar)
    st.caption("Limiar configurável, exclusivamente visual; não representa tolerância ministerial.")
    # Linha consolidada ao final: soma contagens e recalcula taxas pelo total,
    # evitando a soma incorreta de percentuais entre municípios.
    table = pivot.reset_index()
    columns_to_sum = ["Insatisfatória", "Rejeitada", "Satisfatória", "total"]
    totals = table[columns_to_sum].sum()
    denominator = totals["total"]
    total_row = {
        "municipio": "Total",
        **{column: totals[column] for column in columns_to_sum},
        "taxa_insatisfatorias_pct": (
            totals["Insatisfatória"] / denominator * 100 if denominator > 0 else float("nan")
        ),
        "taxa_rejeitadas_pct": (
            totals["Rejeitada"] / denominator * 100 if denominator > 0 else float("nan")
        ),
        "alerta_exploratorio": "—",
    }
    table = pd.concat([table, pd.DataFrame([total_row])], ignore_index=True)
    st.markdown(
        """
        <style>
        .pet-table tbody tr:last-child {
            background: #e7f1f8 !important;
            font-weight: 750;
            border-top: 2px solid #006C9A;
        }
        .pet-table tbody tr:last-child td {
            font-weight: 750;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    export_table(table, "siscan_adequabilidade.csv")
