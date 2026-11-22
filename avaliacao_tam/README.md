# Avaliação TAM — Dashboard SISCAN

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?style=flat&logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7%2B-11557C?style=flat&logo=python&logoColor=white)](https://matplotlib.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-1.0%2B-F37626?style=flat&logo=jupyter&logoColor=white)](https://jupyter.org/)
[![unittest](https://img.shields.io/badge/Tests-unittest-0A9EDC?style=flat&logo=python&logoColor=white)](https://docs.python.org/3/library/unittest.html)
[![PNG](https://img.shields.io/badge/Exporta%C3%A7%C3%A3o-PNG%20320%20DPI-64748B?style=flat)](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)

Módulo de análise das respostas ao questionário de aceitação de tecnologia (*Technology Acceptance Model* — TAM) aplicado ao Dashboard SISCAN em 2026. Implementa o tratamento dos dados, o cálculo de indicadores descritivos e de consistência interna e a geração automatizada de visualizações e tabelas.

A avaliação é independente da aplicação Streamlit e do pipeline de engenharia de dados nas camadas Bronze, Silver e Gold.

## Tecnologias utilizadas

| Componente | Tecnologia | Aplicação |
| --- | --- | --- |
| Linguagem | Python 3.11 | Implementação do processamento e dos cálculos. |
| Análise de dados | Pandas e NumPy | Leitura do CSV, seleção das respostas, codificação da escala Likert e estatísticas descritivas. |
| Visualização | Matplotlib | Geração de gráficos e tabelas em PNG (320 DPI). |
| Ambiente analítico | Jupyter Notebook | Execução documentada dos procedimentos e demonstração dos cálculos. |
| Testes | `unittest` | Verificações automatizadas dos indicadores e resultados. |
| Fonte de dados | Google Forms (CSV) | Respostas ao questionário TAM. |

As dependências estão declaradas em `avaliacao_tam/requirements.txt`.

## Organização

```text
avaliacao_tam/
├── analise_tam.py                    # processamento, indicadores e exportações
├── notebooks/
│   └── 01_analise_tam.ipynb          # execução e detalhamento dos cálculos
├── dados/
│   ├── respostas_tam.csv             # respostas originais do questionário
│   └── respostas_abertas_codificacao_local.csv
├── figuras/                          # gráficos PNG (320 DPI)
├── tabelas/                          # tabelas PNG, resultados CSV e metadados JSON
├── test_analise_tam.py               # testes automatizados
├── requirements.txt                 # dependências do módulo
└── README.md
```

## Execução

Na raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r avaliacao_tam/requirements.txt
python avaliacao_tam/analise_tam.py
```

Execução dos testes:

```bash
python -m unittest discover -s avaliacao_tam -p 'test_*.py' -v
```

O notebook `avaliacao_tam/notebooks/01_analise_tam.ipynb` apresenta os procedimentos, as fórmulas, os exemplos numéricos e a conferência dos indicadores gerados pelo script. Os caminhos de entrada e saída são resolvidos em relação ao diretório `avaliacao_tam/`.

## Tratamento das respostas

| Etapa | Quantidade |
| --- | ---: |
| Respostas recebidas | 43 |
| Resposta sem consentimento | 1 |
| Respostas com consentimento | 42 |
| Participante sem exploração do dashboard | 1 |
| **Respostas elegíveis para a análise TAM** | **41** |

A base analítica principal reúne as 41 respostas com consentimento e exploração declarada da plataforma. O registro sem consentimento é excluído da análise; a resposta consentida sem exploração não integra os indicadores de experiência de uso.

Na questão de dificuldades, um registro apresenta marcações simultâneas de ausência e presença de dificuldade. O processamento considera as dificuldades assinaladas e registra a inconsistência nos metadados. Como a questão admite múltiplas respostas, os percentuais por categoria não são mutuamente exclusivos.

## Indicadores e regras de cálculo

As 16 afirmações TAM utilizam escala Likert de cinco pontos, codificada de 1 (discordo totalmente) a 5 (concordo totalmente). Os enunciados são positivos e não requerem recodificação reversa.

| Código | Construto | Itens |
| --- | --- | ---: |
| PU | Utilidade percebida | 5 |
| PEOU | Facilidade de uso percebida | 5 |
| AT | Atitude em relação ao uso | 3 |
| BI | Intenção de uso | 3 |

Os indicadores são calculados separadamente para cada construto:

- **Escore individual:** média dos itens respondidos integralmente pelo participante no construto.
- **Média e mediana:** calculadas sobre os escores individuais completos.
- **Desvio-padrão:** desvio-padrão amostral dos escores individuais (`ddof=1`).
- **Concordância positiva:** percentual de respostas 4 ou 5 entre as respostas válidas dos itens do construto; representa respostas a itens, não a proporção de participantes.
- **Alfa de Cronbach:** consistência interna dos itens, calculada com variâncias amostrais e casos completos, pela expressão `k/(k−1) × (1 − Σvar(itens)/var(soma dos itens))`.

Na avaliação das oito funcionalidades (F1–F8), a alternativa `Não utilizei / Não se aplica` é contabilizada separadamente e excluída dos cálculos de média e concordância. O percentual de não utilização considera os 41 participantes; a concordância utiliza o total de respostas válidas de cada funcionalidade.

As respostas abertas estão disponíveis para codificação manual em `dados/respostas_abertas_codificacao_local.csv`, com identificadores analíticos. O módulo não atribui automaticamente categorias temáticas.

## Escopo e limitações

A avaliação possui caráter descritivo e exploratório, com participação voluntária e sem amostragem probabilística. Os resultados descrevem os respondentes elegíveis e não representam estimativas populacionais da aceitação entre profissionais da 10ª CRS.

O alfa de Cronbach fornece evidências de consistência interna, sem estabelecer isoladamente a validade dos construtos. A intenção declarada de uso não corresponde à utilização futura observada. A avaliação TAM é distinta das etapas de validação do problema analítico e do dashboard realizadas com profissionais da saúde durante o desenvolvimento.