"""Análise descritiva da avaliação TAM do Dashboard SISCAN.

Executar a partir da raiz do repositório ou diretamente:
    python avaliacao_tam/analise_tam.py

Arquivo de entrada: avaliacao_tam/dados/respostas_tam.csv
Arquivos de saída: avaliacao_tam/figuras/*.png e avaliacao_tam/tabelas/*.csv/*.png

As estatísticas são descritivas; não inferem representatividade populacional.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
ARQUIVO = BASE / "dados" / "respostas_tam.csv"
FIG = BASE / "figuras"
TAB = BASE / "tabelas"

CORES = {"marinho": "#1A3B5C", "azul": "#347BA5", "cinza": "#64748B",
         "fundo": "#F4F7FA", "borda": "#DDE5EC", "claro": "#9FBECE"}
LIKERT = {"Discordo totalmente": 1, "Discordo parcialmente": 2,
          "Nem concordo nem discordo": 3, "Concordo parcialmente": 4,
          "Concordo totalmente": 5}
LIKERT_CORES = ["#B34A64", "#E2A3AB", "#C4CBD4", "#83B6C9", "#1A3B5C"]
CONSTRUTOS = {"PU": list(range(6, 11)), "PEOU": list(range(11, 16)),
              "AT": list(range(16, 19)), "BI": list(range(19, 22))}
NOMES = {"PU": "Utilidade percebida", "PEOU": "Facilidade de uso percebida",
         "AT": "Atitude em relação ao uso", "BI": "Intenção de uso"}
TAM_RESUMO = {
    "PU1": "Acesso às informações", "PU2": "Compreensão dos dados",
    "PU3": "Diferenças entre municípios", "PU4": "Evolução ao longo do tempo",
    "PU5": "Ferramenta útil para consulta", "PEOU1": "Aprendizado do dashboard",
    "PEOU2": "Organização e navegação", "PEOU3": "Utilização dos filtros",
    "PEOU4": "Clareza das funcionalidades", "PEOU5": "Facilidade geral de uso",
    "AT1": "Percepção positiva do uso", "AT2": "Boa forma de consultar dados",
    "AT3": "Experiência satisfatória", "BI1": "Utilizaria novamente",
    "BI2": "Consideraria utilizar", "BI3": "Interesse em uso futuro",
}
FUNC_RESUMO = ["Menu lateral", "Filtros de anos e municípios", "Comparação nos gráficos",
               "Explicações dos indicadores", "Organização visual e legibilidade",
               "Interação com gráficos", "Exportação de gráficos e tabelas",
               "Fontes e limitações dos dados"]


def config_graficos() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 15, "axes.titleweight": "bold",
                         "axes.labelcolor": CORES["marinho"],
                         "text.color": CORES["marinho"],
                         "xtick.color": CORES["cinza"],
                         "ytick.color": CORES["marinho"],
                         "figure.facecolor": "white", "axes.facecolor": "white",
                         "savefig.facecolor": "white"})


def ler_bases(caminho: Path = ARQUIVO) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Retorna original, participantes consentidos, elegíveis para TAM."""
    bruto = pd.read_csv(caminho, encoding="utf-8-sig")
    if bruto.shape[1] != 34 or not "Carimbo de data/hora" in bruto.columns[0]:
        raise ValueError("Layout CSV inesperado; confira o formulário antes de executar.")
    for i in range(6, 30):
        if "Indique seu grau de concordância" not in bruto.columns[i]:
            raise ValueError(f"Coluna de escala inesperada: {i}")
    consentidos = bruto[bruto.iloc[:, 1].eq("Sim, concordo em participar.")].copy()
    nao_explorou = consentidos.iloc[:, 5].fillna("").str.contains(
        "Não consegui acessar ou explorar o dashboard", regex=False
    )
    elegiveis = consentidos.loc[~nao_explorou].copy()
    if elegiveis.empty:
        raise ValueError("Não há participantes elegíveis.")
    return bruto, consentidos, elegiveis


def codificar(coluna: pd.Series, permitir_nao_utilizei: bool = False) -> pd.Series:
    valores = coluna.astype("string").str.strip()
    desconhecidos = set(valores.dropna().unique()) - set(LIKERT)
    if permitir_nao_utilizei:
        desconhecidos.discard("Não utilizei / Não se aplica")
    if desconhecidos:
        raise ValueError(f"Alternativas Likert não reconhecidas: {desconhecidos}")
    return valores.map(LIKERT).astype(float)


def alpha_cronbach(itens: pd.DataFrame) -> float:
    """Alfa de Cronbach clássico usando apenas casos completos, DDof=1."""
    completo = itens.dropna()
    k = completo.shape[1]
    if k < 2 or len(completo) < 2:
        return float("nan")
    variancia_total = completo.sum(axis=1).var(ddof=1)
    if variancia_total == 0 or pd.isna(variancia_total):
        return float("nan")
    return float(k / (k - 1) * (1 - completo.var(axis=0, ddof=1).sum() / variancia_total))


def extrair_texto(coluna: str) -> str:
    retorno = re.search(r"\[(.*?)\]\s*$", coluna)
    return retorno.group(1) if retorno else coluna


def resumo_amostra(bruto: pd.DataFrame, consentidos: pd.DataFrame,
                   elegiveis: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        ("Respostas recebidas", len(bruto)),
        ("Sem consentimento (excluídas)", len(bruto) - len(consentidos)),
        ("Respostas consentidas", len(consentidos)),
        ("Consentidos sem exploração da plataforma", len(consentidos) - len(elegiveis)),
        ("Elegíveis para TAM e funcionalidades", len(elegiveis))
    ], columns=["Critério", "n"])


def analise_construtos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Retorna tabela por construto, por item e escores dos participantes."""
    itens, construtos, escores = [], [], pd.DataFrame(index=df.index)
    for sigla, indices in CONSTRUTOS.items():
        bloco = pd.DataFrame(index=df.index)
        for pos, ind in enumerate(indices, start=1):
            codigo = f"{sigla}{pos}"
            valores = codificar(df.iloc[:, ind])
            bloco[codigo] = valores
            validos = valores.dropna()
            n = len(validos)
            cont = validos.value_counts().reindex(range(1, 6), fill_value=0)
            itens.append({"Construto": sigla, "Código": codigo,
                          "Afirmação": extrair_texto(df.columns[ind]),
                          "Resumo gráfico": TAM_RESUMO[codigo], "n válido": n,
                          **{f"n({i})": int(cont.loc[i]) for i in range(1, 6)},
                          **{f"%({i})": 100 * int(cont.loc[i]) / n if n else np.nan
                             for i in range(1, 6)},
                          "Média": validos.mean(),
                          "Concordância positiva (%)": 100 * validos.isin([4, 5]).mean()
                          if n else np.nan})
        # Escore individual calculado somente com todos os itens preenchidos.
        escore = bloco.mean(axis=1).where(bloco.notna().all(axis=1))
        escores[sigla] = escore
        validos = escore.dropna()
        total_validos = sum(bloco.notna().sum())
        total_positivos = sum(bloco.isin([4, 5]).sum())
        construtos.append({"Código": sigla, "Construto": NOMES[sigla],
                           "Itens": len(indices), "n participantes": len(validos),
                           "Média": validos.mean(), "Mediana": validos.median(),
                           "Desvio-padrão amostral": validos.std(ddof=1),
                           "Concordância positiva (%)": 100 * total_positivos / total_validos,
                           "Alfa de Cronbach": alpha_cronbach(bloco)})
    return pd.DataFrame(construtos), pd.DataFrame(itens), escores


def analise_funcionalidades(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for pos, ind in enumerate(range(22, 30), start=1):
        coluna = df.iloc[:, ind].astype("string").str.strip()
        cod = codificar(coluna, permitir_nao_utilizei=True)
        validos = cod.dropna()
        n_nao = int(coluna.eq("Não utilizei / Não se aplica").sum())
        linhas.append({"Código": f"F{pos}", "Funcionalidade": FUNC_RESUMO[pos - 1],
                       "Afirmação": extrair_texto(df.columns[ind]),
                       "n válido": len(validos), "Não utilizou (n)": n_nao,
                       "Não utilizou (%)": n_nao / len(df) * 100,
                       "Concordância positiva (n)": int(validos.isin([4, 5]).sum()),
                       "Concordância positiva (%)": validos.isin([4, 5]).mean() * 100,
                       "Média": validos.mean()})
    return pd.DataFrame(linhas)


def perfil(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    var = {"perfil_atuacao": 2, "familiaridade_dashboards": 3,
           "experiencia_sistemas_saude": 4, "pagina_mais_util": 30}
    tabelas = {}
    for nome, pos in var.items():
        cont = df.iloc[:, pos].fillna("Não informado").value_counts()
        tabelas[nome] = pd.DataFrame({"Categoria": cont.index,
                                     "n": cont.values,
                                     "%": cont.values / len(df) * 100})
    paginas = Counter()
    for item in df.iloc[:, 5].fillna(""):
        for pagina in str(item).split(";"):
            pagina = pagina.strip().rstrip(".")
            if pagina and not pagina.startswith("Não consegui"):
                paginas[pagina] += 1
    tabelas["paginas_acessadas"] = pd.DataFrame([
        {"Página": k, "n": v, "% dos participantes": 100 * v / len(df)}
        for k, v in paginas.most_common()
    ])
    return tabelas


def dificuldades(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    cont = Counter()
    contradicoes = 0
    for registro in df.iloc[:, 31].fillna(""):
        partes = [p.strip().rstrip(".") for p in str(registro).split(";") if p.strip()]
        # Se houver 'não encontrei' juntamente com dificuldade, prevalece a dificuldade.
        sem = [p for p in partes if p.casefold().startswith("não encontrei dificuldades")]
        com = [p for p in partes if p not in sem]
        if com and sem:
            contradicoes += 1
            partes = com
        for p in sorted(set(partes)):
            cont[p] += 1
    dados = pd.DataFrame([{"Dificuldade": k, "n": v,
                           "% dos participantes": 100 * v / len(df)}
                          for k, v in cont.most_common()])
    return dados, contradicoes


def abertas(df: pd.DataFrame) -> pd.DataFrame:
    """Consolida as respostas para codificação HUMANA; sem atribuir temas automáticos."""
    return pd.DataFrame({"ID analítico": [f"P{i:02d}" for i in range(1, len(df) + 1)],
                         "Sugestão de melhoria": df.iloc[:, 32].fillna("").values,
                         "Comentário adicional": df.iloc[:, 33].fillna("").values,
                         "Categoria temática (preencher)": "",
                         "Notas de codificação (preencher)": ""})


def salvar_fig(fig: plt.Figure, nome: str) -> None:
    FIG.mkdir(exist_ok=True, parents=True)
    fig.savefig(FIG / nome, dpi=320, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)


def barras_categorias(tabela: pd.DataFrame, coluna: str, titulo: str,
                      arquivo: str, n_part: int, largura: float = 10.0) -> None:
    dados = tabela.sort_values("n", ascending=True)
    categorias = [textwrap.fill(str(x).rstrip("."), width=54) for x in dados[coluna]]
    fig, ax = plt.subplots(figsize=(largura, max(3.7, 1.0 + len(dados) * 0.66)))
    bars = ax.barh(categorias, dados["n"], color=CORES["marinho"], height=0.64)
    ax.set_xlim(0, max(1, dados["n"].max() * 1.26))
    ax.set_xlabel("Número de participantes")
    ax.set_title(titulo, pad=18, loc="left")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)
    for barra, valor in zip(bars, dados["n"]):
        ax.text(barra.get_width() + .25, barra.get_y() + barra.get_height() / 2,
                f"{valor} ({100 * valor / n_part:.2f}%)".replace(".", ","),
                va="center", fontsize=9.2, color=CORES["marinho"])
    fig.subplots_adjust(left=0.42, bottom=0.12, right=0.94)
    salvar_fig(fig, arquivo)


def grafico_concordancia_itens(itens: pd.DataFrame, n: int) -> None:
    """Figura principal para artigo: quatro painéis sem segmentos minúsculos."""
    fig, eixos = plt.subplots(4, 1, figsize=(7.6, 8.75),
                             gridspec_kw={"height_ratios": [5.3, 5.3, 3.4, 3.4]})
    fig.suptitle("Concordância positiva por item TAM", x=.05, y=.975,
                 ha="left", fontsize=15, fontweight="bold")
    fig.text(.05, .933, "Participação das respostas 4 ou 5 em cada afirmação | n = " + str(n),
             fontsize=9.0, color=CORES["cinza"])
    fig.subplots_adjust(left=.410, right=.88, top=.868, bottom=.085, hspace=.78)

    for ax, (sigla, nome) in zip(eixos, NOMES.items()):
        t = itens.loc[itens["Construto"] == sigla].copy()
        valores = t["Concordância positiva (%)"].to_numpy(dtype=float)[::-1]
        rotulos = (t["Código"] + "  ·  " + t["Resumo gráfico"]).tolist()[::-1]
        y = np.arange(len(t))
        ax.barh(y, valores, height=.46, color=CORES["azul"], zorder=2)
        ax.scatter(valores, y, color=CORES["marinho"], s=35, zorder=3)
        ax.set_yticks(y, rotulos, fontsize=8.6)
        ax.set_xlim(0, 117)
        ax.set_ylim(-.55, len(t)-.45)
        ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
        ax.tick_params(axis="x", labelsize=7.8, length=0, pad=5)
        ax.tick_params(axis="y", length=0, pad=8)
        ax.grid(axis="x", alpha=.13, zorder=0)
        ax.spines[:].set_visible(False)
        ax.set_title(f"{sigla}  |  {nome}", loc="left", color=CORES["marinho"],
                     fontsize=10.1, fontweight="bold", pad=10)
        for j, valor in enumerate(valores):
            ax.text(102.0, j, fmt(valor, "%"), ha="left", va="center",
                    fontsize=8.3, color=CORES["marinho"], fontweight="bold")

    salvar_fig(fig, "02_itens_tam_concordancia.png")


def graficos_likert_por_construto(itens: pd.DataFrame, n: int) -> None:
    """Gráficos complementares: todas as 5 alternativas, uma dimensão por PNG."""
    from matplotlib.patches import Patch
    for sigla, nome in NOMES.items():
        dados = itens.loc[itens["Construto"] == sigla].copy()
        k = len(dados)
        fig, ax = plt.subplots(figsize=(7.7, 3.7 if k == 5 else 3.25))
        fig.subplots_adjust(left=.395, right=.96, top=.73, bottom=.14)
        y = np.arange(k)[::-1]
        esquerdo = np.zeros(k)
        for escore in range(1, 6):
            valores = dados[f"%({escore})"].to_numpy(dtype=float)
            barras = ax.barh(y, valores, left=esquerdo, height=.54,
                             color=LIKERT_CORES[escore-1], edgecolor="white", linewidth=.7)
            for barra, val in zip(barras, valores):
                if val >= 16.0:
                    ax.text(barra.get_x()+barra.get_width()/2,
                            barra.get_y()+barra.get_height()/2,
                            f"{val:.1f}%".replace(".", ","), ha="center", va="center",
                            fontsize=7.6, color="white" if escore == 5 else CORES["marinho"])
            esquerdo += valores
        ax.set_yticks(y, [f"{r['Código']}  ·  {r['Resumo gráfico']}" for _, r in dados.iterrows()], fontsize=8.6)
        ax.set_xticks([0,25,50,75,100],["0%","25%","50%","75%","100%"])
        ax.set_xlim(0,100)
        ax.tick_params(axis="both", length=0, pad=5)
        ax.spines[:].set_visible(False)
        ax.grid(axis="x", alpha=.1)
        ax.set_axisbelow(True)
        fig.suptitle(f"Distribuição Likert | {sigla} — {nome}", ha="left", x=.05, y=.975,
                     fontsize=12, fontweight="bold")
        legenda = [Patch(facecolor=cor, label=lab) for cor, lab in zip(LIKERT_CORES,
                   ["1 · Discordo totalmente", "2 · Discordo parcialmente", "3 · Neutro",
                    "4 · Concordo parcialmente", "5 · Concordo totalmente"])]
        fig.legend(handles=legenda, loc="upper center", bbox_to_anchor=(.52,.885),
                   ncol=3, frameon=False, fontsize=7.1, columnspacing=1)
        salvar_fig(fig, f"02_likert_{sigla.lower()}.png")


def grafico_construtos(tabela: pd.DataFrame) -> None:
    t = tabela.iloc[::-1]
    fig, ax = plt.subplots(figsize=(10.1, 4.5))
    bars = ax.barh(t["Construto"], t["Média"], color=CORES["marinho"], height=.59)
    ax.set_xlim(0, 5.3)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Escore médio por construto (escala de 1 a 5)")
    ax.set_title("Escores médios dos construtos TAM", loc="left", pad=17)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, t["Média"]):
        ax.text(val + .06, bar.get_y() + bar.get_height()/2,
                f"{val:.2f}".replace(".", ","), va="center", weight="bold")
    fig.subplots_adjust(left=.30, right=.95, bottom=.16)
    salvar_fig(fig, "03_medias_construtos.png")


def grafico_funcionalidades(tabela: pd.DataFrame, n: int) -> None:
    t = tabela.iloc[::-1]
    fig, ax = plt.subplots(figsize=(11.8, 6.2))
    bars = ax.barh(t["Funcionalidade"], t["Concordância positiva (%)"],
                   color=CORES["marinho"], height=.62)
    ax.set_xlim(0, 117)
    ax.set_xticks([0, 20, 40, 60, 80, 100], [f"{x}%" for x in [0,20,40,60,80,100]])
    ax.set_title("Avaliação das funcionalidades do dashboard", loc="left", pad=20)
    ax.set_xlabel("Concordância positiva entre respostas válidas (%)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
    for bar, (_, row) in zip(bars, t.iterrows()):
        label = f"{row['Concordância positiva (%)']:.2f}%".replace(".", ",")
        ax.text(bar.get_width() + 1.3, bar.get_y() + bar.get_height()/2,
                f"{label}   (n={int(row['n válido'])})", va="center", fontsize=9)
    fig.subplots_adjust(left=.39, right=.96, bottom=.13)
    salvar_fig(fig, "04_funcionalidades_concordancia.png")


def tabela_png(df: pd.DataFrame, nome: str, titulo: str,
               tamanhos: list[float], font: float = 10, linha_altura: float = .58) -> None:
    """Exporta tabela compacta para PNG de alta resolução e dimensões apropriadas ao artigo."""
    linhas = len(df)
    fig_h = 1.28 + (linhas + 1) * .39
    fig, ax = plt.subplots(figsize=(11.1, fig_h))
    ax.axis("off")
    fig.text(.035, .915, titulo, fontsize=14, fontweight="bold", color=CORES["marinho"])
    tb = ax.table(cellText=df.astype(str).values.tolist(), colLabels=list(df.columns),
                  colWidths=tamanhos, cellLoc="left", bbox=[.035, .11, .93, .72])
    tb.auto_set_font_size(False)
    tb.set_fontsize(font)
    for (r, c), cel in tb.get_celld().items():
        cel.set_linewidth(.5)
        cel.set_edgecolor(CORES["borda"])
        cel.PAD = .075
        if r == 0:
            cel.set_facecolor(CORES["marinho"])
            cel.get_text().set_color("white")
            cel.get_text().set_fontweight("bold")
            cel.get_text().set_ha("center" if c else "left")
        else:
            cel.set_facecolor(CORES["fundo"] if r % 2 == 0 else "white")
            cel.get_text().set_color(CORES["marinho"])
            if c > 0:
                cel.get_text().set_ha("center")
    TAB.mkdir(parents=True, exist_ok=True)
    fig.savefig(TAB / nome, dpi=320, bbox_inches="tight", pad_inches=.10)
    plt.close(fig)


def fmt(x: float, sufixo: str = "") -> str:
    return f"{x:.2f}".replace(".", ",") + sufixo if pd.notna(x) else "—"


def executar(caminho: Path = ARQUIVO) -> dict:
    """Executa as análises, exporta os gráficos e tabelas, retorna metadados."""
    config_graficos()
    FIG.mkdir(exist_ok=True, parents=True)
    TAB.mkdir(exist_ok=True, parents=True)
    bruto, consentidos, elegiveis = ler_bases(caminho)
    amostra = resumo_amostra(bruto, consentidos, elegiveis)
    construtos, itens, escores = analise_construtos(elegiveis)
    fun = analise_funcionalidades(elegiveis)
    grupos = perfil(elegiveis)
    dif, contradicoes = dificuldades(elegiveis)

    tabelas = {"01_fluxo_amostral": amostra, "02_indicadores_construtos": construtos,
               "03_itens_tam": itens, "04_funcionalidades": fun,
               "05_dificuldades": dif, **grupos}
    for nome, tabela in tabelas.items():
        tabela.to_csv(TAB / f"{nome}.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    # Escore individual é usado internamente para conferência, não é exportado.
    abertas(elegiveis).to_csv(BASE / "dados" / "respostas_abertas_codificacao_local.csv",
                               index=False, encoding="utf-8-sig")

    tabela_png(amostra, "01_fluxo_amostral.png", "Fluxo de seleção das respostas",
               [.81, .19])
    reduzida = construtos[["Construto", "Itens", "n participantes", "Média", "Mediana",
                           "Concordância positiva (%)", "Alfa de Cronbach"]].copy()
    for c in ["Média", "Mediana", "Alfa de Cronbach"]:
        reduzida[c] = reduzida[c].map(fmt)
    reduzida["Concordância positiva (%)"] = reduzida["Concordância positiva (%)"].map(lambda x: fmt(x, "%"))
    reduzida.columns = ["Construto", "Itens", "n", "Média", "Mediana", "Concordância", "Alfa"]
    tabela_png(reduzida, "02_indicadores_construtos.png", "Síntese dos quatro construtos TAM",
               [.29, .085, .065, .11, .115, .19, .115], font=9.7)
    funcional = fun[["Funcionalidade", "n válido", "Não utilizou (n)", "Concordância positiva (%)"]].copy()
    funcional["Concordância positiva (%)"] = funcional["Concordância positiva (%)"].map(lambda x: fmt(x, "%"))
    funcional.columns = ["Funcionalidade", "n válido", "Não utilizou", "Concordância"]
    tabela_png(funcional, "03_funcionalidades.png", "Síntese da avaliação das funcionalidades",
               [.54, .14, .15, .17], font=9.4, linha_altura=.61)
    ranking = dif.copy()
    ranking["% dos participantes"] = ranking["% dos participantes"].map(lambda x: fmt(x, "%"))
    ranking.columns = ["Resposta assinalada", "n", "% participantes"]
    ranking["Resposta assinalada"] = ranking["Resposta assinalada"].map(
        lambda x: textwrap.fill(x, width=65))
    tabela_png(ranking, "04_dificuldades.png", "Dificuldades relatadas na utilização",
               [.72, .10, .18], font=9.1, linha_altura=.8)
    for nome, titulo, arquivo, coluna in [
        ("perfil_atuacao", "Perfil de atuação dos participantes", "01a_perfil_atuacao.png", "Categoria"),
        ("familiaridade_dashboards", "Familiaridade com dashboards", "01b_familiaridade.png", "Categoria"),
        ("experiencia_sistemas_saude", "Experiência com sistemas de saúde pública", "01c_experiencia_saude.png", "Categoria"),
        ("pagina_mais_util", "Página considerada mais útil", "01d_pagina_mais_util.png", "Categoria"),
        ("paginas_acessadas", "Páginas acessadas durante a avaliação", "01e_paginas_acessadas.png", "Página"),
    ]:
        barras_categorias(grupos[nome], coluna, titulo, arquivo, len(elegiveis))
    grafico_concordancia_itens(itens, len(elegiveis))
    graficos_likert_por_construto(itens, len(elegiveis))
    grafico_construtos(construtos)
    grafico_funcionalidades(fun, len(elegiveis))
    barras_categorias(dif, "Dificuldade", "Dificuldades assinaladas pelos participantes",
                       "05_dificuldades_relato.png", len(elegiveis), largura=12)
    meta = {
        "respostas_recebidas": len(bruto), "respostas_consentidas": len(consentidos),
        "respostas_elegiveis_tam": len(elegiveis), "contradicoes_dificuldades": contradicoes,
        "respostas_abertas_sugestoes": int(elegiveis.iloc[:, 32].notna().sum()),
        "respostas_abertas_comentarios": int(elegiveis.iloc[:, 33].notna().sum()),
        "total_figuras_png": len(list(FIG.glob("*.png"))),
        "total_tabelas_png": len(list(TAB.glob("*.png")))
    }
    (TAB / "00_metadados_analise.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Análise concluída:", json.dumps(meta, ensure_ascii=False))
    return {"metadados": meta, "construtos": construtos, "itens": itens,
            "funcionalidades": fun, "dificuldades": dif,
            "perfil": grupos, "escores": escores}


if __name__ == "__main__":
    executar()
