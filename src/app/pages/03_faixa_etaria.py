"""Conformidade etária (Q3) e matriz exploratória de alterações (Q3 × Q5)."""
import re
from html import escape
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.theme import (
    apply_custom_css, page_header, display_chart, export_table,
    fmt_num, fmt_pct, pct, style_chart, OCEAN, SKY, ORANGE, NAVY,
)
from utils.data_loader import MUNICIPIOS, filtered, sidebar_filters, require, years_label


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


def q5_group(label):
    """Agrupa faixas Q5 fechadas somente quando não cruzam limites de 25/65."""
    text = normalize(label).replace("–", "-").replace("—", "-")
    if not text or "ignorado" in text or "sem informacao" in text:
        return None
    if "ate 9" in text:
        return None  # Em consonância com a página de exames alterados.
    if "menor" in text and "25" in text:
        return "<25 anos"
    if "25 a 64" in text or "25-64" in text:
        return "25–64 anos"
    if "65 anos ou mais" in text or "65 ou mais" in text or ">=65" in text or "acima de 79" in text:
        return "≥65 anos"
    nums = [int(n) for n in re.findall(r"\d+", text)]
    if len(nums) >= 2:
        low, high = nums[:2]
        if high < 25:
            return "<25 anos"
        if 25 <= low and high <= 64:
            return "25–64 anos"
        if low >= 65:
            return "≥65 anos"
    if len(nums) == 1 and ("mais" in text or "+" in text) and nums[0] >= 65:
        return "≥65 anos"
    return None


def safe_percent(numerator, denominator):
    return numerator.div(denominator.where(denominator.gt(0))).mul(100)


def build_matrix(q3, q5, municipalities):
    """Cruza agregações municipais: nunca junta linhas brutas (evita multiplicação)."""
    volume = q3.loc[q3["grupo"].eq("<25 anos")].groupby("municipio")["quantidade_exames"].sum()
    total_q3 = q3.groupby("municipio")["quantidade_exames"].sum()
    result = pd.DataFrame(index=pd.Index(municipalities, name="municipio"))
    result["Volume <25"] = volume
    result["Participação <25 (%)"] = safe_percent(volume, total_q3)

    result["Taxa <25 (%)"] = float("nan")
    result["Taxa 25–64 (%)"] = float("nan")
    result["Taxa ≥65 (%)"] = float("nan")
    if not q5.empty:
        needed = {"municipio", "faixa_etaria", "quantidade_alterados", "total_exames_validos"}
        if needed.issubset(q5.columns):
            work = q5.copy()
            work["grupo"] = work["faixa_etaria"].map(q5_group)
            work = work.loc[work.grupo.notna()]
            grouped = work.groupby(["municipio", "grupo"])[
                ["quantidade_alterados", "total_exames_validos"]
            ].sum(min_count=1)
            rates = safe_percent(grouped["quantidade_alterados"], grouped["total_exames_validos"])
            for group, column in [
                ("<25 anos", "Taxa <25 (%)"),
                ("25–64 anos", "Taxa 25–64 (%)"),
                ("≥65 anos", "Taxa ≥65 (%)"),
            ]:
                if group in rates.index.get_level_values("grupo"):
                    result[column] = rates.xs(group, level="grupo").reindex(result.index)
    result["Razão (<25 / Alvo)"] = result["Taxa <25 (%)"].div(
        result["Taxa 25–64 (%)"].where(result["Taxa 25–64 (%)"].gt(0))
    )
    return result.reset_index().rename(columns={"municipio": "Município"})


def impact(row, threshold):
    """Regra visual exploratória: baseada na participação Q3 e na razão Q5."""
    share, ratio = row["Participação <25 (%)"], row["Razão (<25 / Alvo)"]
    if pd.isna(share):
        return "⚪ Dados insuficientes"
    if share <= threshold:
        return "🟢 Boa Adesão Local"
    if pd.isna(ratio):
        return "⚪ Dados insuficientes"
    if ratio < 0.25:
        return "🔴 Alto Desperdício"
    return "🟡 Baixo Retorno"


st.set_page_config(page_title="Faixa etária | SISCAN", layout="wide")
apply_custom_css()
sidebar_filters()
page_header(
    "Faixa etária · Q3 × Q5",
    "Conformidade etária",
    "Distribuição dos exames por grupos etários e comparação exploratória de alterações citológicas.",
)

st.markdown("""
<style>
.q3-section {margin:2.1rem 0 1rem;padding-bottom:12px;border-bottom:2px solid #006C9A;}
.q3-section strong {font-size:1.12rem;color:#1A3B5C;}
.q3-section p {font-size:.86rem;color:#516476;margin:8px 0 0;line-height:1.65;}
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
.st-key-age_bar_card {margin-top:24px;background:#fff;border:1px solid #dce4eb;border-radius:14px;padding:16px 18px 22px;box-shadow:0 2px 8px rgba(26,59,92,.04);min-height:454px;}
.st-key-age_bar_card [data-testid="stPlotlyChart"] {border:0!important;box-shadow:none!important;padding:0!important;background:transparent!important;}
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
        st.plotly_chart(style_chart(fig, height=320), use_container_width=True)
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
            'Composição etária por município · 100%</div>'
            '<div style="color:#7C8FA0;font-size:.77rem">Percentual (%)</div>',
            unsafe_allow_html=True,
        )
        # Barras horizontais empilhadas 100%, alinhadas à referência visual.
        bar_order = ["25–64 anos", "<25 anos", "≥65 anos"]
        cities_order = list(dict.fromkeys(agg["municipio"].tolist()))
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
        fig.update_xaxes(range=[0, 100], dtick=25, ticksuffix="%",
                         showgrid=True, gridcolor="#e9edf1", title=None)
        fig.update_yaxes(title=None, autorange="reversed", automargin=True,
                         tickfont=dict(size=10))
        fig.update_layout(
            margin=dict(l=12, r=8, t=8, b=10),
            legend=dict(orientation="h", yanchor="top", y=-0.12,
                        xanchor="center", x=0.5, title=None,
                        font=dict(size=10)),
            bargap=0.22,
        )
        st.plotly_chart(style_chart(fig, height=355), use_container_width=True)

st.markdown("""
<div class="q3-section">
<strong>🔬 Matriz Cruzada de Efetividade: Sobrerrastreamento vs. Alterações Citológicas (Q3 × Q5)</strong>
<p>Avaliação epidemiológica do retorno diagnóstico dos exames realizados fora do público-alvo prioritário do Ministério da Saúde.<br>
Comparação municipal agregada (não individual); as proporções Q5 são estimativas operacionais e não medem efetividade clínica ou desperdício comprovado.</p>
</div>
""", unsafe_allow_html=True)

q5 = filtered("alterados")
selected_cities = [c for c in MUNICIPIOS.values()
                   if c in st.session_state.get("city_preference", list(MUNICIPIOS.values()))]
matrix = build_matrix(groups, q5, selected_cities)
threshold = st.slider(
    "Limiar exploratório de participação de exames em menores de 25 anos (%)",
    min_value=5.0, max_value=20.0, value=10.0, step=0.5,
    help="Critério visual configurável pelo usuário, não é uma referência oficial.",
)
matrix["Classificação de impacto"] = matrix.apply(impact, axis=1, threshold=threshold)
if q5.empty:
    st.warning("A tabela Gold de exames alterados (Q5) não retornou registros. Taxas e razão serão exibidas como N/D.")

def format_br(value, digits=2):
    """Formata número no padrão brasileiro, sem transformar ausências em zero."""
    if pd.isna(value):
        return "N/D"
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def impact_badge(label):
    """Badges acessíveis, com rótulos explícitos além da cor."""
    classes = {
        "🟢 Boa Adesão Local": "ok",
        "🟡 Baixo Retorno": "low",
        "🔴 Alto Desperdício": "waste",
        "⚪ Dados insuficientes": "unknown",
    }
    color = classes.get(label, "unknown")
    return f'<span class="q3-badge q3-{color}">{escape(label)}</span>'


def matrix_html(table):
    """Tabela responsiva fiel à referência; somente valores escapados."""
    headers = [
        "Município",
        "Volume &lt;25 anos",
        "Taxa de alteração &lt;25 (%)",
        "Taxa de alteração 25–64 (%)",
        "Taxa de alteração ≥65 (%)",
        "Razão de efetividade",
        "Classificação de impacto",
    ]
    rows = []
    for _, row in table.iterrows():
        volume = format_br(row["Volume <25"], 0)
        cells = [
            f'<strong>{escape(str(row["Município"]))}</strong>',
            escape(volume),
            escape(format_br(row["Taxa <25 (%)"]) + "%") if pd.notna(row["Taxa <25 (%)"]) else "N/D",
            escape(format_br(row["Taxa 25–64 (%)"]) + "%") if pd.notna(row["Taxa 25–64 (%)"]) else "N/D",
            escape(format_br(row["Taxa ≥65 (%)"]) + "%") if pd.notna(row["Taxa ≥65 (%)"]) else "N/D",
            escape(format_br(row["Razão (<25 / Alvo)"])),
            impact_badge(str(row["Classificação de impacto"])),
        ]
        rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    if not rows:
        rows = ['<tr><td colspan="7">Nenhum município selecionado.</td></tr>']
    header = "".join(f"<th scope='col'>{value}</th>" for value in headers)
    return (
        '<div class="q3-matrix-scroll" role="region" aria-label="Matriz Q3 e Q5" tabindex="0">'
        '<table class="q3-matrix"><thead><tr>' + header + '</tr></thead><tbody>'
        + "".join(rows) + '</tbody></table></div>'
    )


st.markdown("""
<style>
.q3-matrix-scroll {width:100%;overflow-x:auto;border-radius:8px;
  box-shadow:0 2px 7px rgba(26,59,92,.09);margin:12px 0 17px;}
.q3-matrix {border-collapse:collapse;width:100%;min-width:1040px;background:white;
  color:#1A3B5C;font-family:Manrope,Arial,sans-serif;font-size:.83rem;}
.q3-matrix th {background:#1A3B5C;color:#fff;text-align:left;
  padding:13px 12px;font-size:.76rem;line-height:1.35;font-weight:750;}
.q3-matrix td {padding:13px 12px;border-bottom:1px solid #e7ebef;vertical-align:middle;}
.q3-matrix tbody tr:nth-child(even) {background:#f6f8fa;}
.q3-matrix tbody tr:hover {background:#ecf5fa;}
.q3-matrix td:first-child {font-weight:700;min-width:125px;}
.q3-matrix td:last-child {min-width:165px;}
.q3-badge {display:inline-block;border-radius:5px;padding:5px 9px;
  line-height:1.4;font-size:.76rem;font-weight:750;white-space:normal;}
.q3-ok {background:#e2f0d9;color:#385723;}
.q3-low {background:#fff3cd;color:#856404;}
.q3-waste {background:#ffe6e6;color:#b72323;}
.q3-unknown {background:#e9edf1;color:#4a5968;}
@media(max-width:800px) {
  .q3-matrix th,.q3-matrix td {padding:11px 9px;}
}
</style>
""", unsafe_allow_html=True)
st.markdown(matrix_html(matrix), unsafe_allow_html=True)
st.caption(
    "Rótulos heurísticos exploratórios: verde se a participação <25 é ≤ ao limiar; "
    "vermelho se excede o limiar e a razão é <0,25; amarelo nos demais casos com razão válida. "
    "Não representam critérios oficiais, julgamento de conduta clínica ou desperdício comprovado. "
    "Taxas Q5: estimativas operacionais, sem exclusão verificável de amostras rejeitadas/insatisfatórias "
    "do denominador. Uma razão de 0,25 significa taxa <25 igual a um quarto da taxa 25–64. "
    f"Período selecionado: {years_label()}."
)
st.download_button(
    "⬇️ Exportar matriz Q3 × Q5 (CSV)",
    matrix.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
    file_name="siscan_matriz_q3_q5.csv", mime="text/csv",
)
with st.expander("Ver dados detalhados da distribuição etária (Q3)"):
    export_table(agg, "siscan_faixa_etaria.csv")
st.caption("Fonte: SISCAN/DATASUS · camada Gold (Q3 e Q5). Sem vinculação individual entre exames.")
