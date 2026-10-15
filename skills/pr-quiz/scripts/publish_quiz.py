#!/usr/bin/env python3
"""Render a multiple-choice quiz into a PR description.

Usage: publish_quiz.py <pr-number> <quiz.json> [--dry-run]

quiz.json:
{
  "questions": [
    {
      "question": "Why does X ...?",
      "options": ["correct option", "distractor", "distractor", "distractor"],
      "correct": 0,
      "explanation": "One or two sentences on why the correct option is right."
    }
  ]
}

Options are shuffled, lettered A-F and rendered as task-list checkboxes, so a
reviewer answers by ticking boxes. The answer key is stored base64-encoded in a
hidden HTML comment that the pr-quiz GitHub Action reads. Any existing quiz block
in the description is replaced, which gives the quiz a new id and resets the pass.
"""

import base64
import json
import random
import re
import secrets
import subprocess
import sys

START = "<!-- pr-quiz:start -->"
END = "<!-- pr-quiz:end -->"
LETTERS = "ABCDEF"


def load_quiz(path):
    with open(path, encoding="utf-8") as f:
        quiz = json.load(f)
    questions = quiz.get("questions") or []
    if not 1 <= len(questions) <= 10:
        sys.exit("Quiz needs between 1 and 10 questions.")
    for i, q in enumerate(questions, 1):
        options = q.get("options") or []
        if not 2 <= len(options) <= len(LETTERS):
            sys.exit(f"Question {i} needs between 2 and {len(LETTERS)} options.")
        if not isinstance(q.get("correct"), int) or not 0 <= q["correct"] < len(options):
            sys.exit(f"Question {i} has an invalid 'correct' index.")
        if not q.get("question") or not q.get("explanation"):
            sys.exit(f"Question {i} needs 'question' and 'explanation'.")
    return questions


def one_line(text):
    # The Action parses the quiz line by line, so each question and option must stay on one line.
    return " ".join(text.split())


def render(questions):
    quiz_id = secrets.token_hex(6)
    answers, explanations, lines = {}, {}, []

    for n, q in enumerate(questions, 1):
        order = list(range(len(q["options"])))
        random.shuffle(order)
        lines.append(f"**{n}. {one_line(q['question'])}**")
        lines.append("")
        for pos, original in enumerate(order):
            lines.append(f"- [ ] **{LETTERS[pos]})** {one_line(q['options'][original])}")
            if original == q["correct"]:
                answers[str(n)] = LETTERS[pos]
        lines.append("")
        explanations[str(n)] = q["explanation"].strip()

    key = json.dumps({"id": quiz_id, "answers": answers, "explanations": explanations})
    encoded = base64.b64encode(key.encode("utf-8")).decode("ascii")
    example = " ".join(f"{n}A" for n in answers)

    block = "\n".join([
        START,
        "## PR Quiz",
        "",
        "This PR can only be merged after a reviewer answers these questions about the changes.",
        "Tick exactly one answer per question. The result is posted as a comment once all questions are answered.",
        f"You can also answer with a single comment like `/answer {example}`.",
        "",
        *lines,
        f"<!-- pr-quiz-key:{encoded} -->",
        END,
    ])
    return quiz_id, block


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv
    if len(args) != 2:
        sys.exit(__doc__)
    pr, quiz_path = args

    quiz_id, block = render(load_quiz(quiz_path))

    if dry_run:
        print(block)
        return

    body = json.loads(gh("pr", "view", pr, "--json", "body"))["body"] or ""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(body):
        body = pattern.sub(lambda _: block, body)
    else:
        body = f"{body.rstrip()}\n\n{block}\n" if body.strip() else f"{block}\n"

    subprocess.run(["gh", "pr", "edit", pr, "--body-file", "-"], input=body, text=True, check=True)
    print(f"Quiz {quiz_id} published to PR #{pr}.")


if __name__ == "__main__":
    main()
