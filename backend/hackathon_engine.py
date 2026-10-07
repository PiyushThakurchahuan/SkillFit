"""Official hackathon analytics used by SkillFit.

The organizer datasets are kept as separate analytical lenses because they do
not share an individual-level person key:
- Analytics Jobs / Data Science Jobs -> market intelligence
- JDS Skill Traits -> technical-skill outcome intelligence
- SDS Personality Traits -> personality outcome intelligence
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parent / "hackathon_data"


def _path(name: str) -> Path:
    p = DATA / name
    if not p.exists():
        raise FileNotFoundError(
            f"Missing {name}. Put the official hackathon files in {DATA}"
        )
    return p


def _clean(x) -> str:
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", " ", str(x).strip().lower())


def _nums(x):
    return [float(v) for v in re.findall(r"\d+(?:\.\d+)?", str(x))]


def _lpa(x):
    n = _nums(x)
    return n[0] if n else np.nan


def _classification_models():
    return {
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


def _validated_model_result(kind: str):
    """Return the Phase 3 benchmark already validated from the official data.

    The reproducible training code remains in phase3_model_hackathon.py.
    Keeping the validated benchmark here prevents the demo UI from retraining
    4,000+ trees on every browser refresh.
    """
    if kind == "jds":
        return {
            "rows": 139,
            "models": [
                {"model": "random_forest", "accuracy": 0.8345, "precision": 0.8472, "recall": 0.8356, "f1": 0.8414, "roc_auc": 0.8654},
                {"model": "logistic_regression", "accuracy": 0.8201, "precision": 0.8158, "recall": 0.8493, "f1": 0.8322, "roc_auc": 0.8924},
            ],
            "best_by_f1": {"model": "random_forest", "accuracy": 0.8345, "precision": 0.8472, "recall": 0.8356, "f1": 0.8414, "roc_auc": 0.8654},
            "random_forest_feature_importance": [
                {"feature": "dashboard_and_storytelling_skills", "importance": 0.350625},
                {"feature": "maths-stats_skills", "importance": 0.249027},
                {"feature": "coding_skills", "importance": 0.163690},
                {"feature": "ai_and_ml_skills", "importance": 0.146368},
                {"feature": "big_data_skills", "importance": 0.090290},
            ],
        }

    return {
        "rows": 161,
        "models": [
            {"model": "random_forest", "accuracy": 0.9565, "precision": 0.9643, "recall": 0.9529, "f1": 0.9586, "roc_auc": 0.9924},
            {"model": "logistic_regression", "accuracy": 0.9068, "precision": 0.8889, "recall": 0.9412, "f1": 0.9143, "roc_auc": 0.9571},
        ],
        "best_by_f1": {"model": "random_forest", "accuracy": 0.9565, "precision": 0.9643, "recall": 0.9529, "f1": 0.9586, "roc_auc": 0.9924},
        "random_forest_feature_importance": [
            {"feature": "conscientiousness", "importance": 0.374685},
            {"feature": "openness_to_experience", "importance": 0.336980},
            {"feature": "extraversion", "importance": 0.132120},
            {"feature": "agreeableness", "importance": 0.130818},
            {"feature": "neuroticism", "importance": 0.025397},
        ],
    }


def _model_results(df, features, target):
    # Kept for reproducibility/debugging. The demo endpoint uses the validated
    # Phase 3 benchmark above instead of retraining on every request.
    work = df[features + [target]].copy()
    for col in features:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    work[target] = pd.to_numeric(work[target], errors="coerce")
    work = work.dropna()

    X = work[features]
    y = work[target].astype(int)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results = []
    importance = {}
    for name, model in _classification_models().items():
        pred = cross_val_predict(model, X, y, cv=cv, method="predict")
        prob = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
        results.append({
            "model": name,
            "accuracy": round(float(accuracy_score(y, pred)), 4),
            "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y, prob)), 4),
        })
        model.fit(X, y)
        if name == "random_forest":
            importance = {f: round(float(v), 6) for f, v in sorted(
                zip(features, model.feature_importances_), key=lambda z: z[1], reverse=True
            )}
    best = max(results, key=lambda r: (r["f1"], r["roc_auc"]))
    return {
        "rows": int(len(work)),
        "class_balance": {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
        "models": results,
        "best_by_f1": best,
        "random_forest_feature_importance": [{"feature": k, "importance": v} for k, v in importance.items()],
    }


def analytics_summary(limit=20):
    df = pd.read_csv(_path("Analytics Jobs.csv"))
    skills = (
        df["key_skills"]
        .fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .map(_clean)
    )
    skills = skills[(skills != "") & (skills != "...")]
    return {
        "rows": int(len(df)),
        "top_skills": [
            {"skill": k, "count": int(v)}
            for k, v in skills.value_counts().head(limit).items()
        ],
        "top_roles": [
            {"role": k, "count": int(v)}
            for k, v in df["job_desig"].fillna("").map(_clean).value_counts().head(limit).items()
        ],
        "top_locations": [
            {"location": k, "count": int(v)}
            for k, v in df["location"].fillna("").map(_clean).value_counts().head(limit).items()
        ],
        "missing_job_description": int(df["job_description"].isna().sum()),
        "missing_job_type": int(df["job_type"].isna().sum()),
    }


def data_science_summary(limit=20):
    df = pd.read_csv(_path("DataScience Jobs.csv"))
    for c in ["avg_salary", "min_salary", "max_salary"]:
        df[c + "_num"] = df[c].map(_lpa)

    role = (
        df.groupby("job_title", as_index=False)
        .agg(
            postings=("job_title", "size"),
            avg_salary_lpa=("avg_salary_num", "mean"),
            total_jobs=("num_of_jobs", "sum"),
        )
        .sort_values("total_jobs", ascending=False)
        .head(limit)
    )
    return {
        "rows": int(len(df)),
        "median_avg_salary_lpa": round(float(df["avg_salary_num"].median()), 2),
        "mean_avg_salary_lpa": round(float(df["avg_salary_num"].mean()), 2),
        "max_salary_lpa": round(float(df["max_salary_num"].max()), 2),
        "top_roles_by_total_jobs": role.round(2).to_dict("records"),
    }


def skill_model():
    # Official JDS benchmark produced by backend/phase3_model_hackathon.py.
    return _validated_model_result("jds")

    df = pd.read_excel(_path("JDS Skill Traits.xlsx"))
    df.columns = df.columns.str.strip()
    features = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    return _model_results(df, features, "salary_hike_high_or_low")


def personality_model():
    # Official SDS benchmark produced by backend/phase3_model_hackathon.py.
    return _validated_model_result("sds")

    df = pd.read_excel(_path("SDS Personality Traits.xlsx"))
    df.columns = df.columns.str.strip()
    features = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    return _model_results(df, features, "success_ classification_ high_low")


def insights():
    return {
        "source": "Official Build for Bharat / SAS hackathon datasets supplied by the organizers",
        "warning": (
            "The four datasets are analyzed as separate modules; they are not "
            "joined at individual level."
        ),
        "analytics_jobs": analytics_summary(),
        "data_science_jobs": data_science_summary(),
        "skill_success_model": skill_model(),
        "personality_success_model": personality_model(),
    }


def career_intelligence(profile):
    """Return hackathon-backed intelligence for a live SkillFit profile.

    This is recommendation support, not a causal prediction of salary or
    career success. Candidate skills are compared with market skill vocabulary;
    JDS/SDS models are presented as benchmark signals.
    """
    market = analytics_summary(limit=20)
    skill_result = skill_model()
    personality_result = personality_model()

    candidate = {_clean(x) for x in (profile.get("skills") or []) if _clean(x)}
    market_skills = [x["skill"] for x in market["top_skills"]]
    matched_market = [s for s in market_skills if s in candidate]
    coverage = round((len(matched_market) / len(market_skills)) * 100, 1) if market_skills else 0

    return {
        "profile_id": profile.get("id"),
        "candidate_skills": sorted(candidate),
        "market_signal": {
            "top_market_skills": market["top_skills"][:10],
            "matched_top_market_skills": matched_market,
            "top_20_market_skill_coverage_pct": coverage,
            "message": (
                "Coverage is a market-alignment signal against the supplied "
                "job-posting vocabulary, not a hiring probability."
            ),
        },
        "skill_success_signal": {
            "rows": skill_result["rows"],
            "best_model": skill_result["best_by_f1"],
            "top_dimensions": skill_result["random_forest_feature_importance"],
            "message": (
                "Technical dimensions are ranked by Random Forest feature "
                "importance for the observed salary-hike class."
            ),
        },
        "personality_success_signal": {
            "rows": personality_result["rows"],
            "best_model": personality_result["best_by_f1"],
            "top_traits": personality_result["random_forest_feature_importance"],
            "message": (
                "Personality dimensions are ranked by Random Forest feature "
                "importance for the observed success class."
            ),
        },
    }
