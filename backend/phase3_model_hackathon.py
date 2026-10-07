"""Hackathon Phase 3: ML model evaluation.

Run from SkillFit project root:
    python backend/phase3_model_hackathon.py

Compares Logistic Regression (baseline) and Random Forest for:
- JDS Skill Traits: salary_hike_high_or_low
- SDS Personality Traits: success_ classification_ high_low

Outputs metrics, confusion matrices, feature importance/coefficients and
model-ready JSON/CSV files to backend/hackathon_output/phase3/.
"""

from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "hackathon_data"
OUT = ROOT / "hackathon_output" / "phase3"
OUT.mkdir(parents=True, exist_ok=True)


def evaluate_dataset(
    df: pd.DataFrame,
    features: list[str],
    target: str,
    dataset_name: str,
) -> dict:
    work = df[features + [target]].copy()
    for col in features:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    work[target] = pd.to_numeric(work[target], errors="coerce")
    work = work.dropna()

    X = work[features]
    y = work[target].astype(int)

    if y.nunique() != 2:
        raise ValueError(f"{dataset_name}: target must contain exactly two classes.")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "logistic_regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=2000, random_state=42)),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            max_depth=5,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
        ),
    }

    results = []
    artifacts = {}

    for name, model in models.items():
        y_pred = cross_val_predict(model, X, y, cv=cv, method="predict")
        y_prob = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]

        metrics = {
            "dataset": dataset_name,
            "model": name,
            "rows_used": int(len(work)),
            "accuracy": round(float(accuracy_score(y, y_pred)), 4),
            "precision": round(float(precision_score(y, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y, y_pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y, y_prob)), 4),
        }
        results.append(metrics)

        cm = confusion_matrix(y, y_pred).tolist()
        report = classification_report(y, y_pred, output_dict=True, zero_division=0)
        artifacts[name] = {"confusion_matrix": cm, "classification_report": report}

        # Fit on all available rows only to derive explainability artifacts.
        model.fit(X, y)
        if name == "random_forest":
            importance = pd.DataFrame(
                {
                    "feature": features,
                    "importance": model.feature_importances_,
                }
            ).sort_values("importance", ascending=False)
            importance["importance"] = importance["importance"].round(6)
            importance.to_csv(OUT / f"{dataset_name}_random_forest_feature_importance.csv", index=False)
        else:
            lr = model.named_steps["model"]
            coef = pd.DataFrame(
                {
                    "feature": features,
                    "coefficient": lr.coef_[0],
                    "odds_ratio": np.exp(lr.coef_[0]),
                }
            ).sort_values("coefficient", ascending=False)
            coef["coefficient"] = coef["coefficient"].round(6)
            coef["odds_ratio"] = coef["odds_ratio"].round(6)
            coef.to_csv(OUT / f"{dataset_name}_logistic_coefficients.csv", index=False)

    results_df = pd.DataFrame(results).sort_values(["f1", "roc_auc"], ascending=False)
    results_df.to_csv(OUT / f"{dataset_name}_model_comparison.csv", index=False)

    best = results_df.iloc[0].to_dict()

    return {
        "dataset": dataset_name,
        "features": features,
        "target": target,
        "rows_used": int(len(work)),
        "class_balance": {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
        "models": results,
        "best_model_by_f1": {
            "model": str(best["model"]),
            "f1": float(best["f1"]),
            "roc_auc": float(best["roc_auc"]),
        },
        "artifacts": artifacts,
    }


def run() -> None:
    jds = pd.read_excel(DATA / "JDS Skill Traits.xlsx")
    jds.columns = jds.columns.str.strip()

    sds = pd.read_excel(DATA / "SDS Personality Traits.xlsx")
    sds.columns = sds.columns.str.strip()

    jds_features = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    jds_result = evaluate_dataset(
        jds,
        jds_features,
        "salary_hike_high_or_low",
        "jds_skill_traits",
    )

    sds_features = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    sds_result = evaluate_dataset(
        sds,
        sds_features,
        "success_ classification_ high_low",
        "sds_personality_traits",
    )

    summary = {
        "methodology": {
            "validation": "5-fold stratified cross-validation",
            "models": ["logistic_regression", "random_forest"],
            "metrics": ["accuracy", "precision", "recall", "f1", "roc_auc"],
            "interpretation_note": (
                "These models estimate associations in the supplied datasets. "
                "They do not prove causation or guarantee future salary, promotion, or success."
            ),
        },
        "jds_skill_traits": jds_result,
        "sds_personality_traits": sds_result,
    }

    (OUT / "phase3_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    print("\nPHASE 3 COMPLETE")
    print(f"Output folder: {OUT}")
    for result in [jds_result, sds_result]:
        best = result["best_model_by_f1"]
        print(
            f"{result['dataset']}: best={best['model']} "
            f"F1={best['f1']:.4f} ROC-AUC={best['roc_auc']:.4f}"
        )
    print("Open phase3_summary.json and the model_comparison CSVs for results.")


if __name__ == "__main__":
    run()
