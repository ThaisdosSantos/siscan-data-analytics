import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_custom_css,page_header,display_chart,metric_row,export_table,fmt_num,fmt_pct,pct,format_percent_chart,OCEAN
from utils.data_loader import filtered,require,sidebar_filters
st.set_page_config(page_title="Exames alterados | SISCAN",layout="wide")
apply_custom_css()
sidebar_filters()
page_header("Resultados", "Exames citopatológicos alterados")
st.warning("Limitação metodológica: o denominador Gold é o total de exames por faixa etária, sem exclusão verificável de amostras rejeitadas/insatisfatórias. As proporções abaixo são estimativas operacionais, não taxas clínicas validadas.")
df=filtered("alterados")
# Alinhamento metodológico (31/out/2026): 'Ignorado' e 'Até 9 anos' têm bases ínfimas
# (0 alterados sobre ~1-2 exames) e não compõem grupos da diretriz de rastreio.
# Excluídas das proporções (barra e matriz territorial); os dados permanecem íntegros
# na Gold e nos contadores globais. Mesma regra aplicada no dashboard AI/BI.
df=df[~df["faixa_etaria"].isin(["Ignorado","Até 9 anos"])]
if require(df,["municipio","faixa_etaria","quantidade_alterados","total_exames_validos"]):
    num=df.quantidade_alterados.sum(min_count=1)
    den=df.total_exames_validos.sum(min_count=1)
    metric_row([("Exames alterados",fmt_num(num)),("Proporção operacional",fmt_pct(pct(num,den))),
                ("Exames no denominador disponível",fmt_num(den) if pd.notna(den) else "N/D")])
    byage=df.groupby("faixa_etaria",as_index=False)[["quantidade_alterados","total_exames_validos"]].sum(min_count=1)
    byage["taxa"]=byage.quantidade_alterados.div(byage.total_exames_validos.where(byage.total_exames_validos>0)).mul(100)
    fig=px.bar(byage,x="faixa_etaria",y="taxa",color_discrete_sequence=[OCEAN],
               labels={"faixa_etaria":"Faixa etária","taxa":"Proporção (%)"},
               title="Exames alterados por faixa etária")
    fig.update_xaxes(tickangle=-45)
    display_chart(format_percent_chart(fig))
    matrix=df.groupby(["municipio","faixa_etaria"],as_index=False)[["quantidade_alterados","total_exames_validos"]].sum(min_count=1)
    matrix["taxa"]=matrix.quantidade_alterados.div(matrix.total_exames_validos.where(matrix.total_exames_validos>0)).mul(100)
    heat=matrix.pivot(index="municipio",columns="faixa_etaria",values="taxa")
    if not heat.empty:
        fig=px.imshow(heat,aspect="auto",color_continuous_scale="Blues",
                      labels={"x":"Faixa etária","y":"Município","color":"%"},
                      title="Matriz territorial de proporção operacional")
        fig.update_traces(hovertemplate="Faixa etária: %{x}<br>Município: %{y}<br>Proporção: %{z:.2f}%<extra></extra>")
        fig.update_coloraxes(colorbar_tickformat=".2f", colorbar_ticksuffix="%")
        display_chart(fig)
    export_table(matrix,"siscan_exames_alterados.csv")
