#### **High-Level Pipeline + Low-level Pipeline**

- Describe the system as a sequence of stages
- Remember to first create most simplistic working system then build ontop of it

1. First high-level then low-level
   1. for high-level mention the core data manipulations + actions + key system components + deliverables for respective section
   2. for low-level mention key datastructures + add implementation details to key components/deliverables for respective section so that you can implement the simplistic working system
   3. Once MVP is built add more details, optimizations, etc
   4. Optionally later on mention run artifacts produced + what datapoints to log

---

##### **0. Setup**

###### **Key Components / Deliverables**

1. local code environment setup
2. Create top-level directories:
   - assets/
     - diagrams/
     - figures/
   - artifacts/
     - runs/
       - use this naming convention: {date}_{model}_{experiment}_{reward}_{seed}
       - each folder should contain:
         - config.yaml
         - metrics.json
         - rewards.csv
         - generated_samples_manifest.json
         - training_log.csv
         - errors.log
         - summary.md
     - checkpoints/
       - diffdock/
       - pepflow/
     - generated_samples/
       - diffdock/
       - pepflow/
     - rewards/
       - diffdock/
       - pepflow/
     - metrics/
       - diffdock/
       - pepflow/
     - logs/
       - training/
       - evaluation/
       - errors/
   - configs/
     - diffdock/
       - baseline.yaml
       - rerank_baseline.yaml
       - reward_filtering.yaml
       - posttraining.yaml
     - pepflow/
       - baseline.yaml
       - posttraining.yaml
     - global.yaml
   - src/
     - \_\_init\_\_.py
     - data/
       - loaders.py
       - validation.py
       - preprocessing.py
       - manifests.py
     - models/
       - diffdock_adapter.py
       - pepflow_adapter.py
     - utils/
       - run_logger.py
       - artifact_logger.py
       - error_logger.py
       - config.py
       - paths.py
       - seeds.py
       - io.py
     - generation/
       - generate_diffdock.py
       - generate_pepflow.py
       - sampling.py
     - rewards/
       - rmsd_reward.py
       - docking_reward.py
       - energy_reward.py
       - composite_reward.py
     - posttraining/
       - ddpo_trainer.py
       - dpo_trainer.py
       - reward_backprop.py
       - training_utils.py
     - pipeline/
       - run_baseline.py
       - run_posttraining.py
       - run_evaluation.py
       - run_full_experiment.py
   - data/
     - raw/
       - pdbbind/
       - pepflow/
     - processed/
       - diffdock/
         - manifests/
         - splits/
       - pepflow/
   - tests/
     - test_data_loading.py
     - test_reward_computation.py
     - test_rmsd.py
     - test_config_loading.py
     - test_artifact_logging.py
   - docs/
     - experiment_plan.md
   - notebooks/
     - 01_data_exploration.ipynb
     - 02_baseline_analysis.ipynb
     - 03_reward_diagnostics.ipynb
     - 04_results_visualization.ipynb
   - scripts/
     - setup_data.sh
     - run_diffdock_baseline.sh
     - run_diffdock_posttraining.sh
     - evaluate_diffdock.sh
     - run_all.sh
3. Follow [[Software Implementation Guide]] until 2. Working on the Frontend or 3. Working on the Backend
   1. Define your config system
      1. Create configs/global.yaml
      2. Create configs/baseline.yaml
      3. Create configs/reward_filtering.yaml
      4. Create configs/posttraining.yaml
   2. Implement config loading utilities
      1. Create src/utils/config.py
      2. Create a test tests/test_config_loading.py
   3. Define artifact naming + run directory creation
      1. Create src/utils/paths.py
      2. every run folder should follow {date}\_{model}\_{experiment}\_{reward}\_{seed}
      3. Performance Monitoring - Track:
         - generation time per sample
         - training step time
         - reward computation cost
   4. Define Artifact schemas
      1. Create src/utils/schemas.py and define input, output object schemas
   5. Build artifact Logging utilities
      1. Create src/utils/artifact_logger.py
      2. Define your first required artifacts
         - config.yaml
         - metrics.json
         - rewards.csv
         - generated_samples_manifest.json
         - errors.log
         - summary.md
      3. Implement run logger in src/utils/run_logger.py
      4. Create tests/test_artifact_logging.py
   6. Implement Seed Control
      1. Create src/utils/seeds.py
   7. Create a dry-run pipeline with fake data
      1. Create src/pipeline/run_baseline.py
      2. This should not call the actual pipeline yet but instead prove that your pipeline can:
         1. Load config
         2. Create run directory
         3. Create fake generated samples
         4. Create fake rewards
         5. Create fake metrics
         6. Save all artifacts
4. Write README + developer documentation 1. Include: - project overview - pipeline stages - setup instructions - how to run: - single task - benchmark - artifact structure 2. Add: - expected outputs - common failure cases

##### \*\*1. Data Processing + Task Loading

###### Key Components / Deliverables

1. Task Loader
   1. Create a Task Loader Module in `~/dataset/task_loader.py`
      1. Load benchmark entries from:
         - SWE-bench Verified subset
         - optional synthetic HumanEval bug tasks later
         1. Normalize benchmark row
         2. Validate missing_required_fields
         3. Extract raw fields from each task and populate `TaskObject`
            1. Validate required fields before further processing
            2. Skip or log malformed tasks
      2. Score tasks
         1. Score based on patch hits, text hits, negative text hits, negative patch hits, changed line count, changed file list, repo score, repo exclusions, patch size score
         2. Restrict to selected repositories if needed:
            - sympy
            - pandas
            - numpy
            - scikit-learn
            - matplotlib
         3. Apply logic-heavy heuristics:
            - patch modifies conditional logic or comparisons
            - issue text suggests edge cases / wrong logic / assertions
         4. Remove tasks with:
            - dependency changes
            - import fixes
            - config changes
            - large refactors
      3. Create task subsets:
         - smoke tasks
         - final evaluation tasks

##### 2. **Local Bug Localization + Context Extraction**

###### Key Components / Deliverables

- LocalContextSelector
  - avoid full repo-wide retrieval unless needed
  1.  Read 1 task from `smoke_tasks.jsonl` into `task`
  2.  Create main function `def localize_and_extract_context`
      1. Extract the underlying TaskObject:
         - task = candidate_task.raw
      2. Read key fields from TaskObject:
         - task.instance_id
         - task.repo
         - task.problem_statement
         - task.failing_tests
         - task.passing_tests
         - task.base_commit
         - task.source_path
         - task.execution_trace
      3. Build `LocalizationEvidence` with `def build_localization_evidence`
         1. Parse traceback from `problem_statement` with `def extract_traceback_evidence`
            - Write a helper that extracts:
              - file paths
              - line numbers
              - function names
              - exception location
            1. Search for traceback-like patterns, for example:
               1. `File "...", line N, in function_name`
               2. repo-relative file paths like `sympy/simplify/fu.py`
               3. function names like `_TR56`, `_f`
               4. exception class names like `TypeError`, `ZeroDivisionError`
            2. Extract and normalize:
               1. `traceback_files: tuple[str, ...]`
               2. `traceback_line_numbers: tuple[int, ...]`
               3. `traceback_functions: tuple[str, ...]`
               4. `error_types: tuple[str, ...]`
            3. If multiple traceback frames exist:
               1. keep them in order from outermost to innermost
               2. also mark the deepest frame as highest-priority localization evidence
            4. Store these in `LocalizationEvidence`.
            5. If no traceback is present:
               1. return empty tuples, not `None`
            6. Persist optional debug artifact:
               1. `artifacts/tasks/<instance_id>/traceback_evidence.json
         2. Extract Failing and passing Test Names from TaskObject with `def extract_test_evidence`
            1. Read:
               1. `task.failing_tests`
               2. `task.passing_tests`
            2. Normalize test names:
               1. strip whitespace
               2. remove duplicates
               3. preserve original order
            3. Add failing tests into `LocalizationEvidence.failing_test_names`.
            4. Optionally include `passing_tests` only if `include_passing_tests=True`.
         3. Extract issue text hints from `problem_statement` with `extract_issue_text_hints`
            1. Parse `TaskObject.problem_statement` for likely hint tokens:
               1. function names
               2. module names
               3. API names
               4. exception words
               5. symbolic/math expressions
               6. obvious identifiers in backticks or code fences
            2. Extract possible:
               1. symbol names
               2. mentioned file/module substrings
               3. suspicious expressions like `rv.exp < 0`
            3. Add these to:
               1. `LocalizationEvidence.mentioned_symbols`
               2. `LocalizationEvidence.mentioned_paths`
            4. Deduplicate while preserving order.
            5. Persist optional artifact:
               1. `artifacts/tasks/<instance_id>/issue_text_hints.json`
         4. Merge all extracted signals into one `LocalizationEvidence`.
         5. Ensure every field is populated with tuples, never `None`.
         6. Return a fully constructed `LocalizationEvidence`.
  3.  Generate localization candidates
  4.  If candidate list is empty or weak:
      1. Fallback Local scan
         - If the above are weak, do a small local scan:
           - grep-like symbol search
           - filename match
           - function name match
         1. Only run this if:
            1. traceback evidence is weak or absent
            2. candidate list is empty or low-confidence
         2. Fallback strategies:
            1. Filename match
               1. search for files whose path contains substrings from mentioned_paths
            2. Function name match
               1. grep-like search for symbol definitions matching mentioned_symbols
            3. String search in source
               1. search for suspicious expressions or keywords from issue text
            4. Test-to-source heuristic
               1. if a failing test file is known, infer same module / neighboring source file
            5. Produce LocalizationCandidates with weaker evidence labels like:
               1. "fallback_symbol_search"
               2. "fallback_filename_search"
               3. "fallback_issue_text_match"
  5.  Rank candidates by score and evidence strength.
      1. Score candidates using evidence weights:
         1. traceback file match: highest weight
         2. traceback function match: high weight
         3. failing test linkage: medium-high weight
         4. issue text symbol match: medium weight
         5. fallback matches: lower weight
      2. Prefer:
         1. smaller local regions
         2. directly implicated functions
         3. files appearing in traceback
      3. Penalize:
         1. very large files
         2. generic utility modules with weak evidence
      4. Sort descending by score.
      5. Keep:
         1. top-1 for normal pipeline
         2. top-3 for debugging artifacts if desired
      6. Persist ranking artifact:
         1. `artifacts/tasks/<instance_id>/localization_candidates.json`
  6.  Select best candidate
  7.  Extract `LocalizedRegion`
      1. Extract a small surrounding window
         1. Open `candidate.file_path` from the local repo.
         2. If `candidate.function_name` is known and can be located:
            1. extract the full enclosing function definition
         3. Else if `candidate.start_line` is known:
            1. extract a bounded window around the line:
               1. for example `line - 15` to `line + 15`
         4. If both are available:
            1. prefer enclosing function
            2. fallback to line window if function extraction fails
         5. Store the final snippet in:
            1. `LocalizedRegion.source_snippet`
         6. Also store:
            1. `primary_file`
            2. `primary_function`
            3. `line_start`
            4. `line_end`
            5. `selection_reason`
         7. Persist optional artifact:
            1. `artifacts/tasks/<instance_id>/localized_region.json`
  8.  Extract the failing test snippet(s) if available with `def locate_test_snippets`
      1. Traverse likely test files under the repo:
         1. prioritize paths containing:
            1. `tests/`
            2. `test_*.py`
      2. For each failing test name in `task.failing_tests`:
         1. search for definitions like:
            1. `def test_name(...):`
      3. If found:
         1. extract the enclosing test function body
         2. preserve exact source text
      4. Return a tuple of extracted test snippets.
      5. If a failing test cannot be found:
         1. log the missing test name
         2. continue without failing the pipeline
      6. Persist optional artifact:
         1. `artifacts/tasks/<instance_id>/failing_test_snippets.json`
  9.  Persist:
      - artifacts/tasks/<instance_id>/context_package.json
      - artifacts/tasks/<instance_id>/prompt_ready_context.txt
  10. Write debug artifacts

##### 3. **Prompt + Neural Proposal**

###### **Key Components / Deliverables**

1. [Key files to implement/algorithms/manipulations/components/modules]
   1. [Key functions to implement/Key considerations/Key behavior]
2. Prompt Builder
   - Role:
     - Construct structured prompts for the LLM using task + context + feedback
   - Input → Output:
     - Input:
       - Task
       - Context
       - optional Critique
       - optional previous Patch
     - Output:
       - Prompt
   - Interaction:
     - Feeds into Neural Patch Generator
     - Updated every iteration
   1. Build `ContextPackage`
      1. Use:
         1. `task.problem_statement`
         2. `localized_region.source_snippet`
         3. `failing_test_snippets`
         4. optional `helper_snippets`
      2. Build `prompt_ready_context` in a stable order:
         1. bug report / problem statement
         2. failing test names
         3. failing test snippet(s)
         4. localized source snippet
         5. optional helper snippet(s)
      3. Keep context minimal:
         1. do not include entire file unless necessary
         2. do not include unrelated passing tests by default
      4. Construct and return ContextPackage
   2. LLM generates candidate patch
3. Neural Patch Generator (LLM Agent)
   - Role:
     - Generate candidate patches using the LLM
   - Input → Output:
     - Input:
       - Prompt
     - Output:
       - Patch
   - Interaction:
     - Feeds into:
       - Patch Applier
       - Impact Slicer
     - Receives feedback via updated prompts

##### 4. **Patch Application**

- apply the candidate patch to an isolated working copy of the repository
- prepare patched code for validation

###### **Key Components / Deliverables**

1. Patch Applier
   - Role:
     - Apply candidate patches to a temporary working copy of the repository
   - Input → Output:
     - Input:
       - Patch
       - Task.repo_path
     - Output:
       - patched repository state
   - Interaction:
     - Feeds into:
       - Impact Slicer
       - optional test execution
     - Ensures isolation via per-task workspace

##### 5. **Impact Slicing**

- isolate the patched program region that should be analyzed
- identify relevant variables, predicates, and local conditions

1. Impact Slicer (Post-Patch Localization)
   - Role:
     - Identify the program region affected by the patch for analysis
   - Input → Output:
     - Input:
       - patched code
       - RepoIndex
       - Patch
     - Output:
       - ProgramSlice
   - Interaction:
     - Feeds into Constraint Extractor
     - Reduces symbolic reasoning scope

###### **Key Components / Deliverables**

1. [Key files to implement/algorithms/manipulations/components/modules]
   1. [Key functions to implement/Key considerations/Key behavior]

##### 6. **Constraint Extraction**

- convert the sliced patched code into symbolic / logical constraints
- extract:
  - domain assumptions
  - path conditions
  - postconditions / expected behavior

###### **Key Components / Deliverables**

1. Constraint Extractor
   - Role:
     - Convert program behavior into a formal symbolic representation
   - Input → Output:
     - Input:
       - ProgramSlice
     - Output:
       - SymbolicProblem
   - Interaction:
     - Feeds into Symbolic Verifier
     - Encodes logic for solver reasoning

##### 7. **Symbolic Verification**

- run the solver on the patched local region
- determine whether there exists a violating input or invalid logical condition

###### **Key Components / Deliverables**

1. Symbolic Verifier (Solver Engine)
   - Role:
     - Check whether the patch satisfies logical constraints
   - Input → Output:
     - Input:
       - SymbolicProblem
     - Output:
       - SolverResult (sat / unsat / unknown / timeout)
   - Interaction:
     - If sat → passes to Counterexample Generator
     - If unsat → signals termination

##### 8. **Counterexample Generation**

- if the solver finds a violation, convert it into a concrete failing input or failing logical condition

###### **Key Components / Deliverables**

1. [Key files to implement/algorithms/manipulations/components/modules]
   1. [Key functions to implement/Key considerations/Key behavior]
2. Counterexample Generator
   - Role:
     - Convert solver output into a concrete failing input
   - Input → Output:
     - Input:
       - SolverResult
     - Output:
       - Counterexample
   - Interaction:
     - Feeds into Feedback Generator
     - Bridges symbolic → concrete domain

##### 9. **Feedback Transformation**

- convert the symbolic failure into a concise natural-language critique for the LLM

###### **Key Components / Deliverables**

1. [Key files to implement/algorithms/manipulations/components/modules]
   1. [Key functions to implement/Key considerations/Key behavior]
2. Feedback Generator (Critique Builder)
   - Role:
     - Translate counterexamples into natural-language critiques
   - Input → Output:
     - Input:
       - Counterexample
     - Output:
       - Critique
   - Interaction:
     - Feeds back into Prompt Builder
     - Drives the CEGF loop

##### 10. **Patch Refinement (CEGF Loop)**

- feed the critique back into the next prompt
- generate a refined patch
- repeat verification and refinement as needed

###### **Key Components / Deliverables**

1. [Key files to implement/algorithms/manipulations/components/modules]
   1. [Key functions to implement/Key considerations/Key behavior]
2. Iteration Controller (CEGF Loop Manager)
   - Role:
     - Manage iterative refinement and termination conditions
   - Input → Output:
     - Input:
       - IterationState
       - SolverResult
     - Output:
       - updated IterationState
       - final termination decision
   - Interaction:
     - Coordinates:
       - patch generation
       - symbolic verification
       - feedback loop
     - Enforces:
       - max iterations
       - convergence criteria

##### 11. **Termination / Evaluation**

- Current status:
  - implemented at the harness level
  - still needs real smoke runs, dev ablation runs, and final evaluation runs
  - next work is experimental validation, not more scaffold work
- Goal:
  - decide whether a generated patch actually resolves the SWE-bench task
  - use real tests as the final authority when available
  - record termination reasons so failed runs can be debugged systematically
  - aggregate results across experiment conditions

###### Datastructures

1. TestSuiteResult

   - stores the result of running one pytest group
   - examples:
     - `FAIL_TO_PASS`
     - `PASS_TO_PASS`

   ```python
   class TestSuiteResult(BaseModel):
       name: str
       tests: list[str]
       command: list[str]
       returncode: int | None
       passed: bool | None
       duration_ms: int
       stdout: str
       stderr: str
       error: str | None
   ```

2. TestEvaluationResult

   - stores the full test verdict for one patched task at one iteration

   ```python
   class TestEvaluationResult(BaseModel):
       task_id: str
       iteration: int
       resolved: bool
       evaluated: bool
       fail_to_pass: TestSuiteResult
       pass_to_pass: TestSuiteResult
       duration_ms: int
       error: str | None
   ```

3. RunMetrics

   - stores one task result for one experiment condition

   ```python
   class RunMetrics(BaseModel):
       task_id: str
       run_id: str
       condition: str
       success: bool
       termination_reason: str
       total_iterations: int
       total_prompt_tokens: int
       total_completion_tokens: int
       total_duration_ms: int
       solver_duration_ms: int
       solver_outcomes: dict[str, int]
       patch_apply_failures: int
       repeated_counterexamples: int
       test_evaluated: bool
       test_resolved: bool
       final_test_evaluation: TestEvaluationResult | None
       iterations: list[IterationRecord]
   ```

###### Key Components / Deliverables

1. Evaluation Engine

   - Files:
     - `symbiotic_swe/evaluation/test_runner.py`
     - `symbiotic_swe/evaluation/metrics.py`
     - `symbiotic_swe/orchestration/loop.py`
     - `symbiotic_swe/orchestration/runner.py`
   - Role:
     - run `FAIL_TO_PASS` tests on the patched repo
     - run `PASS_TO_PASS` tests to catch regressions
     - convert pytest results into structured records
     - set `RunMetrics.success` from real test resolution when tests are available
     - aggregate per-condition metrics for the report

2. Termination Controller

   - stop cases:
     1. `tests_resolved`
        - patch applied successfully
        - all `FAIL_TO_PASS` tests pass
        - all available `PASS_TO_PASS` tests pass
        - this is the strongest success signal
     2. `tests_failed`
        - patch applied, but target tests or regression tests failed
        - this is the main failure to inspect during smoke runs
     3. `tests_failed_after_slicing`
        - patch applied and impact slicing completed
        - real tests still failed
        - mainly diagnoses the `neural_slicing` condition
     4. `tests_failed_after_solver`
        - solver did not block the patch
        - real tests still failed
        - indicates symbolic coverage is too weak or not modeling the relevant behavior
     5. `solver_sat_no_feedback`
        - solver found a counterexample in `neural_solver`
        - no feedback is sent because this ablation intentionally disables CEGF
     6. `budget_exhausted`
        - max iterations reached before finding a resolved patch
     7. patch apply failure
        - generated diff did not apply cleanly
        - counted in `patch_apply_failures`
        - inspect `patch_manifest.json` and `errors.log`
     8. solver non-decision
        - `not_applicable`, `unknown`, `timeout`, `error`, or `no_slice`
        - use real test results as the final authority when available

3. Test Execution Algorithm

   1. Receive:
      - CanonicalTask
      - patched working copy path
      - current iteration number
   2. Read test targets:
      - `FAIL_TO_PASS` from `task.failing_tests`
      - `PASS_TO_PASS` from `task.oracle.spec["passing_tests"]` when present
   3. Run target tests:

      ```bash
      python -m pytest -q <FAIL_TO_PASS tests>
      ```

   4. Run regression tests:

      ```bash
      python -m pytest -q <PASS_TO_PASS tests>
      ```

   5. Capture:
      - command
      - return code
      - pass/fail status
      - duration
      - stdout tail
      - stderr tail
      - timeout or execution error
   6. Mark `resolved=True` only if:
      - at least one `FAIL_TO_PASS` test exists
      - all `FAIL_TO_PASS` tests pass
      - all available `PASS_TO_PASS` tests pass
   7. Attach the result to:
      - IterationRecord
      - RunMetrics.final_test_evaluation
      - `evaluation_results.jsonl`

4. Run Artifacts To Inspect

   - `metrics.json`
     - aggregate result by condition
     - use this for tables and headline numbers
   - `evaluation_results.jsonl`
     - true test verdicts
     - inspect this first when a run looks suspicious
   - `patch_manifest.json`
     - patch parse/apply status
     - target files
     - patch errors
   - `solver_results.jsonl`
     - solver statuses
     - counterexample-related findings
   - `stage_timings.csv`
     - per-task and per-stage timing
   - `errors.log`
     - human-readable failures to triage
   - `summary.md`
     - short run summary for lab notes

5. Metrics To Report

   - per condition:
     - `n_tasks`
     - `bug_resolution_rate`
     - `test_evaluated_tasks`
     - `test_resolution_rate`
     - `avg_iterations`
     - `avg_tokens`
     - `tokens_per_success`
     - `avg_duration_ms`
     - `solver_overhead_fraction`
     - `avg_patch_apply_failures`
     - `repeated_counterexample_rate`
     - `solver_outcomes`
     - `termination_reasons`
   - comparisons:
     - `neural_only` vs `neural_cegf`
     - `neural_slicing` vs `neural_solver`
     - model provider/model comparisons, for example `openai:gpt-5.4-mini` vs `openai:gpt-5.5`
     - solver overhead vs test-resolution improvement
     - counterexample feedback usefulness

###### Current Phase: Real-Run Validation

1. Phase 11A: Run smoke experiments

   - Purpose:
     - verify the harness works on real prepared tasks
     - verify the LLM API path works
     - verify generated patches can apply
     - verify pytest can execute inside materialized repos
     - verify artifacts are written correctly
   - Preconditions:
     - prepared smoke tasks exist under `data/prepared/prepared/smoke`
     - local task workspaces exist under `data/prepared/workspaces/{task_id}/repo`
     - each local task workspace is a git checkout at the task's `repo_commit`
     - one model API key is set:
       - `OPENAI_API_KEY` for `--provider openai`
       - `ANTHROPIC_API_KEY` for `--provider anthropic`
   - Materialize or repair smoke repositories:

     ```bash
     scripts/materialize_smoke_repos.sh
     ```

   - Dry-run materialization first:

     ```bash
     DRY_RUN=1 scripts/materialize_smoke_repos.sh
     ```

   - Force-repair one stale or empty task workspace:

     ```bash
     TASK_ID=sympy__sympy-20801 \
     FORCE=1 \
     scripts/materialize_smoke_repos.sh
     ```

   - Preflight command:

     ```bash
     uv run symbiotic-swe smoke \
       --preflight-only \
       --prepared-dir data/prepared/prepared/smoke \
       --output-dir artifacts/runs/manual_smoke_test \
       --provider openai \
       --model gpt-5.4-mini \
       --max-iterations 1
     ```

   - Run command:

     ```bash
     scripts/run_smoke.sh
     ```

   - One-task artifact/protocol check:

     ```bash
     scripts/run_one_task_smoke.sh
     ```

   - One-task preflight only:

     ```bash
     PREFLIGHT_ONLY=1 scripts/run_one_task_smoke.sh
     ```

   - Useful one-task overrides:

     ```bash
     TASK_ID=sympy__sympy-20801 \
     CONDITIONS=neural_cegf \
     MAX_ITERATIONS=1 \
     scripts/run_one_task_smoke.sh
     ```

   - Equivalent direct command:

     ```bash
     uv run symbiotic-swe smoke \
       --task-id sympy__sympy-20801 \
       --prepared-dir data/prepared/prepared/smoke \
       --output-dir artifacts/runs/manual_smoke_test \
       --conditions neural_only,neural_slicing,neural_solver,neural_cegf \
       --provider openai \
       --model gpt-5.4-mini \
       --max-iterations 1
     ```

   - What to inspect first:
     1. `artifacts/runs/manual_smoke_test/errors.log`
     2. `artifacts/runs/manual_smoke_test/evaluation_results.jsonl`
     3. `artifacts/runs/manual_smoke_test/patch_manifest.json`
     4. `artifacts/runs/manual_smoke_test/metrics.json`
   - Smoke run success criteria:
     - command completes without crashing
     - every task has a metrics record
     - every task has either a test result or a clear non-evaluation reason
     - patch failures are captured instead of crashing the run
     - run artifacts pass structure validation

2. Phase 11A.1: Run model smoke ablations

   - Purpose:
     - compare software repair agents before committing to expensive dev/final runs
     - test whether coding-specialized models improve patch apply rate or test resolution
     - separate model quality failures from solver/feedback failures
   - Script:

     ```bash
     scripts/run_model_ablation.sh
     ```

   - Default model comparison:
     - `openai:gpt-5.4-mini`
     - `openai:gpt-5.5`
     - `openai:gpt-5.3-codex`
   - Anthropic can still be tested later by overriding `MODELS` with an `anthropic:<model>` entry and setting `ANTHROPIC_API_KEY`.

   - Useful environment overrides:

     ```bash
     PREPARED_DIR=data/prepared/prepared/smoke \
     CONDITIONS=neural_only,neural_cegf \
     MAX_ITERATIONS=1 \
     OUTPUT_ROOT=artifacts/runs/model_ablation \
     MODELS="openai:gpt-5.4-mini openai:gpt-5.5 openai:gpt-5.3-codex" \
     scripts/run_model_ablation.sh
     ```

   - What to compare:
     - patch parse failure rate
     - patch apply failure rate
     - test resolution rate
     - average tokens
     - tokens per success
     - whether CEGF improves more for one model than another
   - Keep model ablations small at first:
     - smoke split first
     - `max_iterations=1` first
     - only run dev model ablations after smoke artifacts are interpretable

3. Phase 11B: Debug real test execution failures

   - Common failure classes:
     1. patch generation failure
        - symptoms:
          - empty diff
          - malformed diff
          - no target files
        - inspect:
          - `patch_manifest.json`
          - patch raw text in per-task metrics
        - likely fix:
          - tighten prompt format
          - improve diff parser
     2. patch apply failure
        - symptoms:
          - patch parse ok but apply fails
          - rejected hunks
        - inspect:
          - `patch_manifest.json`
          - `errors.log`
        - likely fix:
          - improve context selection
          - include more exact file context in prompt
          - reduce model output formatting drift
     3. test collection failure
        - symptoms:
          - pytest cannot find tests
          - import errors before target test runs
        - inspect:
          - `evaluation_results.jsonl`
          - `stderr` field for the failing suite
        - likely fix:
          - normalize SWE-bench test target names
          - add repo-specific test command handling
          - ensure repo dependencies are installed or documented as unsupported
     4. environment failure
        - symptoms:
          - missing dependencies
          - Python version mismatch
          - package import failures
        - inspect:
          - `stderr`
          - `errors.log`
        - likely fix:
          - materialize repo environment more faithfully
          - cache/install dependencies per repo
     5. solver/test disagreement
        - symptoms:
          - solver returns `unsat`
          - tests still fail
        - inspect:
          - `solver_results.jsonl`
          - `evaluation_results.jsonl`
        - likely fix:
          - document as symbolic coverage limitation
          - improve constraint extraction or solver heuristics later
   - Debugging order:
     1. make the run complete without crashing
     2. make test execution reliable
     3. reduce patch apply failures
     4. inspect solver/test disagreements
     5. only then tune model prompts or symbolic heuristics

4. Phase 11C: Run dev ablations

   - Purpose:
     - compare all four experiment conditions before final evaluation
     - use dev results to debug and calibrate the pipeline
   - Command:

     ```bash
     uv run symbiotic-swe ablation \
       --prepared-dir data/prepared/prepared/dev \
       --output-dir artifacts/runs/dev_ablation \
       --max-iterations 3
     ```

   - Conditions to compare:
     1. `neural_only`
        - baseline LLM patch generation with test evaluation
     2. `neural_slicing`
        - tests whether slicing adds overhead or changes failure modes
     3. `neural_solver`
        - tests solver checking without feedback
     4. `neural_cegf`
        - full symbolic-feedback loop
   - Dev ablation success criteria:
     - every condition runs on the same task set
     - `metrics.json` includes all four conditions
     - test resolution rates are computed
     - termination reasons are interpretable
     - at least a few representative success and failure examples can be explained

5. Phase 11D: Run final evaluation

   - Purpose:
     - produce the final held-out results for the project/report
   - Command:

     ```bash
     uv run symbiotic-swe benchmark \
       --prepared-dir data/prepared/prepared/final_eval \
       --output-dir artifacts/runs/final_eval \
       --conditions neural_only,neural_slicing,neural_solver,neural_cegf \
       --max-iterations 3
     ```

   - Rule:
     - do not tune the system on final-eval failures after looking at the results
   - Final deliverables:
     - aggregate results table from `metrics.json`
     - qualitative examples from:
       - `evaluation_results.jsonl`
       - `patch_manifest.json`
       - `solver_results.jsonl`
     - short limitations section explaining:
       - solver coverage limitations
       - dependency/test environment failures
       - patch apply failures
       - cases where feedback helped or hurt

6. Completion Criteria For Section 11

   - MVP complete:
     - evaluation harness exists
     - tests can be run on patched working copies
     - metrics and artifacts are written
   - Current next milestone:
     - smoke run completes on real prepared tasks
     - real failures are categorized and debugged
   - Dev-ready:
     - all four ablation conditions run on dev tasks
     - results are comparable across conditions
   - Project complete:
     - final evaluation run completed
     - results and limitations are written up
     - artifacts are reproducible from commands in this section
