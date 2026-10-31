"""Conformidade etária (Q3) e matriz exploratória de alterações (Q3 × Q5)."""
import re
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.theme import (
    apply_custom_css, page_header, display_chart, export_table,
    fmt_num, fmt_pct, pct, OCEAN, SKY, ORANGE, NAVY,
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
with a:
    fig = px.pie(
        agg, names="grupo", values="quantidade_exames", hole=.62,
        color="grupo",
        category_orders={"grupo": labels},
        color_discrete_map={"25–64 anos": OCEAN, "<25 anos": SKY, "≥65 anos": ORANGE},
        title="Distribuição dos exames",
    )
    fig.update_traces(texttemplate="%{percent:.2%}", hovertemplate="%{label}<br>%{percent:.2%}<extra></extra>")
    display_chart(fig)
with b:
    fig = px.bar(
        agg, x="municipio", y="percentual", color="grupo", barmode="stack",
        category_orders={"grupo": labels},
        color_discrete_map={"25–64 anos": OCEAN, "<25 anos": SKY, "≥65 anos": ORANGE},
        labels={"municipio": "Município", "percentual": "Participação (%)", "grupo": "Faixa etária"},
        title="Composição etária por município · 100%",
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    fig.update_xaxes(tickangle=-45)
    fig.update_traces(hovertemplate="%{x}<br>%{y:.2f}%<extra>%{fullData.name}</extra>")
    display_chart(fig)

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

columns = ["Município", "Volume <25", "Taxa <25 (%)", "Taxa 25–64 (%)",
           "Taxa ≥65 (%)", "Razão (<25 / Alvo)", "Classificação de impacto"]
st.dataframe(
    matrix[columns], use_container_width=True, hide_index=True,
    height=min(40 * (len(matrix) + 1) + 14, 540),
    column_config={
        "Município": st.column_config.TextColumn("Município", pinned=True),
        "Volume <25": st.column_config.NumberColumn("Volume <25 anos", format="%d"),
        "Taxa <25 (%)": st.column_config.NumberColumn("Taxa de alteração <25 (%)", format="%.2f%%"),
        "Taxa 25–64 (%)": st.column_config.NumberColumn("Taxa de alteração 25–64 (%)", format="%.2f%%"),
        "Taxa ≥65 (%)": st.column_config.NumberColumn("Taxa de alteração ≥65 (%)", format="%.2f%%"),
        "Razão (<25 / Alvo)": st.column_config.NumberColumn("Razão de efetividade", format="%.2f"),
        "Classificação de impacto": st.column_config.TextColumn("Classificação de impacto"),
    },
)
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
