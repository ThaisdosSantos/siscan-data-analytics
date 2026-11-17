# Testes automatizados

A suíte utiliza pytest e Playwright (Chromium) contra o Streamlit local.
Os fatos Gold são gerados em um diretório temporário, sem Databricks e
sem credenciais. A variável `SISCAN_GOLD_CSV_DIR` é configurada apenas
no processo de teste; o dashboard publicado continua usando Databricks SQL.

Na raiz do repositório:

```bash
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m pytest tests/test_metrics.py -v
python -m pytest tests/e2e -v --browser chromium --tracing retain-on-failure
```

Para visualizar o navegador, acrescente `--headed` ao comando E2E.
No Linux, utilize `python -m playwright install --with-deps chromium`
se faltarem bibliotecas do sistema.

O GitHub Actions executa compilação, testes unitários e E2E. Os relatórios
JUnit, logs do Streamlit, screenshots e traces de falhas são disponibilizados
como artefatos da execução. Os testes cobrem a aplicação e os cálculos
locais; não validam a disponibilidade do Databricks nem a exatidão dos dados reais.
