# Interview Prep AI – Prompt Recovery Plan

The first attempt used a single, catch-all instruction that produced a flat layout and broken features. This document keeps that original brief as **Phase 1** and then introduces follow-up prompts to systematically reshape the product into a stable, feature-complete experience.

---

## Phase 1 – Original Vague Prompt (for context only)
```
Create an interview preparation companion called Interview Prep AI. It should include: resume + job description compatibility scoring with matched/missing skills and improvement tips; an interview question generator tied to the user’s resume/JD; practice sessions for written/audio/video answers with AI scoring and STAR feedback; a document writer for resumes, cover letters, cold emails; job search results ranked by fit plus an application planner to track statuses; an AI career coach that remembers context and offers quick advice; and a mock interview studio with configurable formats, recordings, and post-session reports. Build it as a desktop app and make settings available to switch LLM providers.
```
*Result: produced a UI skeleton but most widgets were unhooked (no real data flow, navigation broke, and several views competed for space).*

---

## Phase 2 – Re-establish the MVP Core
```
Reset the project so Phase 2 only delivers a polished MVP: navigation shell, profile analysis (resume upload + JD input + compatibility scoring), question generation, and settings for LLM selection. Keep each view self-contained, wire buttons to placeholder service calls, and verify navigation works before adding more tabs.
```

## Phase 3 – Layer Practice & Writer Features
```
Add the Practice hub (written/audio/video responses with mock evaluation placeholders) and the Document Writer (resume/cover letter/cold email generation panes). Ensure these screens borrow data from the résumé/JD objects established in Phase 2 and do not disturb previously working flows.
```

## Phase 4 – Add Job Opportunities & Application Planner
```
Introduce job search results (stub compatibility ranks are fine) and an application planner board. Focus on CRUD flows, filter controls, and empty states. Confirm the earlier Profile, Questions, Practice, Writer, and Settings tabs still load without regression.
```

## Phase 5 – Bring in the Agentic Career Coach
```
Create a dedicated Career Coach view with chat history, quick-advice buttons, and attachment placeholders. Ensure the coach uses the same resume/JD context objects and that navigation/state persistence remain intact across all tabs.
```

## Phase 6 – Finish with the Mock Interview Studio & Polish
```
Implement the mock interview wizard, per-question flow, and results summary. Once this phase is stable, sweep the app for layout consistency, responsive behavior, and defensive error handling on every screen.
```

---

Use this recovery plan whenever a single overloaded prompt yields an unstable build: replay Phase 2 onward, verifying stability after each step before stacking the next feature set.

