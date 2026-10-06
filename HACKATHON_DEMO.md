# SkillFit — Hackathon Demo Flow

## 60-second demo
1. Open `/` and introduce SkillFit as a career intelligence layer, not just a job board.
2. Open Career Passport and enter candidate context: skills, experience, career break, location, work preference and target role.
3. Upload a resume. SkillFit extracts skills and updates the living profile.
4. Open Dashboard. Show profile strength, detected skills, top opportunity, opportunity count, location intelligence and next best action.
5. Open Opportunity Radar. Filter by location and work mode to show where opportunities are available.
6. Open a top role's Skill Gap. Show matched vs missing skills and mapped learning resources.
7. Open What-If Paths. Explain that a small skill bridge can unlock additional roles.

## Explainable matching
The demo score combines:
- 45% skill coverage
- 20% experience compatibility
- 15% location compatibility
- 10% work-mode compatibility
- 10% target-role relevance

Remote roles receive full location compatibility. A same-city role also receives full location compatibility. A different non-remote city is treated as a lower compatibility signal, not an automatic rejection.

Career breaks are stored as context and are not directly penalized by the scoring engine.

## Important demo note
The included jobs dataset is a curated demo dataset for the hackathon MVP. It is intentionally offline so the demo works reliably without third-party API keys or internet dependency. Do not describe it as live market availability. The architecture can later replace `backend/data/jobs.json` with a verified jobs API/connector.
