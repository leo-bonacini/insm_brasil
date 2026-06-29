"""Train ML models to predict INSM score and explain with SHAP."""
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score, silhouette_score
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)

FEATURE_COLS = [
    "pib_per_capita", "densidade_pop", "pct_nativa", "pct_florestal",
    "pct_agro", "pct_urbana", "variacao_nativa_pp", "indice_pressao_ambiental",
    "area_km2", "populacao", "rebanho_por_km2",
]


def prepare_features(insm: pd.DataFrame, master: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Merge master indicators with INSM scores; return X, y."""
    df = master.merge(insm[["geocodigo", "insm_score"]], on="geocodigo", how="inner")
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available_features].copy()
    y = df["insm_score"].copy()
    return X, y, available_features


def train_and_evaluate(X: pd.DataFrame, y: pd.Series, feature_names: list[str]) -> dict:
    """Train multiple models, evaluate with 5-fold CV, return best model and metrics."""
    # Drop columns that are all-NaN before imputing
    X = X.dropna(axis=1, how="all")
    imputer = SimpleImputer(strategy="median")
    X_imp = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X_imp), columns=X.columns)

    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
        "XGBoost": xgb.XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
        "LightGBM": lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1),
        "ElasticNet": ElasticNet(random_state=42),
    }

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = {}

    for name, model in models.items():
        X_in = X_imp if name in ["RandomForest", "GradientBoosting", "XGBoost", "LightGBM"] else X_scaled
        cv_rmse = cross_val_score(model, X_in, y, cv=kf, scoring="neg_root_mean_squared_error", n_jobs=-1)
        cv_r2   = cross_val_score(model, X_in, y, cv=kf, scoring="r2", n_jobs=-1)

        model.fit(X_in, y)
        y_pred = model.predict(X_in)
        train_r2 = r2_score(y, y_pred)

        results[name] = {
            "model": model,
            "X": X_in,
            "cv_rmse_mean": -cv_rmse.mean(),
            "cv_rmse_std": cv_rmse.std(),
            "cv_r2_mean": cv_r2.mean(),
            "cv_r2_std": cv_r2.std(),
            "train_r2": train_r2,
        }
        logger.info(
            f"{name}: CV RMSE={-cv_rmse.mean():.3f}±{cv_rmse.std():.3f} | "
            f"CV R²={cv_r2.mean():.3f}±{cv_r2.std():.3f}"
        )

    # Best model = lowest CV RMSE
    best_name = min(results, key=lambda k: results[k]["cv_rmse_mean"])
    logger.success(f"Best model: {best_name} (CV RMSE={results[best_name]['cv_rmse_mean']:.3f})")

    return results, best_name, imputer, scaler


def compute_feature_importance(results: dict, best_name: str, feature_names: list[str]) -> pd.DataFrame:
    """Extract feature importances from the best model."""
    model = results[best_name]["model"]
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_)
    else:
        importances = np.ones(len(feature_names)) / len(feature_names)

    fi = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False)
    return fi


def compute_shap(results: dict, best_name: str, feature_names: list[str]) -> pd.DataFrame | None:
    """Compute SHAP values for the best model."""
    try:
        import shap
        model = results[best_name]["model"]
        X = results[best_name]["X"]

        if best_name in ["XGBoost", "LightGBM", "RandomForest", "GradientBoosting"]:
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.LinearExplainer(model, X)

        shap_values = explainer.shap_values(X)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        shap_df = pd.DataFrame({
            "feature": feature_names,
            "mean_abs_shap": mean_abs_shap,
        }).sort_values("mean_abs_shap", ascending=False)
        logger.success("SHAP values computed.")
        return shap_df
    except Exception as e:
        logger.warning(f"SHAP failed: {e}")
        return None


def cluster_municipalities(master: pd.DataFrame, insm: pd.DataFrame, n_clusters: int = 6) -> pd.DataFrame:
    """K-Means clustering of municipalities based on sustainability profile."""
    df = master.merge(insm[["geocodigo", "insm_score"]], on="geocodigo", how="inner")
    cluster_features = [c for c in FEATURE_COLS + ["insm_score"] if c in df.columns]

    X = df[cluster_features].copy()
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_prep = scaler.fit_transform(imputer.fit_transform(X))

    # Find optimal k via silhouette
    best_k, best_sil = n_clusters, -1
    for k in range(3, min(10, len(df) // 100)):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_prep)
        sil = silhouette_score(X_prep, labels, sample_size=min(2000, len(X_prep)))
        if sil > best_sil:
            best_sil, best_k = sil, k
    logger.info(f"Optimal clusters: k={best_k} (silhouette={best_sil:.3f})")

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X_prep)

    # Label clusters by mean INSM score
    cluster_means = df.groupby("cluster")["insm_score"].mean().sort_values()
    cluster_labels = {
        0: "Municípios sob risco ambiental crítico",
        1: "Municípios em recuperação",
        2: "Municípios agrícolas moderados",
        3: "Municípios urbanos industriais",
        4: "Municípios com boa conservação",
        5: "Municípios florestais conservados",
    }
    rank_map = {old: new for new, old in enumerate(cluster_means.index)}
    df["cluster_rank"] = df["cluster"].map(rank_map)
    df["cluster_label"] = df["cluster_rank"].map(cluster_labels)

    logger.success(f"Clustering done: {best_k} clusters, silhouette={best_sil:.3f}")
    return df[["geocodigo", "municipio", "uf_sigla", "cluster", "cluster_rank", "cluster_label", "insm_score"]]


if __name__ == "__main__":
    from src.utils.config import PARQUET_DIR

    master = pd.read_parquet(PARQUET_DIR / "master_indicators.parquet")
    insm = pd.read_parquet(PARQUET_DIR / "insm_ranking.parquet")

    logger.info("Preparing features...")
    X, y, feature_names = prepare_features(insm, master)
    logger.info(f"X shape: {X.shape}, features: {feature_names}")

    logger.info("Training models...")
    results, best_name, imputer, scaler = train_and_evaluate(X, y, feature_names)

    # Use the actual feature names from the fitted model's data
    actual_feature_names = list(results[best_name]["X"].columns)
    fi = compute_feature_importance(results, best_name, actual_feature_names)
    logger.info(f"\nFeature Importance ({best_name}):\n{fi.to_string(index=False)}")
    fi.to_parquet(PARQUET_DIR / "feature_importance.parquet", index=False)

    shap_df = compute_shap(results, best_name, actual_feature_names)
    if shap_df is not None:
        logger.info(f"\nSHAP values:\n{shap_df.to_string(index=False)}")
        shap_df.to_parquet(PARQUET_DIR / "shap_values.parquet", index=False)

    logger.info("Clustering municipalities...")
    clusters = cluster_municipalities(master, insm)
    clusters.to_parquet(PARQUET_DIR / "clusters.parquet", index=False)
    logger.info(f"\nCluster distribution:\n{clusters['cluster_label'].value_counts().to_string()}")

    # Summary stats by cluster
    summary = clusters.groupby("cluster_label")["insm_score"].agg(["count", "mean", "min", "max"])
    logger.info(f"\nCluster summary:\n{summary.to_string()}")
