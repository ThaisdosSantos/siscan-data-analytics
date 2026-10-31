import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,page_header,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,format_percent_chart,OCEAN,ORANGE,SKY
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
    totals=series.groupby("ano").quantidade_amostras.transform("sum")
    series["taxa"]=series.quantidade_amostras.div(totals).mul(100).where(totals>0)
    series=series[series.categoria.isin(["Insatisfatória","Rejeitada"])]
    if not series.empty:
        fig=px.line(series,x="ano",y="taxa",color="categoria",markers=True,
                    color_discrete_map={"Insatisfatória":ORANGE,"Rejeitada":SKY},
                    title="Taxa anual por categoria",labels={"taxa":"Taxa (%)","ano":"Ano"})
        fig.update_xaxes(type="category")
        display_chart(format_percent_chart(fig))
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
    export_table(pivot.reset_index(),"siscan_adequabilidade.csv")
