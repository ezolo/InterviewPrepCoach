# Interview Prep AI – Agent Development Blueprint

This document explains how to build the Interview Prep AI agent step by step. Use it as a reference when orchestrating multiple AI components or delegating work to collaborators.

---

## 1. Define Persona & Responsibilities
```
- Persona: Experienced career coach + technical interviewer who understands resumes, job descriptions, interview frameworks (STAR), and job search workflows.
- Core responsibilities:
  1. Provide resume/JD compatibility insights and actionable feedback.
  2. Generate tailored interview questions with evaluation criteria.
  3. Guide practice sessions (written/audio/video) and score responses.
  4. Draft professional documents (resumes, cover letters, cold emails).
  5. Surface job opportunities and keep track of applications.
  6. Offer conversational coaching with contextual memory.
  7. Run mock interviews and deliver comprehensive reports.
```

## 2. Establish Knowledge Inputs
```
- Resume data: parsed text, extracted skills, work history, achievements.
- Job descriptions: requirements, responsibilities, company info.
- Practice history: previous responses, scores, strengths/gaps.
- Application data: saved jobs, application stages, reminders.
- Coaching logs: prior conversations, quick advice topics.
- Settings: preferred LLM provider, model, temperature, token limits.
```

## 3. Define Conversation & Tooling Interfaces
```
- Chat interface: handles free-form questions, quick advice, and file uploads (resume/JD).
- Structured prompts: predefined templates for compatibility analysis, question generation, practice evaluation, document writing, and mock interview feedback.
- Job search connector: wrapper around JSearch (or future APIs) that ranks results by fit.
- Application planner hooks: CRUD endpoints for applications and reminders.
- Mock interview engine: orchestrates session setup, response capture, and feedback loops.
```

## 4. Architect the Agent Workflow
```
Step 1: Intake
  - Detect whether the user is uploading a resume/JD, asking for advice, searching jobs, or launching a mock interview.
  - Update context objects (resume_context, jd_context, coaching_context).

Step 2: Intent Routing
  - Compatibility tasks -> invoke CompatibilityService + ResponseNormalizer.
  - Question requests -> QuestionService (with fallback parsing).
  - Practice responses -> PracticeService evaluation pipeline.
  - Document requests -> DocumentService with targeted prompts.
  - Job search/planner -> JSearchService + ApplicationService.
  - Coaching dialog -> CoachService + conversation memory.
  - Mock interviews -> MockInterviewService orchestration.

Step 3: Output Packaging
  - Summarize results in user-friendly formats (cards, tables, chips).
  - Persist insights (e.g., analyses, question sets, feedback) for later reuse.
```

## 5. Design Prompt Library & Guardrails
```
- Maintain dedicated system prompts for each capability (compatibility, questions, practice, writer, coach, mock interview).
- Include strict format instructions (JSON schemas) with normalization safeguards.
- Add fallback instructions for when responses exceed token limits or return malformed JSON.
- Keep a quick advice catalog that swaps placeholders (target role, industry, pain point).
```

## 6. Implement Memory & Personalization
```
- Store conversation summaries, goals, and action items per user.
- Track skill gaps, practice scores, and application statuses to personalize recommendations.
- When generating outputs, pull in the latest resume/JD context and note improvements since last session.
```

## 7. Validate Experience Loops
```
For each major workflow:
1. User uploads resume + JD -> receives compatibility score + next steps -> can reuse in Questions, Practice, Writer.
2. User practices a question -> gets STAR feedback -> sees impact on dashboard.
3. User searches jobs -> saves opportunities -> converts them into planner entries -> tracks progress.
4. User chats with coach -> receives tailored advice -> coach references prior history automatically.
5. User runs mock interview -> receives report -> improvements feed back into Practice and Planner views.
```

## 8. Plan Safety & Monitoring
```
- Log all agent actions with timestamps and context snippets.
- Watch for empty or low-confidence responses and trigger retries or human-in-the-loop prompts.
- Respect API quotas and secure secrets (API keys encrypted at rest).
- Provide clear messaging when a feature is offline or requires additional setup (e.g., missing API key).
```

## 9. Iterate & Expand
```
- Once the base agent is reliable, explore:
  - Multi-provider ensembles (choose best answer among providers).
  - Automated follow-up reminders for applications based on planner data.
  - Richer mock interview analytics (speech pacing, sentiment analysis).
  - Community templates for resumes/question sets.
```

---

**How to use this blueprint:** share it with engineers, prompt engineers, or product collaborators to ensure everyone understands how the agent should behave, what data it needs, and how each feature ties into the larger experience. Update it as the agent evolves.

