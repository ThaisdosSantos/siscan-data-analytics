import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,OCEAN
from utils.data_loader import filtered,require,sidebar_filters
st.set_page_config(page_title="Panorama | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
st.title("01 · Panorama temporal e territorial")
df=filtered("temporal")
if require(df,["municipio","ano","mes","quantidade"]):
    total=df.quantidade.sum(min_count=1)
    monthly=df.groupby(["ano","mes"],as_index=False).quantidade.sum(min_count=1).sort_values(["ano","mes"])
    monthly["data"]=pd.to_datetime(dict(year=monthly.ano,month=monthly.mes,day=1))
    bycity=df.groupby("municipio",as_index=False).quantidade.sum(min_count=1).sort_values("quantidade",ascending=False)
    top=bycity.iloc[0] if not bycity.empty else None
    metric_row([("Total de exames",fmt_num(total)),("Média por mês com registro",fmt_num(monthly.quantidade.mean())),
                ("Município com maior participação",f"{top.municipio} · {fmt_pct(pct(top.quantidade,total))}" if top is not None else "N/D")])
    fig=px.line(monthly,x="data",y="quantidade",markers=True,color_discrete_sequence=[OCEAN],
                labels={"data":"Competência","quantidade":"Exames"},title="Evolução mensal")
    display_chart(fig)
    fig=px.bar(bycity.sort_values("quantidade"),x="quantidade",y="municipio",orientation="h",
               color_discrete_sequence=[OCEAN],labels={"quantidade":"Exames","municipio":"Município"},
               title="Volume de exames por município")
    display_chart(fig)
    st.subheader("Dados detalhados")
    export_table(df[["municipio","ano","mes","quantidade"]].sort_values(["ano","mes","municipio"]),
                 "siscan_panorama.csv")
    st.caption("Participação calculada sobre os exames dos municípios selecionados. Exames não equivalem a pessoas únicas.")
