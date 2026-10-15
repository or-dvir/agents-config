---
name: pr-quiz
description: Add a multiple-choice quiz to a GitHub pull request that a reviewer must pass before the PR can be merged. The quiz tests understanding of the important decisions in this specific PR (system design, strategies like caching, retries or offline-first, architecture-level wiring, trade-offs, unusual choices), not code-level details or general programming knowledge. Use this skill right after creating a pull request with `gh pr create`, when the user runs `/pr-quiz` or `/pr-quiz <number>`, asks to "add a quiz to the PR", "regenerate the PR quiz", or "set up the PR quiz" in a repository.
---

# PR Quiz

Writes a multiple-choice quiz into a PR description, with each option as a task-list checkbox. A reviewer answers by ticking one box per question (or by commenting `/answer 1B 2D 3A`). A GitHub Action (`.github/workflows/pr-quiz.yml`) grades the answers, posts the result in a single comment that it updates in place, and sets the `pr-quiz` commit status. Branch protection that requires `pr-quiz` blocks the merge until someone passes.

This is a discipline tool, not a security boundary. The answer key sits base64-encoded in the PR description.

## 1. Find the PR

- If the user passed a number, use it.
- Otherwise use the PR for the current branch: `gh pr view --json number,title,baseRefName,headRefName,url`.
- If there's no PR, stop and say so. Don't create one unless the user asked for that.

## 2. Check the repo is set up

Check whether `.github/workflows/pr-quiz.yml` exists on the default branch:

```bash
gh api "repos/{owner}/{repo}/contents/.github/workflows/pr-quiz.yml" --silent && echo present
```

If it's missing, tell the user and offer to add it from `assets/pr-quiz.yml` in this skill's directory. Point out that:
- The workflow must be merged into the **default branch** first. `issue_comment` workflows always run from there, so the `/answer` fallback won't work before that.
- The merge is only blocked if branch protection or a ruleset on the default branch requires the `pr-quiz` status check. On private repos that needs a paid GitHub plan.

Don't skip writing the quiz because of this. The quiz is still useful once the setup lands.

## 3. Understand the change

- Read the full diff: `gh pr diff <number>`. For large diffs, also read the surrounding code of the key changed files so the questions are about how things connect, not only the changed lines.
- If this session wrote the code, use what you know from the conversation: the alternatives that were rejected, constraints, and trade-offs. These make the best questions, because the diff alone doesn't show them.

## 4. Write the questions

Number of questions by size of the change:
- Small (under ~150 changed lines, one concern): 3
- Medium: 4–5
- Large or cross-cutting: 6–7

The quiz checks that the reviewer understands the **important decisions** in this PR, the things they'd need to know to maintain it or to spot a wrong call. It doesn't check that they read every line.

Start by listing the decisions in the PR, then write one question per decision, most important first. Focus on:

- **System design decisions:** how responsibilities are split, which component owns what, where the source of truth lives, how parts communicate.
- **Strategies and mechanisms:** how a cross-cutting behavior works as a whole, such as the caching or offline-first strategy, how retries work and which failures they cover, how sync or conflict handling works, what happens on errors.
- **Wiring at the architecture level:** how the new pieces are connected and who creates and owns them, such as DI setup or object lifetimes and scopes.
- **Trade-offs and rejected alternatives:** why this approach was chosen over an obvious other one, and what it costs.
- **Anything unusual:** deviations from the codebase's normal patterns or from common practice, workarounds, and surprising behavior a future developer could trip over.
- **Blast radius:** which existing behavior changed, and which features or callers are affected.

Before keeping a question, check: could someone who understood the design but never read the function bodies answer it? If not, it's too low-level. Rewrite it at the level of the decision, or drop it.

Do not ask about:
- The internals of a single composable, function, or algorithm: how a UI component is laid out, how a list is filtered or sorted, local control flow.
- Exact constants or parameters, like delays, timeouts, or debounce values. Ask about the behavior and the reason behind it instead. For example, ask "which failures are retried, and why only those" rather than "what are the retry delays".
- Language or framework features, syntax, or general best practices.
- Naming, formatting, file locations, or trivial details.
- Anything someone could answer correctly without reading this PR.

Options:
- 4 options per question, exactly one defensibly correct.
- Distractors must be plausible to someone who only skimmed the PR: a reasonable alternative design, the old behavior before this PR, or a real alternative that was considered.
- Keep option lengths similar so the correct one doesn't stand out. Don't use "all of the above" or "none of the above".
- If you can't write a question with one clear correct answer, drop it.

Each question also gets a 1–2 sentence `explanation` of why the correct answer is right. It's shown to the reviewer after a wrong answer.

## 5. Publish

Write the quiz to a temp file in the scratchpad directory, in this format. Put the correct option anywhere; the script shuffles the options.

```json
{
  "questions": [
    {
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct": 0,
      "explanation": "..."
    }
  ]
}
```

Preview first, then publish:

```bash
python3 ~/.claude/skills/pr-quiz/scripts/publish_quiz.py <number> <quiz.json> --dry-run
python3 ~/.claude/skills/pr-quiz/scripts/publish_quiz.py <number> <quiz.json>
```

The script replaces an existing quiz block in the description. A new quiz gets a new id, so an earlier pass no longer counts and the PR is blocked until the new quiz is passed. Only regenerate when the user asks for it.

## 6. Report

Tell the user, briefly:
- the PR URL and how many questions were added,
- that a reviewer answers by ticking one box per question in the description,
- any missing setup from step 2.

Don't print the answers.
