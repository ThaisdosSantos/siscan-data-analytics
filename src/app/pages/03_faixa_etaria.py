import streamlit as st
import plotly.express as px
from utils.theme import apply_custom_css,display_chart,metric_row,export_table,fmt_pct,pct,OCEAN,SKY,ORANGE
from utils.data_loader import filtered,require,sidebar_filters
st.set_page_config(page_title="Faixa etária | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
st.title("03 · Conformidade etária")
df=filtered("etaria")
if require(df,["municipio","grupo_etario_diretriz","quantidade_exames"]):
    groups=df.copy()
    def classify(s):
        s=str(s).lower()
        return "25–64 anos" if "25 a 64" in s else ("<25 anos" if "<25" in s else ("≥65 anos" if "65 anos" in s else "Outros"))
    groups["grupo"]=groups.grupo_etario_diretriz.map(classify)
    sums=groups.groupby("grupo").quantidade_exames.sum(min_count=1)
    total=sums.sum(min_count=1)
    metric_row([("População-alvo (25–64 anos)",fmt_pct(pct(sums.get("25–64 anos",0),total))),
                ("Menores de 25 anos",fmt_pct(pct(sums.get("<25 anos",0),total))),
                ("65 anos ou mais",fmt_pct(pct(sums.get("≥65 anos",0),total)))])
    agg=groups.groupby(["municipio","grupo"],as_index=False).quantidade_exames.sum(min_count=1)
    a,b=st.columns([1,2])
    with a:
        fig=px.pie(agg,names="grupo",values="quantidade_exames",hole=.6,
                   color="grupo",color_discrete_map={"25–64 anos":OCEAN,"<25 anos":SKY,"≥65 anos":ORANGE},
                   title="Distribuição dos exames")
        display_chart(fig)
    with b:
        fig=px.bar(agg,x="municipio",y="quantidade_exames",color="grupo",
                   color_discrete_map={"25–64 anos":OCEAN,"<25 anos":SKY,"≥65 anos":ORANGE},
                   labels={"municipio":"Município","quantidade_exames":"Percentual (%)"},
                   title="Composição etária por município")
        fig.update_layout(barnorm="percent")
        fig.update_xaxes(tickangle=-45)
        display_chart(fig)
    export_table(agg,"siscan_faixa_etaria.csv")
    st.caption("Grupos etários são classificações analíticas e não permitem diagnosticar inadequação individual do rastreio.")
