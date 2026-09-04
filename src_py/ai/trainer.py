"""
Model Training Pipeline for FINRES ML.
Trains multiple models on real-world data and saves artifacts.
"""
import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import joblib

from .data_loader import load_all_datasets, get_feature_target_split
from .features import build_real_features, build_enriched_features, FEATURE_NAMES

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def train_all_models(force_retrain: bool = False) -> Dict:
    """Train all models on real-world data and save artifacts."""
    print("=" * 60)
    print("FINRES ML Training Pipeline")
    print("=" * 60)

    print("\n[1/5] Loading real-world datasets...")
    raw_df = load_all_datasets()

    print(f"\n[2/5] Engineering features...")
    X_base = build_real_features(raw_df)
    X_enriched = build_enriched_features(raw_df)
    y = raw_df["default"]

    print(f"  Base features: {X_base.shape[1]} columns, {len(X_base)} rows")
    print(f"  Enriched features: {X_enriched.shape[1]} columns")
    print(f"  Target distribution: {y.value_counts().to_dict()}")

    print(f"\n[3/5] Splitting data...")
    X_train_b, X_test_b, y_train, y_test = train_test_split(
        X_base, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train_e, X_test_e, _, _ = train_test_split(
        X_enriched, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler_base = StandardScaler()
    X_train_b_scaled = scaler_base.fit_transform(X_train_b)
    X_test_b_scaled = scaler_base.transform(X_test_b)

    scaler_enriched = StandardScaler()
    X_train_e_scaled = scaler_enriched.fit_transform(X_train_e)
    X_test_e_scaled = scaler_enriched.transform(X_test_e)

    print(f"  Train: {len(X_train_b)} samples, Test: {len(X_test_b)} samples")

    print(f"\n[4/5] Training models...")
    results = {}

    # Model 1: Logistic Regression (distress engine baseline)
    print("\n  Training Logistic Regression...")
    t0 = time.time()
    lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=42)
    lr.fit(X_train_b_scaled, y_train)
    lr_time = time.time() - t0
    lr_pred = lr.predict(X_test_b_scaled)
    lr_proba = lr.predict_proba(X_test_b_scaled)[:, 1]
    results["distress_logistic"] = _evaluate("LogisticRegression", lr, X_test_b_scaled, y_test, lr_proba, lr_time, FEATURE_NAMES)
    results["distress_logistic"]["model"] = lr
    results["distress_logistic"]["scaler"] = scaler_base

    # Model 2: Random Forest (base features)
    print("  Training Random Forest (base)...")
    t0 = time.time()
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_split=10, random_state=42, n_jobs=-1)
    rf.fit(X_train_b, y_train)
    rf_time = time.time() - t0
    rf_pred = rf.predict(X_test_b)
    rf_proba = rf.predict_proba(X_test_b)[:, 1]
    results["distress_random_forest"] = _evaluate("RandomForest", rf, X_test_b, y_test, rf_proba, rf_time, FEATURE_NAMES)
    results["distress_random_forest"]["model"] = rf
    results["distress_random_forest"]["scaler"] = None

    # Model 3: Gradient Boosting (enriched features)
    print("  Training Gradient Boosting (enriched)...")
    t0 = time.time()
    gb = GradientBoostingClassifier(n_estimators=150, max_depth=5, learning_rate=0.1, random_state=42)
    gb.fit(X_train_e, y_train)
    gb_time = time.time() - t0
    gb_pred = gb.predict(X_test_e)
    gb_proba = gb.predict_proba(X_test_e)[:, 1]
    enriched_features = list(X_enriched.columns)
    results["distress_gradient_boost"] = _evaluate("GradientBoosting", gb, X_test_e, y_test, gb_proba, gb_time, enriched_features)
    results["distress_gradient_boost"]["model"] = gb
    results["distress_gradient_boost"]["scaler"] = scaler_enriched

    # Model 4: Random Forest (enriched features) - best performer
    print("  Training Random Forest (enriched)...")
    t0 = time.time()
    rf_e = RandomForestClassifier(n_estimators=150, max_depth=15, min_samples_split=5, random_state=42, n_jobs=-1)
    rf_e.fit(X_train_e, y_train)
    rf_e_time = time.time() - t0
    rf_e_pred = rf_e.predict(X_test_e)
    rf_e_proba = rf_e.predict_proba(X_test_e)[:, 1]
    results["distress_rf_enriched"] = _evaluate("RandomForest_Enriched", rf_e, X_test_e, y_test, rf_e_proba, rf_e_time, enriched_features)
    results["distress_rf_enriched"]["model"] = rf_e
    results["distress_rf_enriched"]["scaler"] = scaler_enriched

    print(f"\n[5/5] Saving model artifacts...")
    training_meta = _save_artifacts(results, scaler_base, scaler_enriched, raw_df, y)

    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    for name, res in results.items():
        print(f"  {name}: AUC={res['auc']:.3f}, F1={res['f1']:.3f}, Acc={res['accuracy']:.3f}")

    return training_meta


def _evaluate(name: str, model, X_test, y_test, y_proba, train_time: float, feature_names: List[str]) -> Dict:
    """Evaluate a model and return metrics."""
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.5
    cm = confusion_matrix(y_test, y_pred).tolist()

    cv_scores = cross_val_score(model, X_test, y_test, cv=min(5, len(y_test)), scoring="roc_auc", n_jobs=-1)
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()

    feature_importance = {}
    if hasattr(model, "feature_importances_") and feature_names:
        importances = model.feature_importances_
        for fname, imp in zip(feature_names, importances):
            feature_importance[fname] = round(float(imp), 4)
    elif hasattr(model, "coef_") and feature_names:
        coefs = np.abs(model.coef_[0])
        for fname, coef in zip(feature_names, coefs):
            feature_importance[fname] = round(float(coef), 4)

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "auc": round(auc, 4),
        "cv_auc_mean": round(cv_mean, 4),
        "cv_auc_std": round(cv_std, 4),
        "confusion_matrix": cm,
        "train_time_sec": round(train_time, 3),
        "feature_importance": dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)),
        "n_features": len(feature_names),
        "n_train_samples": 0,
    }


def _save_artifacts(results: Dict, scaler_base, scaler_enriched, df, y) -> Dict:
    """Save all model artifacts to disk."""
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    best_model_name = max(results.keys(), key=lambda k: results[k]["auc"])
    best_result = results[best_model_name]

    for name, res in results.items():
        model_path = os.path.join(ARTIFACTS_DIR, f"{name}.joblib")
        joblib.dump(res["model"], model_path)
        print(f"  Saved: {model_path}")

    joblib.dump(scaler_base, os.path.join(ARTIFACTS_DIR, "scaler_base.joblib"))
    joblib.dump(scaler_enriched, os.path.join(ARTIFACTS_DIR, "scaler_enriched.joblib"))

    feature_meta = {
        "base_features": FEATURE_NAMES,
        "enriched_features": list(build_enriched_features(df.head(1)).columns),
    }
    with open(os.path.join(ARTIFACTS_DIR, "feature_config.json"), "w") as f:
        json.dump(feature_meta, f, indent=2)

    model_registry = {}
    for name, res in results.items():
        model_registry[name] = {
            "accuracy": res["accuracy"],
            "precision": res["precision"],
            "recall": res["recall"],
            "f1": res["f1"],
            "auc": res["auc"],
            "cv_auc_mean": res["cv_auc_mean"],
            "cv_auc_std": res["cv_auc_std"],
            "train_time_sec": res["train_time_sec"],
            "n_features": res["n_features"],
            "feature_importance": res["feature_importance"],
            "status": "active" if name == best_model_name else "active",
            "version": f"1.0.{timestamp}",
            "trained_at": timestamp,
            "training_samples": int(len(df) * 0.8),
            "test_samples": int(len(df) * 0.2),
            "dataset_sources": df["source"].unique().tolist() if "source" in df.columns else [],
            "dataset_size": len(df),
            "default_rate": float(y.mean()),
        }

    registry_path = os.path.join(ARTIFACTS_DIR, "model_registry.json")
    with open(registry_path, "w") as f:
        json.dump(model_registry, f, indent=2)
    print(f"  Saved: {registry_path}")

    training_meta = {
        "timestamp": timestamp,
        "best_model": best_model_name,
        "best_auc": best_result["auc"],
        "total_models": len(results),
        "models": model_registry,
    }
    with open(os.path.join(ARTIFACTS_DIR, "training_meta.json"), "w") as f:
        json.dump(training_meta, f, indent=2)

    return training_meta


if __name__ == "__main__":
    meta = train_all_models()
    print(f"\nBest model: {meta['best_model']} (AUC: {meta['best_auc']:.3f})")
