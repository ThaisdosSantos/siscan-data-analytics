import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,ORANGE,OCEAN,SKY,NAVY
from utils.data_loader import filtered,require
st.set_page_config(page_title="Outubro Rosa | SISCAN",layout="wide")
apply_custom_css()
st.title("02 · Outubro Rosa")
st.caption("Análise descritiva da variação de exames em relação a setembro; não demonstra causalidade atribuível à campanha.")
df=filtered("outubro")
if require(df,["ano","mes","municipio","exames_mes","exames_referencia_setembro"]):
    octdf=df[df.mes==10].copy()
    # A referência de setembro é repetida por linha de outubro/novembro/dezembro: contar uma só vez.
    sept=octdf["exames_referencia_setembro"].sum(min_count=1)
    octval=octdf["exames_mes"].sum(min_count=1)
    metric_row([("Exames em setembro",fmt_num(sept) if pd.notna(sept) else "N/D"),
                ("Exames em outubro",fmt_num(octval) if pd.notna(octval) else "N/D"),
                ("Variação outubro/setembro",fmt_pct(pct(octval,sept)))])
    plot=df.groupby(["ano","mes"],as_index=False).exames_mes.sum(min_count=1)
    ref=octdf.groupby("ano",as_index=False).exames_referencia_setembro.sum(min_count=1)
    ref["mes"]=9
    ref=ref.rename(columns={"exames_referencia_setembro":"exames_mes"})
    plot=pd.concat([plot,ref],ignore_index=True)
    names={9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
    plot["periodo"]=plot.mes.map(names)
    fig=px.bar(plot,x="ano",y="exames_mes",color="periodo",barmode="group",
               color_discrete_map={"Setembro":SKY,"Outubro":ORANGE,"Novembro":OCEAN,"Dezembro":NAVY},
               category_orders={"periodo":list(names.values())},
               labels={"ano":"Ano","exames_mes":"Exames","periodo":"Mês"},title="Comparação setembro a dezembro")
    fig.update_xaxes(type="category")
    display_chart(fig)
    city=octdf.groupby("municipio",as_index=False)[["exames_mes","exames_referencia_setembro"]].sum(min_count=1)
    city["variacao_pct"]=(city.exames_mes/city.exames_referencia_setembro-1)*100
    city.loc[city.exames_referencia_setembro<=0,"variacao_pct"]=float("nan")
    if city.variacao_pct.notna().any():
        fig=px.bar(city.sort_values("variacao_pct"),y="municipio",x="variacao_pct",orientation="h",
                   color_discrete_sequence=[ORANGE],labels={"municipio":"Município","variacao_pct":"Variação (%)"},
                   title="Variação outubro × setembro por município (agregada no período)")
        display_chart(fig)
    export_table(city,"siscan_outubro_rosa.csv")
    st.caption("Comparações agregadas são calculadas com somas dos volumes, não com a média de percentuais municipais.")
