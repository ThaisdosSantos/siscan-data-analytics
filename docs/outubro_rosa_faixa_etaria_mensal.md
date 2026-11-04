# Outubro Rosa — proporção mensal de exames por faixa etária

## Situação da fonte

O gráfico da página `src/app/pages/02_outubro_rosa.py` foi implementado com leitura
condicional de `gold.fato_outubro_rosa_faixa_etaria`. **Esta tabela ainda não foi criada
no Databricks**. Sem ela, a página apresenta uma mensagem informativa e não calcula
proporções mensais artificiais.

As tabelas atuais `gold.fato_conformidade_faixa_etaria` (município × ano × faixa)
e `gold.fato_analise_outubro_rosa` (município × ano × mês) **não podem ser unidas
para recuperar distribuição mensal verdadeira de faixa etária**. Uma junção por
município e ano repetiria volumes mensais entre faixas e produziriam percentuais
enganosos. A origem atualmente consultada para Q3 também tem somente ano.

## Contrato da nova tabela Gold

Criar a tabela `tcc-analise-siscan-10crs.gold.fato_outubro_rosa_faixa_etaria`,
a partir de uma **extração SISCAN que contenha simultaneamente mês de competência,
ano, município de residência, faixa etária e quantidade de exames**.

| Coluna | Tipo | Regra |
|---|---|---|
| `codigo_municipio` | STRING ou INT | Código IBGE do município da 10ª CRS |
| `municipio` | STRING | Município de residência |
| `ano` | INT | 2020 a 2025 |
| `mes` | INT | 9, 10, 11 ou 12 |
| `grupo_etario` | STRING | `<25 anos`, `25–64 anos`, `≥65 anos` |
| `quantidade_exames` | BIGINT | Número não negativo de exames efetivamente observados na competência |

**Granularidade única:** `codigo_municipio × ano × mes × grupo_etario`.

Agrupar as faixas detalhadas desta maneira:

- **<25 anos:** até 9, 10–14, 15–19 e 20–24.
- **25–64 anos:** 25–29 até 60–64.
- **≥65 anos:** 65–69, 70–74, 75–79 e acima de 79.

A faixa `Ignorado` deve ser registrada em uma métrica de qualidade
separada; não deve ser atribuída a nenhum dos três grupos.

## Cálculo no dashboard

1. Aplicar os filtros globais de ano e município.
2. Somar `quantidade_exames` por `mes × grupo_etario` entre os anos selecionados.
3. Para cada mês, dividir o volume do grupo pelo total dos três grupos com idade
conhecida no mesmo mês e multiplicar por 100.
4. Mostrar barras empilhadas de 100% para setembro, outubro, novembro e dezembro,
com tooltip contendo quantidade e proporção. A exportação PNG mantém os valores.

A percentagem é uma **composição dos registros do mês**, não uma taxa de
participação populacional e nem uma medida de efetividade causal da campanha.

## Validações antes de publicar os dados

- Confirmar ausência de chaves duplicadas por município, ano, mês e grupo.
- Garantir `quantidade_exames >= 0` e todos os grupos válidos.
- Conferir quantidade dos três grupos + idade ignorada contra o total do mesmo
município/ano/mês nas extrações da mesma população e critério.
- Não preencher competências ausentes com zero.
- Comparar os agregados de setembro a dezembro com a fonte TABNET extraída.
- Após criar a tabela, limpar o cache do Streamlit ou aguardar atualização do cache
para que a página comece a mostrar o gráfico automaticamente.

**Não** estimar distribuição mensal a partir de proporções anuais da Q3.
