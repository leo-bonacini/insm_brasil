"""Build the National Municipal Sustainability Index (INSM) using PCA + Entropy Weight Method."""
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler

# Indicators included in the INSM with their direction (1 = higher is better, -1 = higher is worse)
INDICATOR_CONFIG = {
    "pib_per_capita":          {"dir": 1,  "label": "PIB per capita (R$)"},
    "densidade_pop":           {"dir": -1, "label": "Densidade demográfica"},
    "pct_nativa":              {"dir": 1,  "label": "Cobertura nativa (%)"},
    "pct_florestal":           {"dir": 1,  "label": "Cobertura florestal (%)"},
    "pct_agro":                {"dir": -1, "label": "Área agropecuária (%)"},
    "pct_urbana":              {"dir": -1, "label": "Área urbana (%)"},
    "variacao_nativa_pp":      {"dir": 1,  "label": "Variação vegetação nativa (p.p.)"},
    "indice_pressao_ambiental":{"dir": -1, "label": "Índice pressão ambiental"},
}


def build_insm(master: pd.DataFrame) -> pd.DataFrame:
    """Compute the INSM for all municipalities.

    Steps:
    1. Select and orient indicators
    2. Impute missing values (median)
    3. Normalize 0-100 (MinMax)
    4. Compute weights via PCA (variance explained per component) + Entropy Weight Method
    5. Combine into INSM score 0-100
    6. Generate ranking
    """
    df = master.copy()
    available = [k for k in INDICATOR_CONFIG if k in df.columns]
    missing = [k for k in INDICATOR_CONFIG if k not in df.columns]
    if missing:
        logger.warning(f"Missing indicators (will be excluded from INSM): {missing}")

    X = df[available].copy()

    # Flip negative-direction indicators
    for col in available:
        if INDICATOR_CONFIG[col]["dir"] == -1:
            X[col] = -X[col]

    # Impute NaN with column median
    imputer = SimpleImputer(strategy="median")
    X_imp = pd.DataFrame(imputer.fit_transform(X), columns=X.columns, index=X.index)

    # MinMax normalize to [0, 100]
    scaler = MinMaxScaler(feature_range=(0, 100))
    X_norm = pd.DataFrame(scaler.fit_transform(X_imp), columns=X.columns, index=X.index)

    # ── PCA-based weights ────────────────────────────────────────────────────
    n_components = min(len(available), 3)
    pca = PCA(n_components=n_components, random_state=42)
    pca.fit(X_norm)
    pca_weights = _pca_weights(pca, X_norm.columns.tolist())
    logger.info(f"PCA weights: {pca_weights}")

    # ── Entropy Weight Method ────────────────────────────────────────────────
    ewm_weights = _entropy_weights(X_norm)
    logger.info(f"EWM weights: {ewm_weights}")

    # ── Combined weights (average of PCA and EWM) ────────────────────────────
    w_pca = np.array([pca_weights[c] for c in available])
    w_ewm = np.array([ewm_weights[c] for c in available])
    w_combined = (w_pca + w_ewm) / 2
    w_combined = w_combined / w_combined.sum()  # normalize to sum=1

    final_weights = dict(zip(available, w_combined))
    logger.info(f"Final combined weights: {final_weights}")

    # ── INSM Score ────────────────────────────────────────────────────────────
    X_mat = X_norm[available].values
    score = X_mat @ w_combined  # weighted sum already in [0,100] domain

    # Rescale final score to 0-100
    score_series = pd.Series(score, index=X_norm.index)
    score_min, score_max = score_series.min(), score_series.max()
    insm = (score_series - score_min) / (score_max - score_min) * 100

    # ── Assemble result ───────────────────────────────────────────────────────
    result = df[["geocodigo", "municipio", "uf_sigla", "area_km2", "populacao", "pib_mil_reais"]].copy()
    result["insm_score"] = insm.values
    result["insm_ranking"] = result["insm_score"].rank(ascending=False, method="min").astype(int)

    # Add sub-index scores
    env_cols = [c for c in ["pct_nativa", "pct_florestal", "variacao_nativa_pp"] if c in X_norm.columns]
    eco_cols = [c for c in ["pib_per_capita"] if c in X_norm.columns]

    if env_cols:
        result["subindex_ambiental"] = X_norm[env_cols].mean(axis=1)
    if eco_cols:
        result["subindex_economico"] = X_norm[eco_cols].mean(axis=1)

    # Add all normalized indicator scores
    for col in available:
        result[f"norm_{col}"] = X_norm[col].values

    result = result.sort_values("insm_ranking").reset_index(drop=True)

    logger.success(
        f"INSM built: {len(result)} municipalities | "
        f"score range [{result['insm_score'].min():.1f}, {result['insm_score'].max():.1f}]"
    )
    return result, final_weights


def _pca_weights(pca: PCA, columns: list[str]) -> dict[str, float]:
    """Derive indicator weights from PCA loadings weighted by explained variance."""
    loadings = np.abs(pca.components_)  # shape: (n_components, n_features)
    var_ratio = pca.explained_variance_ratio_  # shape: (n_components,)
    # Weight = sum of |loading| × explained_variance for each feature
    weights_raw = (loadings * var_ratio[:, np.newaxis]).sum(axis=0)
    weights = weights_raw / weights_raw.sum()
    return dict(zip(columns, weights))


def _entropy_weights(X_norm: pd.DataFrame) -> dict[str, float]:
    """Entropy Weight Method: columns with higher information entropy get higher weight."""
    X = X_norm.copy()
    # Avoid log(0): shift so minimum is epsilon
    X = X + 1e-6
    # Normalize rows to probability
    row_sum = X.sum(axis=1)
    P = X.div(row_sum, axis=0)
    n = len(P)
    # Entropy
    E = -(P * np.log(P + 1e-10)).sum(axis=0) / np.log(n)
    # Diversity
    D = 1 - E
    # Weight
    W = D / D.sum()
    return W.to_dict()


if __name__ == "__main__":
    from src.utils.config import PARQUET_DIR
    master = pd.read_parquet(PARQUET_DIR / "master_indicators.parquet")
    result, weights = build_insm(master)

    out = PARQUET_DIR / "insm_ranking.parquet"
    result.to_parquet(out, index=False)
    logger.success(f"INSM ranking saved: {out}")

    print("\n=== TOP 20 MUNICÍPIOS MAIS SUSTENTÁVEIS DO BRASIL (INSM 2021) ===")
    cols = ["insm_ranking", "municipio", "uf_sigla", "insm_score", "pct_nativa", "pib_per_capita"]
    avail_cols = [c for c in cols if c in result.columns]
    print(result[avail_cols].head(20).to_string(index=False))

    print("\n=== BOTTOM 10 ===")
    print(result[avail_cols].tail(10).to_string(index=False))

    print("\n=== WEIGHTS ===")
    for k, v in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {INDICATOR_CONFIG.get(k, {}).get('label', k)}: {v:.4f}")
