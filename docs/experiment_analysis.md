## 6. Analysis

This section analyzes the held-out SymPy final-evaluation run:

`artifacts/runs/final_eval_gpt_5_3_codex_sympy_real_tests`

The run used `gpt-5.3-codex`, `max_iterations=3`, four ablation conditions, and 14 explicit SymPy SWE-bench tasks from `data/prepared/prepared/final_eval`. The analysis below treats this run as the main final result. Development runs should be used as tuning/validation evidence, not as the primary final claim.

### 6.1 Evaluation Snapshot

| Condition | Resolved Tasks | Real-Test Success Rate | Logical Correctness Rate | Test-Evaluated Tasks | Avg. Iterations | Avg. Tokens | Tokens / Success | Avg. Runtime | Avg. Patch Apply Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `neural_only` | 2 / 14 | 14.3% | 0.0% | 11 / 14 | 1.50 | 16,746.6 | 7,734.0 | 8.6s | 0.71 |
| `neural_slicing` | 3 / 14 | 21.4% | 0.0% | 11 / 14 | 1.71 | 21,835.2 | 15,435.3 | 11.2s | 0.93 |
| `neural_solver` | 3 / 14 | 21.4% | 21.4% | 9 / 14 | 1.79 | 21,002.4 | 12,984.0 | 10.1s | 1.00 |
| `neural_cegf` | 5 / 14 | 35.7% | 35.7% | 11 / 14 | 2.50 | 30,025.9 | 17,420.8 | 16.6s | 1.07 |

Source: `artifacts/runs/final_eval_gpt_5_3_codex_sympy_real_tests/metrics.json`.

### 6.2 Key Observations

1. **CEGF is the strongest held-out final-evaluation condition.**
   - Evidence: `neural_cegf` resolves 5 of 14 tasks, compared with 2 of 14 for `neural_only`, 3 of 14 for `neural_slicing`, and 3 of 14 for `neural_solver`.
   - Pattern: On the final SymPy subset, counterexample-guided feedback improves benchmark-facing real-test success over the neural baseline and over solver-checking without feedback.
   - Transition: This supports the main hypothesis that symbolic feedback is most useful when it is converted into repair guidance, not merely used as a verifier.

2. **Logical correctness improves only when solver evidence is part of the condition.**
   - Evidence: `neural_cegf` reaches a 35.7% logical correctness rate, while `neural_solver` reaches 21.4%. The non-symbolic conditions report 0.0% under this solver-backed metric because they do not generate solver confirmations.
   - Pattern: The solver-backed variants provide an additional correctness signal beyond test passing. CEGF is strongest because it both verifies patches and uses counterexamples to guide later attempts.
   - Transition: This motivates reporting real-test success and logical correctness separately rather than treating test success as the only effectiveness metric.

3. **Solver checking without feedback is not enough.**
   - Evidence: `neural_solver` has the same real-test success rate as `neural_slicing` at 21.4%, but it terminates with `solver_sat_no_feedback` on 2 tasks and `tests_failed_after_solver` on 6 tasks.
   - Pattern: The solver can detect violations, but detection alone does not repair the program. Without critique feedback, solver findings can become a stopping condition rather than a path to improvement.
   - Transition: This isolates the value of the feedback transformation step in the full CEGF loop.

4. **The added feedback loop improves success but increases cost.**
   - Evidence: `neural_cegf` has the highest success rate, but also the highest average iterations, average tokens, tokens per success, and runtime.
   - Pattern: CEGF buys additional repaired tasks by spending more model calls and more feedback iterations. This is a correctness-cost tradeoff, not a free improvement.
   - Transition: Cost-normalized reporting is necessary because the best final-evaluation method is also the most expensive.

5. **Failures are no longer dominated by repository environment issues, but patch application remains a recurring bottleneck.**
   - Evidence: `environment_limited_tasks` is 0 for all conditions, but average patch-apply failures range from 0.71 to 1.07. The final `errors.log` contains repeated failed hunks in files such as `sympy/core/evalf.py`, `sympy/combinatorics/perm_groups.py`, `sympy/utilities/iterables.py`, and `sympy/polys/polytools.py`.
   - Pattern: The evaluation is reaching real repair behavior, but stale or inaccurate diffs still prevent some candidate patches from reaching test execution.
   - Transition: The main remaining systems limitation is patch robustness and context precision, not task materialization.

### 6.3 Per-Condition Task Outcomes

| Condition | Resolved Task IDs |
|---|---|
| `neural_only` | `sympy__sympy-13480`, `sympy__sympy-22714` |
| `neural_slicing` | `sympy__sympy-13480`, `sympy__sympy-14711`, `sympy__sympy-15809` |
| `neural_solver` | `sympy__sympy-13480`, `sympy__sympy-15809`, `sympy__sympy-21847` |
| `neural_cegf` | `sympy__sympy-13480`, `sympy__sympy-14711`, `sympy__sympy-15809`, `sympy__sympy-19495`, `sympy__sympy-21847` |

The methods solve overlapping but not identical task sets. `sympy__sympy-13480` is solved by every condition, which suggests it is within reach of the base neural repair loop. `sympy__sympy-19495` is solved only by `neural_cegf`, which makes it a useful candidate for a qualitative CEGF case study. `sympy__sympy-21847` is solved by both solver-enabled variants but not by `neural_only` or `neural_slicing`, which makes it useful for showing the value of symbolic checking.

### 6.4 Error Analysis

Overall, failures fall into three broad classes: unresolved patches that reach tests but fail, candidates blocked by patch application, and solver outcomes that do not translate into a successful repair within the three-iteration budget.

#### Error Taxonomy

| Failure Type | Pipeline Stage | Diagnostic Signal | Likely Cause | Evidence |
|---|---|---|---|---|
| Test-failing repair | Evaluation | `tests_failed`, `tests_failed_after_slicing`, or `tests_failed_after_solver` | The generated patch applies but does not satisfy the target behavior | `neural_only` records 9 `tests_failed`; `neural_slicing` records 8 `tests_failed_after_slicing`; `neural_solver` records 6 `tests_failed_after_solver` |
| Budget exhaustion | Repair loop | `budget_exhausted` | Three iterations are insufficient, often after repeated patch failures or repeated semantically wrong proposals | `neural_cegf` records 7 `budget_exhausted`; `neural_only`, `neural_slicing`, and `neural_solver` each record 3 |
| Patch application failure | Patch application | failed hunks in `errors.log`; positive `avg_patch_apply_failures` | Model-generated diffs do not match the exact checkout context | `avg_patch_apply_failures` is 0.71-1.07 across conditions |
| Solver finding without repair | Solver / feedback | `solver_sat_no_feedback` | Solver detects a counterexample but the ablation intentionally disables feedback | `neural_solver` records 2 `solver_sat_no_feedback` terminations |
| Weak or insufficient symbolic signal | Solver / constraint extraction | `tests_failed_after_solver` even after solver execution | The extracted slice or constraints do not fully model the semantic behavior needed by the tests | `neural_solver` and `neural_cegf` both include `tests_failed_after_solver` cases |

#### Root Causes

1. **Patch generation remains brittle against exact repository context.**
   - Violated assumption: The model can emit a patch whose hunk context matches the checked-out task repository.
   - Evidence pattern: Repeated `patch does not apply` and `fallback could not locate hunk` messages in `errors.log`.
   - Mitigation: Add stricter diff formatting, include more exact local file context, and keep tolerant patch application as a fallback.

2. **Symbolic checking needs feedback to improve repair.**
   - Violated assumption: Verification alone is enough to improve outcomes.
   - Evidence pattern: `neural_solver` detects counterexamples but does not outperform `neural_slicing`; it stops on `solver_sat_no_feedback`.
   - Mitigation: Prefer CEGF over solver-only checking when the goal is repair rather than diagnosis.

3. **The three-iteration budget is tight for harder final-evaluation tasks.**
   - Violated assumption: Most logic-heavy repairs can converge within a small fixed budget.
   - Evidence pattern: `neural_cegf` reaches the highest success rate but also has 7 `budget_exhausted` terminations.
   - Mitigation: Use adaptive iteration budgets when solver feedback continues to change the patch, or stop early only when repeated feedback is not changing model behavior.

4. **Local symbolic encodings do not cover all library semantics.**
   - Violated assumption: The patch-centered slice is sufficient to model the relevant behavior.
   - Evidence pattern: `tests_failed_after_solver` appears in solver-enabled conditions.
   - Mitigation: Expand constraints with test-derived expectations, richer type/domain facts, and targeted summaries for common SymPy objects.

### 6.5 Sensitivity and Robustness

The final run is robust enough to support a controlled SymPy-specific result, but it should not be generalized to all SWE-bench repositories. The strongest robustness property is environment stability: all conditions report 0 environment-limited tasks. The weakest properties are patch application stability and iteration-budget sensitivity.

| Sensitivity Dimension | Observed Pattern | Interpretation |
|---|---|---|
| Repository family | SymPy final tasks ran without environment-limited failures | Restricting to one stable logic-heavy repository reduces build noise and makes repair outcomes more meaningful |
| Iteration budget | CEGF uses 2.50 iterations on average and still records 7 budget-exhausted tasks | The full feedback loop benefits from multiple attempts and may be under-budgeted at `max_iterations=3` for harder tasks |
| Solver coverage | Solver-enabled variants cover 11 of 14 tasks | Symbolic analysis applies to most, but not all, final tasks |
| Patch formatting | All conditions have nonzero patch apply failures | Model output format and exact context remain a cross-cutting bottleneck |
| Method components | CEGF wins final-eval success, while solver-only does not | The feedback transformation is more important than solver invocation alone |

### 6.6 Cost Analysis

CEGF gives the best final-evaluation success rate, but it is also the most expensive condition. Compared with `neural_only`, CEGF increases real-test success from 14.3% to 35.7%, but average tokens rise from 16.7k to 30.0k and average runtime rises from 8.6s to 16.6s.

| Condition | Real-Test Success | Avg. Tokens | Tokens / Success | Avg. Runtime | Avg. Iterations |
|---|---:|---:|---:|---:|---:|
| `neural_only` | 14.3% | 16,746.6 | 7,734.0 | 8.6s | 1.50 |
| `neural_slicing` | 21.4% | 21,835.2 | 15,435.3 | 11.2s | 1.71 |
| `neural_solver` | 21.4% | 21,002.4 | 12,984.0 | 10.1s | 1.79 |
| `neural_cegf` | 35.7% | 30,025.9 | 17,420.8 | 16.6s | 2.50 |

The cost-performance conclusion is conditional. If the goal is the highest number of final held-out repairs, CEGF is worthwhile on this run. If the goal is cheapest successful repair, neural-only has lower tokens per success but solves fewer tasks. The paper should therefore avoid saying that CEGF is more efficient overall. The supported claim is narrower: CEGF improves final-evaluation success and solver-backed logical correctness at increased token and runtime cost.

### 6.7 Mechanistic Explanation

1. **Counterexample feedback helps convert verification into repair.**
   - Observed behavior: `neural_cegf` outperforms `neural_solver` by 2 additional resolved tasks.
   - Responsible component: Natural-language critique generated from symbolic verification results.
   - Explanation: The solver-only condition can identify violations but cannot use them to revise the patch. CEGF adds a repair channel that sends the violation back into the model context.
   - Evidence: `neural_solver` records `solver_sat_no_feedback`, while `neural_cegf` records 12 critique events and 5 resolved tasks.

2. **Slicing helps, but it is not sufficient for the hardest final tasks.**
   - Observed behavior: `neural_slicing` improves over `neural_only`, but does not match `neural_cegf`.
   - Responsible component: Impact slicing without solver feedback.
   - Explanation: Slicing likely improves context focus and reduces irrelevant edits, but it does not provide a semantic counterexample when the candidate patch is logically incomplete.
   - Evidence: `neural_slicing` resolves 3 tasks, while `neural_cegf` resolves 5.

3. **Patch robustness gates downstream evaluation.**
   - Observed behavior: Some tasks never reach test evaluation because repeated patch attempts fail or exhaust the budget.
   - Responsible component: Patch generation and patch application.
   - Explanation: Even a semantically promising patch cannot be evaluated if the diff does not apply to the exact repository checkout.
   - Evidence: `errors.log` contains repeated failed hunks, and all conditions have nonzero average patch apply failures.

4. **Logical correctness is not identical to raw test success.**
   - Observed behavior: CEGF and solver variants report logical correctness because solver evidence is recorded; non-symbolic variants do not.
   - Responsible component: Symbolic verification stage.
   - Explanation: Real tests determine benchmark resolution, but solver checks add an orthogonal diagnostic signal about whether the local symbolic specification found a counterexample.
   - Evidence: `neural_cegf` has both the highest real-test success rate and highest logical correctness rate.

### 6.8 Key Takeaways

1. **The final evaluation supports the core CEGF hypothesis, with scope limits.**
   - Evidence basis: `neural_cegf` resolves 5 of 14 final SymPy tasks, outperforming all other ablations.
   - Actionable implication: Use the final-eval run as the main result, but describe it as held-out SymPy evidence rather than broad SWE-bench-wide proof.

2. **Feedback is the important symbolic component, not solver invocation alone.**
   - Evidence basis: `neural_solver` resolves 3 tasks, while `neural_cegf` resolves 5 and records critique events.
   - Actionable implication: Future work should improve critique quality and feedback memory rather than only improving solver coverage.

3. **The method trades higher correctness for higher cost.**
   - Evidence basis: CEGF has the best success and logical correctness, but also the highest tokens, runtime, and iterations.
   - Actionable implication: Present cost and success together. Do not claim CEGF is universally cheaper.

4. **Patch application remains a first-order systems limitation.**
   - Evidence basis: All conditions have nonzero patch apply failures and `errors.log` includes repeated failed hunks.
   - Actionable implication: Better diff repair and exact context retrieval are likely high-impact engineering improvements.

5. **The current sample is credible for descriptive analysis, not statistical generalization.**
   - Evidence basis: The final set contains 14 tasks from one repository family.
   - Actionable implication: Report the result as a controlled held-out logic-heavy SymPy study. If time permits, add confidence intervals or a paired task-level comparison, but avoid overclaiming statistical significance.

### 6.9 Recommended Tables and Figures

1. **Main Final-Evaluation Table**
   - Use the table in Section 6.1.
   - Caption: Held-out SymPy final-evaluation results across four ablation conditions using `gpt-5.3-codex` and `max_iterations=3`.

2. **Resolved Task Matrix**
   - Rows: the 14 final task IDs.
   - Columns: `neural_only`, `neural_slicing`, `neural_solver`, `neural_cegf`.
   - Cell: checkmark if resolved.
   - Purpose: Show that methods solve different task subsets.

3. **Cost vs Success Bar Chart**
   - X-axis: method condition.
   - Left Y-axis: real-test success rate.
   - Right Y-axis or second panel: tokens per success.
   - Purpose: Show the CEGF correctness-cost tradeoff.

4. **Failure Mode Taxonomy Table**
   - Use Section 6.4.
   - Purpose: Make limitations concrete and separate repair failures from environment failures.

5. **CEGF Case Study Trace**
   - Recommended candidates: `sympy__sympy-19495` because it is solved by `neural_cegf` but not by the other conditions, or `sympy__sympy-21847` because both solver-enabled variants solve it while non-symbolic variants do not.
   - Purpose: Show how symbolic evidence changes the repair trajectory.
