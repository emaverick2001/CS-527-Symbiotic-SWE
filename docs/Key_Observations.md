# Key Observations

Source run: `artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v3`

### **1. Key Observations (What patterns do we see?)**

1. **CEGF matches the best real-test success while adding logical correctness evidence**

   - Evidence:
     - Main ablation metrics: `artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v3/metrics.json`
     - `neural_cegf` resolves 3 of 7 tasks, matching `neural_slicing` and exceeding `neural_only` and `neural_solver`, which each resolve 2 of 7.
     - `neural_cegf` also records the highest logical correctness rate, 3 of 7, because its resolved patches are paired with solver outcomes.
   - Pattern:
     - Across the logic-heavy SymPy subset, CEGF is not only competitive on raw real-test success; it is the only high-performing condition that also produces solver-backed logical correctness evidence.
   - Transition:
     - This motivates analyzing whether the solver feedback improves patch quality directly, or whether the gains come from additional repair iterations and stronger feedback signals.

2. **Slicing alone is a strong ablation but lacks symbolic correctness evidence**

   - Evidence:
     - Main ablation metrics: `metrics.json`
     - `neural_slicing` also resolves 3 of 7 tasks, tying `neural_cegf` on real-test success.
     - However, `neural_slicing` has no solver coverage and therefore no logical correctness confirmations under the defined metric.
   - Pattern:
     - Impact slicing appears useful as a context-control mechanism for this subset, but by itself it does not provide the solver-backed evidence needed for the paper's logical correctness claim.
   - Transition:
     - This motivates separating the effect of better localization from the effect of symbolic verification in the discussion.

3. **Solver feedback is useful only when it is connected to a refinement loop**

   - Evidence:
     - Main ablation metrics: `metrics.json`
     - `neural_solver` reaches full solver coverage but resolves only 2 of 7 tasks.
     - `neural_solver` terminates with `solver_sat_no_feedback` on 2 tasks, while `neural_cegf` records 6 critique events and resolves 3 tasks.
   - Pattern:
     - Symbolic checking alone can detect counterexamples, but the benefit is limited when the system is not allowed to turn those counterexamples into repair feedback.
   - Transition:
     - This motivates analyzing the critique-generation step as the bridge between verification and improved repair behavior.

4. **The strongest methods solve overlapping but not identical tasks**

   - Evidence:
     - Per-task metrics: `artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v3/*/*/metrics.json`
     - `neural_cegf` resolves `sympy__sympy-15875`, `sympy__sympy-19346`, and `sympy__sympy-24539`.
     - `neural_slicing` resolves `sympy__sympy-17318`, `sympy__sympy-24213`, and `sympy__sympy-24539`.
     - `neural_only` resolves `sympy__sympy-19346` and `sympy__sympy-24213`.
   - Pattern:
     - Performance is not uniform across tasks. Different ablations succeed on different repair problems, suggesting that localization, solver checking, and feedback each help under different task conditions.
   - Transition:
     - This motivates a qualitative case-study comparison between tasks solved uniquely by slicing and tasks solved by CEGF.

5. **Patch application is no longer the dominant failure mode in the latest run**

   - Evidence:
     - Patch artifacts: `patch_manifest.json`
     - Error log: `errors.log`
     - `errors.log` contains only one syntax-check failure in the latest run.
     - Average patch-apply failures are below or near 1.0 for all conditions: `neural_solver` 0.29, `neural_only` 0.86, `neural_cegf` 0.86, and `neural_slicing` 1.00.
   - Pattern:
     - The latest run mostly reaches real test evaluation rather than failing early at patch application. Remaining failures are more often true test failures, budget exhaustion, solver feedback limitations, or one syntax error.
   - Transition:
     - This motivates shifting the analysis away from harness reliability and toward repair quality, feedback usefulness, and task-level limitations.

6. **CEGF improves effectiveness but increases model cost**

   - Evidence:
     - Efficiency metrics: `metrics.json`
     - `neural_cegf` has the highest average token usage, while `neural_solver` has the lowest average token usage among the symbolic conditions.
     - `neural_cegf` also has the highest tokens per success among the successful conditions.
   - Pattern:
     - Counterexample-guided repair improves the quality and evidentiary strength of successful patches, but it is more expensive because it performs additional feedback and refinement work.
   - Transition:
     - This motivates reporting effectiveness and efficiency together rather than treating success rate alone as the full result.

7. **A recurring non-method failure is old SymPy compatibility with the local Python runtime**

   - Evidence:
     - Test verdicts: `evaluation_results.jsonl`
     - `sympy__sympy-13031` repeatedly fails during test execution with imports from `collections` that are incompatible with the local Python 3.11 runtime.
   - Pattern:
     - Some failures reflect benchmark environment compatibility rather than the repair strategy itself. These cases should be marked carefully so they do not get overinterpreted as logical repair failures.
   - Transition:
     - This motivates a limitations note about local environment fidelity and historical package compatibility.

