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
# Mesmo padrão de hierarquia e espaçamento das páginas Faixa Etária e Panorama Geral.
# Impede que o primeiro título fique sobreposto ao cabeçalho azul.
st.markdown(
    """
    <style>
    .pet-hero {margin-bottom:0 !important;}
    .adequabilidade-section-title {
      margin:30px 0 17px; padding:9px 0 12px;
      border-bottom:2px solid #D8E5EF;
      font:750 clamp(21px,2vw,26px)/1.35 Manrope,Arial,sans-serif;
      color:#1A3B5C;
    }
    .adequabilidade-section-title .adequabilidade-section-index {
      color:#006C9A; margin-right:10px;
    }
    @media(max-width:768px) {
      .adequabilidade-section-title {margin-top:23px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
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
        '<h2 class="adequabilidade-section-title">'
        '<span class="adequabilidade-section-index">01</span>'
        'Perfil de adequabilidade das amostras</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Os indicadores resumem a **quantidade de amostras registradas** e a "
        "**proporção de amostras satisfatórias, insatisfatórias ou rejeitadas** "
        "no recorte selecionado."
    )
    metric_row([("Amostras avaliadas",fmt_num(tot)),("Satisfatórias",fmt_pct(pct(g.get("Satisfatória",0),tot))),
                ("Insatisfatórias e rejeitadas",fmt_pct(pct(ruim,tot)))])

    # As definições ficam disponíveis sob demanda, como nos demais gráficos.
    with st.expander("ℹ️ Entenda as categorias de adequabilidade", expanded=False):
        st.markdown(
            """
        <style>
        .pet-adequacy-guide {
            margin:3px 0 0; padding:0; border:0;
            background:transparent; color:#1A3B5C;
            font-family:Manrope,Arial,sans-serif;
        }
        .pet-adequacy-guide-grid {
            display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px;
        }
        .pet-adequacy-guide-item {
            background:#FFFFFF; border:1px solid #E2EAF0;
            border-radius:9px; padding:14px 15px;
            line-height:1.55; font-size:.88rem;
        }
        .pet-adequacy-guide-item strong {display:block;margin-bottom:6px;font-size:.95rem;}
        .pet-adequacy-guide-item p {margin:0;}
        .pet-adequacy-guide-foot {
            margin:14px 0 0;font-size:.82rem;line-height:1.5;color:#334E68;
        }
        @media(max-width:800px){
            .pet-adequacy-guide-grid {grid-template-columns:1fr;}
            .pet-adequacy-guide {padding:15px;}
        }
        </style>
        <section class="pet-adequacy-guide" aria-label="Definições de adequabilidade">
          <div class="pet-adequacy-guide-grid">
            <div class="pet-adequacy-guide-item">
              <strong>✅ Satisfatória</strong>
              <p>O material permite a análise microscópica e a emissão de
              resultado citopatológico. Isso não significa, por si só,
              ausência de alterações nas células.</p>
            </div>
            <div class="pet-adequacy-guide-item">
              <strong>⚠️ Insatisfatória</strong>
              <p>O material foi recebido, mas não permite uma avaliação
              confiável, por exemplo, por ter poucas células ou excesso
              de sangue que prejudica a leitura.</p>
            </div>
            <div class="pet-adequacy-guide-item">
              <strong>❌ Rejeitada</strong>
              <p>A amostra não pode ser aceita para análise, por exemplo,
              devido a problemas de identificação, informações incompatíveis
              ou lâmina quebrada.</p>
            </div>
          </div>
          <p class="pet-adequacy-guide-foot"><strong>Importante:</strong>
          insatisfatória e rejeitada não são diagnósticos de câncer nem
          resultados citológicos alterados; indicam que não foi possível
          realizar uma avaliação adequada do material.
          <br><strong>Referência:</strong> INCA/Ministério da Saúde —
          Nomenclatura Brasileira para Laudos Citopatológicos Cervicais.</p>
        </section>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<h2 class="adequabilidade-section-title">'
        '<span class="adequabilidade-section-index">02</span>'
        'Evolução anual da adequabilidade</h2>',
        unsafe_allow_html=True,
    )
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
    st.markdown(
        '<h2 class="adequabilidade-section-title">'
        '<span class="adequabilidade-section-index">03</span>'
        'Comparação municipal da adequabilidade</h2>',
        unsafe_allow_html=True,
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
            "A última linha totaliza as quantidades e recalcula as taxas "
            "sobre o total selecionado, "
            "sem somar percentuais municipais. "
            "As taxas descrevem adequabilidade da amostra, não alterações citológicas."
        )
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
