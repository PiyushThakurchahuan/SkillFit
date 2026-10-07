"""Hackathon Phase 2: EDA + statistical insight generation.

Run from SkillFit project root:
    python backend/eda_hackathon.py

Reads the four organizer datasets from backend/hackathon_data and writes
tables, charts and a narrative-ready JSON summary to backend/hackathon_output.
"""

from pathlib import Path
import json
import re
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "hackathon_data"
OUT = ROOT / "hackathon_output"
CHARTS = OUT / "charts"
OUT.mkdir(exist_ok=True)
CHARTS.mkdir(exist_ok=True)


def clean(x):
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", " ", str(x).strip().lower())


def nums(x):
    return [float(v) for v in re.findall(r"\d+(?:\.\d+)?", str(x))]


def mid_experience(x):
    n = nums(x)
    if len(n) >= 2:
        return (n[0] + n[1]) / 2
    return n[0] if n else np.nan


def mid_salary(x):
    n = nums(x)
    if len(n) >= 2:
        return (n[0] + n[1]) / 2
    return n[0] if n else np.nan


def lpa(x):
    n = nums(x)
    return n[0] if n else np.nan


def skill_series(s):
    return (
        s.fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .map(clean)
        .replace({"powerbi": "power bi", "ml": "machine learning", "ai": "artificial intelligence"})
    )


def savefig(name):
    plt.tight_layout()
    plt.savefig(CHARTS / name, dpi=180, bbox_inches="tight")
    plt.close()


def bar(values, title, xlabel, filename, horizontal=False):
    plt.figure(figsize=(10, 6))
    if horizontal:
        values.sort_values().plot(kind="barh")
    else:
        values.plot(kind="bar")
        plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Count")
    savefig(filename)


def run():
    analytics = pd.read_csv(DATA / "Analytics Jobs.csv")
    ds = pd.read_csv(DATA / "DataScience Jobs.csv")
    jds = pd.read_excel(DATA / "JDS Skill Traits.xlsx")
    sds = pd.read_excel(DATA / "SDS Personality Traits.xlsx")

    # ---------- Analytics Jobs ----------
    a = analytics.copy()
    a["experience_mid_years"] = a["experience"].map(mid_experience)
    a["salary_mid_lpa"] = a["salary"].map(mid_salary)
    a["role_clean"] = a["job_desig"].map(clean)
    a["location_clean"] = a["location"].map(clean)

    top_skill = skill_series(a["key_skills"]).value_counts().head(20)
    top_roles = a["role_clean"].value_counts().head(15)
    top_locations = a["location_clean"].value_counts().head(15)

    bar(top_skill, "Top 20 Skills in Analytics Job Postings", "Skill", "top_skills.png", True)
    bar(top_roles, "Top 15 Analytics Job Roles", "Role", "top_roles.png", True)
    bar(top_locations, "Top 15 Analytics Job Locations", "Location", "top_locations.png", True)

    plt.figure(figsize=(9, 6))
    a["salary_mid_lpa"].dropna().clip(upper=a["salary_mid_lpa"].dropna().quantile(.99)).plot(kind="hist", bins=25)
    plt.title("Analytics Jobs: Salary Distribution")
    plt.xlabel("Approx. salary midpoint (LPA)")
    plt.ylabel("Job postings")
    savefig("analytics_salary_distribution.png")

    plt.figure(figsize=(9, 6))
    a["experience_mid_years"].dropna().clip(upper=a["experience_mid_years"].dropna().quantile(.99)).plot(kind="hist", bins=20)
    plt.title("Analytics Jobs: Experience Distribution")
    plt.xlabel("Approx. experience midpoint (years)")
    plt.ylabel("Job postings")
    savefig("analytics_experience_distribution.png")

    role_salary = (
        a.groupby("role_clean", as_index=False)
        .agg(postings=("role_clean", "size"), median_salary_lpa=("salary_mid_lpa", "median"))
        .query("postings >= 10")
        .sort_values("median_salary_lpa", ascending=False)
        .head(15)
    )
    role_salary.to_csv(OUT / "analytics_role_salary.csv", index=False)

    plt.figure(figsize=(10, 7))
    role_salary.set_index("role_clean")["median_salary_lpa"].sort_values().plot(kind="barh")
    plt.title("Highest Median Salary Among Frequently Posted Analytics Roles")
    plt.xlabel("Median approximate salary (LPA)")
    plt.ylabel("Role")
    savefig("role_salary.png")

    # ---------- Data Science Jobs ----------
    d = ds.copy()
    d["avg_salary_lpa"] = d["avg_salary"].map(lpa)
    d["job_title_clean"] = d["job_title"].map(clean)
    ds_roles = (
        d.groupby("job_title_clean", as_index=False)
        .agg(
            postings=("job_title_clean", "size"),
            total_jobs=("num_of_jobs", "sum"),
            avg_salary_lpa=("avg_salary_lpa", "mean"),
            min_experience=("min_experience", "median"),
        )
        .sort_values("total_jobs", ascending=False)
    )
    ds_roles.head(20).round(3).to_csv(OUT / "ds_market_summary.csv", index=False)

    # ---------- JDS ----------
    j = jds.copy()
    j.columns = j.columns.str.strip()
    skill_features = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    target = "salary_hike_high_or_low"
    jds_corr = pd.DataFrame({
        "feature": skill_features,
        "correlation_with_high_hike": [
            j[[f, target]].corr().iloc[0, 1] for f in skill_features
        ],
        "high_group_mean": [
            j.loc[j[target] == 1, f].mean() for f in skill_features
        ],
        "low_group_mean": [
            j.loc[j[target] == 0, f].mean() for f in skill_features
        ],
    }).sort_values("correlation_with_high_hike", ascending=False)
    jds_corr.round(4).to_csv(OUT / "jds_skill_insights.csv", index=False)

    plt.figure(figsize=(10, 6))
    jds_corr.set_index("feature")["correlation_with_high_hike"].sort_values().plot(kind="barh")
    plt.axvline(0, linewidth=1)
    plt.title("JDS Skill Dimensions vs High Salary-Hike Outcome")
    plt.xlabel("Pearson correlation with high-hike class")
    plt.ylabel("Skill dimension")
    savefig("jds_skill_correlation.png")

    # ---------- SDS ----------
    s = sds.copy()
    s.columns = s.columns.str.strip()
    personality_features = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    target2 = "success_ classification_ high_low"
    sds_corr = pd.DataFrame({
        "feature": personality_features,
        "correlation_with_high_success": [
            s[[f, target2]].corr().iloc[0, 1] for f in personality_features
        ],
        "high_group_mean": [
            s.loc[s[target2] == 1, f].mean() for f in personality_features
        ],
        "low_group_mean": [
            s.loc[s[target2] == 0, f].mean() for f in personality_features
        ],
    }).sort_values("correlation_with_high_success", ascending=False)
    sds_corr.round(4).to_csv(OUT / "sds_personality_insights.csv", index=False)

    plt.figure(figsize=(10, 6))
    sds_corr.set_index("feature")["correlation_with_high_success"].sort_values().plot(kind="barh")
    plt.axvline(0, linewidth=1)
    plt.title("SDS Personality Dimensions vs High Success Outcome")
    plt.xlabel("Pearson correlation with high-success class")
    plt.ylabel("Personality dimension")
    savefig("sds_personality_correlation.png")

    # ---------- Narrative-ready summary ----------
    summary = {
        "analytics_jobs": {
            "rows": int(len(a)),
            "top_skills": [{"skill": k, "count": int(v)} for k, v in top_skill.items()],
            "top_roles": [{"role": k, "count": int(v)} for k, v in top_roles.items()],
            "top_locations": [{"location": k, "count": int(v)} for k, v in top_locations.items()],
            "median_salary_lpa": round(float(a["salary_mid_lpa"].median()), 2),
            "median_experience_years": round(float(a["experience_mid_years"].median()), 2),
        },
        "data_science_jobs": {
            "rows": int(len(d)),
            "top_roles": ds_roles.head(10).round(3).to_dict("records"),
            "median_avg_salary_lpa": round(float(d["avg_salary_lpa"].median()), 2),
        },
        "jds": {
            "rows": int(len(j)),
            "class_balance": {str(k): int(v) for k, v in j[target].value_counts().sort_index().items()},
            "ranked_features": jds_corr.round(4).to_dict("records"),
        },
        "sds": {
            "rows": int(len(s)),
            "class_balance": {str(k): int(v) for k, v in s[target2].value_counts().sort_index().items()},
            "ranked_features": sds_corr.round(4).to_dict("records"),
        },
        "interpretation_rule": (
            "Correlations and model outputs indicate associations in the supplied data; "
            "they do not establish causation."
        ),
    }
    (OUT / "eda_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    print("\nPHASE 2 COMPLETE")
    print(f"Charts: {CHARTS}")
    print(f"Tables/summary: {OUT}")
    print("Open eda_summary.json and the charts folder for the findings.")


if __name__ == "__main__":
    run()
