const path = window.location.pathname;

if (path === '/passport') passportPage();
if (path === '/resume') resumePage();
if (path === '/dashboard') dashboard();
if (path === '/jobs') jobsPage();
if (path === '/gap') gapPage();
if (path === '/assessment') assessmentPage();
if (path === '/reskill') reskillPage();
if (path === '/whatif') whatIfPage();
if (path === '/hackathon') hackathonPage();

/* -------------------------
   Career Passport
------------------------- */
async function passportPage() {
    try {
        const p = await profile();
        if (!p) return;

        document.getElementById('name').value = p.name || '';
        document.getElementById('email').value = p.email || '';
        document.getElementById('education').value = p.education || '';
        document.getElementById('experience').value = p.experience ?? 0;
        document.getElementById('careerBreak').value = p.career_break ?? 0;
        document.getElementById('locationx').value = p.location || '';
        document.getElementById('work').value = p.work_mode || 'Any';
        document.getElementById('role').value = p.target_role || '';
    } catch (error) {
        console.error('Passport load error:', error);
    }
}

async function save() {
    const data = {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        education: document.getElementById('education').value.trim(),
        experience: Number(document.getElementById('experience').value || 0),
        career_break: Number(document.getElementById('careerBreak').value || 0),
        location: document.getElementById('locationx').value.trim(),
        work_mode: document.getElementById('work').value,
        target_role: document.getElementById('role').value.trim()
    };

    if (!data.name) {
        toast('Please enter your name.');
        return;
    }

    try {
        const existingId = pid();
        let existingSkills = [];
        if (existingId) {
            try {
                const existing = await api(`/api/profile/${existingId}`);
                existingSkills = existing.skills || [];
            } catch (_) {}
        }
        data.skills = existingSkills;

        const result = await api(
            existingId ? `/api/profile/${existingId}` : '/api/profile',
            {
                method: existingId ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }
        );

        setid(result.id);
        toast(existingId ? 'Career Passport updated ✦' : 'Career Passport saved ✦');

        setTimeout(() => {
            window.location.href = '/resume';
        }, 650);
    } catch (error) {
        console.error('Save profile error:', error);
        toast(error.message);
    }
}

/* -------------------------
   Resume
------------------------- */
function resumePage() {
    const input = document.getElementById('resumeFile');
    const fileName = document.getElementById('fileName');

    if (!input) return;

    input.addEventListener('change', () => {
        fileName.textContent = input.files[0]?.name || 'No file selected';
    });
}

async function analyze() {
    try {
        const profileId = pid();
        if (!profileId) throw new Error('Create your Career Passport first.');

        const file = document.getElementById('resumeFile').files[0];
        if (!file) throw new Error('Choose a resume first.');

        const form = new FormData();
        form.append('file', file);

        const result = await api(`/api/resume/${profileId}`, {
            method: 'POST',
            body: form
        });

        document.getElementById('resumeOut').innerHTML = `
            <div class="card">
                <div class="kicker">Detected skill intelligence</div>
                <h2>We found ${result.skills.length} skills ✦</h2>
                <p class="muted">Extracted from <b>${result.filename}</b></p>
                <div class="tags" style="margin-top:14px">
                    ${tags(result.skills, 'good')}
                </div>
                <div class="right" style="margin-top:18px">
                    <a class="btn" href="/dashboard">See my dashboard →</a>
                </div>
            </div>
        `;

        toast('Resume analyzed successfully ✦');
    } catch (error) {
        console.error('Resume analysis error:', error);
        toast(error.message);
    }
}

/* -------------------------
   Dashboard
------------------------- */
async function dashboard() {
    const host = document.getElementById('dash');
    const p = await profile();

    if (!p) {
        host.innerHTML = `
            <div class="card" style="text-align:center;padding:50px">
                <h2>Welcome to SkillFit ✦</h2>
                <p class="muted">Create your Career Passport to start.</p>
                <a class="btn" href="/passport">Create passport →</a>
            </div>`;
        return;
    }

    try {
        const matches = await api(`/api/matches/${p.id}`);
        const top = matches[0];

        /* Profile completeness is intentionally different from job-fit.
           It measures whether the living Career Passport is complete. */
        const profileChecks = [
            ['Identity', !!p.name && !!p.email],
            ['Education', !!p.education],
            ['Experience', p.experience !== null && p.experience !== undefined],
            ['Career context', p.career_break !== null && p.career_break !== undefined],
            ['Location', !!p.location],
            ['Work preference', !!p.work_mode],
            ['Target role', !!p.target_role],
            ['Skills / resume', (p.skills || []).length > 0 || !!p.resume]
        ];
        const completion = Math.round(
            profileChecks.filter(x => x[1]).length / profileChecks.length * 100
        );

        const locations = [...new Set(matches.map(j => j.location))].sort();
        const remoteCount = matches.filter(j => j.work_mode.toLowerCase() === 'remote').length;
        const hybridCount = matches.filter(j => j.work_mode.toLowerCase() === 'hybrid').length;
        const onsiteCount = matches.filter(j => j.work_mode.toLowerCase() === 'onsite').length;
        const localJobs = matches.filter(
            j => p.location && j.location.toLowerCase() === p.location.toLowerCase()
        ).length;

        const missing = top ? top.missing_skills : [];
        const nextSkill = missing[0] || 'Explore your strongest match';

        // Count opportunities unlocked by the smallest skill bridge.
        const bridgeSkill = missing[0] ? missing[0].toLowerCase() : '';
        const bridgeUnlocks = bridgeSkill
            ? matches.filter(j => (j.missing_skills || []).some(s => s.toLowerCase() === bridgeSkill)).length
            : 0;

        const locationSummary = locations
            .map(loc => `${loc} (${matches.filter(j => j.location === loc).length})`)
            .join(' • ');

        const fitLabel = top
            ? (top.match_score >= 80 ? 'Excellent fit' : top.match_score >= 65 ? 'Strong potential' : top.match_score >= 50 ? 'Promising with a skill bridge' : 'Needs targeted upskilling')
            : 'No match yet';

        const score = top ? Math.round(top.match_score) : 0;
        const matchedCount = top ? top.matched_skills.length : 0;
        const missingCount = top ? top.missing_skills.length : 0;

        host.innerHTML = `
            <div class="dashboard-banner">
                <div>
                    <div class="kicker">Career command center</div>
                    <h2>Hi ${(p.name || '').split(' ')[0]} — here's your next move. ✦</h2>
                    <p class="muted">One living profile → explainable matching → skill bridge → better opportunities.</p>
                </div>
                <div class="banner-actions">
                    <a class="btn sm" href="/jobs">Explore opportunities →</a>
                    <a class="btn alt sm" href="/passport">Edit passport</a>
                </div>
            </div>

            <div class="grid4 dashboard-kpis" style="margin-top:15px">
                <div class="kpi">
                    <small>Profile completeness</small>
                    <strong>${completion}%</strong>
                    <span class="muted">${completion === 100 ? 'Career Passport complete' : 'Complete missing profile fields'}</span>
                </div>
                <div class="kpi">
                    <small>Skills detected</small>
                    <strong>${p.skills.length}</strong>
                    <span class="muted">${p.resume ? 'Passport + resume intelligence' : 'From Career Passport'}</span>
                </div>
                <div class="kpi">
                    <small>Top opportunity</small>
                    <strong>${top ? Math.round(top.match_score) + '%' : '—'}</strong>
                    <span class="muted">${top ? top.role : 'No match yet'}</span>
                </div>
                <div class="kpi">
                    <small>Opportunity pool</small>
                    <strong>${matches.length}</strong>
                    <span class="muted">${localJobs} local • ${remoteCount} remote</span>
                </div>
            </div>

            <div class="dashboard-insight-grid" style="margin-top:15px">
                <div class="card fit-card">
                    <div class="split-head">
                        <div>
                            <div class="kicker">Explainable match</div>
                            <h2>${top ? top.role : 'No opportunity yet'}</h2>
                            <p class="muted">${top ? `${top.company} • ${top.location} • ${top.work_mode}` : 'Upload a resume and build your profile.'}</p>
                        </div>
                        ${top ? `<div class="match-badge">${score}%<small>FIT</small></div>` : ''}
                    </div>

                    ${top ? `
                    <div class="fit-status">${fitLabel}</div>
                    <div class="match-bars">
                        <div><span>Skills</span><b>${Math.round(top.skill_score)}%</b><i><em style="width:${top.skill_score}%"></em></i></div>
                        <div><span>Experience</span><b>${Math.round(top.experience_score)}%</b><i><em style="width:${top.experience_score}%"></em></i></div>
                        <div><span>Location</span><b>${Math.round(top.location_score)}%</b><i><em style="width:${top.location_score}%"></em></i></div>
                        <div><span>Work mode</span><b>${Math.round(top.work_score)}%</b><i><em style="width:${top.work_score}%"></em></i></div>
                        <div><span>Role relevance</span><b>${Math.round(top.role_score)}%</b><i><em style="width:${top.role_score}%"></em></i></div>
                    </div>
                    <div class="why-row">
                        <div><b>${matchedCount}</b><span>matched skills</span></div>
                        <div><b>${missingCount}</b><span>skills to bridge</span></div>
                        <div><b>${top.salary}</b><span>indicative range</span></div>
                    </div>
                    <div class="tags" style="margin-top:14px">${tags(top.matched_skills, 'good')}</div>
                    ${missingCount ? `<div class="missing-line"><b>Smallest bridge:</b> ${top.missing_skills.slice(0,4).join(', ')}</div>` : `<div class="ready-line">✓ Strong skill coverage — ready to explore this role</div>`}
                    <div style="margin-top:15px"><a class="btn sm" href="/gap?job=${top.id}">See why this matches →</a></div>
                    ` : ''}
                </div>

                <div class="card action-card">
                    <div class="kicker">Next best action</div>
                    <h2>${missing.length ? `Learn ${nextSkill}` : 'You are application-ready'}</h2>
                    <p class="muted">${missing.length
                        ? `${nextSkill} is the first skill bridge for your strongest current match.`
                        : 'Your current profile has strong coverage. Explore opportunities and verify your skills.'}</p>

                    <div class="bridge-hero">
                        <span>SKILL BRIDGE</span>
                        <b>${missing.length ? `${bridgeUnlocks} opportunities` : `${score}% fit`}</b>
                        <small>${missing.length ? `could benefit from learning ${nextSkill}` : 'current strongest match'}</small>
                    </div>

                    <div class="action-checklist">
                        <div>✓ Profile context captured</div>
                        <div>✓ Resume skills extracted</div>
                        <div>${missing.length ? '→' : '✓'} ${missing.length ? `Bridge ${nextSkill}` : 'Ready for opportunity review'}</div>
                    </div>

                    <a class="btn sm" href="${missing.length ? `/gap?job=${top.id}` : '/jobs'}">
                        ${missing.length ? 'Understand skill gap →' : 'View opportunities →'}
                    </a>
                </div>
            </div>

            <div class="card" style="margin-top:15px">
                <div class="split-head">
                    <div>
                        <div class="kicker">Career signal</div>
                        <h2>Capability snapshot</h2>
                        <p class="muted">Your current capabilities become the input for every match, gap and what-if path.</p>
                    </div>
                    <a class="btn alt sm" href="/resume">Analyze / update resume</a>
                </div>
                <div class="tags" style="margin-top:14px">${tags(p.skills, 'good')}</div>
                ${p.career_break > 0 ? `<div class="context-note">↳ ${p.career_break} year career break captured as context — not treated as a skill penalty.</div>` : ''}
            </div>

            <div class="card" style="margin-top:15px">
                <div class="split-head">
                    <div>
                        <div class="kicker">Bharat opportunity radar</div>
                        <h2>Where can you apply?</h2>
                        <p class="muted">Current curated demo dataset: ${locationSummary || 'No locations yet'}. These are demo opportunities, not live vacancies.</p>
                    </div>
                    <a class="btn alt sm" href="/jobs">Filter jobs →</a>
                </div>

                <div class="location-stats">
                    <div><b>${localJobs}</b><span>in your city</span></div>
                    <div><b>${remoteCount}</b><span>remote</span></div>
                    <div><b>${hybridCount}</b><span>hybrid</span></div>
                    <div><b>${onsiteCount}</b><span>onsite</span></div>
                </div>

                <div class="location-grid" style="margin-top:14px">
                    ${locations.map(loc => {
                        const count = matches.filter(j => j.location === loc).length;
                        const isLocal = p.location && loc.toLowerCase() === p.location.toLowerCase();
                        return `<a class="location-chip ${isLocal ? 'selected' : ''}" href="/jobs?location=${encodeURIComponent(loc)}">
                            <span>📍 ${loc}</span>
                            <b>${count} job${count === 1 ? '' : 's'}</b>
                            ${isLocal ? '<small>✓ Your location</small>' : '<small>View matching roles →</small>'}
                        </a>`;
                    }).join('')}
                    <a class="location-chip remote" href="/jobs?mode=Remote">
                        <span>🌐 Remote</span><b>${remoteCount} jobs</b><small>Work from anywhere</small>
                    </a>
                </div>
            </div>

            <div class="card" style="margin-top:15px">
                <div class="split-head">
                    <div>
                        <div class="kicker">Opportunity radar</div>
                        <h2>Best-fit roles</h2>
                        <p class="muted">Ranked using skill coverage, experience, location, work mode and target-role relevance.</p>
                    </div>
                    <a class="btn sm" href="/jobs">See all →</a>
                </div>
                <div class="jobgrid" style="margin-top:14px">${matches.slice(0, 4).map(jobCard).join('')}</div>
            </div>

            <div class="card whatif-preview" style="margin-top:15px">
                <div>
                    <div class="kicker">What-if career paths</div>
                    <h2>One small bridge can expand your opportunity set.</h2>
                    <p class="muted">SkillFit turns missing skills into a concrete next step instead of simply rejecting a candidate.</p>
                </div>
                <a class="btn sm" href="/whatif">Explore what-if paths →</a>
            </div>
        `;
    } catch (error) {
        console.error('Dashboard error:', error);
        host.innerHTML = `<div class="card"><h2>Dashboard error</h2><p class="muted">${error.message}</p><a class="btn sm" href="/passport">Open passport</a></div>`;
    }
}

function jobCard(job) {
    const scoreClass = job.match_score >= 80 ? 'high' : job.match_score >= 60 ? 'mid' : 'low';
    const missing = job.missing_skills || [];
    return `
        <div class="job">
            <div class="jobtop">
                <div><div class="company">${job.company}</div><h3>${job.role}</h3></div>
                <div class="score ${scoreClass}">${Math.round(job.match_score)}%</div>
            </div>
            <div class="meta"><span>📍 ${job.location}</span><span>💼 ${job.work_mode}</span><span>💰 ${job.salary}</span></div>
            <div class="tags" style="margin-top:13px">${tags(job.matched_skills, 'good')}</div>
            ${missing.length ? `<div class="missing-line"><b>Gap:</b> ${missing.slice(0,3).join(', ')}${missing.length > 3 ? ' +' + (missing.length - 3) : ''}</div>` : `<div class="ready-line">✓ Strong skill coverage</div>`}
            <div class="right" style="margin-top:15px"><a class="btn sm" href="/gap?job=${job.id}">See fit & gap →</a></div>
        </div>`;
}

/* -------------------------
   Jobs
------------------------- */
let jobs = [];

async function jobsPage() {
    const host = document.getElementById('jobsList');
    const p = await profile();
    if (!p) {
        host.innerHTML = `<div class="card" style="grid-column:1/-1;text-align:center"><h2>Create your Career Passport first ✦</h2><a class="btn" href="/passport">Create Passport →</a></div>`;
        return;
    }
    try {
        jobs = await api(`/api/matches/${p.id}`);
        const locations = [...new Set(jobs.map(j => j.location))].sort();
        const locationSelect = document.getElementById('jobLocation');
        if (locationSelect) locationSelect.innerHTML = `<option value="">All locations</option>${locations.map(x => `<option>${x}</option>`).join('')}`;
        const params = new URLSearchParams(window.location.search);
        if (locationSelect && params.get('location')) locationSelect.value = params.get('location');
        const mode = document.getElementById('jobMode');
        if (mode && params.get('mode')) mode.value = params.get('mode');
        renderJobs();
    } catch (error) {
        host.innerHTML = `<div class="card" style="grid-column:1/-1">${error.message}</div>`;
    }
}

function renderJobs() {
    const query = (document.getElementById('jobSearch')?.value || '').toLowerCase();
    const minimum = Number(document.getElementById('minMatch')?.value || 0);
    const location = document.getElementById('jobLocation')?.value || '';
    const mode = document.getElementById('jobMode')?.value || '';
    const filtered = jobs.filter(job => {
        const text = `${job.role} ${job.company} ${job.skills.join(' ')} ${job.location}`.toLowerCase();
        return text.includes(query) && job.match_score >= minimum && (!location || job.location === location) && (!mode || job.work_mode === mode);
    });
    document.getElementById('jobsList').innerHTML = filtered.length
        ? filtered.map(jobCard).join('')
        : `<div class="card" style="grid-column:1/-1;text-align:center"><h3>No opportunities match those filters.</h3><p class="muted">Try another location, work mode or match threshold.</p></div>`;
}

/* -------------------------
   Skill Gap
------------------------- */
async function gapPage() {
    const host = document.getElementById('gapOut');
    const p = await profile();

    if (!p) {
        host.innerHTML = `<div class="card"><a class="btn" href="/passport">Create Passport →</a></div>`;
        return;
    }

    try {
        const matches = await api(`/api/matches/${p.id}`);
        const params = new URLSearchParams(window.location.search);
        const jobId = Number(params.get('job')) || matches[0]?.id;

        if (!jobId) throw new Error('No job available.');

        const data = await api(`/api/gap/${p.id}/${jobId}`);

        host.innerHTML = `
            <div class="card">
                <div class="gap">
                    <div class="ring" style="--s:${data.match_score}">
                        <div>
                            <span>${Math.round(data.match_score)}%</span>
                            <small>fit</small>
                        </div>
                    </div>
                    <div>
                        <div class="company">${data.job.company}</div>
                        <h2>${data.job.role}</h2>
                        <p class="muted">${data.job.location} • ${data.job.work_mode} • ${data.job.salary}</p>
                        <div class="tags">${tags(data.job.skills)}</div>
                    </div>
                </div>
            </div>

            <div class="grid3" style="margin-top:15px">
                <div class="kpi"><small>Matched skills</small><strong>${data.matched_skills.length}</strong></div>
                <div class="kpi"><small>Missing skills</small><strong>${data.missing_skills.length}</strong></div>
                <div class="kpi"><small>Skill score</small><strong>${Math.round(data.skill_score)}%</strong></div>
            </div>

            <div class="grid2" style="margin-top:15px">
                <div class="card">
                    <div class="kicker">Matched</div>
                    <h3>Already working for you</h3>
                    <div class="tags">${tags(data.matched_skills, 'good')}</div>
                </div>
                <div class="card">
                    <div class="kicker">Missing</div>
                    <h3>Smallest bridge</h3>
                    <div class="tags">${tags(data.missing_skills, 'bad')}</div>
                </div>
            </div>

            <div class="card" style="margin-top:15px;background:linear-gradient(135deg,#f0ecff,#fff1f7)">
                <div class="kicker">Skill Bridge</div>
                <h2>Learn what actually unlocks the role.</h2>
                <div class="grid2" style="margin-top:15px">
                    ${data.courses.length ? data.courses.map(course => `
                        <div class="card course">
                            <b>${course.skill}</b>
                            <h3>${course.title}</h3>
                            <p class="muted">${course.duration} • ${course.level}</p>
                            <a class="btn alt sm" href="/reskill">Add to plan →</a>
                        </div>
                    `).join('') : `<p class="muted">No mapped learning resource yet.</p>`}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Gap page error:', error);
        host.innerHTML = `<div class="card"><h2>Could not load skill gap</h2><p class="muted">${error.message}</p></div>`;
    }
}

/* -------------------------
   Assessment
------------------------- */
function assessmentPage() {
    const questions = [
        {
            question: 'Which SQL clause groups rows?',
            options: ['GROUP BY', 'ORDER BY', 'WHERE', 'DISTINCT'],
            answer: 0
        },
        {
            question: 'Which Python library handles tabular data?',
            options: ['Pandas', 'Flask', 'FastAPI', 'PyGame'],
            answer: 0
        },
        {
            question: 'Which command combines matching records?',
            options: ['JOIN', 'DROP', 'DELETE', 'TRUNCATE'],
            answer: 0
        },
        {
            question: 'What does KPI represent?',
            options: ['Key Performance Indicator', 'Kernel Program Input', 'Known Process Index', 'Key Python Instruction'],
            answer: 0
        }
    ];

    document.getElementById('quiz').innerHTML = questions.map((q, i) => `
        <div class="card" style="margin-bottom:12px">
            <b>${i + 1}. ${q.question}</b>
            ${q.options.map((option, k) => `
                <label style="display:block;padding:10px;border:1px solid var(--line);border-radius:10px;margin-top:7px;font-size:12px;cursor:pointer">
                    <input type="radio" name="q${i}" value="${k}"> ${option}
                </label>
            `).join('')}
        </div>
    `).join('');

    window.skillFitQuestions = questions;
}

async function submitQuiz() {
    const p = await profile();
    if (!p) {
        toast('Create your Career Passport first.');
        return;
    }

    let correct = 0;

    window.skillFitQuestions.forEach((question, i) => {
        const selected = document.querySelector(`input[name="q${i}"]:checked`);
        if (selected && Number(selected.value) === question.answer) {
            correct++;
        }
    });

    const score = Math.round(correct / window.skillFitQuestions.length * 100);

    try {
        await api('/api/assessment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile_id: p.id,
                role: p.target_role || 'Data Analyst',
                score
            })
        });

        document.getElementById('assessmentOut').innerHTML = `
            <div class="card" style="background:linear-gradient(135deg,#f0ecff,#fff1f7)">
                <div class="kicker">Assessment complete</div>
                <h2>${score}% skill verification</h2>
                <p class="muted">You got ${correct} out of ${window.skillFitQuestions.length} correct.</p>
                <a class="btn" href="/reskill">Open reskill plan →</a>
            </div>
        `;
    } catch (error) {
        toast(error.message);
    }
}

/* -------------------------
   Reskill
------------------------- */
async function reskillPage() {
    const host = document.getElementById('reskillOut');
    const p = await profile();

    if (!p) {
        host.innerHTML = `<div class="card"><a class="btn" href="/passport">Create Passport →</a></div>`;
        return;
    }

    try {
        const matches = await api(`/api/matches/${p.id}`);
        const top = matches[0];
        if (!top) throw new Error('No opportunity available.');

        const data = await api(`/api/gap/${p.id}/${top.id}`);

        host.innerHTML = `
            <div class="card" style="background:linear-gradient(135deg,#effcf8,#f1edff)">
                <div class="kicker">ReSkill → ReAssess → ReApply</div>
                <h2>Learning sprint for ${top.role}</h2>
                <p class="muted">Focus on the smallest set of skills that can move your fit.</p>
                <div class="tags" style="margin-top:13px">${tags(data.missing_skills, 'bad')}</div>
            </div>

            <div class="grid3" style="margin-top:15px">
                ${data.courses.length ? data.courses.map((course, i) => `
                    <div class="card course">
                        <div class="kicker">Sprint ${i + 1} • ${course.skill}</div>
                        <h3>${course.title}</h3>
                        <p class="muted">${course.duration} • ${course.level}</p>
                        <a class="btn sm" href="/assessment">Reassess →</a>
                    </div>
                `).join('') : `
                    <div class="card">
                        <h3>You're already strongly aligned ✦</h3>
                        <p class="muted">No mapped skill bridge is needed for the current top opportunity.</p>
                    </div>
                `}
            </div>
        `;
    } catch (error) {
        host.innerHTML = `<div class="card"><h2>Could not load reskill plan</h2><p class="muted">${error.message}</p></div>`;
    }
}

/* -------------------------
   What-If
------------------------- */
async function whatIfPage() {
    const host = document.getElementById('whatifOut');
    const p = await profile();

    if (!p) {
        host.innerHTML = `<div class="card"><a class="btn" href="/passport">Create Passport →</a></div>`;
        return;
    }

    try {
        const paths = await api(`/api/whatif/${p.id}`);

        host.innerHTML = `
            <div class="card" style="background:linear-gradient(135deg,#fff1f7,#f0ecff)">
                <div class="kicker">What-if paths</div>
                <h2>Small upgrade. New role. ✦</h2>
                <p class="muted">See which roles become more realistic when you close a targeted skill gap.</p>
                <div class="whatif-explainer">
                    <span>HOW IT WORKS</span>
                    <b>Your current skills → targeted bridge → projected opportunity fit</b>
                </div>
            </div>

            ${paths.length ? `
            <div class="whatif-grid" style="margin-top:15px">
                ${paths.map(path => `
                    <div class="card whatif-card">
                        <div class="split-head">
                            <div>
                                <div class="company">${path.company}</div>
                                <h2 style="font-size:22px">${path.role}</h2>
                                <p class="muted" style="font-size:10px">📍 ${path.location} • ${path.work_mode}</p>
                            </div>
                            <div class="unlock-badge">+${path.gain}%<small>potential</small></div>
                        </div>

                        <div class="whatif-score-row">
                            <div><span>Current fit</span><b>${Math.round(path.current_match)}%</b></div>
                            <div class="arrow">→</div>
                            <div><span>After bridge</span><b>${Math.round(path.projected_match)}%</b></div>
                        </div>

                        <div class="muted" style="font-size:10px;margin-top:15px">You already have</div>
                        <div class="tags" style="margin:8px 0">${tags(path.have, 'good')}</div>

                        <div class="bridge-label">TARGETED SKILL BRIDGE</div>
                        <div class="tags" style="margin:8px 0">${tags(path.unlock, 'bad')}</div>

                        <div class="bridge-copy">Learn these ${path.unlock.length === 1 ? 'skill' : 'skills'} to make this role more accessible.</div>
                        <a class="btn alt sm" href="/reskill">Build this bridge →</a>
                    </div>
                `).join('')}
            </div>` : `
                <div class="card empty-state" style="margin-top:15px">
                    <div class="empty-icon">✦</div>
                    <h2>No what-if paths yet</h2>
                    <p class="muted">Add more skills through your Career Passport or Resume Analyzer and SkillFit will show nearby career paths you can unlock.</p>
                    <a class="btn sm" href="/resume">Analyze resume →</a>
                </div>
            `}
        `;
    } catch (error) {
        console.error('What-if error:', error);
        host.innerHTML = `<div class="card"><h2>Could not load career paths</h2><p class="muted">${error.message}</p></div>`;
    }
}

/* -------------------------
   Hackathon Intelligence
------------------------- */
async function hackathonPage() {
    const host = document.getElementById('hackathonOut');
    try {
        host.innerHTML = `
            <div class="card hackathon-loading">
                <div class="kicker">Official hackathon analytics</div>
                <h2>Loading SkillFit intelligence…</h2>
                <p class="muted">Reading the organizer datasets and calculating the validated model benchmarks. This can take a few seconds.</p>
            </div>
        `;

        const [data, p] = await Promise.all([
            api('/api/hackathon/insights'),
            profile()
        ]);

        const market = data.analytics_jobs;
        const ds = data.data_science_jobs;
        const skill = data.skill_success_model;
        const personality = data.personality_success_model;

        const candidateSkills = new Set((p?.skills || []).map(x => String(x).trim().toLowerCase()));
        const marketTop = market.top_skills || [];
        const matchedMarket = marketTop.filter(x => candidateSkills.has(String(x.skill).toLowerCase()));
        const coverage = marketTop.length
            ? Math.round(matchedMarket.length / marketTop.length * 100)
            : 0;

        const modelCard = (title, subtitle, result, label) => {
            const best = result.best_by_f1;
            const rows = result.models || [];
            const importance = result.random_forest_feature_importance || [];
            return `
                <div class="card hack-card">
                    <div class="kicker">${label}</div>
                    <h2>${title}</h2>
                    <p class="muted">${subtitle}</p>
                    <div class="hack-model-best">
                        <span>Best by F1</span>
                        <b>${best.model.replace('_', ' ')}</b>
                        <strong>${(best.f1 * 100).toFixed(1)}%</strong>
                    </div>
                    <div class="hack-metrics">
                        ${rows.map(row => `
                            <div>
                                <small>${row.model.replace('_', ' ')}</small>
                                <b>F1 ${(row.f1 * 100).toFixed(1)}%</b>
                                <span>ROC-AUC ${(row.roc_auc * 100).toFixed(1)}%</span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="hack-subhead">Random Forest feature importance</div>
                    <div class="importance-list">
                        ${importance.map((x, i) => `
                            <div class="importance-row">
                                <div class="importance-label"><span>${i + 1}. ${x.feature.replaceAll('_', ' ')}</span><b>${(x.importance * 100).toFixed(1)}%</b></div>
                                <div class="importance-bar"><i style="width:${Math.max(4, x.importance * 100)}%"></i></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        };

        host.innerHTML = `
            <div class="hack-hero">
                <div>
                    <div class="kicker">Build for Bharat 2.0 • Data Intelligence</div>
                    <h2>SkillFit × Official Hackathon Data</h2>
                    <p>Market demand + technical skill signals + personality signals, converted into explainable career intelligence.</p>
                </div>
                <div class="hack-hero-badge">DATA<br>BACKED</div>
            </div>

            <div class="grid4 hack-kpis" style="margin-top:15px">
                <div class="kpi"><small>Analytics job records</small><strong>${market.rows.toLocaleString()}</strong><span class="muted">Organizer dataset</span></div>
                <div class="kpi"><small>Data Science records</small><strong>${ds.rows.toLocaleString()}</strong><span class="muted">Organizer dataset</span></div>
                <div class="kpi"><small>JDS model F1</small><strong>${(skill.best_by_f1.f1 * 100).toFixed(1)}%</strong><span class="muted">5-fold CV benchmark</span></div>
                <div class="kpi"><small>SDS model F1</small><strong>${(personality.best_by_f1.f1 * 100).toFixed(1)}%</strong><span class="muted">5-fold CV benchmark</span></div>
            </div>

            <div class="card" style="margin-top:15px">
                <div class="split-head">
                    <div>
                        <div class="kicker">How the datasets connect</div>
                        <h2>Four datasets → three intelligence lenses</h2>
                        <p class="muted">The organizer files do not share an individual-level key, so SkillFit does not falsely join them. Each dataset contributes evidence to a separate analytical layer.</p>
                    </div>
                </div>
                <div class="hack-flow">
                    <div><b>01</b><strong>Job Market</strong><span>Analytics + Data Science postings</span></div>
                    <div><b>02</b><strong>Skill Success</strong><span>JDS technical skill dimensions</span></div>
                    <div><b>03</b><strong>Personality Success</strong><span>SDS Big Five dimensions</span></div>
                    <div><b>04</b><strong>Career Intelligence</strong><span>Combined at recommendation layer</span></div>
                </div>
            </div>

            <div class="grid2 hack-grid" style="margin-top:15px">
                <div class="card hack-card">
                    <div class="kicker">Job Market Intelligence</div>
                    <h2>What the market is asking for</h2>
                    <p class="muted">Top skills appearing in the supplied Analytics Jobs dataset.</p>
                    <div class="hack-list">
                        ${marketTop.slice(0, 10).map((x, i) => `
                            <div class="hack-list-row"><span><b>${i + 1}</b> ${x.skill}</span><strong>${x.count.toLocaleString()}</strong></div>
                        `).join('')}
                    </div>
                </div>

                <div class="card hack-card">
                    <div class="kicker">Candidate → Market Alignment</div>
                    <h2>${coverage}% top-skill coverage</h2>
                    <p class="muted">Your current SkillFit skills compared with the top market skills in the organizer dataset.</p>
                    <div class="tags" style="margin-top:13px">${tags(matchedMarket.map(x => x.skill), 'good')}</div>
                    <div class="hack-note">${matchedMarket.length ? `Matched ${matchedMarket.length} of the top ${marketTop.length} market skill signals.` : 'No exact overlap with the top market skill labels yet. This is a vocabulary alignment signal, not a hiring probability.'}</div>
                    <div class="hack-subhead">Top locations</div>
                    <div class="tags">${(market.top_locations || []).slice(0, 8).map(x => `<span class="tag">${x.location} • ${x.count.toLocaleString()}</span>`).join('')}</div>
                </div>
            </div>

            <div class="grid2 hack-grid" style="margin-top:15px">
                ${modelCard(
                    'Technical Skill Success',
                    'Observed salary-hike high/low classification from the JDS Skill Traits dataset.',
                    skill,
                    'JDS • Technical skill benchmark'
                )}
                ${modelCard(
                    'Personality Success',
                    'Observed success high/low classification from the SDS Personality Traits dataset.',
                    personality,
                    'SDS • Personality benchmark'
                )}
            </div>

            <div class="grid2 hack-grid" style="margin-top:15px">
                <div class="card hack-card">
                    <div class="kicker">Data Science Market</div>
                    <h2>Salary & role signals</h2>
                    <div class="hack-stats">
                        <div><span>Median average salary</span><b>${ds.median_avg_salary_lpa} LPA</b></div>
                        <div><span>Mean average salary</span><b>${ds.mean_avg_salary_lpa} LPA</b></div>
                        <div><span>Maximum salary</span><b>${ds.max_salary_lpa} LPA</b></div>
                    </div>
                    <div class="hack-subhead">Top roles by total jobs</div>
                    <div class="hack-list">
                        ${(ds.top_roles_by_total_jobs || []).slice(0, 8).map(x => `
                            <div class="hack-list-row"><span>${x.job_title}</span><strong>${Number(x.total_jobs || 0).toLocaleString()}</strong></div>
                        `).join('')}
                    </div>
                </div>

                <div class="card hack-card hack-caveat">
                    <div class="kicker">Responsible interpretation</div>
                    <h2>What the model does — and does not — say</h2>
                    <ul>
                        <li>Feature importance shows predictive contribution within the fitted Random Forest, not causation.</li>
                        <li>High/low outcomes are observed labels in the supplied datasets, not guaranteed future success.</li>
                        <li>Personality is not inferred from a resume. A future assessment can provide those dimensions explicitly.</li>
                        <li>Market coverage is a vocabulary-alignment signal, not a probability of getting hired.</li>
                        <li>The What-If engine remains a scenario-based fit projection, not a salary forecast.</li>
                    </ul>
                </div>
            </div>

            <div class="card hack-final" style="margin-top:15px">
                <div>
                    <div class="kicker">Hackathon story</div>
                    <h2>From data → evidence → personalized action.</h2>
                    <p class="muted">SkillFit uses the official datasets as evidence layers, then connects those insights to the candidate's existing profile, skill gaps and explainable opportunity matching.</p>
                </div>
                <div class="hack-final-flow">Resume → Skill DNA → Market Demand → Success Signals → Skill Gap → Career Action</div>
            </div>
        `;
    } catch (error) {
        console.error('Hackathon intelligence error:', error);
        host.innerHTML = `
            <div class="card">
                <div class="kicker">Hackathon Intelligence</div>
                <h2>Could not load the organizer datasets</h2>
                <p class="muted">${error.message}</p>
                <p class="muted">Make sure the four official files are inside <code>backend/hackathon_data</code>.</p>
            </div>
        `;
    }
}
