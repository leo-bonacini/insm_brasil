"""Tests for index construction and INSM score properties."""
import numpy as np
import pandas as pd
import pytest
from src.models.index_builder import build_insm, _pca_weights, _entropy_weights
from sklearn.decomposition import PCA


@pytest.fixture
def sample_master():
    """Small synthetic master table for index testing."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "geocodigo": [str(1100000 + i) for i in range(n)],
        "municipio": [f"Município {i}" for i in range(n)],
        "uf_sigla": np.random.choice(["AM", "PA", "SP", "MG", "RS"], n),
        "area_km2": np.random.uniform(100, 50000, n),
        "populacao": np.random.uniform(5000, 5_000_000, n),
        "pib_mil_reais": np.random.uniform(10_000, 100_000_000, n),
        "pct_nativa": np.random.uniform(5, 90, n),
        "pct_florestal": np.random.uniform(2, 80, n),
        "pct_agro": np.random.uniform(5, 70, n),
        "pct_urbana": np.random.uniform(0.1, 30, n),
        "variacao_nativa_pp": np.random.uniform(-10, 5, n),
        "indice_pressao_ambiental": np.random.uniform(0, 10, n),
        "pib_per_capita": np.random.uniform(5000, 200000, n),
        "densidade_pop": np.random.uniform(1, 5000, n),
    })


def test_insm_score_range(sample_master):
    result, _ = build_insm(sample_master)
    assert result["insm_score"].min() >= 0
    assert result["insm_score"].max() <= 100.001  # floating point tolerance


def test_insm_all_municipalities(sample_master):
    result, _ = build_insm(sample_master)
    assert len(result) == len(sample_master)


def test_insm_ranking_unique(sample_master):
    result, _ = build_insm(sample_master)
    # Rankings should be integers 1..n
    assert result["insm_ranking"].min() == 1
    assert result["insm_ranking"].max() == len(sample_master)


def test_insm_weights_sum_to_one(sample_master):
    _, weights = build_insm(sample_master)
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-6, f"Weights sum to {total}, expected 1.0"


def test_insm_weights_positive(sample_master):
    _, weights = build_insm(sample_master)
    assert all(w >= 0 for w in weights.values())


def test_entropy_weights_sum(sample_master):
    cols = ["pct_nativa", "pct_florestal", "pib_per_capita"]
    X = sample_master[cols].fillna(0) + 1
    from sklearn.preprocessing import MinMaxScaler
    X_norm = pd.DataFrame(MinMaxScaler(feature_range=(0, 100)).fit_transform(X), columns=cols)
    w = _entropy_weights(X_norm)
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_insm_sorted_descending(sample_master):
    result, _ = build_insm(sample_master)
    scores = result["insm_score"].values
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))


def test_insm_missing_columns_partial(sample_master):
    # Remove some columns; INSM should still work with available indicators
    partial = sample_master.drop(columns=["variacao_nativa_pp", "indice_pressao_ambiental"])
    result, weights = build_insm(partial)
    assert len(result) == len(partial)
    assert result["insm_score"].notna().all()
