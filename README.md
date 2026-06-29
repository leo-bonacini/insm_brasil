# Ranking Nacional de Sustentabilidade dos Municípios Brasileiros

**Índice Nacional de Sustentabilidade Municipal (INSM)** · Dados 100% públicos · Ano base 2021

## Visão Geral

Este projeto constrói um ranking científico de sustentabilidade para todos os 5.572 municípios brasileiros, integrando dados do IBGE, INPE, MapBiomas e outras fontes oficiais. O INSM mede simultaneamente desenvolvimento econômico, conservação ambiental e eficiência de uso do solo.

## Principais Resultados

| Posição | Município | UF | INSM |
|---------|-----------|-----|------|
| 1 | Serra do Navio | AP | 100.0 |
| 2 | Guaramiranga | CE | 99.9 |
| 3 | Atalaia do Norte | AM | 99.9 |

Municípios amazônicos e serranos com alta cobertura de vegetação nativa lideram o ranking.

## Fontes de Dados

| Fonte | Dados | Período |
|-------|-------|---------|
| IBGE SIDRA | PIB municipal, população, PAM, PPM | 2018-2021 |
| IBGE Malha Municipal | Shapefile 2022, áreas territoriais | 2022 |
| MapBiomas Coleção 9 | Uso do solo por classe | 1985-2023 |
| INPE TerraBrasilis | Desmatamento PRODES | 2010-2023 |
| SICONFI/FINBRA | Finanças municipais, gasto ambiental | 2015-2022 |
| INEP | IDEB municipal | 2013-2021 |

## Metodologia

### Construção do INSM

1. **Normalização MinMax** (0-100) por indicador
2. **Pesos PCA**: derivados dos loadings ponderados pela variância explicada
3. **Pesos EWM** (Entropy Weight Method): mais peso para indicadores com maior informação
4. **Peso final**: média PCA + EWM, normalizada para soma = 1

### Indicadores do INSM

| Indicador | Peso | Direção |
|-----------|------|---------|
| % área agropecuária (MapBiomas) | 20.4% | Negativa |
| % vegetação nativa (MapBiomas) | 19.2% | Positiva |
| % cobertura florestal (MapBiomas) | 18.9% | Positiva |
| Índice pressão ambiental | 12.0% | Negativa |
| % área urbana (MapBiomas) | 9.9% | Negativa |
| Densidade demográfica | 9.4% | Negativa |
| Variação vegetação nativa 2015-2021 | 8.9% | Positiva |
| PIB per capita | 1.2% | Positiva |

### Machine Learning

Melhor modelo: **LightGBM** (CV R²=0.999, CV RMSE=0.687)

| Modelo | CV RMSE | CV R² |
|--------|---------|-------|
| LightGBM | 0.687 | 0.999 |
| XGBoost | 0.775 | 0.999 |
| GradientBoosting | 0.853 | 0.998 |
| RandomForest | 0.908 | 0.998 |
| ElasticNet | 3.765 | 0.969 |

## Estrutura do Projeto

```
municipal_sustainability/
├── data/
│   ├── raw/          # dados brutos por fonte
│   ├── parquet/      # tabelas fato/dimensão e master table
│   └── external/     # shapefiles IBGE
├── pipeline/
│   ├── download.py   # download automático de todas as fontes
│   └── transform.py  # ETL: clean + features + DuckDB
├── src/
│   ├── download/     # downloaders por fonte
│   ├── preprocessing/ # limpeza e padronização
│   ├── feature_engineering/ # indicadores derivados
│   ├── models/       # INSM index_builder + ML trainer
│   ├── visualization/ # gráficos Plotly + mapa
│   └── dashboard/    # app Streamlit
├── reports/figures/  # HTMLs interativos gerados
├── tests/            # 17 testes automatizados
└── .github/workflows/ci.yml
```

## Como Reproduzir

```bash
pip install uv && uv venv .venv && source .venv/bin/activate
uv pip install -e .

python -m pipeline.download    # download de dados
python -m pipeline.transform   # ETL + features
python -m src.models.index_builder  # INSM
python -m src.models.trainer   # ML
streamlit run src/dashboard/app.py  # dashboard
```

### Docker

```bash
docker build -t sustainability . && docker run -p 8501:8501 sustainability
```

## Testes

```bash
pytest tests/ -v --cov=src
# 17 passed in 1.22s
```

## Tecnologias

Python 3.10 · Pandas · DuckDB · PyArrow · GeoPandas · Scikit-Learn · XGBoost · LightGBM · SHAP · Plotly · Streamlit · Pytest · Ruff · uv · GitHub Actions

## Licença

MIT License · Dados públicos sob licenças abertas de cada fonte oficial.
