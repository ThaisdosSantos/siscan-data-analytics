"""Testes unitários das regras analíticas, sem acesso à Gold real."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

APP = Path(__file__).resolve().parents[1] / "src/app"


@pytest.fixture
def carregar_modulo(monkeypatch: pytest.MonkeyPatch):
    """Importa a página sem executar sua função main."""
    monkeypatch.syspath_prepend(str(APP))

    def carregar(arquivo: str):
        spec = importlib.util.spec_from_file_location("pagina_testada", APP / arquivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    return carregar


def test_variacao_anual_sem_ano_intermediario(carregar_modulo):
    panorama = carregar_modulo("pages/01_panorama_geral.py")
    dados = pd.DataFrame({
        "municipio": ["Alegrete"] * 4,
        "ano": [2020, 2021, 2023, 2024],
        "quantidade": [100, 150, 200, 100],
    })
    resultado = panorama.calcular_variacao_anual(dados)
    assert resultado["variacao_pct"].iloc[1] == pytest.approx(50)
    assert pd.isna(resultado["variacao_pct"].iloc[2])
    assert resultado["variacao_pct"].iloc[3] == pytest.approx(-50)


def test_proporcao_ponderada(carregar_modulo):
    alterados = carregar_modulo("pages/05_exames_alterados.py")
    dados = pd.DataFrame({
        "grupo_3": ["25–64 anos", "25–64 anos", "≥65 anos"],
        "quantidade_alterados": [10, 2, 0],
        "total_exames_validos": [100, 10, 0],
    })
    taxas = alterados.agregar_proporcao(dados, ["grupo_3"]).set_index("grupo_3")
    assert taxas.loc["25–64 anos", "proporcao_pct"] == pytest.approx(12 / 110 * 100)
    assert pd.isna(taxas.loc["≥65 anos", "proporcao_pct"])


def test_totalizador_adequabilidade(carregar_modulo):
    adeq = carregar_modulo("pages/04_adequabilidade.py")
    dados = pd.DataFrame({
        "municipio": ["Alegrete", "Alegrete", "Itaqui", "Itaqui"],
        "ano": [2020] * 4,
        "categoria_adequabilidade": ["Satisfatoria", "Insatisfatoria", "Satisfatória", "Rejeitada"],
        "quantidade_amostras": [90, 10, 45, 5],
    })
    limpos, desconhecidas = adeq.preparar_adequabilidade(dados)
    resultado = adeq.adicionar_totalizador(adeq.agregar_municipios(limpos))
    assert desconhecidas == 0
    total = resultado.iloc[-1]
    assert total["total"] == 150
    assert total["taxa_insatisfatorias_pct"] == pytest.approx(10 / 150 * 100)
    assert total["taxa_rejeitadas_pct"] == pytest.approx(5 / 150 * 100)


def test_lacunas_mensais(carregar_modulo):
    main = carregar_modulo("main.py")
    calendario = pd.date_range("2020-01-01", "2025-12-01", freq="MS")
    serie = pd.Series(100, index=calendario).drop(pd.Timestamp("2022-08-01"))
    resultado, ausentes, meses = main.preparar_serie_mensal(serie, list(range(2020, 2026)))
    assert meses == 71
    assert list(ausentes) == [pd.Timestamp("2022-08-01")]
    assert pd.isna(resultado.loc["2022-08-01"])
    resultado, ausentes, meses = main.preparar_serie_mensal(serie, [2020, 2022])
    assert meses == 23
    assert len(ausentes) == 1
    assert resultado.loc["2021"].isna().all()


@pytest.mark.parametrize("rotulo,esperado", [
    ("25–64 anos", "25–64 anos"), (">=65 anos", "≥65 anos"),
    ("<25 anos", "<25 anos"), ("Ignorado", None),
])
def test_classificacao_etaria(carregar_modulo, rotulo, esperado):
    faixa = carregar_modulo("pages/03_faixa_etaria.py")
    assert faixa.q3_group(rotulo) == esperado


@pytest.mark.parametrize(("variacao", "esperado"), [
    (37.70, "Aumento percentual em relação a setembro."),
    (-12.5, "Redução percentual em relação a setembro."),
    (0.0, "Sem variação em relação a setembro."),
    (float("nan"), "Comparação indisponível no recorte."),
])
def test_interpretacao_variacao_outubro(carregar_modulo, variacao, esperado):
    outubro = carregar_modulo("pages/02_outubro_rosa.py")
    assert outubro.interpretar_variacao_mensal(variacao) == esperado
