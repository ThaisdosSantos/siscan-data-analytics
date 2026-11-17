"""Gera tabelas Gold sintéticas, sem dados reais ou credenciais."""

from pathlib import Path

import pandas as pd

MUNICIPIOS = {
    "430040": "Alegrete", "430187": "Barra do Quaraí", "431060": "Itaqui",
    "431171": "Maçambará", "431175": "Manoel Viana", "431530": "Quaraí",
    "431640": "Rosário do Sul", "431697": "Santa Margarida do Sul",
    "431710": "Sant'Ana do Livramento", "431830": "São Gabriel",
    "432240": "Uruguaiana",
}
ANOS = range(2020, 2026)
GRUPOS = (
    ("<25 anos", "<= 24 anos", "20 a 24 anos", 10, 2),
    ("25-64 anos", "25 a 64 anos", "30 a 34 anos", 80, 10),
    (">=65 anos", ">= 65 anos", "65 a 69 anos", 10, 1),
)
TOTAL_EXAMES = 79420
TOTAL_ALEGRETE_2020 = 1220


def gerar_gold(destino: Path) -> None:
    """Materializa os fatos necessários às seis páginas em CSV.

    Cada município registra 100 exames por mês, 120 em outubro, e
    nenhum registro em agosto/2022. Há três exclusões por município/ano.
    """
    tabelas = {
        nome: [] for nome in (
            "fato_exames_temporais_territoriais",
            "fato_conformidade_faixa_etaria",
            "fato_evolucao_cobertura_municipios",
            "fato_adequabilidade_amostras",
            "fato_exames_alterados",
            "fato_categoria_anual",
            "fato_categoria_faixa_etaria",
            "fato_outubro_rosa_mensal_grupo_etario",
            "fato_outubro_rosa_grupo_etario",
        )
    }
    por_mes = {}
    for codigo, municipio in MUNICIPIOS.items():
        local = {"codigo_municipio": codigo, "municipio": municipio}
        for ano in ANOS:
            base = {**local, "ano": ano}
            producao = 0
            for mes in range(1, 13):
                if (ano, mes) == (2022, 8):
                    continue
                quantidade = 120 if mes == 10 else 100
                producao += quantidade
                tabelas["fato_exames_temporais_territoriais"].append(
                    {**base, "mes": mes, "quantidade": quantidade}
                )
                if mes >= 9:
                    por_mes[ano, mes] = por_mes.get((ano, mes), 0) + quantidade
            for grupo, grupo_gold, faixa, parcela, alterados in GRUPOS:
                quantidade = producao * parcela // 100
                tabelas["fato_conformidade_faixa_etaria"].append({
                    **base, "grupo_etario_diretriz": grupo,
                    "quantidade_exames": quantidade,
                })
                tabelas["fato_exames_alterados"].append({
                    **base, "faixa_etaria": faixa, "grupo_etario_3": grupo_gold,
                    "quantidade_alterados": alterados,
                    "total_exames_validos": quantidade - 1,
                })
            tabelas["fato_evolucao_cobertura_municipios"].append({
                **base, "total_exames_25_64": producao * 80 // 100,
                "mulheres_25_64_anos": 4000,
            })
            for categoria, quantidade in (
                ("Satisfatoria", producao - 3), ("Insatisfatoria", 2), ("Rejeitada", 1),
            ):
                tabelas["fato_adequabilidade_amostras"].append({
                    **base, "categoria_adequabilidade": categoria,
                    "quantidade_amostras": quantidade,
                })
            for categoria, quantidade in (("ASC-US", 10), ("ASC-H", 3)):
                tabelas["fato_categoria_anual"].append({
                    **base, "categoria": categoria, "quantidade_alterados": quantidade,
                })
        for grupo, grupo_gold, _, parcela, alterados in GRUPOS:
            tabelas["fato_outubro_rosa_grupo_etario"].append({
                **local, "grupo_etario": grupo, "quantidade_exames": 420 * 6 * parcela // 100,
            })
            for categoria, quantidade in (
                ("ASC-US", alterados if parcela == 80 else 0),
                ("ASC-H", alterados if parcela != 80 else 0),
            ):
                tabelas["fato_categoria_faixa_etaria"].append({
                    **local, "grupo_etario_3": grupo_gold,
                    "categoria": categoria, "quantidade_alterados": quantidade * 6,
                })
    for (ano, mes), quantidade in sorted(por_mes.items()):
        for grupo, _, _, parcela, _ in GRUPOS:
            tabelas["fato_outubro_rosa_mensal_grupo_etario"].append({
                "ano": ano, "mes_num": mes, "grupo_etario": grupo,
                "quantidade_exames": quantidade * parcela // 100,
            })
    destino.mkdir(parents=True, exist_ok=True)
    for nome, linhas in tabelas.items():
        pd.DataFrame(linhas).to_csv(destino / f"{nome}.csv", index=False)
