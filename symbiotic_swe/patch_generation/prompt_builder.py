from __future__ import annotations

from typing import List, Optional

from symbiotic_swe.contracts import CanonicalTask, CritiqueContract


SYSTEM_PROMPT = """\
You are an expert software engineer specializing in logic-heavy Python bug fixes.
Your task is to produce a minimal, correct patch for the given bug.

Rules:
- Your ENTIRE response must be a single ```diff ... ``` code block. No text before or after it.
- Do not output multiple diff blocks. Output exactly one final patch.
- Make the smallest change necessary to fix the bug.
- Do not change imports, add comments, or reformat unrelated code.
- The patch must be a git-style unified diff that starts with `diff --git a/path b/path`.
- Include the correct file headers immediately after each `diff --git`: `--- a/path` and `+++ b/path`.
- Use only repository-relative paths that appear in the supplied source context.
- Base every hunk on the exact checked-out source shown in the prompt; do not invent or paraphrase context lines.
- Do not include source line-number prefixes in the patch.
- Hunk line counts in @@ -X,Y +X,Y @@ must exactly match the lines in the hunk.
- The diff must apply cleanly with `git apply`.
"""


def build_patch_prompt(
    task: CanonicalTask,
    context_source: str,
    iteration: int,
    critique: Optional[CritiqueContract] = None,
) -> List[dict]:
    messages: List[dict] = []

    task_block = f"""\
## Bug Report
{task.bug_description}

## Failing Tests
{chr(10).join(f'- {t}' for t in task.failing_tests)}

## Repository: {task.repo} @ {task.repo_commit}
"""

    context_block = f"""\
## Relevant Repository Code
The following snippets are copied from the checked-out repository at the task commit.
Use these exact lines as patch context.

```python
{context_source[:40_000]}
```
"""

    if iteration == 0 or critique is None:
        user_content = (
            task_block
            + '\n'
            + context_block
            + '\nProduce exactly one git-style unified diff patch that fixes the bug.'
        )
    else:
        user_content = (
            task_block
            + '\n'
            + context_block
            + f'\n## Symbolic Verifier Feedback (iteration {iteration})\n'
            + critique.short_text
            + '\n\nRefine your patch to address the above failure. '
            + 'Produce exactly one git-style unified diff that fixes both the original bug and the counterexample.'
        )

    messages.append({'role': 'user', 'content': user_content})
    return messages
