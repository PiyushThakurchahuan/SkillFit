# Official Hackathon Data

Copy the four organizer-provided files into this folder:

1. Analytics Jobs.csv
2. DataScience Jobs.csv
3. JDS Skill Traits.xlsx
4. SDS Personality Traits.xlsx

Do not rename the files.

The files are intentionally not committed here. The application code reads them
locally so the official hackathon data remains separate from SkillFit's demo
job catalog.

Run the API from the SkillFit project root:

    uvicorn backend.main:app --reload

Then open:

    http://127.0.0.1:8000/docs

Use GET /api/hackathon/insights to run the official-data analysis.


## Phase 1: Data Audit + Cleaning

From the SkillFit project root run:

    python backend/analyze_hackathon.py

This creates backend/hackathon_output/ containing cleaned CSVs and JSON summaries for the Approach Note. The generated output is intentionally local and should not be uploaded to the repository.
