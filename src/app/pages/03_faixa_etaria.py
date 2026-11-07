"""Conformidade etária (Q3): distribuição e composição por município."""
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.theme import (
    apply_custom_css, page_header, display_chart, export_table,
    fmt_num, fmt_pct, pct, style_chart, OCEAN, SKY, ORANGE, NAVY,
)
from utils.chart_download import chart_with_right_click_download
from utils.data_loader import filtered, sidebar_filters, require


def normalize(value):
    return unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower().strip()


def q3_group(label):
    """Mapeia somente grupos etários inequivocamente identificados na Q3."""
    text = normalize(label).replace("–", "-").replace("—", "-")
    if "25 a 64" in text or "25-64" in text or "populacao-alvo" in text:
        return "25–64 anos"
    if "<25" in text or "< 25" in text or "menores de 25" in text or "menor de 25" in text:
        return "<25 anos"
    if "65 anos" in text or ">=65" in text or "≥65" in text or "65 ou mais" in text:
        return "≥65 anos"
    return None


def safe_percent(numerator, denominator):
    return numerator.div(denominator.where(denominator.gt(0))).mul(100)


st.set_page_config(page_title="Faixa etária | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
page_header(
    "Faixa etária · Q3",
    "Conformidade etária",
    "Distribuição dos exames por grupos etários e comparação entre municípios.",
)

st.markdown("""
<style>
div[data-testid="stMetric"] {border-left:5px solid #006C9A;border-radius:12px;background:#fff;}
</style>
""", unsafe_allow_html=True)

df = filtered("etaria")
if not require(df, ["municipio", "grupo_etario_diretriz", "quantidade_exames"]):
    st.stop()

groups = df.copy()
groups["grupo"] = groups["grupo_etario_diretriz"].map(q3_group)
unknown = groups.loc[groups.grupo.isna(), "quantidade_exames"].sum()
groups = groups.loc[groups.grupo.notna()].copy()
if groups.empty:
    st.warning("Não foi possível identificar os grupos etários na tabela Gold da Q3.")
    st.stop()
if unknown:
    st.warning(f"Há {fmt_num(unknown)} exames em categorias etárias não classificáveis; esses registros não entram nos percentuais apresentados.")

sums = groups.groupby("grupo")["quantidade_exames"].sum()
total = sums.sum()
labels = ["25–64 anos", "<25 anos", "≥65 anos"]
titles = ["População-alvo (25–64 anos)", "Menores de 25 anos", "65 anos ou mais"]
descriptions = ["Dentro do grupo etário analisado", "Fora da faixa-alvo: <25 anos", "Fora da faixa-alvo: ≥65 anos"]
for col, label, title, desc in zip(st.columns(3), labels, titles, descriptions):
    with col:
        value = sums.get(label, 0)
        st.metric(title, fmt_pct(pct(value, total)), help=f"{fmt_num(value)} exames. {desc}")
        st.caption(f"{fmt_num(value)} exames · {desc}")

agg = groups.groupby(["municipio", "grupo"], as_index=False)["quantidade_exames"].sum()
total_city = agg.groupby("municipio")["quantidade_exames"].transform("sum")
agg["percentual"] = safe_percent(agg["quantidade_exames"], total_city)
a, b = st.columns([2, 3], gap="medium")

st.markdown("""
<style>
.st-key-age_donut_card {
  min-height:625px;
  box-sizing:border-box;
  background:#fff;
  border:1px solid #dce4eb;
  border-radius:14px;
  padding:16px 18px 22px;
  box-shadow:0 2px 8px rgba(26,59,92,.04);
}
.st-key-age_donut_card [data-testid="stPlotlyChart"] {
  border:0!important;box-shadow:none!important;padding:0!important;
  background:transparent!important;
}
.st-key-age_donut_card .age-legend {padding:0 4px 4px;}
.st-key-age_bar_card {margin-top:0;min-height:625px;box-sizing:border-box;background:#fff;border:1px solid #dce4eb;border-radius:14px;padding:16px 18px 22px;box-shadow:0 2px 8px rgba(26,59,92,.04);min-height:454px;}
.st-key-age_bar_card [data-testid="stPlotlyChart"] {border:0!important;box-shadow:none!important;padding:0!important;background:transparent!important;}
@media(max-width:900px) {
  .st-key-age_donut_card,.st-key-age_bar_card {min-height:0!important;padding:14px!important;}
  .st-key-age_bar_card {margin-top:0!important;}
  .age-legend-row {font-size:.8rem!important;}
}
</style>
""", unsafe_allow_html=True)
with a:
    with st.container(border=True, key="age_donut_card"):
        # Rosca e legenda conforme referência visual; valores são calculados da Gold.
        donut_order = ["25–64 anos", "≥65 anos", "<25 anos"]
        donut_colors = {"25–64 anos": "#0076A5", "≥65 anos": "#4A9FD8", "<25 anos": "#EE5325"}
        donut_values = [float(sums.get(group, 0)) for group in donut_order]
        target_percent = pct(sums.get("25–64 anos", 0), total)
        fig = px.pie(
            names=donut_order,
            values=donut_values,
            hole=0.66,
            color=donut_order,
            color_discrete_map=donut_colors,
        )
        fig.update_traces(
            sort=False,
            direction="clockwise",
            rotation=270,
            textinfo="none",
            marker=dict(line=dict(color="#FFFFFF", width=3)),
            hovertemplate="%{label}<br>%{value:,.0f} exames<br>%{percent:.2%}<extra></extra>",
        )
        fig.update_traces(domain=dict(x=[0.08, 0.92], y=[0.04, 0.96]))
        fig.update_layout(
            showlegend=False,
            height=320,
            margin=dict(t=6, b=6, l=6, r=6),
            annotations=[dict(
                text=(f"<span style='font-size:32px;color:#006C9A'>{target_percent:.0f}%</span>"
                      "<br><span style='font-size:11px;color:#7C8FA0'>na faixa-alvo</span>")
                if pd.notna(target_percent) else "N/D",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, align="center",
            )],
        )
        st.markdown('<div style="font-size:1.12rem;color:#1A3B5C;font-weight:700">Distribuição dos exames</div>'
                    '<div style="color:#7C8FA0;font-size:.77rem">Por grupo etário</div>', unsafe_allow_html=True)
        # A legenda HTML fica fora do Plotly e não é capturada no PNG.
        # Criamos uma cópia exclusiva para exportação com legenda incorporada.
        import copy
        styled_donut = style_chart(fig, height=320)
        export_donut = copy.deepcopy(styled_donut)
        export_donut.update_traces(
            domain=dict(x=[0.05, 0.70], y=[0.05, 0.95]),
            texttemplate="%{percent:.2%}",
            textposition="inside",
            insidetextfont=dict(color="#FFFFFF", size=15),
            showlegend=True,
        )
        export_donut.update_layout(
            title=dict(
                text="Distribuição dos exames por grupo etário",
                x=0.5, xanchor="center",
                y=0.975, yanchor="top",
                font=dict(family="Arial", size=24, color="#1A3B5C"),
            ),
            showlegend=True,
            legend=dict(
                title=dict(text="Faixa etária"),
                x=0.77, xanchor="left", y=0.5, yanchor="middle",
                orientation="v",
                font=dict(size=17, color="#1A3B5C"),
                bgcolor="rgba(255,255,255,0)",
                itemsizing="constant",
            ),
            annotations=[
                dict(
                    text=(
                        f"<span style='font-size:32px;color:#006C9A'>{target_percent:.0f}%</span>"
                        "<br><span style='font-size:12px;color:#7C8FA0'>na faixa-alvo</span>"
                    ) if pd.notna(target_percent) else "N/D",
                    x=0.375, y=0.5, xref="paper", yref="paper",
                    showarrow=False, align="center",
                )
            ],
            margin=dict(l=80, r=120, t=110, b=65),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
        )
        chart_with_right_click_download(
            styled_donut,
            filename="faixa_etaria_distribuicao.png",
            height=320,
            export_fig=export_donut,
        )
        legend_rows = []
        for group in donut_order:
            val = pct(sums.get(group, 0), total)
            formatted = fmt_pct(val)
            legend_rows.append(
                '<div class="age-legend-row"><span class="age-legend-dot" style="background:'
                + donut_colors[group] + '"></span><span class="age-legend-label">'
                + group + '</span><strong>' + formatted + '</strong></div>'
            )
        st.markdown(
            '<style>.age-legend-row{display:flex;align-items:center;gap:9px;'
            'color:#1A3B5C;font-size:.83rem;padding:5px 0}'
            '.age-legend-dot{height:10px;width:10px;border-radius:50%;flex:0 0 10px}'
            '.age-legend-label{flex:1}.age-legend-row strong{font-weight:750}</style>'
            + '<div class="age-legend">' + "".join(legend_rows) + '</div>',
            unsafe_allow_html=True,
        )
with b:
    with st.container(border=True, key="age_bar_card"):
        st.markdown(
            '<div style="font-size:1.12rem;color:#1A3B5C;font-weight:700">'
            'Composição etária por município</div>'
            '<div style="color:#7C8FA0;font-size:.77rem">Percentual (%)</div>',
            unsafe_allow_html=True,
        )
        # Barras horizontais empilhadas 100%, alinhadas à referência visual.
        bar_order = ["25–64 anos", "<25 anos", "≥65 anos"]
        st.markdown("""
        <style>
        .st-key-sort_composicao_etaria [data-testid="stSelectbox"] label p {
            color:#1A3B5C!important;font-size:.88rem!important;font-weight:700!important;
        }
        .st-key-sort_composicao_etaria [data-baseweb="select"] > div {
            background:#fff!important;border:1.5px solid #8FAFC5!important;
            border-radius:9px!important;min-height:43px!important;
        }
        .st-key-sort_composicao_etaria [data-baseweb="select"] > div:hover,
        .st-key-sort_composicao_etaria [data-baseweb="select"] > div:focus-within {
            border-color:#006C9A!important;
        }
        .st-key-sort_composicao_etaria [data-baseweb="select"] * {
            color:#1A3B5C!important;
        }
        </style>
        """, unsafe_allow_html=True)
        with st.container(key="sort_composicao_etaria"):
            sort_mode = st.selectbox(
                "Ordenar por",
                ["A–Z", "Maior para menor"],
                key="ordenacao_composicao_etaria",
                help="Maior para menor: percentual de exames na faixa-alvo (25–64 anos).",
            )
        cities_order = sorted(agg["municipio"].dropna().unique(), key=normalize)
        if sort_mode == "Maior para menor":
            target_shares = (
                agg.loc[agg["grupo"].eq("25–64 anos")]
                .set_index("municipio")["percentual"]
            )
            cities_order.sort(
                key=lambda city: (
                    -float(target_shares.loc[city])
                    if city in target_shares.index and pd.notna(target_shares.loc[city])
                    else float("inf"),
                    normalize(city),
                )
            )
        fig = px.bar(
            agg, x="percentual", y="municipio", color="grupo",
            orientation="h", barmode="stack",
            category_orders={"grupo": bar_order, "municipio": cities_order},
            color_discrete_map={"25–64 anos": OCEAN, "<25 anos": SKY, "≥65 anos": ORANGE},
            labels={"municipio": "", "percentual": "Participação (%)", "grupo": "Faixa etária"},
        )
        fig.update_traces(
            hovertemplate="%{y}<br>%{fullData.name}: %{x:.2f}%<extra></extra>"
        )
        fig.update_xaxes(range=[0, 103], tickmode="array", tickvals=[0, 25, 50, 75, 100],
                         ticktext=["0%", "25%", "50%", "75%", "100%"],
                         showgrid=True, gridcolor="#e9edf1", title=None)
        # Plotly Express já organiza as categorias horizontais de cima para baixo.
        # Inverter novamente o eixo fazia A–Z e Maior para menor aparecerem ao contrário.
        fig.update_yaxes(title=None, automargin=True,
                         tickfont=dict(size=12, color="#405a70"))
        fig.update_layout(
            margin=dict(l=12, r=8, t=8, b=10),
            legend=dict(orientation="h", yanchor="top", y=-0.12,
                        xanchor="center", x=0.5, title=None,
                        font=dict(size=12)),
            bargap=0.12,
        )
        # Exportação específica: rótulos centralizados nas barras com contraste
        # adaptado à cor de cada grupo. O gráfico interativo permanece intacto.
        import copy
        chart_height = max(480, 40 * len(cities_order) + 90)
        styled_fig = style_chart(fig, height=chart_height)
        export_fig = copy.deepcopy(styled_fig)
        text_colors = {
            "25–64 anos": "#FFFFFF",  # branco sobre azul oceano
            "<25 anos": "#143650",    # azul-marinho sobre azul-claro
            "≥65 anos": "#FFFFFF",    # branco sobre laranja
        }
        for trace in export_fig.data:
            trace.update(
                texttemplate="%{x:.2f}",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(
                    family="Arial", size=15,
                    color=text_colors.get(trace.name, "#143650"),
                ),
                cliponaxis=True,
            )
        export_fig.update_layout(
            title=dict(
                text="Composição etária por município",
                x=0.5, xanchor="center",
                font=dict(family="Arial", size=24, color="#1A3B5C"),
            ),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=190, r=65, t=100, b=110),
            uniformtext=dict(minsize=11, mode="show"),
        )
        chart_with_right_click_download(
            styled_fig,
            filename="faixa_etaria_composicao_municipios.png",
            height=chart_height,
            min_chart_width=650,
            export_fig=export_fig,
        )

# Evolução anual da população-alvo, aproveitando a granularidade
# município × ano × faixa etária da Gold Q3. Somar contagens, não percentuais.
st.markdown("### Evolução anual de exames na faixa etária de 25–64 anos por município")
st.markdown(
    '<p style="font-size:18px;line-height:1.55;color:#334E68;'
    'font-weight:400;margin:4px 0 18px 0;">'
    'Mostra a quantidade anual de exames registrados entre pessoas de 25 a 64 anos '
    'em cada município da 10ª CRS, de 2020 a 2025. Permite identificar '
    'aumentos ou reduções no volume de exames da faixa etária prioritária. '
    'Quantidade de exames não equivale à cobertura populacional.</p>',
    unsafe_allow_html=True,
)
if "ano" not in groups.columns:
    st.info("A tabela Gold de faixa etária não contém o ano necessário à evolução temporal.")
else:
    alvo_anual = groups.loc[groups["grupo"].eq("25–64 anos")].copy()
    alvo_anual["ano"] = pd.to_numeric(alvo_anual["ano"], errors="coerce")
    alvo_anual["quantidade_exames"] = pd.to_numeric(
        alvo_anual["quantidade_exames"], errors="coerce"
    )
    alvo_anual = alvo_anual.dropna(
        subset=["municipio", "ano", "quantidade_exames"]
    )
    if alvo_anual.empty:
        st.info("Não há exames da faixa 25–64 anos para os filtros selecionados.")
    else:
        alvo_anual = (
            alvo_anual.groupby(["municipio", "ano"], as_index=False)[
                "quantidade_exames"
            ].sum(min_count=1)
        )
        alvo_anual["ano"] = alvo_anual["ano"].astype(int)
        alvo_anual["ano_label"] = alvo_anual["ano"].astype(str)
        anos_grafico = sorted(alvo_anual["ano"].unique().tolist())
        municipios_grafico = sorted(
            alvo_anual["municipio"].unique(), key=normalize
        )

        ordenar_faixa = st.selectbox(
            "Ordenar por",
            ["A–Z", "Maior para menor"],
            key="ordenacao_evolucao_anual_25_64",
            help="Maior para menor considera a soma de exames na faixa 25–64 anos durante os anos selecionados.",
        )
        if ordenar_faixa == "Maior para menor":
            volumes = alvo_anual.groupby("municipio")[
                "quantidade_exames"
            ].sum(min_count=1)
            municipios_grafico.sort(
                key=lambda municipio: (
                    -float(volumes.loc[municipio])
                    if pd.notna(volumes.loc[municipio]) else float("inf"),
                    normalize(municipio),
                )
            )
        grafico_anual = px.line(
            alvo_anual,
            x="ano_label",
            y="quantidade_exames",
            facet_col="municipio",
            facet_col_wrap=3,
            facet_col_spacing=0.055,
            facet_row_spacing=0.09,
            category_orders={
                "municipio": municipios_grafico,
                "ano_label": [str(ano) for ano in anos_grafico],
            },
            markers=True,
            color_discrete_sequence=[OCEAN],
            labels={
                "ano_label": "Anos",
                "quantidade_exames": "Exames registrados (25–64 anos)",
                "municipio": "Município",
            },
        )
        grafico_anual.for_each_annotation(
            lambda annotation: annotation.update(
                text=annotation.text.split("=", 1)[-1],
                font=dict(size=13, color=NAVY),
            )
        )
        grafico_anual.update_traces(
            line=dict(width=2.7),
            marker=dict(size=7),
            connectgaps=False,
            hovertemplate=(
                "Ano: %{x}<br>Exames registrados (25–64 anos): "
                "%{y:,.0f}<extra></extra>"
            ),
        )
        grafico_anual.update_xaxes(
            matches=None,
            type="category",
            categoryorder="array",
            categoryarray=[str(ano) for ano in anos_grafico],
            showticklabels=True,
            title_text=None,
        )
        grafico_anual.update_yaxes(
            matches=None, showticklabels=True, title_text=None,
            rangemode="tozero", tickformat=",.0f",
            gridcolor="#E9EDF1", zeroline=False,
        )
        grafico_anual.add_annotation(
            x=-0.065, y=0.5, xref="paper", yref="paper",
            text="Exames registrados", textangle=-90, showarrow=False,
            font=dict(size=13, color=NAVY),
        )
        grafico_anual.add_annotation(
            x=0.5, y=-0.025, xref="paper", yref="paper",
            text="Anos", showarrow=False,
            font=dict(size=13, color=NAVY),
        )
        quantidade_linhas = (len(municipios_grafico) + 2) // 3
        grafico_anual.update_layout(
            height=max(520, 330 * quantidade_linhas),
            showlegend=False,
            margin=dict(l=100, r=25, t=65, b=110),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color=NAVY, size=11),
        )
        export_anual = copy.deepcopy(grafico_anual)
        export_anual.update_traces(
            mode="lines+markers+text",
            texttemplate="%{y:,.0f}",
            textposition="top center",
            textfont=dict(size=13, color=NAVY),
            cliponaxis=False,
        )
        export_anual.update_yaxes(automargin=True)
        export_anual.update_layout(
            title=dict(
                text="Evolução anual de exames de 25–64 anos por município",
                x=0.5, xanchor="center",
                font=dict(size=24, color=NAVY),
            ),
            width=1650,
            height=max(850, 430 * quantidade_linhas),
            margin=dict(l=115, r=65, t=135, b=130),
        )
        chart_with_right_click_download(
            grafico_anual,
            filename="faixa_etaria_evolucao_anual_25_64_municipios.png",
            height=grafico_anual.layout.height,
            min_chart_width=820,
            export_fig=export_anual,
        )

with st.expander("Ver dados detalhados da distribuição etária (Q3)"):
    export_table(agg, "siscan_faixa_etaria.csv")
st.caption("Fonte: SISCAN/DATASUS · camada Gold (Q3).")

# ---------------------------------------------------------------------------
# Cobertura Populacional Anual (Q3) — consome gold.fato_evolucao_cobertura_municipios.
# Fórmula: TC(%) = (exames 25–64 no ano t ÷ população feminina 25–64 IBGE 2022) × 100.
# Denominador fixo (Censo 2022); 33% usado apenas como referência visual.
# Produção de exames não permite identificar mulheres únicas / primeiro exame.
# ---------------------------------------------------------------------------
import copy

st.markdown("### Razão anual de exames por população feminina (25–64 anos)")
st.markdown(
    '<p style="font-size:18px;line-height:1.55;color:#334E68;'
    'font-weight:400;margin:4px 0 18px 0;">'
    'Compara o total anual de exames citopatológicos registrados em mulheres '
    'de 25 a 64 anos com a população feminina da mesma faixa etária (IBGE 2022). '
    '<b>Razão anual (%) = exames registrados no município e ano ÷ população '
    'feminina de 25–64 anos do município (IBGE 2022) × 100.</b> '
    'A linha laranja em 33% é uma referência visual, não uma meta de cobertura '
    'individual comprovada. Como os registros são agregados por exames, '
    'não é possível identificar o primeiro procedimento nem mulheres únicas: '
    'este indicador mede produção relativa à população, e não cobertura '
    'efetiva de rastreamento.</p>',
    unsafe_allow_html=True,
)

# Compatibilidade com instâncias do Streamlit que mantenham em memória
# uma versão anterior do data_loader.TABLES, sem a chave "cobertura".
# A tabela já existe na Gold (11 municípios × 6 anos).
from utils import data_loader as gold_loader
gold_loader.TABLES.setdefault("cobertura", "fato_evolucao_cobertura_municipios")

try:
    df_cob = gold_loader.filtered("cobertura")
except ValueError:
    st.error(
        "Não foi possível carregar o indicador de cobertura populacional. "
        "Atualize a aplicação para sincronizar o catálogo de tabelas Gold."
    )
    st.stop()

if not require(df_cob, ["municipio", "ano", "total_exames_25_64",
                        "mulheres_25_64_anos", "taxa_cobertura_pct",
                        "st_meta_ans"]):
    st.stop()

cob = df_cob.copy()
cob["ano"] = pd.to_numeric(cob["ano"], errors="coerce")
cob["taxa_cobertura_pct"] = pd.to_numeric(cob["taxa_cobertura_pct"], errors="coerce")
cob = cob.dropna(subset=["municipio", "ano", "taxa_cobertura_pct"])
cob["ano"] = cob["ano"].astype(int)
if cob.empty:
    st.info("Não há registros de cobertura populacional para os filtros selecionados.")
    st.stop()

# KPIs respeitam os filtros globais de município e ano.
exames_periodo = int(cob["total_exames_25_64"].sum(min_count=1))
cobertura_media = float(cob["taxa_cobertura_pct"].mean())
ano_recente = int(cob["ano"].max())
na_meta_ano_recente = int(
    cob.loc[cob["ano"].eq(ano_recente) & cob["taxa_cobertura_pct"].ge(33),
            "municipio"].nunique()
)
municipios_filtrados = int(cob["municipio"].nunique())

kpi_titles = [
    "Exames 25–64 anos (período)",
    "Razão média anual",
    f"Municípios ≥33% em {ano_recente}",
]
kpi_values = [fmt_num(exames_periodo), fmt_pct(cobertura_media),
              f"{na_meta_ano_recente} de {municipios_filtrados}"]
kpi_helps = [
    "Somatório de exames da população-alvo nos anos selecionados.",
    "Média aritmética das razões município–ano selecionadas; não é a razão regional ponderada.",
    "Municípios cuja razão anual de exames atingiu 33% ou mais; referência visual, não cobertura individual.",
]
for col, titulo, valor, ajuda in zip(st.columns(3), kpi_titles, kpi_values, kpi_helps):
    with col:
        st.metric(titulo, valor, help=ajuda)

# Evolução da razão de produção por município, com referência visual de 33%.
cob["ano_label"] = cob["ano"].astype(str)
municipios_cob = sorted(cob["municipio"].dropna().unique(), key=normalize)
anos_cob = sorted(cob["ano"].unique().tolist())

fig_cob = px.line(
    cob,
    x="ano_label",
    y="taxa_cobertura_pct",
    facet_col="municipio",
    facet_col_wrap=3,
    facet_col_spacing=0.055,
    facet_row_spacing=0.09,
    category_orders={
        "municipio": municipios_cob,
        "ano_label": [str(ano) for ano in anos_cob],
    },
    markers=True,
    color_discrete_sequence=[OCEAN],
    labels={
        "ano_label": "Anos",
        "taxa_cobertura_pct": "Exames por 100 mulheres (%)",
        "municipio": "Município",
    },
)
fig_cob.for_each_annotation(
    lambda annotation: annotation.update(
        text=annotation.text.split("=", 1)[-1],
        font=dict(size=13, color=NAVY),
    )
)
# Referência visual de 33% em todos os subgráficos (não comprova cobertura).
fig_cob.add_hline(y=33, line_dash="dash", line_color=ORANGE, line_width=1.6)
fig_cob.update_traces(
    line=dict(width=2.7),
    marker=dict(size=7),
    connectgaps=False,
    hovertemplate=(
        "Ano: %{x}<br>Exames por 100 mulheres: %{y:.2f}%<extra></extra>"
    ),
)
fig_cob.update_xaxes(
    matches=None,
    type="category",
    categoryorder="array",
    categoryarray=[str(ano) for ano in anos_cob],
    showticklabels=True,
    title_text=None,
)
fig_cob.update_yaxes(
    matches=None, showticklabels=True, title_text=None,
    rangemode="tozero", ticksuffix="%", tickformat=",.0f",
    gridcolor="#E9EDF1", zeroline=False,
)
fig_cob.add_annotation(
    x=-0.065, y=0.5, xref="paper", yref="paper",
    text="Exames / população (%)", textangle=-90, showarrow=False,
    font=dict(size=13, color=NAVY),
)
fig_cob.add_annotation(
    x=0.5, y=-0.025, xref="paper", yref="paper",
    text="Anos", showarrow=False,
    font=dict(size=13, color=NAVY),
)
qtd_linhas_cob = (len(municipios_cob) + 2) // 3
fig_cob.update_layout(
    height=max(520, 330 * qtd_linhas_cob),
    showlegend=False,
    margin=dict(l=100, r=25, t=65, b=110),
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(color=NAVY, size=11),
)
export_cob = copy.deepcopy(fig_cob)
export_cob.update_traces(
    mode="lines+markers+text",
    texttemplate="%{y:.2f}%",
    textposition="top center",
    textfont=dict(size=13, color=NAVY),
    cliponaxis=False,
)
export_cob.update_yaxes(automargin=True)
export_cob.update_layout(
    title=dict(
        text="Razão anual de exames por população feminina (25–64 anos)",
        x=0.5, xanchor="center",
        font=dict(size=24, color=NAVY),
    ),
    width=1650,
    height=max(850, 430 * qtd_linhas_cob),
    margin=dict(l=115, r=65, t=135, b=130),
)
chart_with_right_click_download(
    fig_cob,
    filename="faixa_etaria_razao_anual_exames_populacao_municipios.png",
    height=fig_cob.layout.height,
    min_chart_width=820,
    export_fig=export_cob,
)

# Matriz município × ano da razão, com gradiente e referência de 33%.
st.markdown("#### Razão anual de exames por município e ano (%)")
pivo_cob = (
    cob.pivot_table(index="municipio", columns="ano",
                    values="taxa_cobertura_pct", aggfunc="mean")
    .reindex(municipios_cob)
)
pivo_cob.columns = [str(coluna) for coluna in pivo_cob.columns]
vmax_cob = max(33.0, float(pivo_cob.max().max())) if not pivo_cob.empty else 33.0
st.dataframe(
    pivo_cob.style
    .format("{:.2f}%", na_rep="—")
    .background_gradient(cmap="RdYlGn", axis=None, vmin=0, vmax=vmax_cob),
    use_container_width=True,
)
st.caption(
    "Faixas exploratórias da razão: 🟢 ≥33% · 🟡 de 3% a menos de 33% · "
    "🔴 abaixo de 3%. Essas categorias não representam cobertura comprovada. "
    "Fonte: SISCAN/DATASUS (exames) · Censo IBGE 2022 (população fixa) · Gold."
)

with st.expander("Ver dados detalhados da razão anual (Q3)"):
    detalhe_cob = cob[
        ["codigo_municipio", "municipio", "ano", "total_exames_25_64",
         "mulheres_25_64_anos", "taxa_cobertura_pct", "meta_ans_pct",
         "st_meta_ans"]
    ].sort_values(["municipio", "ano"])
    export_table(detalhe_cob, "siscan_razao_anual_exames_populacao.csv")
st.caption("Fonte: SISCAN/DATASUS · camada Gold (Q3).")
