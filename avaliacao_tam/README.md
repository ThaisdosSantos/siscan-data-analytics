# Avaliação TAM — Dashboard SISCAN

Análise reprodutível das respostas ao questionário de aceitação de tecnologia aplicado ao Dashboard SISCAN (2026). **Não faz parte da execução do Streamlit nem das camadas Bronze/Silver/Gold.**

## Organização

```text
avaliacao_tam/
├── analise_tam.py                       # pipeline reproduzível (Pandas + Matplotlib)
├── notebooks/
│   └── 01_analise_tam.ipynb             # demonstração passo a passo dos cálculos e reprodução da tabela TAM
├── dados/
│   ├── respostas_tam.csv                # exportação ORIGINAL do formulário
│   └── respostas_abertas_codificacao_local.csv  # ficha para codificação manual
├── figuras/                             # PNG, 320 dpi
├── tabelas/                             # PNG (artigo) + CSV (auditoria) + metadados JSON
├── test_analise_tam.py                  # verificações do conjunto analisado
├── requirements.txt
└── README.md
```

## Executar a partir da raiz do projeto SISCAN

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r avaliacao_tam/requirements.txt
python avaliacao_tam/analise_tam.py
python -m unittest discover -s avaliacao_tam -p 'test_*.py' -v
```

Também é possível abrir `avaliacao_tam/notebooks/01_analise_tam.ipynb` no Jupyter e executar as células na ordem. O notebook explica os **sete campos da tabela de construtos** e mostra as fórmulas e cálculos numéricos dos quatro construtos, com conferência automatizada em relação ao script. O script e o notebook utilizam caminhos relativos a `avaliacao_tam/`, independentemente de onde o terminal foi aberto.

## Tratamento das respostas

- Registros recebidos: **43**.
- Sem concordância em participar: **1**, excluído de qualquer resultado.
- Com consentimento: **42**. Esse conjunto pode servir para descrever os participantes que consentiram, se isso estiver explicitado na redação.
- Com consentimento, mas sem conseguir explorar o dashboard: **1**, não incluído nas análises de aceitação e de experiência de uso.
- **Base analítica principal: 41 respondentes**, utilizada nas figuras e tabelas geradas.
- O formulário foi aplicado por adesão voluntária. Não inferir representatividade de profissionais da 10ª CRS nem causalidade.
- Resposta contraditória em questão de dificuldades: **1** participante marcou ausência e presença de dificuldades. O script prioriza a marcação de dificuldade e registra a ocorrência nos metadados. A questão admite múltiplas respostas: percentuais por categoria não devem somar 100%.

## Cálculos e regras

**Escala Likert de 1 a 5:** discordo totalmente (1), discordo parcialmente (2), neutro (3), concordo parcialmente (4), concordo totalmente (5). Todos os itens TAM foram formulados positivamente; nenhuma inversão é aplicada.

**Construtos:**

| Sigla | Dimensão | Itens |
|---|---|---:|
| PU | Utilidade percebida | PU1 a PU5 |
| PEOU | Facilidade de uso percebida | PEOU1 a PEOU5 |
| AT | Atitude em relação ao uso | AT1 a AT3 |
| BI | Intenção de uso | BI1 a BI3 |

O notebook demonstra com números a média, mediana, concordância (por exemplo, **193/205 = 94,15% para PU**) e alfa (por exemplo, **5/4 × (1 − 2,8780/11,3280) = 0,93 para PU**). A média do construto é a média dos **escores individuais completos**, cada escore correspondendo à média dos itens daquele construto. O desvio-padrão é amostral (`ddof=1`) entre os escores individuais. A mediana também é calculada sobre os escores individuais. A **concordância positiva** equivale à proporção de respostas 4 ou 5 entre todas as respostas válidas dos itens do construto. Assim, é um indicador de **respostas a itens**, não a proporção de participantes com escore acima de determinado ponto.

O **alfa de Cronbach** é calculado separadamente por construto: `k/(k−1) × (1 − Σvar(item)/var(soma de itens))`, com variâncias amostrais e casos completos. Ele avalia consistência interna, não demonstra validade do construto.

**Funcionalidades (F1–F8):** a opção `Não utilizei / Não se aplica` é excluída das respostas válidas para média e concordância, e contabilizada em coluna separada. Seus percentuais de não utilização utilizam o total de 41 participantes; os percentuais de concordância utilizam apenas `n válido` de cada funcionalidade.

**Respostas abertas:** o arquivo `dados/respostas_abertas_codificacao_local.csv` contém uma ficha a ser **revisada e categorizada manualmente**, com identificadores analíticos (P01, P02...). Não foram atribuídas categorias por regras automáticas ou inferidas frequências temáticas não revisadas.

## Produtos para inserir no Overleaf

### Figuras (PNG, 320 dpi)

| Arquivo | Conteúdo |
|---|---|
| `figuras/01a_perfil_atuacao.png` | Perfil dos participantes |
| `figuras/01b_familiaridade.png` | Familiaridade com dashboards |
| `figuras/01c_experiencia_saude.png` | Experiência com sistemas de saúde pública |
| `figuras/01d_pagina_mais_util.png` | Página considerada mais útil |
| `figuras/01e_paginas_acessadas.png` | Páginas acessadas |
| `figuras/02_itens_tam_concordancia.png` | Concordância positiva dos 16 itens, agrupada em quatro painéis para o artigo |
| `figuras/02_likert_pu.png` | Distribuição nas 5 categorias Likert, apenas PU |
| `figuras/02_likert_peou.png` | Distribuição nas 5 categorias Likert, apenas PEOU |
| `figuras/02_likert_at.png` | Distribuição nas 5 categorias Likert, apenas AT |
| `figuras/02_likert_bi.png` | Distribuição nas 5 categorias Likert, apenas BI |
| `figuras/03_medias_construtos.png` | Média dos quatro construtos |
| `figuras/04_funcionalidades_concordancia.png` | Concordância nas oito funcionalidades |
| `figuras/05_dificuldades_relato.png` | Dificuldades assinaladas |

### Tabelas (PNG e CSV)

| PNG | Conteúdo |
|---|---|
| `tabelas/01_fluxo_amostral.png` | Critérios de inclusão/exclusão |
| `tabelas/02_indicadores_construtos.png` | Média, mediana, concordância e alfa |
| `tabelas/03_funcionalidades.png` | Concordância válida e não utilização |
| `tabelas/04_dificuldades.png` | Frequências e percentuais de dificuldades |

Os arquivos CSV são mantidos para inspeção numérica, arredondamentos e possível futura transcrição para tabelas LaTeX. Os PNG contêm valores com **duas casas decimais** e utilizam uma paleta azul compatível com o dashboard. A exportação é feita a **320 dpi**.

### Exemplo no Overleaf

Carregue o arquivo PNG na pasta `img/` do seu projeto Overleaf e use, no corpo do artigo:

```latex
\begin{figure}[htbp]
    \centering
    \caption{Concordância positiva nos itens do modelo TAM}
    \includegraphics[width=\linewidth]{img/02_itens_tam_concordancia.png}
    \label{fig:tam_likert}
\end{figure}
```

O exemplo exige `\usepackage{graphicx}`. Para figuras muito altas, avalie dimensões e legibilidade no PDF final. A disposição e a identificação formal de tabelas/quadros devem seguir o modelo institucional do artigo; PNG é uma escolha de produção gráfica, não substitui automaticamente uma tabela LaTeX acessível.

## Atenção ao compartilhamento das respostas

A exportação original **não contém nomes nem e-mails explícitos** nas 34 colunas inspecionadas, mas inclui **carimbos de data/hora e respostas abertas**. Dependendo do contexto, a combinação desses elementos pode permitir identificação indireta. Por isso, é aconselhável revisar o arquivo antes de torná-lo publicamente acessível. O CSV original foi preservado a pedido da autora. O conjunto é publicado no repositório, conforme autorização da autora, após avaliação do risco de identificação indireta.

## Interpretação e limites

Esta análise é descritiva e exploratória. Médias e alfa de Cronbach complementam frequências e medianas; não se recomenda classificar pontuações como "validadas" apenas com base no alfa. Intenção de uso não equivale a uso futuro observado. A avaliação TAM com respondentes não substitui a validação anterior do problema analítico e da plataforma com profissionais da saúde.

### Rodapés e citação no artigo

Os PNGs são exportados **sem rodapé de fonte ou notas**, para evitar duplicação com a legenda/fonte inseridas no Overleaf. As definições dos indicadores e denominadores permanecem documentadas no notebook e nos CSVs.
