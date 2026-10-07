"""Official hackathon data engine for SkillFit.

Expected files inside backend/hackathon_data/:
- Analytics Jobs.csv
- DataScience Jobs.csv
- JDS Skill Traits.xlsx
- SDS Personality Traits.xlsx

This module keeps the four official datasets as separate analytical lenses.
They are NOT joined at individual level because their IDs do not represent a
shared person across all four files.
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

DATA = Path(__file__).resolve().parent / "hackathon_data"


def _path(name: str) -> Path:
    p = DATA / name
    if not p.exists():
        raise FileNotFoundError(
            f"Missing {name}. Put the official hackathon files in {DATA}"
        )
    return p


def _metrics(model, X, y):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_validate(
        model, X, y, cv=cv,
        scoring=["accuracy", "precision", "recall", "f1", "roc_auc"]
    )
    return {
        k.replace("test_", ""): round(float(scores[k].mean()), 3)
        for k in ["test_accuracy", "test_precision", "test_recall", "test_f1", "test_roc_auc"]
    }


def _clean_skill(x):
    x = str(x).strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x


def analytics_summary(limit=20):
    df = pd.read_csv(_path("Analytics Jobs.csv"))
    skills = (
        df["key_skills"].fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .map(_clean_skill)
    )
    skills = skills[(skills != "") & (skills != "...")]
    top_skills = [
        {"skill": k, "count": int(v)}
        for k, v in skills.value_counts().head(limit).items()
    ]
    top_roles = [
        {"role": k, "count": int(v)}
        for k, v in df["job_desig"].value_counts().head(limit).items()
    ]
    top_locations = [
        {"location": k, "count": int(v)}
        for k, v in df["location"].value_counts().head(limit).items()
    ]
    salary = df["salary"].value_counts().to_dict()
    return {
        "rows": int(len(df)),
        "missing_job_description": int(df["job_description"].isna().sum()),
        "missing_job_type": int(df["job_type"].isna().sum()),
        "salary_bands": {str(k): int(v) for k, v in salary.items()},
        "top_skills": top_skills,
        "top_roles": top_roles,
        "top_locations": top_locations,
    }


def data_science_summary(limit=20):
    df = pd.read_csv(_path("DataScience Jobs.csv"))
    for c in ["avg_salary", "min_salary", "max_salary"]:
        df[c + "_num"] = (
            df[c].astype(str).str.replace("L", "", regex=False).astype(float)
        )
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
        "top_roles_by_total_jobs": role.round(2).to_dict("records"),
        "max_salary_lpa": round(float(df["max_salary_num"].max()), 2),
    }


def skill_model():
    df = pd.read_excel(_path("JDS Skill Traits.xlsx"))
    df.columns = df.columns.str.strip()
    target = "salary_hike_high_or_low"
    features = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    X, y = df[features], df[target].astype(int)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=4, min_samples_leaf=3, random_state=42
    )
    return {
        "rows": int(len(df)),
        "class_balance": {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
        "model": "Random Forest",
        "metrics_5fold": _metrics(model, X, y),
        "feature_importance": [
            {"feature": f, "importance": round(float(v), 4)}
            for f, v in sorted(
                zip(features, model.fit(X, y).feature_importances_),
                key=lambda z: z[1], reverse=True
            )
        ],
        "correlation_with_target": {
            f: round(float(df[[f, target]].corr().iloc[0, 1]), 3)
            for f in features
        },
    }


def personality_model():
    df = pd.read_excel(_path("SDS Personality Traits.xlsx"))
    df.columns = df.columns.str.strip()
    target = "success_ classification_ high_low"
    features = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    X, y = df[features], df[target].astype(int)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=4, min_samples_leaf=3, random_state=42
    )
    return {
        "rows": int(len(df)),
        "class_balance": {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
        "model": "Random Forest",
        "metrics_5fold": _metrics(model, X, y),
        "feature_importance": [
            {"feature": f, "importance": round(float(v), 4)}
            for f, v in sorted(
                zip(features, model.fit(X, y).feature_importances_),
                key=lambda z: z[1], reverse=True
            )
        ],
        "correlation_with_target": {
            f: round(float(df[[f, target]].corr().iloc[0, 1]), 3)
            for f in features
        },
    }


def insights():
    return {
        "source": "Official Build for Bharat / SAS hackathon datasets supplied by the organizers",
        "warning": "The four datasets are analyzed as separate modules; they are not joined at individual level.",
        "analytics_jobs": analytics_summary(),
        "data_science_jobs": data_science_summary(),
        "skill_success_model": skill_model(),
        "personality_success_model": personality_model(),
    }
