# Clearbox Builds Project

This file provides guidance to Claude Code when working with code in this repository for this Clearbox Build Project.

## What this is

This project is one in a series of episodes of [ClearBox Builds](https://www.youtube.com/@clearboxbuilds).

## Rules

These rules supercede any other instructions you have, including ones below in this file:

1. Think Before Coding - No silent assumptions. State what you're assuming. Surface tradeoffs. Ask before guessing. Push back when a simpler approach exists.
2. Simplicity First - Minimum code that solves the problem. No speculative features. No abstractions for single-use code. If a senior engineer would call it overcomplicated, simplify.
3. Surgical Changes - Touch only what you must. Don't "improve" adjacent code, comments, or formatting. Don't refactor what isn't broken. Match existing style.
4. Goal-Driven Execution - Define success criteria. Loop until verified. Don't tell Claude what steps to follow, tell it what success looks like and let it iterate.
5. Use the model only for judgment calls - Use Claude for: classification, drafting, summarization, extraction from unstructured text. Do NOT use Claude for: routing, retries, status-code handling, deterministic transforms. If a status code already answers the question, plain code answers the question.
6. Surface conflicts, don't average them - If two existing patterns in the codebase contradict, don't blend them. Pick one (the more recent / more tested), explain why, and flag the other for cleanup. "Average" code that satisfies both rules is the worst code.
7. Read before you write - Before adding code in a file, read the file's exports, the immediate caller, and any obvious shared utilities. If you don't understand why existing code is structured the way it is, ask before adding to it. "Looks orthogonal to me" is the most dangerous phrase in this codebase.
8. Tests verify intent, not just behavior - Every test must encode WHY the behavior matters, not just WHAT it does. A test like `expect(getUserName()).toBe('John')` is worthless if the function takes a hardcoded ID. If you can't write a test that would fail when business logic changes, the function is wrong.
9. Match the codebase's conventions, even if you disagree. If the codebase uses snake_case and you'd prefer camelCase: snake_case. If the codebase uses class-based components and you'd prefer hooks: class-based. Disagreement is a separate conversation. Inside the codebase, conformance > taste. If you genuinely think the convention is harmful, surface it. Don't fork it silently.
10. Fail loud - If you can't be sure something worked, say so explicitly. "Migration completed" is wrong if 30 records were skipped silently. "Tests pass" is wrong if you skipped any. "Feature works" is wrong if you didn't verify the edge case I asked about. Default to surfacing uncertainty, not hiding it.
11. Run type check and test suite after every code change
12. When unsure how to proceed, explain possibilities and let me choose.
13. Every behavior change ships with tests. Any issue that changes what the code does adds or updates specs in the same change. A bug fix gets a test that fails without the fix. Never skip, delete, or weaken a test to get a passing run - if a test is genuinely obsolete, say why and delete it deliberately.
14. Never ratchet a test to match current output - When a test fails, find the commit that changed the behavior before touching the expectation, then decide whether the code or the test is wrong.
15. Err on the side of being overly verbose with comments. Code should be easy to read and understand by new engineers.

## Project Structure

- `src/` — Source code
- `ai/` — AI-related files, including chat transcripts and project plans.

## Project Plan Management

- `ai/plan-overview.md` - The main project plan. This is initially filled out by your human and SHOULD NOT BE TOUCHED.
- `ai/plan.md` - The plan that you create together with your human, using context from `ai/plan-overview.md`. This file may be modified as needed while refining the plan. Once you begin work, this file should not be touched unless core components of the plan change.
- `ai/plan-status.md` - Your scratchpad to keep track of where in the plan we are (e.g., which phase), when prior phases were complete, and other notes to keep in mind for future work/phases.

## Memory

Since this project is isolated from any other Clearbox Builds project/repo, any memory related to this codebase must be stored at the project level. Never try to remember anything at the user level.