---
name: project-planning
description: Run the collaborative planning process for a Clearbox Builds project — read ai/plan-overview.md, ask clarifying questions with a suggested answer for every open question/decision, then create ai/plan.md (the full agreed plan, including decisions) and ai/plan-status.md (the phase tracker). Use this whenever the user says things like "let's plan this project", "start planning", "kick off planning", "help me plan this out", "turn the overview into a plan", or otherwise wants to go from the plan overview to a real plan — use it INSTEAD of plan mode, EnterPlanMode, or /plan.
---

# Project Planning

Turn the human's `ai/plan-overview.md` into an agreed-upon plan through conversation, then record it in `ai/plan.md` and `ai/plan-status.md`.

This skill exists instead of plan mode on purpose: the human wants a back-and-forth conversation whose result lives in the repo, not a plan-mode flow that escalates into ultraplan. So don't call EnterPlanMode or suggest /plan — just talk it through here.

## The three files

| File | Owner | What you do with it |
|---|---|---|
| `ai/plan-overview.md` | The human | **Read only.** Never edit, reformat, fix typos in, or append to it. It's the record of the human's original intent; how that intent evolves is captured in `plan.md`. |
| `ai/plan.md` | Shared | Create it once decisions are settled. Refine it as the conversation continues. Once implementation starts, it only changes if core parts of the plan change. |
| `ai/plan-status.md` | You | Create it alongside `plan.md`. It tracks every phase's status and holds notes future sessions need. |

## Step 1: Read and check preconditions

1. Read `ai/plan-overview.md`, `CLAUDE.md`, and glance at what already exists in `src/` so your questions reflect reality.
2. If the overview is missing, or still has template placeholders (e.g. `Name`, `Description of new project`, `List of requirements`), stop. Tell the human which sections need filling in. Don't invent a project to plan.
3. If `ai/plan.md` or `ai/plan-status.md` already exists, don't overwrite it. Say what's there and ask whether to keep refining it or start over.

## Step 2: First response — understanding, questions, suggested answers

Reply in chat (not in a file) with:

1. **My understanding** — 2–4 sentences restating the project. Misreadings are cheapest to catch here.
2. **Open questions & decisions from the overview** — every item listed under the overview's outstanding questions/decisions section, none skipped. For each: a **suggested answer**, a one-line reason, and the real alternative(s) if the tradeoff is close.
3. **My clarifying questions** — gaps you found: vague or conflicting requirements, unstated scope, tech stack, success criteria, testing approach, deployment/hosting, data/storage, anything whose answer would change the plan. Give each one a suggested answer too, so the human can just agree.
4. **Assumptions** — what you're assuming that isn't stated anywhere.
5. **Pushback** — if a requirement looks overcomplicated or a simpler approach exists, say so.

Number every item across sections 2 and 3 (1, 2, 3, …) so the human can reply tersely, e.g. "1 yes, 2 use SQLite, 3–5 fine".

Only ask questions whose answers actually change the plan. A handful of sharp questions is better than twenty generic ones.

Then **stop and wait**. Don't write `plan.md` in this turn: the plan should record the human's decisions, not your guesses.

## Step 3: Iterate until decisions are settled

Work through the human's answers. Ask follow-ups only if the answers raise new questions. "Go with your suggestions" (for everything or specific numbers) means those suggestions are accepted decisions. An item the human explicitly defers goes into Open items instead of becoming a decision.

When every listed question and every question you asked is decided or explicitly deferred, write both files.

## Step 4: Write `ai/plan.md`

Use this structure. Leave out any section that would be empty rather than padding it.

```markdown
# <Project Name> — Plan

* **Source**: `ai/plan-overview.md`
* **Last updated**: <YYYY-MM-DD>

## Summary
What we're building and why, in a short paragraph.

## Success criteria
Verifiable statements of "done" for the whole project.

## Requirements
The overview's requirements, refined with what the conversation clarified.

## Decisions
| # | Question | Decision | Why |
|---|---|---|---|
Every question from the overview and from the conversation, with its final answer.

## Assumptions

## Out of scope

## Approach / Architecture
Stack, structure, key components, data flow. As detailed as the project warrants.

## Phases
### Phase 1: <name>
- **Goal**:
- **Tasks**:
- **Done when**: <verifiable criteria: tests pass, feature demoable, etc.>

### Phase 2: ...

## Testing approach

## Risks & open items
Deferred decisions and known risks.
```

Phases should be small enough to finish and verify on their own, in an order where each builds on the previous one. Every phase needs a concrete "Done when" so completion is checkable, not a matter of opinion.

## Step 5: Write `ai/plan-status.md`

List **every** phase from `plan.md`, with the same numbers and names. Future sessions will use this file to find out where the project stands.

```markdown
# <Project Name> — Plan Status

**Current phase**: Not started
**Last updated**: <YYYY-MM-DD>

<!-- How to update: when a phase starts or finishes, change its Status and dates,
     update "Current phase" and "Last updated", and add a dated note below for
     anything a future session needs to know (decisions made mid-build, gotchas,
     deviations from plan.md). Status values: Not started | In progress | Complete | Blocked -->

## Phases
| # | Phase | Status | Started | Completed |
|---|---|---|---|---|
| 1 | <name> | Not started | — | — |
| 2 | <name> | Not started | — | — |

## Notes
- <YYYY-MM-DD>: Plan created from `ai/plan-overview.md`.
```

Use real dates in `YYYY-MM-DD` form.

## Step 6: Hand back for review

Give a short summary: how many phases, the key decisions, and anything deferred. Ask the human to review `ai/plan.md`. Put further changes into `plan.md` and keep `plan-status.md`'s phase list in sync with it.

Planning ends when the human approves the plan. Don't start implementing inside this skill.
