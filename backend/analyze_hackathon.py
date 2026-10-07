"""Build for Bharat / SAS hackathon Phase 1: data audit, cleaning and EDA.

Run from the SkillFit project root:
    python backend/analyze_hackathon.py

The four organizer datasets must be present in backend/hackathon_data/.
Outputs are written to backend/hackathon_output/ (ignored by git).

This script deliberately keeps the four datasets separate. The organizer
files do not contain a shared individual-level key, so no row-level merge is
performed between them.
"""

from pathlib import Path
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "hackathon_data"
OUT = ROOT / "hackathon_output"
OUT.mkdir(exist_ok=True)


def clean_text(x):
    if pd.isna(x):
        return ""
    x = str(x).strip().lower()
    return re.sub(r"\s+", " ", x)


def parse_experience(value):
    s = clean_text(value)
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return np.nan, np.nan
    if len(nums) == 1:
        return nums[0], nums[0]
    return nums[0], nums[1]


def salary_band_mid(value):
    s = clean_text(value).replace(" ", "")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    return np.nan


def lpa(value):
    if pd.isna(value):
        return np.nan
    nums = re.findall(r"\d+(?:\.\d+)?", str(value))
    return float(nums[0]) if nums else np.nan


def normalize_skill(skill):
    s = clean_text(skill)
    aliases = {
        "sql server": "sql",
        "ms sql": "sql",
        "postgres": "postgresql",
        "powerbi": "power bi",
        "ms excel": "excel",
        "microsoft excel": "excel",
        "ml": "machine learning",
        "ai": "artificial intelligence",
    }
    return aliases.get(s, s)


def top_skills(series, n=25):
    skills = (
        series.fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .map(normalize_skill)
    )
    skills = skills[(skills != "") & (skills != "...")]
    vc = skills.value_counts().head(n)
    return [{"skill": k, "count": int(v)} for k, v in vc.items()]


def audit(df):
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values": {
            str(k): int(v) for k, v in df.isna().sum().items() if int(v) > 0
        },
        "unique_values": {str(k): int(df[k].nunique()) for k in df.columns},
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
    }


def save_json(name, obj):
    (OUT / name).write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def run():
    analytics = pd.read_csv(DATA / "Analytics Jobs.csv")
    ds = pd.read_csv(DATA / "DataScience Jobs.csv")
    jds = pd.read_excel(DATA / "JDS Skill Traits.xlsx")
    sds = pd.read_excel(DATA / "SDS Personality Traits.xlsx")

    # ---------------- Analytics Jobs ----------------
    a = analytics.copy()
    bounds = a["experience"].map(parse_experience)
    a["experience_min_years"] = bounds.map(lambda x: x[0])
    a["experience_max_years"] = bounds.map(lambda x: x[1])
    a["experience_mid_years"] = (
        a["experience_min_years"] + a["experience_max_years"]
    ) / 2
    a["salary_mid_lpa"] = a["salary"].map(salary_band_mid)
    a["role_clean"] = a["job_desig"].map(clean_text)
    a["location_clean"] = a["location"].map(clean_text)
    a["job_type_clean"] = a["job_type"].map(clean_text)
    a["skill_count"] = (
        a["key_skills"].fillna("").astype(str)
        .map(
            lambda x: len(
                [s for s in x.split(",") if clean_text(s) and clean_text(s) != "..."]
            )
        )
    )

    # Quality flags instead of silently deleting records.
    a["quality_missing_description"] = a["job_description"].isna()
    a["quality_missing_job_type"] = a["job_type"].isna()
    a["quality_missing_skills"] = a["key_skills"].isna()
    a.to_csv(OUT / "analytics_jobs_cleaned.csv", index=False)

    analytics_summary = {
        "audit": audit(analytics),
        "top_roles": [
            {"role": k, "count": int(v)}
            for k, v in a["role_clean"].value_counts().head(20).items()
        ],
        "top_locations": [
            {"location": k, "count": int(v)}
            for k, v in a["location_clean"].value_counts().head(20).items()
        ],
        "top_skills": top_skills(a["key_skills"], 30),
        "experience": {
            "median_years": round(float(a["experience_mid_years"].median()), 2),
            "mean_years": round(float(a["experience_mid_years"].mean()), 2),
        },
        "salary": {
            "median_lpa": round(float(a["salary_mid_lpa"].median()), 2),
            "mean_lpa": round(float(a["salary_mid_lpa"].mean()), 2),
        },
        "quality": {
            "missing_description_pct": round(
                float(a["quality_missing_description"].mean() * 100), 2
            ),
            "missing_job_type_pct": round(
                float(a["quality_missing_job_type"].mean() * 100), 2
            ),
            "missing_skills_pct": round(
                float(a["quality_missing_skills"].mean() * 100), 2
            ),
            "salary_band_values": sorted(
                a["salary"].dropna().astype(str).unique().tolist()
            ),
        },
    }
    save_json("analytics_summary.json", analytics_summary)

    # ---------------- Data Science Jobs ----------------
    d = ds.copy()
    for c in ["avg_salary", "min_salary", "max_salary"]:
        d[c + "_lpa"] = d[c].map(lpa)
    d["job_title_clean"] = d["job_title"].map(clean_text)
    d["company_clean"] = d["company_name"].map(clean_text)
    d.to_csv(OUT / "data_science_jobs_cleaned.csv", index=False)

    role = (
        d.groupby("job_title_clean", as_index=False)
        .agg(
            postings=("job_title_clean", "size"),
            total_jobs=("num_of_jobs", "sum"),
            avg_salary_lpa=("avg_salary_lpa", "mean"),
            median_min_experience=("min_experience", "median"),
        )
        .sort_values(["total_jobs", "postings"], ascending=False)
    )
    role.head(30).round(3).to_csv(OUT / "ds_role_summary.csv", index=False)

    ds_summary = {
        "audit": audit(ds),
        "role_summary": role.head(20).round(3).to_dict("records"),
        "salary": {
            "median_avg_salary_lpa": round(float(d["avg_salary_lpa"].median()), 2),
            "mean_avg_salary_lpa": round(float(d["avg_salary_lpa"].mean()), 2),
            "max_salary_lpa": round(float(d["max_salary_lpa"].max()), 2),
        },
    }
    save_json("data_science_summary.json", ds_summary)

    # ---------------- JDS Skill Traits ----------------
    j = jds.copy()
    j.columns = j.columns.str.strip()
    skill_features = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    j.to_csv(OUT / "jds_skill_traits_cleaned.csv", index=False)
    skill_target = "salary_hike_high_or_low"
    skill_summary = {
        "audit": audit(j),
        "class_balance": {
            str(k): int(v)
            for k, v in j[skill_target].value_counts().sort_index().items()
        },
        "feature_means": {
            f: round(float(j[f].mean()), 3) for f in skill_features
        },
        "correlation_with_target": {
            f: round(float(j[[f, skill_target]].corr().iloc[0, 1]), 3)
            for f in skill_features
        },
    }
    save_json("jds_summary.json", skill_summary)

    # ---------------- SDS Personality Traits ----------------
    s = sds.copy()
    s.columns = s.columns.str.strip()
    personality_features = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    personality_target = "success_ classification_ high_low"
    s.to_csv(OUT / "sds_personality_traits_cleaned.csv", index=False)
    personality_summary = {
        "audit": audit(s),
        "class_balance": {
            str(k): int(v)
            for k, v in s[personality_target].value_counts().sort_index().items()
        },
        "feature_means": {
            f: round(float(s[f].mean()), 3) for f in personality_features
        },
        "correlation_with_target": {
            f: round(float(s[[f, personality_target]].corr().iloc[0, 1]), 3)
            for f in personality_features
        },
    }
    save_json("sds_summary.json", personality_summary)

    master = {
        "source": "Organizer-provided Build for Bharat / SAS hackathon datasets",
        "datasets": {
            "Analytics Jobs": analytics_summary["audit"],
            "DataScience Jobs": ds_summary["audit"],
            "JDS Skill Traits": skill_summary["audit"],
            "SDS Personality Traits": personality_summary["audit"],
        },
        "methodology_note": (
            "Datasets are analyzed as separate modules because they do not contain "
            "a shared individual-level key. No arbitrary row-level merge is performed."
        ),
    }
    save_json("master_audit.json", master)

    print("\nPHASE 1 COMPLETE")
    print(f"Output folder: {OUT}")
    print("Created:")
    for p in sorted(OUT.iterdir()):
        print(" -", p.name)


if __name__ == "__main__":
    run()
