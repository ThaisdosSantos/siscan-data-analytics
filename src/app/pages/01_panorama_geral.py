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
    col_total,col_media,col_municipio=st.columns(3)
    with col_total:
        st.metric("Total de exames",fmt_num(total))
    with col_media:
        st.metric("Média por mês com registro",fmt_num(monthly.quantidade.mean()))
    with col_municipio:
        st.metric("Maior participação nos exames",fmt_pct(pct(top.quantidade,total)) if top is not None else "N/D")
        if top is not None:
            st.caption(f"Município: **{top.municipio}**")
    st.info("Auditoria dos dados: agosto/2022 ausente na Gold. O intervalo é exibido como lacuna, não como zero.")
    start_year = int(df.ano.min())
    end_year = int(df.ano.max())
    complete = pd.date_range(f"{start_year}-01-01",f"{end_year}-12-01",freq="MS")
    series = monthly.set_index("data").reindex(complete)
    left,right=st.columns([3,2],gap="medium")
    with left:
        st.markdown("#### Evolução mensal")
        fig=px.line(x=series.index,y=series.quantidade,markers=True,
                    labels={"x":"Competência","y":"Exames"},
                    color_discrete_sequence=[OCEAN])
        fig.update_traces(connectgaps=False,hovertemplate="%{x|%m/%Y}<br>%{y:,.0f} exames<extra></extra>")
        display_chart(fig)
    with right:
        st.markdown("#### Volume por município")
        fig=px.bar(bycity.sort_values("quantidade"),x="quantidade",y="municipio",orientation="h",
                   color_discrete_sequence=[OCEAN],labels={"quantidade":"Exames","municipio":""})
        fig.update_traces(hovertemplate="%{y}<br>%{x:,.0f} exames<extra></extra>")
        display_chart(fig)
    st.subheader("Dados detalhados")
    export_table(df[["municipio","ano","mes","quantidade"]].sort_values(["ano","mes","municipio"]),
                 "siscan_panorama.csv")
    st.caption("Participação calculada sobre os exames dos municípios selecionados. Exames não equivalem a pessoas únicas.")
