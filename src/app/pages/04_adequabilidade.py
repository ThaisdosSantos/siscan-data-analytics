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
page_header("Qualidade da amostra", "Adequabilidade das amostras")
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
    metric_row([("Amostras avaliadas",fmt_num(tot)),("Satisfatórias",fmt_pct(pct(g.get("Satisfatória",0),tot))),
                ("Insatisfatórias e rejeitadas",fmt_pct(pct(ruim,tot)))])
    series=df.groupby(["ano","categoria"],as_index=False).quantidade_amostras.sum(min_count=1)
    series=series[series.categoria.isin(["Insatisfatória","Rejeitada"])]
    if not series.empty:
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
