"""Valida jornadas do usuário no dashboard, com dados determinísticos."""

import csv
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


def navegar(page: Page, nome: str, titulo: str) -> None:
    """Abre uma página pelo menu e aguarda seu cabeçalho."""
    page.get_by_test_id("stSidebar").get_by_test_id("stPageLink").get_by_text(nome, exact=True).click()
    expect(page.get_by_role("heading", level=1)).to_have_text(titulo, timeout=30_000)


def sem_erros(page: Page) -> None:
    """Verifica que a aplicação não apresentou exceções ou erros de consulta."""
    expect(page.get_by_test_id("stException")).to_have_count(0)
    expect(page.get_by_text("Não foi possível consultar a camada Gold", exact=False)).to_have_count(0)
    expect(page.get_by_text("Não foi possível carregar a tabela CSV", exact=False)).to_have_count(0)


def abrir_filtro(page: Page, chave: str) -> None:
    """Abre o painel de filtro identificado pela chave do Streamlit."""
    summary = page.locator(f".st-key-{chave} summary")
    if summary.locator("xpath=..").get_attribute("open") is None:
        summary.click()


def test_visao_executiva(dashboard: Page) -> None:
    """Confirma indicadores e aviso de competência ausente."""
    expect(dashboard.locator(".exec-metric-value")).to_have_text(
        ["79.420", "11 de 11", "71 de 72", "1,08%"]
    )
    dashboard.locator(".exec-metric-help summary").click()
    expect(dashboard.locator(".exec-metric-tip")).to_contain_text("08/2022")
    expect(dashboard.get_by_text("Explore as análises", exact=True)).to_be_visible()
    sem_erros(dashboard)


@pytest.mark.parametrize(("chave", "titulo", "rota"), [
    ("exec-nav-panorama", "Volume de exames por competência e município", "panorama_geral"),
    ("exec-nav-alterados", "Exames citopatológicos alterados", "exames_alterados"),
    ("exec-nav-outubro", "Outubro Rosa: produção e perfil etário dos exames", "outubro_rosa"),
])
def test_atalhos_visao_executiva(dashboard: Page, chave: str, titulo: str, rota: str) -> None:
    """Clica na região da seta de cada card e verifica a navegação interna."""
    link = dashboard.locator(f".st-key-{chave}").get_by_role("link")
    expect(link).to_be_visible()
    caixa = link.bounding_box()
    assert caixa is not None and caixa["height"] >= 70
    link.click(position={"x": caixa["width"] - 20, "y": caixa["height"] / 2})
    expect(dashboard).to_have_url(re.compile(rf"/{rota}/?(?:\?.*)?$"))
    expect(dashboard.get_by_role("heading", level=1)).to_have_text(titulo, timeout=30_000)
    sem_erros(dashboard)


@pytest.mark.parametrize(("nome", "titulo", "marco"), [
    ("Panorama geral", "Volume de exames por competência e município",
     "Variação anual de exames por município (ano a ano)"),
    ("Faixa etária", "Faixa etária e produção de exames",
     "Tabela consolidada de exames na população-alvo (25–64 anos)"),
    ("Outubro Rosa", "Outubro Rosa: produção e perfil etário dos exames",
     "Dados para consulta e exportação"),
    ("Adequabilidade", "Adequabilidade das amostras",
     "Adequabilidade das amostras por município"),
    ("Exames alterados", "Exames citopatológicos alterados",
     "Composição dos resultados citopatológicos"),
])
def test_navegacao(dashboard: Page, nome: str, titulo: str, marco: str) -> None:
    """Confirma navegação e renderização das cinco páginas analíticas."""
    navegar(dashboard, nome, titulo)
    expect(dashboard.get_by_role("heading", name=re.compile(re.escape(marco)))).to_be_visible(
        timeout=40_000
    )
    sem_erros(dashboard)


@pytest.mark.parametrize(("largura", "altura"), [(1280, 900), (1015, 740), (414, 736)])
def test_cabecalho_adequabilidade_sem_corte(dashboard: Page, largura: int, altura: int) -> None:
    """O cabeçalho deve começar abaixo da barra superior, inclusive em telas menores."""
    # Navega antes de reduzir a largura para não depender do menu móvel.
    navegar(dashboard, "Adequabilidade", "Adequabilidade das amostras")
    dashboard.set_viewport_size({"width": largura, "height": altura})
    kicker = dashboard.locator(".st-key-adequabilidade_header .pet-hero-kicker")
    expect(kicker).to_have_text("Qualidade da amostra")
    expect(kicker).to_be_visible()
    dashboard.wait_for_function("""() => {
        const barra = document.querySelector('[data-testid="stHeader"]');
        const hero = document.querySelector('.st-key-adequabilidade_header .pet-hero');
        const kicker = hero?.querySelector('.pet-hero-kicker');
        if (!barra || !hero || !kicker) return false;
        const limite = barra.getBoundingClientRect().bottom;
        return hero.getBoundingClientRect().top >= limite &&
            kicker.getBoundingClientRect().top >= limite;
    }""")
    sem_erros(dashboard)


def test_espacamento_perfil_etario(dashboard: Page) -> None:
    """Evita espaços vazios entre as fontes e o primeiro título da faixa etária."""
    navegar(dashboard, "Faixa etária", "Faixa etária e produção de exames")
    fontes = dashboard.locator(".st-key-q3_sources_panel [data-testid=stExpander]")
    perfil = dashboard.locator(".q3-profile-title")
    expect(fontes).to_be_visible()
    expect(perfil).to_be_visible()
    for largura, altura in [(1280, 900), (414, 736)]:
        dashboard.set_viewport_size({"width": largura, "height": altura})
        expect(perfil).to_be_visible()
        dashboard.wait_for_function("""() => {
            const fontes = document.querySelector('.st-key-q3_sources_panel [data-testid=stExpander]');
            const titulo = document.querySelector('.q3-profile-title');
            if (!fontes || !titulo) return false;
            const distancia = titulo.getBoundingClientRect().top - fontes.getBoundingClientRect().bottom;
            return distancia >= 0 && distancia <= 45;
        }""")
    sem_erros(dashboard)


def test_navegacao_preserva_menu(dashboard: Page) -> None:
    """Confirma que o menu permanece no DOM e o filtro durante a troca."""
    sidebar = dashboard.get_by_test_id("stSidebar")
    marca = sidebar.locator(".lovable-brand")
    expect(marca).to_be_visible()
    abrir_filtro(dashboard, "siscan_year_panel")
    anos = dashboard.locator(".st-key-siscan_year_panel")
    anos.get_by_role("button", name="Limpar", exact=True).click()
    expect(anos.get_by_role("progressbar")).to_have_attribute("aria-valuenow", "0")
    anos.get_by_role("button", name="2020", exact=True).click()
    expect(anos.get_by_role("progressbar")).to_have_attribute("aria-valuenow", "1")
    dashboard.evaluate("""() => {
        window.__siscanSidebar = document.querySelector(".lovable-brand");
        window.__siscanNav = document.querySelector('[data-testid="stSidebar"]');
        window.__siscanMenuWasRemoved = false;
        window.__siscanObserver = new MutationObserver(() => {
            if (!window.__siscanNav.isConnected) window.__siscanMenuWasRemoved = true;
        });
        window.__siscanObserver.observe(document.body, {childList: true, subtree: true});
    }""")
    navegar(dashboard, "Faixa etária", "Faixa etária e produção de exames")
    expect(sidebar.get_by_text("Painel SISCAN", exact=True)).to_be_visible()
    expect(dashboard.get_by_role("button", name="Aplicar filtros")).to_be_visible()
    expect(dashboard.get_by_role("status", name="Recorte ativo")).to_contain_text("2020–2025")
    assert dashboard.evaluate("""() => {
        window.__siscanObserver.disconnect();
        return !window.__siscanMenuWasRemoved &&
            window.__siscanSidebar === document.querySelector(".lovable-brand");
    }""")
    sem_erros(dashboard)


def test_interpretacao_kpis_outubro_rosa(dashboard: Page) -> None:
    """Verifica as médias anuais e os desvios com a Gold sintética."""
    navegar(dashboard, "Outubro Rosa", "Outubro Rosa: produção e perfil etário dos exames")
    kpis = dashboard.locator(".st-key-outubro_producao_kpis")
    for rotulo, valor in [
        ("Média de exames em setembro", "1.100,00"),
        ("Média de exames em outubro", "1.320,00"),
        ("Variação percentual média", "+20,00%"),
    ]:
        kpi = kpis.get_by_test_id("stMetric").filter(has_text=rotulo)
        expect(kpi.get_by_test_id("stMetricValue")).to_have_text(valor)
    expect(kpis.get_by_text("Desvio padrão: 0,00 exames.", exact=True)).to_have_count(2)
    expect(kpis.get_by_text(
        "Aumento médio anual de setembro para outubro.",
        exact=False,
    )).to_be_visible()
    expect(kpis.get_by_text("Desvio padrão: 0,00 pontos percentuais.", exact=False)).to_be_visible()
    expect(dashboard.get_by_text("Base da comparação: 6 ano(s)", exact=False)).to_be_visible()
    sem_erros(dashboard)


def test_lacuna_agosto_2022_visao_executiva(dashboard: Page) -> None:
    """Confirma que o mês ausente aparece no próprio gráfico e na legenda."""
    card = dashboard.locator(".st-key-exec-month-card")
    expect(card.get_by_text("08/2022", exact=False)).to_be_visible()
    expect(card.get_by_text("A lacuna não representa zero exames.", exact=False)).to_be_visible()
    frame = card.frame_locator("iframe")
    expect(frame.locator(".xtick text").filter(has_text="08/22")).to_contain_text(
        "Sem dados", timeout=30_000,
    )
    expect(frame.locator(".annotation-text")).to_have_count(0)
    sem_erros(dashboard)


def test_lacuna_agosto_2022(dashboard: Page) -> None:
    """Confirma a identificação visual da competência sem dados no gráfico."""
    navegar(dashboard, "Panorama geral", "Volume de exames por competência e município")
    expect(dashboard.get_by_text(
        "Agosto/2022 — sem registros na base analisada.", exact=False
    )).to_be_visible()
    frame = dashboard.frame_locator("iframe").first
    expect(frame.locator(".xtick text").filter(has_text="ago/22*")).to_have_text(
        "ago/22*", timeout=30_000,
    )
    sem_erros(dashboard)


def test_filtros_persistem_entre_paginas(dashboard: Page) -> None:
    """Aplica um ano e município e verifica persistência após navegação."""
    abrir_filtro(dashboard, "siscan_year_panel")
    anos = dashboard.locator(".st-key-siscan_year_panel")
    anos.get_by_role("button", name="Limpar", exact=True).click()
    expect(anos.get_by_role("progressbar")).to_have_attribute("aria-valuenow", "0")
    anos.get_by_role("button", name="2020", exact=True).click()
    abrir_filtro(dashboard, "siscan_city_panel")
    cidades = dashboard.locator(".st-key-siscan_city_panel")
    cidades.get_by_role("button", name="Limpar", exact=True).click()
    expect(cidades.get_by_role("progressbar")).to_have_attribute("aria-valuenow", "0")
    cidades.get_by_role("button", name="Alegrete", exact=True).click()
    expect(dashboard.locator(".exec-metric-value").first).to_have_text("79.420")
    dashboard.get_by_role("button", name="Aplicar filtros").click()
    expect(dashboard.locator(".exec-metric-value").first).to_have_text("1.220", timeout=30_000)
    expect(dashboard.locator(".exec-metric-value").nth(2)).to_have_text("12 de 12")
    dashboard.locator(".st-key-exec-nav-panorama").get_by_role("link").click()
    expect(dashboard.get_by_role("heading", level=1)).to_have_text(
        "Volume de exames por competência e município", timeout=30_000,
    )
    escopo = dashboard.get_by_role("status", name="Recorte ativo")
    expect(escopo).to_contain_text("2020")
    expect(escopo).to_contain_text("1 de 11 municípios")
    expect(dashboard.get_by_test_id("stMetricValue").first).to_have_text("1.220")
    sem_erros(dashboard)


def test_filtro_vazio(dashboard: Page) -> None:
    """Nenhum ano selecionado exibe estado vazio sem exceção."""
    abrir_filtro(dashboard, "siscan_year_panel")
    dashboard.locator(".st-key-siscan_year_panel").get_by_role("button", name="Limpar").click()
    dashboard.get_by_role("button", name="Aplicar filtros").click()
    expect(dashboard.get_by_text("Não há registros para os filtros selecionados", exact=False)).to_be_visible()
    expect(dashboard.locator(".exec-metric-value")).to_have_count(0)
    sem_erros(dashboard)


def test_exportacao_csv_adequabilidade(dashboard: Page, tmp_path: Path) -> None:
    """Baixa a tabela real e verifica o totalizador e as contagens."""
    navegar(dashboard, "Adequabilidade", "Adequabilidade das amostras")
    with dashboard.expect_download() as evento:
        dashboard.get_by_role("button", name=re.compile("Exportar CSV")).click()
    download = evento.value
    assert download.suggested_filename == "siscan_adequabilidade.csv"
    destino = tmp_path / download.suggested_filename
    download.save_as(destino)
    with destino.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))
    assert len(linhas) == 12
    assert linhas[-1]["municipio"] == "Total"
    assert float(linhas[-1]["total"]) == 79420
    assert float(linhas[-1]["Insatisfatória"]) == 132
    assert float(linhas[-1]["Rejeitada"]) == 66
    assert float(linhas[-1]["taxa_insatisfatorias_pct"]) == pytest.approx(132 / 79420 * 100)
    sem_erros(dashboard)


def test_exportacao_png(dashboard: Page, tmp_path: Path) -> None:
    """Exporta PNG pelo menu contextual do gráfico mensal."""
    frame = dashboard.frame_locator(".st-key-exec-month-card iframe").first
    grafico = frame.locator(".js-plotly-plot .main-svg").first
    expect(grafico).to_be_visible(timeout=30_000)
    grafico.click(button="right", position={"x": 100, "y": 100})
    menu = frame.get_by_role("menuitem", name=re.compile("Baixar imagem PNG"))
    expect(menu).to_be_visible()
    with dashboard.expect_download(timeout=60_000) as evento:
        menu.click()
    download = evento.value
    assert download.suggested_filename == "visao_executiva_evolucao_mensal.png"
    destino = tmp_path / download.suggested_filename
    download.save_as(destino)
    assert destino.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_analises_avancadas(dashboard: Page) -> None:
    """Abre a composição citopatológica e alterna quantidade/percentual."""
    navegar(dashboard, "Exames alterados", "Exames citopatológicos alterados")
    dashboard.get_by_text("Exibir análises avançadas por categoria citopatológica", exact=True).click()
    expect(dashboard.get_by_role("heading", name="Distribuição etária dos exames alterados por categoria")).to_be_visible(
        timeout=40_000
    )
    seletor = dashboard.locator(".st-key-q5_categoria_anual_visual")
    seletor.get_by_role("combobox").click()
    dashboard.get_by_role("option", name="Participação por categoria (%)", exact=True).click()
    expect(seletor.get_by_role("combobox")).to_have_value("Participação por categoria (%)")
    expect(dashboard.get_by_role("heading", name="Distribuição etária dos exames alterados por categoria")).to_be_visible()
    sem_erros(dashboard)


def test_responsividade(dashboard: Page) -> None:
    """Confirma a presença dos cartões após redimensionar para celular."""
    dashboard.set_viewport_size({"width": 414, "height": 736})
    expect(dashboard.get_by_role("heading", level=1)).to_be_visible()
    expect(dashboard.locator(".exec-metric-value").first).to_have_text("79.420")
    expect(dashboard.locator(".exec-metric-value")).to_have_count(4)
    sem_erros(dashboard)
