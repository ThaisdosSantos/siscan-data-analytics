"""Infraestrutura da suíte E2E: servidor isolado e navegador Chromium."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import plotly
import pytest
from playwright.sync_api import Page, expect

from gold_fixtures import gerar_gold

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def app_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Inicia Streamlit em uma porta livre e encerra o processo ao final."""
    gold_dir = tmp_path_factory.mktemp("gold")
    gerar_gold(gold_dir)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    artifacts = ROOT / "test-results"
    artifacts.mkdir(exist_ok=True)
    log_path = artifacts / "streamlit.log"
    env = {**os.environ, "SISCAN_GOLD_CSV_DIR": str(gold_dir), "PYTHONUNBUFFERED": "1"}
    command = [
        sys.executable, "-m", "streamlit", "run", "main.py",
        "--server.address=127.0.0.1", f"--server.port={port}",
        "--server.headless=true", "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, cwd=ROOT / "src/app", env=env,
            stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail(f"Streamlit encerrou antes de iniciar. Consulte {log_path}.")
                try:
                    with urlopen(f"{url}/_stcore/health", timeout=2) as response:
                        if response.status == 200 and response.read().strip() == b"ok":
                            break
                except (URLError, TimeoutError):
                    time.sleep(0.2)
            else:
                pytest.fail(f"Streamlit não iniciou em 60 segundos. Consulte {log_path}.")
            yield url
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


@pytest.fixture
def dashboard(page: Page, app_url: str) -> Page:
    """Abre a aplicação real e fornece Plotly JS local para os iframes."""
    js = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
    page.context.route("https://cdn.plot.ly/**", lambda route: route.fulfill(
        path=js, content_type="application/javascript",
    ))
    page.set_default_timeout(20_000)
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(app_url)
    expect(page.get_by_role("heading", level=1)).to_contain_text(
        "Rastreamento do câncer do colo do útero", timeout=40_000,
    )
    expect(page.locator(".exec-metric-value").first).to_have_text("79.420", timeout=40_000)
    return page
